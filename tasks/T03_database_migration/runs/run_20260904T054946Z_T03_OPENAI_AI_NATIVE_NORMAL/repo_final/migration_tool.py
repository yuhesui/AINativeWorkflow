#!/usr/bin/env python3
"""Apply the checkpoint-1 JSON schema migrations to a SQLite database."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any


SUPPORTED_TYPES = {"INTEGER", "TEXT", "REAL", "BLOB", "TIMESTAMP"}
FOREIGN_KEY_ACTIONS = {"CASCADE", "RESTRICT", "SET NULL", "NO ACTION", "SET DEFAULT"}
IDENTIFIER_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
)


class MigrationError(Exception):
    """A user-facing migration failure."""


class CommandError(MigrationError):
    """A command failure that must still emit accumulated JSONL diagnostics."""

    def __init__(self, message: str, events: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.events = events


class MigrationArgumentParser(argparse.ArgumentParser):
    """Make invalid CLI usage follow the command's error-output contract."""

    def error(self, message: str) -> None:
        raise MigrationError(f"invalid command arguments: {message}")


def quote_identifier(identifier: str) -> str:
    """Return a validated SQLite identifier quoted for SQL construction."""
    if not isinstance(identifier, str) or not identifier:
        raise MigrationError("invalid migration schema: identifier must be a non-empty string")
    if identifier[0] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
        raise MigrationError(f"invalid migration schema: invalid identifier '{identifier}'")
    if any(character not in IDENTIFIER_CHARS for character in identifier):
        raise MigrationError(f"invalid migration schema: invalid identifier '{identifier}'")
    return f'"{identifier}"'


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MigrationError(f"invalid migration schema: {context} must be an object")
    return value


def require_string(mapping: dict[str, Any], field: str, context: str) -> str:
    if field not in mapping:
        raise MigrationError(
            f"invalid migration schema: missing required field '{field}' in {context}"
        )
    value = mapping[field]
    if not isinstance(value, str):
        raise MigrationError(f"invalid migration schema: {context}.{field} must be a string")
    return value


def optional_boolean(mapping: dict[str, Any], field: str, context: str) -> bool:
    value = mapping.get(field, False)
    if not isinstance(value, bool):
        raise MigrationError(f"invalid migration schema: {context}.{field} must be a boolean")
    return value


def require_identifier_list(
    mapping: dict[str, Any], field: str, context: str
) -> list[str]:
    if field not in mapping:
        raise MigrationError(
            f"invalid migration schema: missing required field '{field}' in {context}"
        )
    value = mapping[field]
    if not isinstance(value, list) or not value:
        raise MigrationError(
            f"invalid migration schema: {context}.{field} must be a non-empty array"
        )
    identifiers: list[str] = []
    for item_number, item in enumerate(value):
        if not isinstance(item, str):
            raise MigrationError(
                f"invalid migration schema: {context}.{field}[{item_number}] must be a string"
            )
        quote_identifier(item)
        identifiers.append(item)
    if len(identifiers) != len(set(identifiers)):
        raise MigrationError(
            f"invalid migration schema: {context}.{field} contains duplicate identifiers"
        )
    return identifiers


def optional_foreign_key_action(
    mapping: dict[str, Any], field: str, context: str
) -> str:
    action = mapping.get(field, "NO ACTION")
    if not isinstance(action, str) or action not in FOREIGN_KEY_ACTIONS:
        expected = ", ".join(sorted(FOREIGN_KEY_ACTIONS))
        raise MigrationError(
            f"invalid migration schema: {context}.{field} must be one of {expected}"
        )
    return action


def validate_column(value: Any, context: str) -> dict[str, Any]:
    column = require_mapping(value, context)
    name = require_string(column, "name", context)
    column_type = require_string(column, "type", context)
    quote_identifier(name)
    if column_type not in SUPPORTED_TYPES:
        supported = ", ".join(sorted(SUPPORTED_TYPES))
        raise MigrationError(
            f"invalid migration schema: {context}.type must be one of {supported}"
        )

    primary_key = optional_boolean(column, "primary_key", context)
    auto_increment = optional_boolean(column, "auto_increment", context)
    not_null = optional_boolean(column, "not_null", context)
    unique = optional_boolean(column, "unique", context)
    default = column.get("default")
    if default is not None and not isinstance(default, str):
        raise MigrationError(f"invalid migration schema: {context}.default must be a string or null")
    if auto_increment and (column_type != "INTEGER" or not primary_key):
        raise MigrationError(
            "invalid migration schema: auto_increment requires an INTEGER primary_key column"
        )

    return {
        "name": name,
        "type": column_type,
        "primary_key": primary_key,
        "auto_increment": auto_increment,
        "not_null": not_null,
        "unique": unique,
        "default": default,
    }


def validate_migration(value: Any) -> dict[str, Any]:
    migration = require_mapping(value, "migration")

    if "version" not in migration:
        raise MigrationError("invalid migration schema: missing required field 'version'")
    version = migration["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
        raise MigrationError("invalid migration schema: version must be a positive integer")

    description = require_string(migration, "description", "migration")
    if "operations" not in migration:
        raise MigrationError("invalid migration schema: missing required field 'operations'")
    operations_value = migration["operations"]
    if not isinstance(operations_value, list):
        raise MigrationError("invalid migration schema: operations must be an array")

    depends_on_value = migration.get("depends_on", [])
    if not isinstance(depends_on_value, list):
        raise MigrationError("invalid migration schema: depends_on must be an array")
    depends_on: list[int] = []
    for dependency_number, dependency in enumerate(depends_on_value):
        if isinstance(dependency, bool) or not isinstance(dependency, int) or dependency <= 0:
            raise MigrationError(
                f"invalid migration schema: depends_on[{dependency_number}] must be a positive integer"
            )
        depends_on.append(dependency)
    if len(depends_on) != len(set(depends_on)):
        raise MigrationError("invalid migration schema: depends_on contains duplicate versions")

    operations: list[dict[str, Any]] = []
    for operation_number, raw_operation in enumerate(operations_value, start=1):
        context = f"operations[{operation_number - 1}]"
        operation = require_mapping(raw_operation, context)
        operation_type = require_string(operation, "type", context)
        if operation_type not in {
            "create_table",
            "add_column",
            "drop_column",
            "transform_data",
            "migrate_column_data",
            "backfill_data",
            "add_foreign_key",
            "drop_foreign_key",
            "create_index",
            "drop_index",
            "add_check_constraint",
            "drop_check_constraint",
        }:
            raise MigrationError(
                f"invalid migration schema: unsupported operation type '{operation_type}'"
            )

        if operation_type == "drop_index":
            name = require_string(operation, "name", context)
            quote_identifier(name)
            operations.append({"type": operation_type, "name": name})
            continue

        table = require_string(operation, "table", context)
        quote_identifier(table)
        normalized: dict[str, Any] = {"type": operation_type, "table": table}
        if operation_type == "create_table":
            if "columns" not in operation:
                raise MigrationError(
                    f"invalid migration schema: missing required field 'columns' in {context}"
                )
            columns_value = operation["columns"]
            if not isinstance(columns_value, list) or not columns_value:
                raise MigrationError(
                    f"invalid migration schema: {context}.columns must be a non-empty array"
                )
            columns = [
                validate_column(raw_column, f"{context}.columns[{column_number}]")
                for column_number, raw_column in enumerate(columns_value)
            ]
            column_names = [column["name"] for column in columns]
            if len(column_names) != len(set(column_names)):
                raise MigrationError(
                    f"invalid migration schema: {context}.columns contains duplicate names"
                )
            if sum(column["primary_key"] for column in columns) > 1:
                raise MigrationError(
                    "invalid migration schema: create_table supports at most one primary_key column"
                )
            normalized["columns"] = columns
        elif operation_type == "add_column":
            if "column" not in operation:
                raise MigrationError(
                    f"invalid migration schema: missing required field 'column' in {context}"
                )
            normalized["column"] = validate_column(operation["column"], f"{context}.column")
        elif operation_type == "drop_column":
            column = require_string(operation, "column", context)
            quote_identifier(column)
            normalized["column"] = column
        elif operation_type == "transform_data":
            if "transformations" not in operation:
                raise MigrationError(
                    f"invalid migration schema: missing required field 'transformations' in {context}"
                )
            transformations_value = operation["transformations"]
            if not isinstance(transformations_value, list) or not transformations_value:
                raise MigrationError(
                    f"invalid migration schema: {context}.transformations must be a non-empty array"
                )
            transformations: list[dict[str, str]] = []
            for transformation_number, raw_transformation in enumerate(transformations_value):
                transformation_context = (
                    f"{context}.transformations[{transformation_number}]"
                )
                transformation = require_mapping(raw_transformation, transformation_context)
                column = require_string(transformation, "column", transformation_context)
                expression = require_string(
                    transformation, "expression", transformation_context
                )
                quote_identifier(column)
                transformations.append({"column": column, "expression": expression})
            normalized["transformations"] = transformations
        elif operation_type == "migrate_column_data":
            from_column = require_string(operation, "from_column", context)
            to_column = require_string(operation, "to_column", context)
            quote_identifier(from_column)
            quote_identifier(to_column)
            default_value = operation.get("default_value")
            if default_value is not None and not isinstance(
                default_value, (str, int, float, bool)
            ):
                raise MigrationError(
                    f"invalid migration schema: {context}.default_value must be a scalar or null"
                )
            normalized["from_column"] = from_column
            normalized["to_column"] = to_column
            normalized["default_value"] = default_value
        elif operation_type == "backfill_data":
            column = require_string(operation, "column", context)
            quote_identifier(column)
            if "value" not in operation:
                raise MigrationError(
                    f"invalid migration schema: missing required field 'value' in {context}"
                )
            value = operation["value"]
            if value is not None and not isinstance(value, (str, int, float, bool)):
                raise MigrationError(
                    f"invalid migration schema: {context}.value must be a scalar or null"
                )
            where = operation.get("where")
            if where is not None and not isinstance(where, str):
                raise MigrationError(
                    f"invalid migration schema: {context}.where must be a string or null"
                )
            normalized["column"] = column
            normalized["value"] = value
            normalized["where"] = where
        elif operation_type == "add_foreign_key":
            name = require_string(operation, "name", context)
            quote_identifier(name)
            columns = require_identifier_list(operation, "columns", context)
            if "references" not in operation:
                raise MigrationError(
                    f"invalid migration schema: missing required field 'references' in {context}"
                )
            references = require_mapping(operation["references"], f"{context}.references")
            referenced_table = require_string(
                references, "table", f"{context}.references"
            )
            quote_identifier(referenced_table)
            referenced_columns = require_identifier_list(
                references, "columns", f"{context}.references"
            )
            if len(columns) != len(referenced_columns):
                raise MigrationError(
                    f"invalid migration schema: {context}.columns and references.columns must have equal lengths"
                )
            normalized.update(
                {
                    "name": name,
                    "columns": columns,
                    "references": {
                        "table": referenced_table,
                        "columns": referenced_columns,
                    },
                    "on_delete": optional_foreign_key_action(operation, "on_delete", context),
                    "on_update": optional_foreign_key_action(operation, "on_update", context),
                }
            )
        elif operation_type == "drop_foreign_key":
            name = require_string(operation, "name", context)
            quote_identifier(name)
            normalized["name"] = name
        elif operation_type == "create_index":
            name = require_string(operation, "name", context)
            quote_identifier(name)
            normalized["name"] = name
            normalized["columns"] = require_identifier_list(operation, "columns", context)
            normalized["unique"] = optional_boolean(operation, "unique", context)
        elif operation_type == "add_check_constraint":
            name = require_string(operation, "name", context)
            expression = require_string(operation, "expression", context)
            quote_identifier(name)
            normalized["name"] = name
            normalized["expression"] = expression
        else:  # drop_check_constraint
            name = require_string(operation, "name", context)
            quote_identifier(name)
            normalized["name"] = name

        operations.append(normalized)

    rollback_operations: list[dict[str, Any]] | None = None
    if "rollback_operations" in migration:
        raw_rollback_operations = migration["rollback_operations"]
        if not isinstance(raw_rollback_operations, list) or not raw_rollback_operations:
            raise MigrationError(
                "invalid migration schema: rollback_operations must be a non-empty array"
            )
        rollback_operations = validate_migration(
            {
                "version": version,
                "description": description,
                "operations": raw_rollback_operations,
            }
        )["operations"]

    return {
        "version": version,
        "description": description,
        "operations": operations,
        "rollback_operations": rollback_operations,
        "depends_on": depends_on,
    }


def column_sql(column: dict[str, Any]) -> str:
    """Render a validated, checkpoint-1 column definition."""
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
        parts.extend(["DEFAULT", column["default"]])
    return " ".join(parts)


def table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    return any(row[1] == column for row in rows)


def apply_create_table(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    if table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' already exists")
    definitions = ", ".join(column_sql(column) for column in operation["columns"])
    connection.execute(f"CREATE TABLE {quote_identifier(table)} ({definitions})")


def apply_add_column(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    column = operation["column"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    if column_exists(connection, table, column["name"]):
        raise MigrationError(
            f"invalid operation: column '{column['name']}' already exists in table '{table}'"
        )
    connection.execute(
        f"ALTER TABLE {quote_identifier(table)} ADD COLUMN {column_sql(column)}"
    )


def table_sql(connection: sqlite3.Connection, table: str) -> str:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    if row is None or row[0] is None:
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    return row[0]


def initialize_constraint_metadata(connection: sqlite3.Connection) -> None:
    """Keep names needed for SQLite constraint recreation in durable local metadata."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS _migration_foreign_keys ("
        "table_name TEXT NOT NULL, "
        "name TEXT NOT NULL, "
        "columns_json TEXT NOT NULL, "
        "referenced_table TEXT NOT NULL, "
        "referenced_columns_json TEXT NOT NULL, "
        "on_delete TEXT NOT NULL, "
        "on_update TEXT NOT NULL, "
        "PRIMARY KEY (table_name, name)"
        ")"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS _migration_check_constraints ("
        "table_name TEXT NOT NULL, "
        "name TEXT NOT NULL, "
        "expression TEXT NOT NULL, "
        "PRIMARY KEY (table_name, name)"
        ")"
    )


def initialize_migration_tracking(connection: sqlite3.Connection) -> None:
    """Initialize and upgrade the durable migration history used by rollback."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS _migrations ("
        "version INTEGER PRIMARY KEY, "
        "description TEXT NOT NULL, "
        "applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "operations TEXT NOT NULL DEFAULT '[]', "
        "rollback_operations TEXT"
        ")"
    )
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(_migrations)").fetchall()
    }
    if "operations" not in columns:
        connection.execute(
            "ALTER TABLE _migrations ADD COLUMN operations TEXT NOT NULL DEFAULT '[]'"
        )
    if "rollback_operations" not in columns:
        connection.execute("ALTER TABLE _migrations ADD COLUMN rollback_operations TEXT")


def managed_foreign_keys(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT name, columns_json, referenced_table, referenced_columns_json, on_delete, on_update "
        "FROM _migration_foreign_keys WHERE table_name = ? ORDER BY name",
        (table,),
    ).fetchall()
    return [
        {
            "name": row[0],
            "columns": json.loads(row[1]),
            "references": {"table": row[2], "columns": json.loads(row[3])},
            "on_delete": row[4],
            "on_update": row[5],
        }
        for row in rows
    ]


def managed_check_constraints(
    connection: sqlite3.Connection, table: str
) -> list[dict[str, str]]:
    rows = connection.execute(
        "SELECT name, expression FROM _migration_check_constraints "
        "WHERE table_name = ? ORDER BY name",
        (table,),
    ).fetchall()
    return [{"name": row[0], "expression": row[1]} for row in rows]


def custom_index_sqls(connection: sqlite3.Connection, table: str) -> list[str]:
    """Capture explicit indexes; automatic UNIQUE/PK indexes follow table creation."""
    rows = connection.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type = 'index' AND tbl_name = ? AND sql IS NOT NULL ORDER BY name",
        (table,),
    ).fetchall()
    return [row[0] for row in rows]


def foreign_key_sql(foreign_key: dict[str, Any]) -> str:
    local_columns = ", ".join(quote_identifier(column) for column in foreign_key["columns"])
    referenced_columns = ", ".join(
        quote_identifier(column) for column in foreign_key["references"]["columns"]
    )
    return (
        f"CONSTRAINT {quote_identifier(foreign_key['name'])} FOREIGN KEY ({local_columns}) "
        f"REFERENCES {quote_identifier(foreign_key['references']['table'])} ({referenced_columns}) "
        f"ON DELETE {foreign_key['on_delete']} ON UPDATE {foreign_key['on_update']}"
    )


def check_constraint_sql(constraint: dict[str, str]) -> str:
    return (
        f"CONSTRAINT {quote_identifier(constraint['name'])} "
        f"CHECK ({constraint['expression']})"
    )


def unique_column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    """Return columns with a per-column UNIQUE constraint created by this tool."""
    unique_columns: set[str] = set()
    index_rows = connection.execute(
        f"PRAGMA index_list({quote_identifier(table)})"
    ).fetchall()
    for index in index_rows:
        # index_list returns (seq, name, unique, origin, partial).  Only origin
        # "u" is the inline UNIQUE constraint the checkpoint schema represents.
        if not index[2] or index[3] != "u":
            continue
        index_name = index[1]
        index_columns = connection.execute(
            f"PRAGMA index_info({quote_identifier(index_name)})"
        ).fetchall()
        if len(index_columns) == 1:
            unique_columns.add(index_columns[0][2])
    return unique_columns


def current_columns(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    """Read supported tool-created column definitions for table reconstruction."""
    rows = connection.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    if not rows:
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    primary_keys = [row for row in rows if row[5]]
    if len(primary_keys) > 1:
        raise MigrationError(
            f"invalid operation: table '{table}' has an unsupported composite primary key"
        )
    table_definition = table_sql(connection, table)
    has_autoincrement = re.search(r"\bAUTOINCREMENT\b", table_definition, re.IGNORECASE) is not None
    unique_columns = unique_column_names(connection, table)
    columns: list[dict[str, Any]] = []
    for _, name, declared_type, not_null, default, primary_key in rows:
        if declared_type not in SUPPORTED_TYPES:
            raise MigrationError(
                f"invalid operation: cannot reconstruct unsupported type '{declared_type}' "
                f"for column '{name}'"
            )
        if has_autoincrement and primary_key and declared_type != "INTEGER":
            raise MigrationError(
                f"invalid operation: AUTOINCREMENT primary key '{name}' must be INTEGER"
            )
        columns.append(
            {
                "name": name,
                "type": declared_type,
                "primary_key": bool(primary_key),
                "auto_increment": bool(has_autoincrement and primary_key),
                "not_null": bool(not_null),
                "unique": name in unique_columns,
                "default": default,
            }
        )
    return columns


def reconstructed_columns(
    connection: sqlite3.Connection, table: str, dropped_column: str
) -> list[dict[str, Any]]:
    """Return current supported columns with a permitted column removed."""
    columns = current_columns(connection, table)
    matching = [column for column in columns if column["name"] == dropped_column]
    if not matching:
        raise MigrationError(
            f"invalid operation: column '{dropped_column}' does not exist in table '{table}'"
        )
    if len(columns) == 1:
        raise MigrationError(
            f"invalid operation: cannot drop the only column from table '{table}'"
        )
    if matching[0]["primary_key"]:
        raise MigrationError(
            f"invalid operation: cannot drop primary key column '{dropped_column}'"
        )
    return [column for column in columns if column["name"] != dropped_column]


def replacement_table_name(connection: sqlite3.Connection, table: str) -> str:
    """Generate an identifier-safe replacement name that cannot collide locally."""
    for _ in range(100):
        candidate = f"_migration_tmp_{table}_{uuid.uuid4().hex}"
        if not table_exists(connection, candidate):
            return candidate
    raise MigrationError(f"SQL error: could not allocate replacement table for '{table}'")


def rebuild_table(
    connection: sqlite3.Connection,
    table: str,
    columns: list[dict[str, Any]],
    foreign_keys: list[dict[str, Any]],
    check_constraints: list[dict[str, str]],
) -> None:
    """Atomically recreate a supported table, including managed constraints/indexes."""
    replacement = replacement_table_name(connection, table)
    definitions = [column_sql(column) for column in columns]
    definitions.extend(foreign_key_sql(foreign_key) for foreign_key in foreign_keys)
    definitions.extend(check_constraint_sql(constraint) for constraint in check_constraints)
    copied_columns = ", ".join(quote_identifier(column["name"]) for column in columns)
    indexes = custom_index_sqls(connection, table)
    connection.execute(
        f"CREATE TABLE {quote_identifier(replacement)} ({', '.join(definitions)})"
    )
    connection.execute(
        f"INSERT INTO {quote_identifier(replacement)} ({copied_columns}) "
        f"SELECT {copied_columns} FROM {quote_identifier(table)}"
    )
    connection.execute(f"DROP TABLE {quote_identifier(table)}")
    connection.execute(
        f"ALTER TABLE {quote_identifier(replacement)} RENAME TO {quote_identifier(table)}"
    )
    for index_sql in indexes:
        connection.execute(index_sql)


def apply_drop_column(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    """Recreate a tool-created table while retaining its supported column semantics."""
    table = operation["table"]
    dropped_column = operation["column"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")

    columns = reconstructed_columns(connection, table, dropped_column)
    foreign_keys = managed_foreign_keys(connection, table)
    if any(dropped_column in foreign_key["columns"] for foreign_key in foreign_keys):
        raise MigrationError(
            f"invalid operation: cannot drop column '{dropped_column}' used by a foreign key"
        )
    rebuild_table(
        connection,
        table,
        columns,
        foreign_keys,
        managed_check_constraints(connection, table),
    )


def require_existing_column(connection: sqlite3.Connection, table: str, column: str) -> None:
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    if not column_exists(connection, table, column):
        raise MigrationError(
            f"invalid operation: column '{column}' does not exist in table '{table}'"
        )


def apply_transform_data(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    for transformation in operation["transformations"]:
        column = transformation["column"]
        require_existing_column(connection, table, column)
        connection.execute(
            f"UPDATE {quote_identifier(table)} SET {quote_identifier(column)} = "
            f"{transformation['expression']}"
        )


def apply_migrate_column_data(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    from_column = operation["from_column"]
    to_column = operation["to_column"]
    require_existing_column(connection, table, from_column)
    require_existing_column(connection, table, to_column)
    if operation["default_value"] is None:
        connection.execute(
            f"UPDATE {quote_identifier(table)} SET {quote_identifier(to_column)} = "
            f"{quote_identifier(from_column)}"
        )
    else:
        connection.execute(
            f"UPDATE {quote_identifier(table)} SET {quote_identifier(to_column)} = "
            f"COALESCE({quote_identifier(from_column)}, ?)",
            (operation["default_value"],),
        )


def apply_backfill_data(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    column = operation["column"]
    require_existing_column(connection, table, column)
    where = operation["where"]
    where_sql = "" if where is None else f" WHERE {where}"
    value = operation["value"]
    if isinstance(value, str):
        connection.execute(
            f"UPDATE {quote_identifier(table)} SET {quote_identifier(column)} = {value}{where_sql}"
        )
    else:
        connection.execute(
            f"UPDATE {quote_identifier(table)} SET {quote_identifier(column)} = ?{where_sql}",
            (value,),
        )


def require_existing_columns(
    connection: sqlite3.Connection, table: str, columns: list[str]
) -> None:
    for column in columns:
        require_existing_column(connection, table, column)


def table_column_definitions(
    connection: sqlite3.Connection, table: str
) -> dict[str, dict[str, Any]]:
    return {column["name"]: column for column in current_columns(connection, table)}


def referenced_columns_form_key(
    connection: sqlite3.Connection, table: str, columns: list[str]
) -> bool:
    rows = connection.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    primary_key_columns = [row[1] for row in sorted(rows, key=lambda row: row[5]) if row[5]]
    if primary_key_columns == columns:
        return True
    for index in connection.execute(f"PRAGMA index_list({quote_identifier(table)})").fetchall():
        if not index[2]:
            continue
        index_columns = connection.execute(
            f"PRAGMA index_info({quote_identifier(index[1])})"
        ).fetchall()
        if [row[2] for row in sorted(index_columns, key=lambda row: row[0])] == columns:
            return True
    return False


def assert_foreign_key_data_valid(
    connection: sqlite3.Connection, foreign_key: dict[str, Any]
) -> None:
    table = foreign_key["table"]
    reference = foreign_key["references"]
    local_columns = foreign_key["columns"]
    referenced_columns = reference["columns"]
    child_not_null = " AND ".join(
        f"child.{quote_identifier(column)} IS NOT NULL" for column in local_columns
    )
    joins = " AND ".join(
        f"parent.{quote_identifier(parent_column)} = child.{quote_identifier(child_column)}"
        for child_column, parent_column in zip(local_columns, referenced_columns)
    )
    violation = connection.execute(
        f"SELECT 1 FROM {quote_identifier(table)} AS child "
        f"WHERE {child_not_null} AND NOT EXISTS ("
        f"SELECT 1 FROM {quote_identifier(reference['table'])} AS parent WHERE {joins}"
        ") LIMIT 1"
    ).fetchone()
    if violation is not None:
        raise MigrationError(
            f"foreign key violation: referenced row in '{reference['table']}' table does not exist"
        )


def apply_add_foreign_key(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    reference = operation["references"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    if not table_exists(connection, reference["table"]):
        raise MigrationError(
            f"cannot add foreign key: referenced table '{reference['table']}' does not exist"
        )
    require_existing_columns(connection, table, operation["columns"])
    for column in reference["columns"]:
        if not column_exists(connection, reference["table"], column):
            raise MigrationError(
                f"cannot add foreign key: referenced column '{reference['table']}.{column}' does not exist"
            )
    local_definitions = table_column_definitions(connection, table)
    referenced_definitions = table_column_definitions(connection, reference["table"])
    for local, referenced in zip(operation["columns"], reference["columns"]):
        if local_definitions[local]["type"] != referenced_definitions[referenced]["type"]:
            raise MigrationError(
                f"cannot add foreign key: incompatible column types '{table}.{local}' and "
                f"'{reference['table']}.{referenced}'"
            )
    if not referenced_columns_form_key(connection, reference["table"], reference["columns"]):
        raise MigrationError(
            f"cannot add foreign key: referenced columns in '{reference['table']}' are not a primary or unique key"
        )

    existing = managed_foreign_keys(connection, table)
    if any(foreign_key["name"] == operation["name"] for foreign_key in existing):
        raise MigrationError(
            f"invalid operation: foreign key constraint '{operation['name']}' already exists in table '{table}'"
        )
    foreign_key = {
        "name": operation["name"],
        "table": table,
        "columns": operation["columns"],
        "references": reference,
        "on_delete": operation["on_delete"],
        "on_update": operation["on_update"],
    }
    assert_foreign_key_data_valid(connection, foreign_key)
    rebuilt_foreign_keys = existing + [{key: value for key, value in foreign_key.items() if key != "table"}]
    rebuild_table(
        connection,
        table,
        current_columns(connection, table),
        rebuilt_foreign_keys,
        managed_check_constraints(connection, table),
    )
    connection.execute(
        "INSERT INTO _migration_foreign_keys "
        "(table_name, name, columns_json, referenced_table, referenced_columns_json, on_delete, on_update) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            table,
            foreign_key["name"],
            json.dumps(foreign_key["columns"]),
            reference["table"],
            json.dumps(reference["columns"]),
            foreign_key["on_delete"],
            foreign_key["on_update"],
        ),
    )


def apply_drop_foreign_key(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    existing = managed_foreign_keys(connection, table)
    matching = [foreign_key for foreign_key in existing if foreign_key["name"] == operation["name"]]
    if not matching:
        raise MigrationError(
            f"invalid operation: foreign key constraint '{operation['name']}' does not exist in table '{table}'"
        )
    rebuild_table(
        connection,
        table,
        current_columns(connection, table),
        [foreign_key for foreign_key in existing if foreign_key["name"] != operation["name"]],
        managed_check_constraints(connection, table),
    )
    connection.execute(
        "DELETE FROM _migration_foreign_keys WHERE table_name = ? AND name = ?",
        (table, operation["name"]),
    )


def apply_create_index(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    require_existing_columns(connection, table, operation["columns"])
    existing = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE name = ?", (operation["name"],)
    ).fetchone()
    if existing is not None:
        raise MigrationError(f"index '{operation['name']}' already exists")
    uniqueness = "UNIQUE " if operation["unique"] else ""
    columns = ", ".join(quote_identifier(column) for column in operation["columns"])
    connection.execute(
        f"CREATE {uniqueness}INDEX {quote_identifier(operation['name'])} "
        f"ON {quote_identifier(table)} ({columns})"
    )


def apply_drop_index(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    row = connection.execute(
        "SELECT type, sql FROM sqlite_master WHERE name = ?", (operation["name"],)
    ).fetchone()
    if row is None or row[0] != "index" or row[1] is None:
        raise MigrationError(f"invalid operation: index '{operation['name']}' does not exist")
    connection.execute(f"DROP INDEX {quote_identifier(operation['name'])}")


def apply_add_check_constraint(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    checks = managed_check_constraints(connection, table)
    if any(constraint["name"] == operation["name"] for constraint in checks):
        raise MigrationError(
            f"invalid operation: check constraint '{operation['name']}' already exists in table '{table}'"
        )
    check = {"name": operation["name"], "expression": operation["expression"]}
    rebuild_table(
        connection,
        table,
        current_columns(connection, table),
        managed_foreign_keys(connection, table),
        checks + [check],
    )
    connection.execute(
        "INSERT INTO _migration_check_constraints (table_name, name, expression) VALUES (?, ?, ?)",
        (table, check["name"], check["expression"]),
    )


def apply_drop_check_constraint(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    table = operation["table"]
    if not table_exists(connection, table):
        raise MigrationError(f"invalid operation: table '{table}' does not exist")
    checks = managed_check_constraints(connection, table)
    if not any(constraint["name"] == operation["name"] for constraint in checks):
        raise MigrationError(
            f"invalid operation: check constraint '{operation['name']}' does not exist in table '{table}'"
        )
    rebuild_table(
        connection,
        table,
        current_columns(connection, table),
        managed_foreign_keys(connection, table),
        [constraint for constraint in checks if constraint["name"] != operation["name"]],
    )
    connection.execute(
        "DELETE FROM _migration_check_constraints WHERE table_name = ? AND name = ?",
        (table, operation["name"]),
    )


def apply_operation(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    operation_type = operation["type"]
    if operation_type == "create_table":
        apply_create_table(connection, operation)
    elif operation_type == "add_column":
        apply_add_column(connection, operation)
    elif operation_type == "drop_column":
        apply_drop_column(connection, operation)
    elif operation_type == "transform_data":
        apply_transform_data(connection, operation)
    elif operation_type == "migrate_column_data":
        apply_migrate_column_data(connection, operation)
    elif operation_type == "backfill_data":
        apply_backfill_data(connection, operation)
    elif operation_type == "add_foreign_key":
        apply_add_foreign_key(connection, operation)
    elif operation_type == "drop_foreign_key":
        apply_drop_foreign_key(connection, operation)
    elif operation_type == "create_index":
        apply_create_index(connection, operation)
    elif operation_type == "drop_index":
        apply_drop_index(connection, operation)
    elif operation_type == "add_check_constraint":
        apply_add_check_constraint(connection, operation)
    else:
        apply_drop_check_constraint(connection, operation)


def index_definition(connection: sqlite3.Connection, name: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT tbl_name, sql FROM sqlite_master WHERE type = 'index' AND name = ?", (name,)
    ).fetchone()
    if row is None or row[1] is None:
        raise MigrationError(f"invalid operation: index '{name}' does not exist")
    table = row[0]
    index_rows = connection.execute(
        f"PRAGMA index_list({quote_identifier(table)})"
    ).fetchall()
    index = next((candidate for candidate in index_rows if candidate[1] == name), None)
    if index is None:
        raise MigrationError(f"invalid operation: index '{name}' does not exist")
    columns = connection.execute(
        f"PRAGMA index_info({quote_identifier(name)})"
    ).fetchall()
    return {
        "type": "create_index",
        "name": name,
        "table": table,
        "columns": [column[2] for column in sorted(columns, key=lambda column: column[0])],
        "unique": bool(index[2]),
    }


def enrich_operation_for_rollback(
    connection: sqlite3.Connection, operation: dict[str, Any]
) -> None:
    """Capture state that SQLite cannot recover from a forward operation alone."""
    operation_type = operation["type"]
    if operation_type == "drop_column":
        columns = current_columns(connection, operation["table"])
        original = next(
            (column for column in columns if column["name"] == operation["column"]), None
        )
        if original is not None:
            operation["original_definition"] = original
    elif operation_type == "drop_foreign_key":
        original = next(
            (
                foreign_key
                for foreign_key in managed_foreign_keys(connection, operation["table"])
                if foreign_key["name"] == operation["name"]
            ),
            None,
        )
        if original is not None:
            operation["original_foreign_key"] = original
    elif operation_type == "drop_index":
        operation["original_index"] = index_definition(connection, operation["name"])
    elif operation_type == "drop_check_constraint":
        original = next(
            (
                constraint
                for constraint in managed_check_constraints(connection, operation["table"])
                if constraint["name"] == operation["name"]
            ),
            None,
        )
        if original is not None:
            operation["original_check_constraint"] = original


def automatic_rollback_operations(
    operations: list[dict[str, Any]], version: int
) -> list[dict[str, Any]]:
    reversed_operations: list[dict[str, Any]] = []
    for operation in reversed(operations):
        operation_type = operation["type"]
        if operation_type == "create_table":
            reversed_operations.append({"type": "drop_table", "table": operation["table"]})
        elif operation_type == "add_column":
            reversed_operations.append(
                {"type": "drop_column", "table": operation["table"], "column": operation["column"]["name"]}
            )
        elif operation_type == "drop_column":
            original = operation.get("original_definition")
            if original is None:
                raise MigrationError(
                    f"cannot rollback version {version}: missing original definition for drop_column"
                )
            reversed_operations.append(
                {"type": "add_column", "table": operation["table"], "column": original}
            )
        elif operation_type == "add_foreign_key":
            reversed_operations.append(
                {"type": "drop_foreign_key", "table": operation["table"], "name": operation["name"]}
            )
        elif operation_type == "drop_foreign_key":
            original = operation.get("original_foreign_key")
            if original is None:
                raise MigrationError(
                    f"cannot rollback version {version}: missing original definition for drop_foreign_key"
                )
            reversed_operations.append(
                {"type": "add_foreign_key", "table": operation["table"], **original}
            )
        elif operation_type == "create_index":
            reversed_operations.append({"type": "drop_index", "name": operation["name"]})
        elif operation_type == "drop_index":
            original = operation.get("original_index")
            if original is None:
                raise MigrationError(
                    f"cannot rollback version {version}: missing original definition for drop_index"
                )
            reversed_operations.append(original)
        elif operation_type == "add_check_constraint":
            reversed_operations.append(
                {"type": "drop_check_constraint", "table": operation["table"], "name": operation["name"]}
            )
        elif operation_type == "drop_check_constraint":
            original = operation.get("original_check_constraint")
            if original is None:
                raise MigrationError(
                    f"cannot rollback version {version}: missing original definition for drop_check_constraint"
                )
            reversed_operations.append(
                {
                    "type": "add_check_constraint",
                    "table": operation["table"],
                    **original,
                }
            )
        elif operation_type == "migrate_column_data":
            reversed_operations.append(
                {
                    "type": "migrate_column_data",
                    "table": operation["table"],
                    "from_column": operation["to_column"],
                    "to_column": operation["from_column"],
                    "default_value": None,
                }
            )
        elif operation_type in {"transform_data", "backfill_data"}:
            raise MigrationError(
                f"cannot rollback version {version}: missing rollback_operations for {operation_type}"
            )
        else:
            raise MigrationError(
                f"cannot rollback version {version}: unsupported operation '{operation_type}'"
            )
    rollback_sources = {
        "drop_table": "create_table",
        "drop_column": "add_column",
        "add_column": "drop_column",
        "drop_foreign_key": "add_foreign_key",
        "add_foreign_key": "drop_foreign_key",
        "drop_index": "create_index",
        "create_index": "drop_index",
        "drop_check_constraint": "add_check_constraint",
        "add_check_constraint": "drop_check_constraint",
        "migrate_column_data": "migrate_column_data",
    }
    for rollback_operation in reversed_operations:
        rollback_operation["rollback_of"] = rollback_sources[rollback_operation["type"]]
    return reversed_operations


def apply_drop_table_for_rollback(connection: sqlite3.Connection, table: str) -> None:
    if not table_exists(connection, table):
        raise MigrationError(f"rollback failed: table '{table}' does not exist")
    connection.execute(f"DROP TABLE {quote_identifier(table)}")
    connection.execute("DELETE FROM _migration_foreign_keys WHERE table_name = ?", (table,))
    connection.execute("DELETE FROM _migration_check_constraints WHERE table_name = ?", (table,))


def apply_rollback_operation(connection: sqlite3.Connection, operation: dict[str, Any]) -> None:
    if operation["type"] == "drop_table":
        apply_drop_table_for_rollback(connection, operation["table"])
    else:
        apply_operation(connection, operation)


def operation_event(
    event_name: str, operation: dict[str, Any], version: int
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "event": event_name,
        "type": operation.get("rollback_of", operation["type"]),
    }
    if "table" in operation:
        event["table"] = operation["table"]
    if operation["type"] in {"add_column", "drop_column"}:
        column = operation["column"]
        event["column"] = column["name"] if isinstance(column, dict) else column
    if operation["type"] in {
        "add_foreign_key",
        "drop_foreign_key",
        "create_index",
        "drop_index",
        "add_check_constraint",
        "drop_check_constraint",
    }:
        event["name"] = operation["name"]
    event["version"] = version
    return event


def load_migration(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    try:
        with path.open("r", encoding="utf-8") as migration_file:
            raw_migration = json.load(migration_file)
    except FileNotFoundError as error:
        raise MigrationError(f"migration file not found: {path_text}") from error
    except json.JSONDecodeError as error:
        raise MigrationError(f"invalid JSON in migration file: {error.msg}") from error
    except (OSError, UnicodeDecodeError) as error:
        raise MigrationError(f"unable to read migration file '{path_text}': {error}") from error
    return validate_migration(raw_migration)


def scan_migrations_directory(directory_text: str) -> dict[int, tuple[Path, dict[str, Any]]]:
    directory = Path(directory_text)
    if not directory.is_dir():
        raise MigrationError(f"migration directory not found: {directory_text}")
    migrations: dict[int, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(directory.glob("*.json"), key=lambda candidate: candidate.name):
        try:
            migration = load_migration(str(path))
        except MigrationError as error:
            raise MigrationError(f"invalid migration file: {path.name}: {error}") from error
        version = migration["version"]
        if version in migrations:
            raise MigrationError(f"duplicate migration version {version}")
        migrations[version] = (path, migration)
    return migrations


def find_dependency_cycle(migrations: dict[int, tuple[Path, dict[str, Any]]]) -> list[int] | None:
    state: dict[int, int] = {version: 0 for version in migrations}
    stack: list[int] = []

    def visit(version: int) -> list[int] | None:
        state[version] = 1
        stack.append(version)
        for dependency in migrations[version][1]["depends_on"]:
            if dependency not in migrations:
                continue
            if state[dependency] == 1:
                start = stack.index(dependency)
                return stack[start:] + [dependency]
            if state[dependency] == 0:
                cycle = visit(dependency)
                if cycle is not None:
                    return cycle
        stack.pop()
        state[version] = 2
        return None

    for version in sorted(migrations):
        if state[version] == 0:
            cycle = visit(version)
            if cycle is not None:
                return cycle
    return None


def dependency_order(migrations: dict[int, tuple[Path, dict[str, Any]]]) -> list[int]:
    for version, (_, migration) in migrations.items():
        for dependency in migration["depends_on"]:
            if dependency not in migrations:
                raise MigrationError(f"dependency version {dependency} not found")

    cycle = find_dependency_cycle(migrations)
    if cycle is not None:
        rendered_cycle = ", ".join(str(version) for version in cycle)
        raise MigrationError(f"circular dependency detected: cycle [{rendered_cycle}]")

    for version, (_, migration) in migrations.items():
        for dependency in migration["depends_on"]:
            if dependency >= version:
                raise MigrationError(
                    f"migration version {version} cannot depend on future version {dependency}"
                )

    remaining_dependencies = {
        version: set(migration["depends_on"])
        for version, (_, migration) in migrations.items()
    }
    resolved: list[int] = []
    ready = sorted(version for version, dependencies in remaining_dependencies.items() if not dependencies)
    while ready:
        version = ready.pop(0)
        resolved.append(version)
        for candidate in sorted(remaining_dependencies):
            if version in remaining_dependencies[candidate]:
                remaining_dependencies[candidate].remove(version)
                if not remaining_dependencies[candidate] and candidate not in resolved and candidate not in ready:
                    ready.append(candidate)
        ready.sort()
    if len(resolved) != len(migrations):
        raise MigrationError("dependency resolution failed: conflicting requirements")
    return resolved


def validate_migration_command(
    migration_file: str, migrations_directory: str | None
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = [
        {"event": "validation_started", "migration_file": Path(migration_file).name}
    ]
    migration: dict[str, Any] | None = None
    try:
        migration = load_migration(migration_file)
        dependencies = migration["depends_on"]
        if migrations_directory is None:
            for dependency in dependencies:
                if dependency >= migration["version"]:
                    raise MigrationError(
                        f"migration version {migration['version']} cannot depend on future version {dependency}"
                    )
            if dependencies:
                events.append(
                    {
                        "event": "dependency_check",
                        "version": migration["version"],
                        "depends_on": dependencies,
                        "status": "warning",
                        "message": "cannot verify dependencies without --migrations-dir",
                    }
                )
            events.append(
                {"event": "validation_complete", "version": migration["version"], "status": "valid"}
            )
            return events

        migrations = scan_migrations_directory(migrations_directory)
        existing = migrations.get(migration["version"])
        if existing is None:
            migrations[migration["version"]] = (Path(migration_file), migration)
        elif existing[0].resolve() != Path(migration_file).resolve():
            raise MigrationError(f"duplicate migration version {migration['version']}")
        dependency_order(migrations)
        events.append(
            {
                "event": "dependency_check",
                "version": migration["version"],
                "depends_on": dependencies,
                "status": "ok",
            }
        )
        events.append(
            {"event": "validation_complete", "version": migration["version"], "status": "valid"}
        )
        return events
    except MigrationError as error:
        message = str(error)
        if message.startswith("circular dependency detected: cycle ["):
            cycle_text = message.removeprefix("circular dependency detected: cycle [").removesuffix("]")
            events.append(
                {
                    "event": "circular_dependency_detected",
                    "cycle": [int(value.strip()) for value in cycle_text.split(",")],
                    "status": "error",
                }
            )
        complete_event: dict[str, Any] = {"event": "validation_complete", "status": "invalid"}
        if migration is not None:
            complete_event["version"] = migration["version"]
        events.append(complete_event)
        raise CommandError(message, events) from error


def validate_applied_dependencies(connection: sqlite3.Connection, migration: dict[str, Any]) -> None:
    for dependency in migration["depends_on"]:
        if dependency >= migration["version"]:
            raise MigrationError(
                f"migration version {migration['version']} cannot depend on future version {dependency}"
            )
        applied = connection.execute(
            "SELECT 1 FROM _migrations WHERE version = ?", (dependency,)
        ).fetchone()
        if applied is None:
            raise MigrationError(
                f"migration version {migration['version']} depends on unapplied version {dependency}"
            )


def migrate_all(directory_text: str, database_path: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = [{"event": "scan_started", "directory": directory_text}]
    try:
        migrations = scan_migrations_directory(directory_text)
        for version in sorted(migrations):
            path, _ = migrations[version]
            events.append(
                {"event": "migration_discovered", "file": path.name, "version": version}
            )
        events.append({"event": "scan_complete", "migrations_found": len(migrations)})
        events.append({"event": "dependency_resolution_started"})
        order = dependency_order(migrations)
        events.append({"event": "dependency_resolved", "order": order})

        if not order:
            events.append(
                {
                    "event": "batch_complete",
                    "migrations_applied": 0,
                    "migrations_skipped": 0,
                    "final_version": None,
                }
            )
            return events

        applied = 0
        skipped = 0
        for version in order:
            _, migration = migrations[version]
            events.append(
                {
                    "event": "migration_started",
                    "version": version,
                    "description": migration["description"],
                }
            )
            result = apply_migration(migration, database_path)
            events.extend(result)
            if result and result[0]["event"] == "migration_skipped":
                skipped += 1
            else:
                applied += 1

        with sqlite3.connect(database_path) as connection:
            final_version = connection.execute("SELECT MAX(version) FROM _migrations").fetchone()[0]
        events.append(
            {
                "event": "batch_complete",
                "migrations_applied": applied,
                "migrations_skipped": skipped,
                "final_version": final_version,
            }
        )
        return events
    except MigrationError as error:
        raise CommandError(str(error), events) from error


def prepare_database_path(path_text: str) -> None:
    if path_text == ":memory:":
        return
    try:
        Path(path_text).parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise MigrationError(f"unable to create database path '{path_text}': {error}") from error


def apply_migration(migration: dict[str, Any], database_path: str) -> list[dict[str, Any]]:
    prepare_database_path(database_path)
    try:
        connection = sqlite3.connect(database_path)
    except sqlite3.Error as error:
        raise MigrationError(f"SQL error: {error}") from error

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        initialize_migration_tracking(connection)
        initialize_constraint_metadata(connection)
        connection.commit()

        version = migration["version"]
        already_applied = connection.execute(
            "SELECT 1 FROM _migrations WHERE version = ?", (version,)
        ).fetchone()
        if already_applied is not None:
            print(f"Warning: Migration version {version} already applied, skipping", file=sys.stderr)
            return [{"event": "migration_skipped", "version": version, "reason": "already_applied"}]

        validate_applied_dependencies(connection, migration)
        events: list[dict[str, Any]] = []
        connection.execute("BEGIN")
        # Keep enforcement enabled while allowing an atomic recreate of a parent
        # table that is temporarily referenced by another table in this migration.
        connection.execute("PRAGMA defer_foreign_keys = ON")
        added_foreign_key = False
        for operation in migration["operations"]:
            enrich_operation_for_rollback(connection, operation)
            apply_operation(connection, operation)
            event = operation_event("operation_applied", operation, version)
            if operation["type"] == "add_foreign_key":
                added_foreign_key = True
            events.append(event)

        if added_foreign_key:
            violation = connection.execute("PRAGMA foreign_key_check").fetchone()
            if violation is not None:
                raise MigrationError(
                    f"foreign key violation: referenced row in '{violation[2]}' table does not exist"
                )

        connection.execute(
            "INSERT INTO _migrations (version, description, operations, rollback_operations) "
            "VALUES (?, ?, ?, ?)",
            (
                version,
                migration["description"],
                json.dumps(migration["operations"]),
                (
                    json.dumps(migration["rollback_operations"])
                    if migration["rollback_operations"] is not None
                    else None
                ),
            ),
        )
        connection.commit()
        events.append(
            {
                "event": "migration_complete",
                "version": version,
                "operations_count": len(migration["operations"]),
            }
        )
        return events
    except MigrationError:
        connection.rollback()
        raise
    except sqlite3.IntegrityError as error:
        connection.rollback()
        message = str(error)
        if "FOREIGN KEY constraint failed" in message:
            raise MigrationError("foreign key violation: referenced row does not exist") from error
        if "CHECK constraint failed" in message:
            raise MigrationError(f"check constraint violation: {message}") from error
        raise MigrationError(f"SQL error: {message}") from error
    except sqlite3.Error as error:
        connection.rollback()
        raise MigrationError(f"SQL error: {error}") from error
    finally:
        connection.close()


def decode_stored_operations(serialized_operations: str, version: int) -> list[dict[str, Any]]:
    try:
        operations = json.loads(serialized_operations)
    except (TypeError, json.JSONDecodeError) as error:
        raise MigrationError(
            f"cannot rollback version {version}: missing valid operation metadata"
        ) from error
    if not isinstance(operations, list):
        raise MigrationError(
            f"cannot rollback version {version}: missing valid operation metadata"
        )
    return operations


def rollback_migrations(
    database_path: str, to_version: int | None, count: int | None
) -> list[dict[str, Any]]:
    prepare_database_path(database_path)
    try:
        connection = sqlite3.connect(database_path)
    except sqlite3.Error as error:
        raise MigrationError(f"SQL error: {error}") from error

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        initialize_migration_tracking(connection)
        initialize_constraint_metadata(connection)
        connection.commit()
        rows = connection.execute(
            "SELECT version, description, operations, rollback_operations "
            "FROM _migrations ORDER BY version DESC"
        ).fetchall()
        if not rows:
            raise MigrationError("no migrations to rollback")

        if to_version is not None:
            if to_version <= 0:
                raise MigrationError("invalid rollback option: to-version must be a positive integer")
            available_versions = {row[0] for row in rows}
            if to_version not in available_versions:
                raise MigrationError(f"version {to_version} not found")
            selected_rows = [row for row in rows if row[0] > to_version]
        else:
            effective_count = 1 if count is None else count
            if effective_count <= 0:
                raise MigrationError("invalid rollback option: count must be a positive integer")
            selected_rows = rows[:effective_count]

        rollback_plans: list[tuple[tuple[Any, ...], list[dict[str, Any]]]] = []
        for row in selected_rows:
            version, _, operations_text, rollback_text = row
            if rollback_text is not None:
                explicit_operations = decode_stored_operations(rollback_text, version)
                rollback_plans.append((row, explicit_operations))
            else:
                rollback_plans.append(
                    (row, automatic_rollback_operations(decode_stored_operations(operations_text, version), version))
                )

        events: list[dict[str, Any]] = []
        connection.execute("BEGIN")
        connection.execute("PRAGMA defer_foreign_keys = ON")
        for row, rollback_operations in rollback_plans:
            version, description, _, _ = row
            events.append(
                {"event": "rollback_started", "version": version, "description": description}
            )
            for operation in rollback_operations:
                apply_rollback_operation(connection, operation)
                events.append(operation_event("operation_rolled_back", operation, version))
            connection.execute("DELETE FROM _migrations WHERE version = ?", (version,))
            events.append({"event": "rollback_complete", "version": version})

        remaining = connection.execute("SELECT MAX(version) FROM _migrations").fetchone()[0]
        connection.commit()
        events.append(
            {
                "event": "rollback_finished",
                "versions_rolled_back": [row[0] for row, _ in rollback_plans],
                "final_version": remaining,
            }
        )
        return events
    except MigrationError:
        connection.rollback()
        raise
    except sqlite3.IntegrityError as error:
        connection.rollback()
        message = str(error)
        if "FOREIGN KEY constraint failed" in message:
            raise MigrationError("cannot rollback: foreign key constraint violation") from error
        raise MigrationError(f"rollback failed: {message}") from error
    except sqlite3.Error as error:
        connection.rollback()
        raise MigrationError(f"rollback failed: {error}") from error
    finally:
        connection.close()


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = MigrationArgumentParser(prog="migration_tool.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("migration_file")
    migrate_parser.add_argument("database_file")
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("database_file")
    rollback_options = rollback_parser.add_mutually_exclusive_group()
    rollback_options.add_argument("--to-version", type=int)
    rollback_options.add_argument("--count", type=int)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("migration_file")
    validate_parser.add_argument("--migrations-dir")
    migrate_all_parser = subparsers.add_parser("migrate-all")
    migrate_all_parser.add_argument("--migrations-dir", required=True)
    migrate_all_parser.add_argument("database_file")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    try:
        parsed = parse_arguments(sys.argv[1:] if arguments is None else arguments)
        if parsed.command == "migrate":
            migration = load_migration(parsed.migration_file)
            events = apply_migration(migration, parsed.database_file)
        elif parsed.command == "rollback":
            events = rollback_migrations(
                parsed.database_file, parsed.to_version, parsed.count
            )
        elif parsed.command == "validate":
            events = validate_migration_command(
                parsed.migration_file, parsed.migrations_dir
            )
        elif parsed.command == "migrate-all":
            events = migrate_all(parsed.migrations_dir, parsed.database_file)
        else:
            raise MigrationError(f"invalid command: {parsed.command}")
        for event in events:
            print(json.dumps(event))
        return 0
    except CommandError as error:
        for event in error.events:
            print(json.dumps(event))
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except MigrationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
