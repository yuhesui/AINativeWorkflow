#!/usr/bin/env python3
"""Apply a single JSON schema migration to a SQLite database.

The tool deliberately uses only the Python standard library so it can be run
with ``uv run --project /app migration_tool.py ...`` without installation.
"""

from __future__ import annotations

import copy
import heapq
import json
import math
import re
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SUPPORTED_TYPES = {"INTEGER", "TEXT", "REAL", "BLOB", "TIMESTAMP"}


class MigrationError(Exception):
    """An expected user-facing migration failure."""


class DependencyCycleError(MigrationError):
    """A dependency cycle with the concrete graph path for JSONL reporting."""

    def __init__(self, cycle: list[int]):
        self.cycle = cycle
        super().__init__(f"circular dependency detected: cycle {cycle}")


def schema_error(message: str) -> MigrationError:
    return MigrationError(f"invalid migration schema: {message}")


def quote_identifier(identifier: str) -> str:
    """Quote a previously validated SQLite identifier defensively."""
    return '"' + identifier.replace('"', '""') + '"'


def require_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise schema_error(f"{context} must be an object")
    return value


def require_string(container: dict[str, Any], field: str, context: str) -> str:
    if field not in container:
        raise schema_error(f"{context} missing required field '{field}'")
    value = container[field]
    if not isinstance(value, str):
        raise schema_error(f"{context} field '{field}' must be a string")
    return value


def validate_identifier(identifier: str, context: str) -> None:
    if not IDENTIFIER_RE.fullmatch(identifier):
        raise schema_error(f"{context} '{identifier}' is not a valid SQLite identifier")


def require_optional_bool(column: dict[str, Any], field: str, context: str) -> bool:
    value = column.get(field, False)
    # bool is deliberately checked exactly: values such as 0 or "false" are
    # ambiguous in a JSON migration and should not silently change a schema.
    if not isinstance(value, bool):
        raise schema_error(f"{context} field '{field}' must be a boolean")
    return value


def validate_column(value: Any, context: str) -> dict[str, Any]:
    column = require_object(value, context)
    name = require_string(column, "name", context)
    column_type = require_string(column, "type", context)
    validate_identifier(name, f"{context} column name")
    if column_type not in SUPPORTED_TYPES:
        supported = ", ".join(sorted(SUPPORTED_TYPES))
        raise schema_error(f"{context} column '{name}' has unsupported type '{column_type}' (expected one of {supported})")

    primary_key = require_optional_bool(column, "primary_key", context)
    auto_increment = require_optional_bool(column, "auto_increment", context)
    not_null = require_optional_bool(column, "not_null", context)
    unique = require_optional_bool(column, "unique", context)

    if "default" in column and column["default"] is not None and not isinstance(column["default"], str):
        raise schema_error(f"{context} field 'default' must be a string or null")
    if auto_increment and (column_type != "INTEGER" or not primary_key):
        raise schema_error(
            f"{context} column '{name}' can use auto_increment only when it is an INTEGER primary key"
        )

    return {
        "name": name,
        "type": column_type,
        "primary_key": primary_key,
        "auto_increment": auto_increment,
        "not_null": not_null,
        "unique": unique,
        "default": column.get("default"),
    }


def validate_sql_value(value: Any, field: str, context: str) -> Any:
    """Validate a JSON value that will be bound as a SQLite literal."""
    if isinstance(value, (dict, list)):
        raise schema_error(f"{context} field '{field}' must be a JSON scalar or null")
    if isinstance(value, float) and not math.isfinite(value):
        raise schema_error(f"{context} field '{field}' must be a finite number")
    return value


def require_identifier_array(container: dict[str, Any], field: str, context: str) -> list[str]:
    if field not in container:
        raise schema_error(f"{context} missing required field '{field}'")
    value = container[field]
    if not isinstance(value, list) or not value:
        raise schema_error(f"{context} field '{field}' must be a non-empty array")
    identifiers: list[str] = []
    for index, identifier in enumerate(value, start=1):
        if not isinstance(identifier, str):
            raise schema_error(f"{context} field '{field}' item {index} must be a string")
        validate_identifier(identifier, f"{context} field '{field}' item {index}")
        identifiers.append(identifier)
    if len(set(identifiers)) != len(identifiers):
        raise schema_error(f"{context} field '{field}' cannot contain duplicate column names")
    return identifiers


def require_optional_action(operation: dict[str, Any], field: str, context: str) -> str:
    value = operation.get(field, "NO ACTION")
    if not isinstance(value, str):
        raise schema_error(f"{context} field '{field}' must be a string")
    action = value.upper()
    valid_actions = {"CASCADE", "RESTRICT", "SET NULL", "NO ACTION", "SET DEFAULT"}
    if action not in valid_actions:
        raise schema_error(f"{context} field '{field}' has invalid action '{value}'")
    return action


def validate_migration(value: Any) -> dict[str, Any]:
    migration = require_object(value, "migration")

    if "version" not in migration:
        raise schema_error("missing required field 'version'")
    version = migration["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
        raise schema_error("field 'version' must be a positive integer")

    raw_dependencies = migration.get("depends_on", [])
    if not isinstance(raw_dependencies, list):
        raise schema_error("field 'depends_on' must be an array")
    depends_on: list[int] = []
    for index, dependency in enumerate(raw_dependencies, start=1):
        if isinstance(dependency, bool) or not isinstance(dependency, int) or dependency <= 0:
            raise schema_error(f"field 'depends_on' item {index} must be a positive integer")
        depends_on.append(dependency)
    if len(set(depends_on)) != len(depends_on):
        raise schema_error("field 'depends_on' cannot contain duplicate versions")

    description = require_string(migration, "description", "migration")

    if "operations" not in migration:
        raise schema_error("missing required field 'operations'")
    operations_value = migration["operations"]
    if not isinstance(operations_value, list):
        raise schema_error("field 'operations' must be an array")

    operations: list[dict[str, Any]] = []
    for index, raw_operation in enumerate(operations_value, start=1):
        context = f"operation {index}"
        operation = require_object(raw_operation, context)
        operation_type = require_string(operation, "type", context)

        if operation_type == "create_table":
            table = require_string(operation, "table", context)
            validate_identifier(table, f"{context} table name")
            if "columns" not in operation:
                raise schema_error(f"{context} missing required field 'columns'")
            raw_columns = operation["columns"]
            if not isinstance(raw_columns, list) or not raw_columns:
                raise schema_error(f"{context} field 'columns' must be a non-empty array")

            columns = [validate_column(raw_column, f"{context}") for raw_column in raw_columns]
            names = [column["name"] for column in columns]
            if len(set(names)) != len(names):
                raise schema_error(f"{context} contains duplicate column names")
            if sum(column["primary_key"] for column in columns) > 1:
                raise schema_error(f"{context} can contain at most one primary key column")
            operations.append({"type": operation_type, "table": table, "columns": columns})

        elif operation_type == "add_column":
            table = require_string(operation, "table", context)
            validate_identifier(table, f"{context} table name")
            if "column" not in operation:
                raise schema_error(f"{context} missing required field 'column'")
            column = validate_column(operation["column"], context)
            operations.append({"type": operation_type, "table": table, "column": column})

        elif operation_type == "transform_data":
            table = require_string(operation, "table", context)
            validate_identifier(table, f"{context} table name")
            if "transformations" not in operation:
                raise schema_error(f"{context} missing required field 'transformations'")
            raw_transformations = operation["transformations"]
            if not isinstance(raw_transformations, list) or not raw_transformations:
                raise schema_error(f"{context} field 'transformations' must be a non-empty array")
            transformations: list[dict[str, str]] = []
            for transformation_index, raw_transformation in enumerate(raw_transformations, start=1):
                transformation_context = f"{context} transformation {transformation_index}"
                transformation = require_object(raw_transformation, transformation_context)
                column = require_string(transformation, "column", transformation_context)
                expression = require_string(transformation, "expression", transformation_context)
                validate_identifier(column, f"{transformation_context} column name")
                transformations.append({"column": column, "expression": expression})
            operations.append(
                {"type": operation_type, "table": table, "transformations": transformations}
            )

        elif operation_type == "migrate_column_data":
            table = require_string(operation, "table", context)
            from_column = require_string(operation, "from_column", context)
            to_column = require_string(operation, "to_column", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(from_column, f"{context} source column name")
            validate_identifier(to_column, f"{context} destination column name")
            default_value = validate_sql_value(operation.get("default_value"), "default_value", context)
            operations.append(
                {
                    "type": operation_type,
                    "table": table,
                    "from_column": from_column,
                    "to_column": to_column,
                    "default_value": default_value,
                }
            )

        elif operation_type == "backfill_data":
            table = require_string(operation, "table", context)
            column = require_string(operation, "column", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(column, f"{context} column name")
            if "value" not in operation:
                raise schema_error(f"{context} missing required field 'value'")
            value = validate_sql_value(operation["value"], "value", context)
            where = operation.get("where")
            if where is not None and not isinstance(where, str):
                raise schema_error(f"{context} field 'where' must be a string")
            operations.append(
                {"type": operation_type, "table": table, "column": column, "value": value, "where": where}
            )

        elif operation_type == "add_foreign_key":
            table = require_string(operation, "table", context)
            name = require_string(operation, "name", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(name, f"{context} constraint name")
            columns = require_identifier_array(operation, "columns", context)
            if "references" not in operation:
                raise schema_error(f"{context} missing required field 'references'")
            references = require_object(operation["references"], f"{context} field 'references'")
            referenced_table = require_string(references, "table", f"{context} references")
            validate_identifier(referenced_table, f"{context} referenced table name")
            referenced_columns = require_identifier_array(references, "columns", f"{context} references")
            if len(columns) != len(referenced_columns):
                raise schema_error(f"{context} foreign key column counts must match")
            operations.append(
                {
                    "type": operation_type,
                    "table": table,
                    "name": name,
                    "columns": columns,
                    "references": {"table": referenced_table, "columns": referenced_columns},
                    "on_delete": require_optional_action(operation, "on_delete", context),
                    "on_update": require_optional_action(operation, "on_update", context),
                }
            )

        elif operation_type == "drop_foreign_key":
            table = require_string(operation, "table", context)
            name = require_string(operation, "name", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(name, f"{context} constraint name")
            operations.append({"type": operation_type, "table": table, "name": name})

        elif operation_type == "create_index":
            table = require_string(operation, "table", context)
            name = require_string(operation, "name", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(name, f"{context} index name")
            columns = require_identifier_array(operation, "columns", context)
            unique = require_optional_bool(operation, "unique", context)
            operations.append(
                {"type": operation_type, "table": table, "name": name, "columns": columns, "unique": unique}
            )

        elif operation_type == "drop_index":
            name = require_string(operation, "name", context)
            validate_identifier(name, f"{context} index name")
            operations.append({"type": operation_type, "name": name})

        elif operation_type == "add_check_constraint":
            table = require_string(operation, "table", context)
            name = require_string(operation, "name", context)
            expression = require_string(operation, "expression", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(name, f"{context} constraint name")
            operations.append(
                {"type": operation_type, "table": table, "name": name, "expression": expression}
            )

        elif operation_type == "drop_check_constraint":
            table = require_string(operation, "table", context)
            name = require_string(operation, "name", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(name, f"{context} constraint name")
            operations.append({"type": operation_type, "table": table, "name": name})

        elif operation_type == "drop_column":
            table = require_string(operation, "table", context)
            column = require_string(operation, "column", context)
            validate_identifier(table, f"{context} table name")
            validate_identifier(column, f"{context} column name")
            operations.append({"type": operation_type, "table": table, "column": column})

        else:
            raise schema_error(f"{context} has unsupported type '{operation_type}'")

    rollback_operations: list[dict[str, Any]] | None = None
    if "rollback_operations" in migration:
        raw_rollback_operations = migration["rollback_operations"]
        if not isinstance(raw_rollback_operations, list):
            raise schema_error("field 'rollback_operations' must be an array")
        # Explicit rollback operations use the same validated operation format
        # as a forward migration, but are executed in the supplied order.
        rollback_operations = validate_migration(
            {
                "version": 1,
                "description": "explicit rollback operations",
                "operations": raw_rollback_operations,
            }
        )["operations"]

    return {
        "version": version,
        "description": description,
        "depends_on": depends_on,
        "operations": operations,
        "rollback_operations": rollback_operations,
    }


def render_column(column: dict[str, Any]) -> str:
    """Render a validated column declaration for CREATE/ALTER TABLE."""
    parts = [quote_identifier(column["name"]), column["type"]]
    if column["primary_key"]:
        parts.append("PRIMARY KEY")
    if column["auto_increment"]:
        parts.append("AUTOINCREMENT")
    if column["not_null"]:
        parts.append("NOT NULL")
    if column["unique"]:
        parts.append("UNIQUE")
    if column["default"] is not None:
        # Defaults are explicitly defined by the migration format as SQL
        # expressions, so they cannot be bound as query parameters.
        parts.append("DEFAULT " + column["default"])
    return " ".join(parts)


def table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def table_columns(connection: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    return connection.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()


def create_migrations_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            operations TEXT NOT NULL,
            rollback_operations TEXT,
            depends_on TEXT NOT NULL
        )
        """
    )
    existing_columns = {
        column["name"]
        for column in connection.execute("PRAGMA table_info(_migrations)")
    }
    # Databases migrated by checkpoints 1-3 already have this table. SQLite
    # can add the required history column safely when a default is supplied.
    if "operations" not in existing_columns:
        connection.execute("ALTER TABLE _migrations ADD COLUMN operations TEXT NOT NULL DEFAULT '[]'")
    if "rollback_operations" not in existing_columns:
        connection.execute("ALTER TABLE _migrations ADD COLUMN rollback_operations TEXT")
    if "depends_on" not in existing_columns:
        connection.execute("ALTER TABLE _migrations ADD COLUMN depends_on TEXT NOT NULL DEFAULT '[]'")
    connection.commit()


def create_table(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    if table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' already exists")
    definitions = ", ".join(render_column(column) for column in operation["columns"])
    connection.execute(f"CREATE TABLE {quote_identifier(table)} ({definitions})")


def add_column(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    column = operation["column"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    if any(existing["name"] == column["name"] for existing in table_columns(connection, table)):
        raise MigrationError(f"invalid operation: column '{column['name']}' already exists in table '{table}'")
    connection.execute(
        f"ALTER TABLE {quote_identifier(table)} ADD COLUMN {render_column(column)}"
    )


def require_existing_table(connection: sqlite3.Connection, table: str) -> None:
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")


def require_existing_column(connection: sqlite3.Connection, table: str, column: str) -> None:
    if not any(existing["name"] == column for existing in table_columns(connection, table)):
        raise MigrationError(f"invalid operation: column '{column}' does not exist in table '{table}'")


def transform_data(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    """Apply ordered expressions, creating an untyped-format target as TEXT."""
    table = operation["table"]
    require_existing_table(connection, table)
    known_columns = {column["name"] for column in table_columns(connection, table)}
    for transformation in operation["transformations"]:
        column = transformation["column"]
        if column not in known_columns:
            # The transform_data format intentionally has no column type. TEXT
            # is the least-surprising SQLite affinity and covers the documented
            # derived-string use case; SQLite retains dynamic values if needed.
            connection.execute(
                f"ALTER TABLE {quote_identifier(table)} ADD COLUMN {quote_identifier(column)} TEXT"
            )
            known_columns.add(column)
        connection.execute(
            f"UPDATE {quote_identifier(table)} SET {quote_identifier(column)} = {transformation['expression']}"
        )


def migrate_column_data(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    from_column = operation["from_column"]
    to_column = operation["to_column"]
    require_existing_table(connection, table)
    require_existing_column(connection, table, from_column)
    require_existing_column(connection, table, to_column)

    table_sql = quote_identifier(table)
    source_sql = quote_identifier(from_column)
    destination_sql = quote_identifier(to_column)
    default_value = operation["default_value"]
    if default_value is None:
        connection.execute(f"UPDATE {table_sql} SET {destination_sql} = {source_sql}")
    else:
        connection.execute(
            f"UPDATE {table_sql} SET {destination_sql} = "
            f"CASE WHEN {source_sql} IS NULL THEN ? ELSE {source_sql} END",
            (default_value,),
        )


def backfill_data(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    column = operation["column"]
    require_existing_table(connection, table)
    require_existing_column(connection, table, column)

    table_sql = quote_identifier(table)
    column_sql = quote_identifier(column)
    where_sql = f" WHERE {operation['where']}" if operation["where"] is not None else ""
    value = operation["value"]
    if isinstance(value, str):
        # Migration strings represent SQL expressions (e.g. "'active'" or
        # "COALESCE(status, 'active')"), as shown by the task examples.
        connection.execute(f"UPDATE {table_sql} SET {column_sql} = {value}{where_sql}")
    else:
        connection.execute(f"UPDATE {table_sql} SET {column_sql} = ?{where_sql}", (value,))


def split_top_level_sql(text: str) -> list[str]:
    """Split a comma-separated SQL list without splitting nested expressions."""
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    index = 0
    while index < len(text):
        character = text[index]
        if quote is not None:
            if character == quote:
                # SQLite escapes single and double quotes by doubling them.
                if quote in {"'", '"'} and index + 1 < len(text) and text[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if character in {"'", '"', "`"}:
            quote = character
        elif character == "[":
            quote = "]"
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "," and depth == 0:
            part = text[start:index].strip()
            if part:
                parts.append(part)
            start = index + 1
        index += 1
    part = text[start:].strip()
    if part:
        parts.append(part)
    return parts


def matching_parenthesis(text: str, opening: int) -> int:
    depth = 0
    quote: str | None = None
    index = opening
    while index < len(text):
        character = text[index]
        if quote is not None:
            if character == quote:
                if quote in {"'", '"'} and index + 1 < len(text) and text[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if character in {"'", '"', "`"}:
            quote = character
        elif character == "[":
            quote = "]"
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise MigrationError("invalid operation: table schema could not be recreated")


def table_definition_parts(connection: sqlite3.Connection, table: str) -> list[str]:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    source_sql = row["sql"] if row else None
    if not source_sql:
        raise MigrationError(f"invalid operation: table '{table}' has no recreatable schema")
    opening = source_sql.find("(")
    if opening < 0:
        raise MigrationError(f"invalid operation: table '{table}' has no recreatable schema")
    closing = matching_parenthesis(source_sql, opening)
    return split_top_level_sql(source_sql[opening + 1 : closing])


def leading_identifier(definition: str) -> str | None:
    """Return the declared column name, or None for a table constraint."""
    stripped = definition.lstrip()
    if re.match(r"(?:CONSTRAINT|PRIMARY|UNIQUE|CHECK|FOREIGN)\b", stripped, re.IGNORECASE):
        return None
    if not stripped:
        return None
    if stripped[0] == '"':
        index = 1
        value: list[str] = []
        while index < len(stripped):
            if stripped[index] == '"':
                if index + 1 < len(stripped) and stripped[index + 1] == '"':
                    value.append('"')
                    index += 2
                    continue
                return "".join(value)
            value.append(stripped[index])
            index += 1
        return None
    match = re.match(r"[A-Za-z_][A-Za-z0-9_]*", stripped)
    return match.group(0) if match else None


def sql_identifier_tokens(text: str) -> set[str]:
    """Extract identifiers while ignoring single-quoted SQL string literals."""
    names: set[str] = set()
    index = 0
    quote: str | None = None
    while index < len(text):
        character = text[index]
        if quote is not None:
            if character == quote:
                if quote in {"'", '"'} and index + 1 < len(text) and text[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if character == "'":
            quote = "'"
            index += 1
            continue
        if character in {'"', "`"}:
            end = character
            index += 1
            value: list[str] = []
            while index < len(text):
                if text[index] == end:
                    if index + 1 < len(text) and text[index + 1] == end:
                        value.append(end)
                        index += 2
                        continue
                    names.add("".join(value))
                    index += 1
                    break
                value.append(text[index])
                index += 1
            continue
        match = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[index:])
        if match:
            names.add(match.group(0))
            index += len(match.group(0))
        else:
            index += 1
    return names


NAMED_CONSTRAINT_RE = re.compile(
    r'^\s*CONSTRAINT\s+(?:"((?:""|[^"])*)"|([A-Za-z_][A-Za-z0-9_]*))\s+'
    r"(FOREIGN\s+KEY|CHECK|UNIQUE|PRIMARY\s+KEY)\b",
    re.IGNORECASE,
)


def named_constraint(definition: str) -> tuple[str, str] | None:
    match = NAMED_CONSTRAINT_RE.match(definition)
    if match is None:
        return None
    name = (match.group(1) or match.group(2)).replace('""', '"')
    return name, " ".join(match.group(3).upper().split())


def existing_constraint_names(definitions: list[str]) -> set[str]:
    return {constraint[0] for definition in definitions if (constraint := named_constraint(definition))}


def explicit_indexes(connection: sqlite3.Connection, table: str) -> list[tuple[str, str, list[str]]]:
    indexes: list[tuple[str, str, list[str]]] = []
    for row in connection.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'index' AND tbl_name = ? AND sql IS NOT NULL",
        (table,),
    ):
        names = [
            index_column["name"]
            for index_column in connection.execute(f"PRAGMA index_info({quote_identifier(row['name'])})")
        ]
        indexes.append((row["name"], row["sql"], names))
    return indexes


def rebuild_table(
    connection: sqlite3.Connection,
    table: str,
    definitions: list[str],
    copied_columns: list[str] | None = None,
    skipped_index_names: set[str] | None = None,
) -> None:
    """Recreate a table while preserving all explicit indexes that still apply."""
    if not definitions:
        raise MigrationError(f"invalid operation: table '{table}' cannot have no definitions")
    original_indexes = explicit_indexes(connection, table)
    temporary_table = f"__migration_new_{uuid.uuid4().hex}"
    if copied_columns is None:
        copied_columns = [column["name"] for column in table_columns(connection, table)]
    columns_sql = ", ".join(quote_identifier(column) for column in copied_columns)
    connection.execute(
        f"CREATE TABLE {quote_identifier(temporary_table)} ({', '.join(definitions)})"
    )
    if copied_columns:
        connection.execute(
            f"INSERT INTO {quote_identifier(temporary_table)} ({columns_sql}) "
            f"SELECT {columns_sql} FROM {quote_identifier(table)}"
        )
    connection.execute(f"DROP TABLE {quote_identifier(table)}")
    connection.execute(
        f"ALTER TABLE {quote_identifier(temporary_table)} RENAME TO {quote_identifier(table)}"
    )
    skipped_index_names = skipped_index_names or set()
    for name, index_sql, _ in original_indexes:
        if name not in skipped_index_names:
            connection.execute(index_sql)


def drop_column(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    dropped_name = operation["column"]
    require_existing_table(connection, table)
    columns = table_columns(connection, table)
    by_name = {column["name"]: column for column in columns}
    if dropped_name not in by_name:
        raise MigrationError(f"invalid operation: column '{dropped_name}' does not exist in table '{table}'")
    if len(columns) == 1:
        raise MigrationError(f"invalid operation: cannot drop the only column in table '{table}'")
    if by_name[dropped_name]["pk"]:
        raise MigrationError(f"invalid operation: cannot drop primary key column '{dropped_name}'")

    definitions = table_definition_parts(connection, table)
    remaining_definitions = [
        definition
        for definition in definitions
        if leading_identifier(definition) != dropped_name
        and (leading_identifier(definition) is not None or dropped_name not in sql_identifier_tokens(definition))
    ]
    skipped_indexes = {
        name
        for name, _, indexed_columns in explicit_indexes(connection, table)
        if dropped_name in indexed_columns
    }
    copied_columns = [column["name"] for column in columns if column["name"] != dropped_name]
    rebuild_table(connection, table, remaining_definitions, copied_columns, skipped_indexes)


def column_affinity(column_type: str) -> str:
    normalized = column_type.upper()
    if "INT" in normalized:
        return "INTEGER"
    if any(token in normalized for token in ("CHAR", "CLOB", "TEXT")):
        return "TEXT"
    if "BLOB" in normalized or not normalized:
        return "BLOB"
    if any(token in normalized for token in ("REAL", "FLOA", "DOUB")):
        return "REAL"
    return "NUMERIC"


def columns_form_parent_key(connection: sqlite3.Connection, table: str, columns: list[str]) -> bool:
    primary_key = sorted(
        (column for column in table_columns(connection, table) if column["pk"]),
        key=lambda column: column["pk"],
    )
    if primary_key and [column["name"] for column in primary_key] == columns:
        return True
    for index in connection.execute(f"PRAGMA index_list({quote_identifier(table)})"):
        if not index["unique"]:
            continue
        indexed_columns = [
            row["name"]
            for row in connection.execute(f"PRAGMA index_info({quote_identifier(index['name'])})")
        ]
        if indexed_columns == columns:
            return True
    return False


def foreign_key_has_violations(
    connection: sqlite3.Connection,
    table: str,
    columns: list[str],
    referenced_table: str,
    referenced_columns: list[str],
) -> bool:
    child_alias = quote_identifier("_migration_child")
    parent_alias = quote_identifier("_migration_parent")
    not_null = " AND ".join(
        f"{child_alias}.{quote_identifier(column)} IS NOT NULL" for column in columns
    )
    matches = " AND ".join(
        f"{parent_alias}.{quote_identifier(parent_column)} = {child_alias}.{quote_identifier(child_column)}"
        for child_column, parent_column in zip(columns, referenced_columns)
    )
    query = (
        f"SELECT 1 FROM {quote_identifier(table)} AS {child_alias} "
        f"WHERE ({not_null}) AND NOT EXISTS "
        f"(SELECT 1 FROM {quote_identifier(referenced_table)} AS {parent_alias} WHERE {matches}) LIMIT 1"
    )
    return connection.execute(query).fetchone() is not None


def has_foreign_key_path(connection: sqlite3.Connection, start: str, target: str) -> bool:
    """Return whether following existing child-to-parent edges reaches target."""
    pending = [start]
    visited: set[str] = set()
    while pending:
        table = pending.pop()
        if table == target:
            return True
        if table in visited:
            continue
        visited.add(table)
        if not table_exists(connection, table):
            continue
        parents = {
            row["table"]
            for row in connection.execute(f"PRAGMA foreign_key_list({quote_identifier(table)})")
        }
        pending.extend(parent for parent in parents if parent not in visited)
    return False


def add_foreign_key(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    name = operation["name"]
    referenced_table = operation["references"]["table"]
    columns = operation["columns"]
    referenced_columns = operation["references"]["columns"]
    require_existing_table(connection, table)
    if not table_exists(connection, referenced_table):
        raise MigrationError(f"cannot add foreign key: referenced table '{referenced_table}' does not exist")
    definitions = table_definition_parts(connection, table)
    if name in existing_constraint_names(definitions):
        raise MigrationError(f"invalid operation: foreign key constraint '{name}' already exists in table '{table}'")

    child_columns = {column["name"]: column for column in table_columns(connection, table)}
    parent_columns = {column["name"]: column for column in table_columns(connection, referenced_table)}
    for child_column, parent_column in zip(columns, referenced_columns):
        if child_column not in child_columns:
            raise MigrationError(f"cannot add foreign key: column '{table}.{child_column}' does not exist")
        if parent_column not in parent_columns:
            raise MigrationError(
                f"cannot add foreign key: referenced column '{referenced_table}.{parent_column}' does not exist"
            )
        if column_affinity(child_columns[child_column]["type"]) != column_affinity(parent_columns[parent_column]["type"]):
            raise MigrationError(
                f"cannot add foreign key: columns '{table}.{child_column}' and "
                f"'{referenced_table}.{parent_column}' have incompatible types"
            )
    if not columns_form_parent_key(connection, referenced_table, referenced_columns):
        raise MigrationError(
            f"cannot add foreign key: referenced columns in table '{referenced_table}' must be a primary or unique key"
        )
    if has_foreign_key_path(connection, referenced_table, table):
        raise MigrationError("cannot add foreign key: circular foreign key dependency detected")
    if foreign_key_has_violations(connection, table, columns, referenced_table, referenced_columns):
        raise MigrationError(
            f"foreign key violation: referenced row in '{referenced_table}' table does not exist"
        )

    child_sql = ", ".join(quote_identifier(column) for column in columns)
    parent_sql = ", ".join(quote_identifier(column) for column in referenced_columns)
    definitions.append(
        f"CONSTRAINT {quote_identifier(name)} FOREIGN KEY ({child_sql}) "
        f"REFERENCES {quote_identifier(referenced_table)} ({parent_sql}) "
        f"ON DELETE {operation['on_delete']} ON UPDATE {operation['on_update']}"
    )
    rebuild_table(connection, table, definitions)


def drop_foreign_key(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    name = operation["name"]
    require_existing_table(connection, table)
    definitions = table_definition_parts(connection, table)
    matching = [
        definition
        for definition in definitions
        if (constraint := named_constraint(definition)) and constraint == (name, "FOREIGN KEY")
    ]
    if not matching:
        raise MigrationError(f"invalid operation: foreign key constraint '{name}' does not exist in table '{table}'")
    rebuild_table(connection, table, [definition for definition in definitions if definition not in matching])


def create_index(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    name = operation["name"]
    require_existing_table(connection, table)
    for column in operation["columns"]:
        require_existing_column(connection, table, column)
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = ?", (name,)).fetchone():
        raise MigrationError(f"index '{name}' already exists")
    unique_sql = "UNIQUE " if operation["unique"] else ""
    columns_sql = ", ".join(quote_identifier(column) for column in operation["columns"])
    connection.execute(
        f"CREATE {unique_sql}INDEX {quote_identifier(name)} ON {quote_identifier(table)} ({columns_sql})"
    )


def drop_index(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    name = operation["name"]
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?", (name,)
    ).fetchone()
    if row is None:
        raise MigrationError(f"invalid operation: index '{name}' does not exist")
    if row["sql"] is None:
        raise MigrationError(f"invalid operation: index '{name}' is managed by a table constraint")
    connection.execute(f"DROP INDEX {quote_identifier(name)}")


def check_existing_rows(connection: sqlite3.Connection, table: str, name: str, expression: str) -> None:
    query = f"SELECT 1 FROM {quote_identifier(table)} WHERE NOT ({expression}) LIMIT 1"
    if connection.execute(query).fetchone() is not None:
        raise MigrationError(f"check constraint violation: {name}")


def add_check_constraint(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    name = operation["name"]
    require_existing_table(connection, table)
    definitions = table_definition_parts(connection, table)
    if name in existing_constraint_names(definitions):
        raise MigrationError(f"invalid operation: check constraint '{name}' already exists in table '{table}'")
    check_existing_rows(connection, table, name, operation["expression"])
    definitions.append(f"CONSTRAINT {quote_identifier(name)} CHECK ({operation['expression']})")
    rebuild_table(connection, table, definitions)


def drop_check_constraint(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    name = operation["name"]
    require_existing_table(connection, table)
    definitions = table_definition_parts(connection, table)
    matching = [
        definition
        for definition in definitions
        if (constraint := named_constraint(definition)) and constraint == (name, "CHECK")
    ]
    if not matching:
        raise MigrationError(f"invalid operation: check constraint '{name}' does not exist in table '{table}'")
    rebuild_table(connection, table, [definition for definition in definitions if definition not in matching])


def original_column_metadata(connection: sqlite3.Connection, table: str, column_name: str) -> tuple[dict[str, Any], str]:
    """Capture a dropped column before its schema definition is removed."""
    require_existing_table(connection, table)
    column = next((item for item in table_columns(connection, table) if item["name"] == column_name), None)
    if column is None:
        raise MigrationError(f"invalid operation: column '{column_name}' does not exist in table '{table}'")
    sql_definition = next(
        (definition for definition in table_definition_parts(connection, table) if leading_identifier(definition) == column_name),
        None,
    )
    if sql_definition is None:
        raise MigrationError(f"invalid operation: column '{column_name}' has no restorable definition")
    tokens = {token.upper() for token in sql_identifier_tokens(sql_definition)}
    return (
        {
            "name": column["name"],
            "type": column["type"] or "TEXT",
            "primary_key": bool(column["pk"]),
            "auto_increment": "AUTOINCREMENT" in tokens,
            "not_null": bool(column["notnull"]),
            "unique": "UNIQUE" in tokens,
            "default": column["dflt_value"],
        },
        sql_definition,
    )


def named_definition(connection: sqlite3.Connection, table: str, name: str, kind: str) -> str:
    require_existing_table(connection, table)
    for definition in table_definition_parts(connection, table):
        if named_constraint(definition) == (name, kind):
            return definition
    label = "foreign key" if kind == "FOREIGN KEY" else "check"
    raise MigrationError(f"invalid operation: {label} constraint '{name}' does not exist in table '{table}'")


def prepare_operation_metadata(connection: sqlite3.Connection, operation: dict[str, Any]) -> dict[str, Any]:
    """Return a durable operation record with data required for its inverse."""
    stored = copy.deepcopy(operation)
    operation_type = operation["type"]
    if operation_type == "drop_column":
        original_definition, original_sql_definition = original_column_metadata(
            connection, operation["table"], operation["column"]
        )
        stored["original_definition"] = original_definition
        stored["original_sql_definition"] = original_sql_definition
    elif operation_type == "drop_foreign_key":
        stored["original_definition"] = named_definition(
            connection, operation["table"], operation["name"], "FOREIGN KEY"
        )
    elif operation_type == "drop_check_constraint":
        stored["original_definition"] = named_definition(
            connection, operation["table"], operation["name"], "CHECK"
        )
    elif operation_type == "drop_index":
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?", (operation["name"],)
        ).fetchone()
        if row is None:
            raise MigrationError(f"invalid operation: index '{operation['name']}' does not exist")
        if row["sql"] is None:
            raise MigrationError(f"invalid operation: index '{operation['name']}' is managed by a table constraint")
        stored["original_definition"] = row["sql"]
    return stored


def dependent_foreign_key_tables(connection: sqlite3.Connection, table: str) -> set[str]:
    dependents: set[str] = set()
    for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
        candidate = row["name"]
        if candidate == table or candidate.startswith("sqlite_"):
            continue
        if any(
            foreign_key["table"] == table
            for foreign_key in connection.execute(f"PRAGMA foreign_key_list({quote_identifier(candidate)})")
        ):
            dependents.add(candidate)
    return dependents


def rollback_drop_table(connection: sqlite3.Connection, table: str) -> None:
    if not table_exists(connection, table):
        raise MigrationError(f"rollback failed: table '{table}' does not exist")
    if dependent_foreign_key_tables(connection, table):
        raise MigrationError("cannot rollback: foreign key constraint violation")
    connection.execute(f"DROP TABLE {quote_identifier(table)}")


def restore_dropped_column(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    original = operation.get("original_definition")
    if not isinstance(original, dict):
        raise MigrationError("cannot rollback: missing original column definition")
    require_existing_table(connection, table)
    name = original.get("name")
    if not isinstance(name, str):
        raise MigrationError("cannot rollback: missing original column definition")
    if any(column["name"] == name for column in table_columns(connection, table)):
        return
    original_sql_definition = operation.get("original_sql_definition")
    if not isinstance(original_sql_definition, str):
        # Metadata written by this checkpoint always includes the exact SQL
        # declaration; this fallback supports the documented JSON form.
        original_sql_definition = render_column(original)
    definitions = table_definition_parts(connection, table)
    definitions.append(original_sql_definition)
    rebuild_table(connection, table, definitions)


def restore_named_constraint(connection: sqlite3.Connection, operation: dict[str, Any], kind: str) -> None:
    table = operation["table"]
    name = operation["name"]
    definition = operation.get("original_definition")
    if not isinstance(definition, str):
        raise MigrationError(f"cannot rollback: missing original {kind.lower()} definition")
    require_existing_table(connection, table)
    definitions = table_definition_parts(connection, table)
    if named_constraint(definition) != (name, kind):
        raise MigrationError(f"cannot rollback: invalid original {kind.lower()} definition")
    if any(named_constraint(existing) == (name, kind) for existing in definitions):
        return
    definitions.append(definition)
    rebuild_table(connection, table, definitions)


def restore_dropped_index(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    name = operation["name"]
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = ?", (name,)).fetchone():
        return
    definition = operation.get("original_definition")
    if not isinstance(definition, str):
        raise MigrationError("cannot rollback: missing original index definition")
    connection.execute(definition)


def automatic_rollback_plan(operations: list[dict[str, Any]], version: int) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Build executable inverse operations and their user-facing event source."""
    plan: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for operation in reversed(operations):
        if not isinstance(operation, dict) or not isinstance(operation.get("type"), str):
            raise MigrationError(f"cannot rollback version {version}: invalid operation metadata")
        operation_type = operation["type"]
        if operation_type == "create_table":
            inverse = {"type": "_rollback_drop_table", "table": operation["table"]}
        elif operation_type == "add_column":
            inverse = {"type": "drop_column", "table": operation["table"], "column": operation["column"]["name"]}
        elif operation_type == "drop_column":
            inverse = {**operation, "type": "_restore_dropped_column"}
        elif operation_type == "add_foreign_key":
            inverse = {"type": "drop_foreign_key", "table": operation["table"], "name": operation["name"]}
        elif operation_type == "drop_foreign_key":
            inverse = {**operation, "type": "_restore_foreign_key"}
        elif operation_type == "create_index":
            inverse = {"type": "drop_index", "name": operation["name"]}
        elif operation_type == "drop_index":
            inverse = {**operation, "type": "_restore_index"}
        elif operation_type == "add_check_constraint":
            inverse = {"type": "drop_check_constraint", "table": operation["table"], "name": operation["name"]}
        elif operation_type == "drop_check_constraint":
            inverse = {**operation, "type": "_restore_check_constraint"}
        elif operation_type == "migrate_column_data":
            inverse = {
                "type": "migrate_column_data",
                "table": operation["table"],
                "from_column": operation["to_column"],
                "to_column": operation["from_column"],
                "default_value": None,
            }
        elif operation_type in {"transform_data", "backfill_data"}:
            raise MigrationError(
                f"cannot rollback version {version}: missing rollback_operations for {operation_type}"
            )
        else:
            raise MigrationError(f"cannot rollback version {version}: unsupported operation '{operation_type}'")
        plan.append((inverse, operation))
    return plan


def execute_rollback_instruction(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    operation_type = operation["type"]
    if operation_type == "_rollback_drop_table":
        rollback_drop_table(connection, operation["table"])
    elif operation_type == "_restore_dropped_column":
        restore_dropped_column(connection, operation)
    elif operation_type == "_restore_foreign_key":
        restore_named_constraint(connection, operation, "FOREIGN KEY")
    elif operation_type == "_restore_index":
        restore_dropped_index(connection, operation)
    elif operation_type == "_restore_check_constraint":
        restore_named_constraint(connection, operation, "CHECK")
    else:
        apply_operation(connection, operation)


def apply_operation(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    operation_type = operation["type"]
    if operation_type == "create_table":
        create_table(connection, operation)
    elif operation_type == "add_column":
        add_column(connection, operation)
    elif operation_type == "transform_data":
        transform_data(connection, operation)
    elif operation_type == "migrate_column_data":
        migrate_column_data(connection, operation)
    elif operation_type == "backfill_data":
        backfill_data(connection, operation)
    elif operation_type == "add_foreign_key":
        add_foreign_key(connection, operation)
    elif operation_type == "drop_foreign_key":
        drop_foreign_key(connection, operation)
    elif operation_type == "create_index":
        create_index(connection, operation)
    elif operation_type == "drop_index":
        drop_index(connection, operation)
    elif operation_type == "add_check_constraint":
        add_check_constraint(connection, operation)
    elif operation_type == "drop_check_constraint":
        drop_check_constraint(connection, operation)
    elif operation_type == "drop_column":
        drop_column(connection, operation)
    else:  # validate_migration guarantees this, but keep the boundary explicit.
        raise MigrationError(f"invalid operation: unsupported type '{operation_type}'")


def operation_event(operation: dict[str, Any], version: int) -> dict[str, Any]:
    operation_type = operation["type"]
    if operation_type == "drop_index":
        return {
            "event": "operation_applied",
            "type": operation_type,
            "name": operation["name"],
            "version": version,
        }
    if operation_type == "create_index":
        return {
            "event": "operation_applied",
            "type": operation_type,
            "name": operation["name"],
            "table": operation["table"],
            "version": version,
        }
    event: dict[str, Any] = {
        "event": "operation_applied",
        "type": operation_type,
        "table": operation["table"],
    }
    if operation_type in {"add_column", "drop_column"}:
        column = operation["column"]
        event["column"] = column["name"] if isinstance(column, dict) else column
    if operation_type in {
        "add_foreign_key",
        "drop_foreign_key",
        "add_check_constraint",
        "drop_check_constraint",
    }:
        event["name"] = operation["name"]
    event["version"] = version
    return event


def emit(event: dict[str, Any]) -> None:
    print(json.dumps(event, ensure_ascii=False), flush=True)


def load_migration(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    if not path.is_file():
        raise MigrationError(f"migration file not found: {path_text}")
    try:
        with path.open("r", encoding="utf-8") as migration_file:
            raw_migration = json.load(migration_file)
    except json.JSONDecodeError as exc:
        raise MigrationError(f"invalid JSON in migration file: {exc.msg}") from exc
    except UnicodeDecodeError as exc:
        raise MigrationError(f"invalid JSON in migration file: invalid UTF-8 ({exc.reason})") from exc
    except OSError as exc:
        raise MigrationError(f"could not read migration file: {exc}") from exc
    return validate_migration(raw_migration)


def discover_migrations(directory_text: str) -> dict[int, tuple[Path, dict[str, Any]]]:
    directory = Path(directory_text)
    if not directory.is_dir():
        raise MigrationError(f"migrations directory not found: {directory_text}")
    discovered: dict[int, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
        try:
            migration = load_migration(str(path))
        except MigrationError as exc:
            raise MigrationError(f"invalid migration file: {path.name}: {exc}") from exc
        version = migration["version"]
        if version in discovered:
            raise MigrationError(f"duplicate migration version {version}")
        discovered[version] = (path, migration)
    return discovered


def find_dependency_cycle(migrations: dict[int, dict[str, Any]]) -> list[int] | None:
    states: dict[int, int] = {version: 0 for version in migrations}
    path: list[int] = []

    def visit(version: int) -> list[int] | None:
        states[version] = 1
        path.append(version)
        for dependency in migrations[version]["depends_on"]:
            if dependency not in migrations:
                continue
            if states[dependency] == 1:
                return path[path.index(dependency) :] + [dependency]
            if states[dependency] == 0:
                cycle = visit(dependency)
                if cycle is not None:
                    return cycle
        path.pop()
        states[version] = 2
        return None

    for version in sorted(migrations):
        if states[version] == 0:
            cycle = visit(version)
            if cycle is not None:
                return cycle
    return None


def validate_dependency_graph(migrations: dict[int, dict[str, Any]]) -> None:
    for version, migration in migrations.items():
        for dependency in migration["depends_on"]:
            if dependency not in migrations:
                raise MigrationError(f"dependency version {dependency} not found")
    cycle = find_dependency_cycle(migrations)
    if cycle is not None:
        raise DependencyCycleError(cycle)
    for version, migration in migrations.items():
        for dependency in migration["depends_on"]:
            if dependency >= version:
                raise MigrationError(
                    f"migration version {version} cannot depend on future version {dependency}"
                )


def dependency_order(migrations: dict[int, dict[str, Any]]) -> list[int]:
    """Return a deterministic topological order after graph validation."""
    in_degree = {version: len(migration["depends_on"]) for version, migration in migrations.items()}
    dependents: dict[int, list[int]] = {version: [] for version in migrations}
    for version, migration in migrations.items():
        for dependency in migration["depends_on"]:
            dependents[dependency].append(version)
    available = [version for version, degree in in_degree.items() if degree == 0]
    heapq.heapify(available)
    resolved: list[int] = []
    while available:
        version = heapq.heappop(available)
        resolved.append(version)
        for dependent in sorted(dependents[version]):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                heapq.heappush(available, dependent)
    if len(resolved) != len(migrations):
        raise MigrationError("dependency resolution failed: conflicting requirements")
    return resolved


def decode_dependency_history(value: Any, version: int) -> list[int]:
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise MigrationError(f"invalid dependency metadata for version {version}") from exc
    if (
        not isinstance(decoded, list)
        or any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in decoded)
    ):
        raise MigrationError(f"invalid dependency metadata for version {version}")
    return decoded


def ensure_single_migration_dependencies(
    connection: sqlite3.Connection, migration: dict[str, Any]
) -> None:
    version = migration["version"]
    pending = list(migration["depends_on"])
    visited: set[int] = set()
    while pending:
        dependency = pending.pop()
        if dependency == version:
            raise DependencyCycleError([version, version])
        if dependency > version:
            raise MigrationError(
                f"migration version {version} cannot depend on future version {dependency}"
            )
        if dependency in visited:
            continue
        visited.add(dependency)
        row = connection.execute(
            "SELECT depends_on FROM _migrations WHERE version = ?", (dependency,)
        ).fetchone()
        if row is None:
            raise MigrationError(f"dependency version {dependency} not found")
        pending.extend(decode_dependency_history(row["depends_on"], dependency))


def validate_command(migration_path: str, migrations_directory: str | None) -> None:
    target_path = Path(migration_path)
    emit({"event": "validation_started", "migration_file": target_path.name})
    completed = False
    try:
        target = load_migration(migration_path)
        if migrations_directory is None:
            if target["depends_on"]:
                emit(
                    {
                        "event": "dependency_check",
                        "version": target["version"],
                        "depends_on": target["depends_on"],
                        "status": "warning",
                        "message": "cannot verify dependencies without --migrations-dir",
                    }
                )
            emit({"event": "validation_complete", "version": target["version"], "status": "valid"})
            completed = True
            return

        discovered = discover_migrations(migrations_directory)
        target_resolved = target_path.resolve()
        discovered_target = next(
            (version for version, (path, _) in discovered.items() if path.resolve() == target_resolved), None
        )
        if discovered_target is None:
            if target["version"] in discovered:
                raise MigrationError(f"duplicate migration version {target['version']}")
            discovered[target["version"]] = (target_path, target)
        elif discovered_target != target["version"]:
            raise MigrationError(f"invalid migration file: {target_path.name}")

        migrations = {version: migration for version, (_, migration) in discovered.items()}
        emit(
            {
                "event": "dependency_check",
                "version": target["version"],
                "depends_on": target["depends_on"],
                "status": "ok",
            }
        )
        validate_dependency_graph(migrations)
        dependency_order(migrations)
        emit({"event": "validation_complete", "version": target["version"], "status": "valid"})
        completed = True
    except DependencyCycleError as exc:
        emit({"event": "circular_dependency_detected", "cycle": exc.cycle, "status": "error"})
        if not completed:
            emit({"event": "validation_complete", "version": target.get("version", None) if 'target' in locals() else None, "status": "invalid"})
        raise
    except MigrationError:
        if not completed and 'target' in locals():
            emit({"event": "validation_complete", "version": target["version"], "status": "invalid"})
        raise


def migrate(migration_path: str, database_path: str) -> bool:
    migration = load_migration(migration_path)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        # SQLite ignores foreign_keys changes while a transaction is active,
        # so enable referential enforcement before the migration transaction.
        connection.execute("PRAGMA foreign_keys = ON")
        create_migrations_table(connection)

        version = migration["version"]
        already_applied = connection.execute(
            "SELECT 1 FROM _migrations WHERE version = ?", (version,)
        ).fetchone()
        if already_applied is not None:
            print(f"Warning: Migration version {version} already applied, skipping", file=sys.stderr)
            emit({"event": "migration_skipped", "version": version, "reason": "already_applied"})
            return False

        ensure_single_migration_dependencies(connection, migration)

        events: list[dict[str, Any]] = []
        stored_operations: list[dict[str, Any]] = []
        rebuild_operations = {
            "drop_column",
            "add_foreign_key",
            "drop_foreign_key",
            "add_check_constraint",
            "drop_check_constraint",
        }
        recreates_tables = any(
            operation["type"] in rebuild_operations for operation in migration["operations"]
        )
        # Recreating a table that is already referenced by another table makes
        # SQLite treat DROP TABLE as a parent deletion when enforcement is on.
        # Disable it only for this internal rebuild window, then validate the
        # completed schema and data before committing.
        if recreates_tables:
            connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN")
        try:
            for operation in migration["operations"]:
                stored_operation = prepare_operation_metadata(connection, operation)
                apply_operation(connection, operation)
                stored_operations.append(stored_operation)
                events.append(operation_event(operation, version))
            if recreates_tables or any(
                operation["type"] == "add_foreign_key" for operation in migration["operations"]
            ):
                violations = connection.execute("PRAGMA foreign_key_check").fetchall()
                if violations:
                    parent = violations[0][2]
                    raise MigrationError(
                        f"foreign key violation: referenced row in '{parent}' table does not exist"
                    )
            connection.execute(
                """
                INSERT INTO _migrations (version, description, operations, rollback_operations, depends_on)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    version,
                    migration["description"],
                    json.dumps(stored_operations, ensure_ascii=False),
                    (
                        json.dumps(migration["rollback_operations"], ensure_ascii=False)
                        if migration["rollback_operations"] is not None
                        else None
                    ),
                    json.dumps(migration["depends_on"]),
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if recreates_tables:
                connection.execute("PRAGMA foreign_keys = ON")

        for event in events:
            emit(event)
        emit(
            {
                "event": "migration_complete",
                "version": version,
                "operations_count": len(migration["operations"]),
            }
        )
        return True
    except sqlite3.Error as exc:
        raise MigrationError(f"SQL error: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def current_database_version(database_path: str) -> int | None:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        create_migrations_table(connection)
        return connection.execute("SELECT MAX(version) FROM _migrations").fetchone()[0]
    except sqlite3.Error as exc:
        raise MigrationError(f"SQL error: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def migrate_all(migrations_directory: str, database_path: str) -> None:
    emit({"event": "scan_started", "directory": migrations_directory})
    discovered = discover_migrations(migrations_directory)
    for version in sorted(discovered):
        path, _ = discovered[version]
        emit({"event": "migration_discovered", "file": path.name, "version": version})
    emit({"event": "scan_complete", "migrations_found": len(discovered)})
    emit({"event": "dependency_resolution_started"})
    migrations = {version: migration for version, (_, migration) in discovered.items()}
    validate_dependency_graph(migrations)
    order = dependency_order(migrations)
    emit({"event": "dependency_resolved", "order": order})

    applied_count = 0
    skipped_count = 0
    for version in order:
        path, migration = discovered[version]
        emit(
            {
                "event": "migration_started",
                "version": version,
                "description": migration["description"],
            }
        )
        if migrate(str(path), database_path):
            applied_count += 1
        else:
            skipped_count += 1
    emit(
        {
            "event": "batch_complete",
            "migrations_applied": applied_count,
            "migrations_skipped": skipped_count,
            "final_version": current_database_version(database_path),
        }
    )


def decode_operation_history(value: Any, version: int, field: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise MigrationError(f"cannot rollback version {version}: invalid {field} metadata") from exc
    if not isinstance(decoded, list) or not all(isinstance(operation, dict) for operation in decoded):
        raise MigrationError(f"cannot rollback version {version}: invalid {field} metadata")
    return decoded


def rollback_event(operation: dict[str, Any], version: int) -> dict[str, Any]:
    event = operation_event(operation, version)
    event["event"] = "operation_rolled_back"
    return event


def rollback(database_path: str, to_version: int | None, count: int) -> None:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        create_migrations_table(connection)
        applied = list(
            connection.execute(
                """
                SELECT version, description, operations, rollback_operations, depends_on
                FROM _migrations
                ORDER BY version DESC
                """
            )
        )
        if not applied:
            raise MigrationError("no migrations to rollback")

        if to_version is not None:
            if not any(row["version"] == to_version for row in applied):
                raise MigrationError(f"version {to_version} not found")
            selected = [row for row in applied if row["version"] > to_version]
        else:
            selected = applied[:count]

        selected_versions = {row["version"] for row in selected}
        for row in applied:
            if row["version"] in selected_versions:
                continue
            dependencies = decode_dependency_history(row["depends_on"], row["version"])
            broken_dependencies = selected_versions.intersection(dependencies)
            if broken_dependencies:
                dependency = min(broken_dependencies)
                raise MigrationError(
                    f"cannot rollback: migration version {row['version']} depends on version {dependency}"
                )

        planned: list[tuple[sqlite3.Row, list[tuple[dict[str, Any], dict[str, Any]]]]] = []
        for row in selected:
            version = row["version"]
            operations = decode_operation_history(row["operations"], version, "operations")
            if row["rollback_operations"] is not None:
                explicit = decode_operation_history(
                    row["rollback_operations"], version, "rollback_operations"
                )
                plan = [(operation, operation) for operation in explicit]
            else:
                plan = automatic_rollback_plan(operations, version)
            planned.append((row, plan))

        events: list[dict[str, Any]] = []
        # The whole batch is atomic. Enforcement is temporarily disabled only
        # while SQLite tables are physically rebuilt; foreign_key_check below
        # validates the completed rollback before the transaction is committed.
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN")
        try:
            for row, plan in planned:
                version = row["version"]
                events.append(
                    {
                        "event": "rollback_started",
                        "version": version,
                        "description": row["description"],
                    }
                )
                for instruction, display_operation in plan:
                    execute_rollback_instruction(connection, instruction)
                    events.append(rollback_event(display_operation, version))
                connection.execute("DELETE FROM _migrations WHERE version = ?", (version,))
                events.append({"event": "rollback_complete", "version": version})

            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise MigrationError("cannot rollback: foreign key constraint violation")
            final_row = connection.execute("SELECT MAX(version) FROM _migrations").fetchone()
            final_version = final_row[0]
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")

        for event in events:
            emit(event)
        emit(
            {
                "event": "rollback_finished",
                "versions_rolled_back": [row["version"] for row, _ in planned],
                "final_version": final_version,
            }
        )
    except sqlite3.Error as exc:
        raise MigrationError(f"rollback failed: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def parse_positive_option(value: str, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise MigrationError(f"{option} must be a positive integer") from exc
    if parsed <= 0:
        raise MigrationError(f"{option} must be a positive integer")
    return parsed


def main(arguments: list[str]) -> int:
    try:
        if len(arguments) == 3 and arguments[0] == "migrate":
            migrate(arguments[1], arguments[2])
            return 0

        if arguments and arguments[0] == "validate":
            if len(arguments) == 2:
                validate_command(arguments[1], None)
                return 0
            if len(arguments) == 4 and arguments[2] == "--migrations-dir":
                validate_command(arguments[1], arguments[3])
                return 0
            raise MigrationError(
                "usage: migration_tool.py validate <migration.json> [--migrations-dir <dir>]"
            )

        if arguments and arguments[0] == "migrate-all":
            if len(arguments) == 4 and arguments[1] == "--migrations-dir":
                migrate_all(arguments[2], arguments[3])
                return 0
            raise MigrationError(
                "usage: migration_tool.py migrate-all --migrations-dir <dir> <database.db>"
            )

        if len(arguments) >= 2 and arguments[0] == "rollback":
            database_path = arguments[1]
            to_version: int | None = None
            count = 1
            count_supplied = False
            index = 2
            while index < len(arguments):
                option = arguments[index]
                if option not in {"--to-version", "--count"} or index + 1 >= len(arguments):
                    raise MigrationError(
                        "usage: migration_tool.py rollback <database.db> [--to-version <version>] [--count <n>]"
                    )
                value = parse_positive_option(arguments[index + 1], option)
                if option == "--to-version":
                    if to_version is not None:
                        raise MigrationError("--to-version may be specified only once")
                    to_version = value
                else:
                    if count_supplied:
                        raise MigrationError("--count may be specified only once")
                    count = value
                    count_supplied = True
                index += 2
            if to_version is not None and count_supplied:
                raise MigrationError("--to-version and --count cannot be used together")
            rollback(database_path, to_version, count)
            return 0

        raise MigrationError(
            "usage: migration_tool.py migrate <migration.json> <database.db> | "
            "migration_tool.py rollback <database.db> [--to-version <version>] [--count <n>] | "
            "migration_tool.py validate <migration.json> [--migrations-dir <dir>] | "
            "migration_tool.py migrate-all --migrations-dir <dir> <database.db>"
        )
    except MigrationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
