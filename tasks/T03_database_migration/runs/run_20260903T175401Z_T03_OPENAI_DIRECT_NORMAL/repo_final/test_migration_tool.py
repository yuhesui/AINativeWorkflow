"""Black-box tests for the checkpoint-one migration CLI."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOOL = ROOT / "migration_tool.py"


class MigrationToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.database = self.directory / "app.db"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_migration(
        self,
        version: int,
        description: str,
        operations: list[dict],
        depends_on: list[int] | None = None,
    ) -> Path:
        path = self.directory / f"migration-{version}.json"
        migration = {"version": version, "description": description, "operations": operations}
        if depends_on is not None:
            migration["depends_on"] = depends_on
        path.write_text(
            json.dumps(migration),
            encoding="utf-8",
        )
        return path

    def run_tool(self, migration: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), "migrate", str(migration), str(self.database)],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_rollback(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), "rollback", str(self.database), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_directory_migration(
        self,
        directory: Path,
        version: int,
        description: str,
        operations: list[dict],
        depends_on: list[int] | None = None,
    ) -> Path:
        directory.mkdir(exist_ok=True)
        path = directory / f"migration_v{version}.json"
        migration = {"version": version, "description": description, "operations": operations}
        if depends_on is not None:
            migration["depends_on"] = depends_on
        path.write_text(json.dumps(migration), encoding="utf-8")
        return path

    def test_full_lifecycle_skip_and_rollback(self) -> None:
        create_users = self.write_migration(
            1,
            "create users",
            [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
                        {"name": "email", "type": "TEXT", "not_null": True, "unique": True},
                        {"name": "name", "type": "TEXT", "not_null": True},
                    ],
                }
            ],
        )
        result = self.run_tool(create_users)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            [json.loads(line) for line in result.stdout.splitlines()],
            [
                {"event": "operation_applied", "type": "create_table", "table": "users", "version": 1},
                {"event": "migration_complete", "version": 1, "operations_count": 1},
            ],
        )

        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO users (email, name) VALUES (?, ?)", ("a@example.test", "Ada"))

        add_age = self.write_migration(
            2,
            "add age",
            [
                {
                    "type": "add_column",
                    "table": "users",
                    "column": {"name": "age", "type": "INTEGER", "default": "0"},
                }
            ],
        )
        result = self.run_tool(add_age)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.splitlines()[0])["column"], "age")

        multiple = self.write_migration(
            3,
            "add nickname and posts",
            [
                {
                    "type": "add_column",
                    "table": "users",
                    "column": {"name": "nickname", "type": "TEXT", "default": "'anonymous'"},
                },
                {
                    "type": "create_table",
                    "table": "posts",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
                        {"name": "title", "type": "TEXT", "not_null": True},
                    ],
                },
            ],
        )
        result = self.run_tool(multiple)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([json.loads(line)["type"] for line in result.stdout.splitlines()[:2]], ["add_column", "create_table"])

        drop_age = self.write_migration(
            4,
            "drop age",
            [{"type": "drop_column", "table": "users", "column": "age"}],
        )
        result = self.run_tool(drop_age)
        self.assertEqual(result.returncode, 0, result.stderr)

        with sqlite3.connect(self.database) as connection:
            columns = [row[1] for row in connection.execute("PRAGMA table_info(users)")]
            self.assertEqual(columns, ["id", "email", "name", "nickname"])
            self.assertEqual(
                connection.execute("SELECT id, email, name, nickname FROM users").fetchone(),
                (1, "a@example.test", "Ada", "anonymous"),
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO users (email, name) VALUES (?, ?)", ("a@example.test", "Other"))
            connection.execute("INSERT INTO users (email, name) VALUES (?, ?)", ("b@example.test", "Bea"))
            self.assertEqual(connection.execute("SELECT max(id) FROM users").fetchone()[0], 2)
            self.assertEqual(
                [row[0] for row in connection.execute("SELECT version FROM _migrations ORDER BY version")],
                [1, 2, 3, 4],
            )

        skipped = self.run_tool(drop_age)
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertEqual(skipped.stderr, "Warning: Migration version 4 already applied, skipping\n")
        self.assertEqual(
            json.loads(skipped.stdout),
            {"event": "migration_skipped", "version": 4, "reason": "already_applied"},
        )

        rollback = self.write_migration(
            5,
            "all operations roll back together",
            [
                {
                    "type": "create_table",
                    "table": "temporary_table",
                    "columns": [{"name": "id", "type": "INTEGER"}],
                },
                {
                    "type": "add_column",
                    "table": "users",
                    "column": {"name": "nickname", "type": "TEXT"},
                },
            ],
        )
        failed = self.run_tool(rollback)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(failed.stdout, "")
        self.assertIn("column 'nickname' already exists", failed.stderr)
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'temporary_table'"
                ).fetchone()
            )
            self.assertIsNone(connection.execute("SELECT 1 FROM _migrations WHERE version = 5").fetchone())

    def test_invalid_schema_and_invalid_drop_operations(self) -> None:
        invalid = self.directory / "invalid.json"
        invalid.write_text('{"version": 1, "description": "bad"}', encoding="utf-8")
        result = self.run_tool(invalid)
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid migration schema: missing required field 'operations'", result.stderr)
        self.assertFalse(self.database.exists())

        one_column = self.write_migration(
            1,
            "create one-column table",
            [{"type": "create_table", "table": "single", "columns": [{"name": "value", "type": "TEXT"}]}],
        )
        self.assertEqual(self.run_tool(one_column).returncode, 0)
        drop_only = self.write_migration(
            2,
            "cannot drop only column",
            [{"type": "drop_column", "table": "single", "column": "value"}],
        )
        result = self.run_tool(drop_only)
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot drop the only column", result.stderr)

        primary_key = self.write_migration(
            3,
            "create primary key table",
            [
                {
                    "type": "create_table",
                    "table": "keyed",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "value", "type": "TEXT"},
                    ],
                }
            ],
        )
        self.assertEqual(self.run_tool(primary_key).returncode, 0)
        drop_key = self.write_migration(
            4,
            "cannot drop primary key",
            [{"type": "drop_column", "table": "keyed", "column": "id"}],
        )
        result = self.run_tool(drop_key)
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot drop primary key column 'id'", result.stderr)

    def test_data_transformations_migration_and_backfill(self) -> None:
        initial = self.write_migration(
            1,
            "create data migration fixture",
            [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "first_name", "type": "TEXT"},
                        {"name": "last_name", "type": "TEXT"},
                        {"name": "old_email", "type": "TEXT"},
                        {"name": "email", "type": "TEXT"},
                        {"name": "status", "type": "TEXT"},
                        {"name": "score", "type": "INTEGER"},
                    ],
                }
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            connection.executemany(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (1, "Ada", "Lovelace", "ada@example.test", "old@example.test", None, None),
                    (2, "Grace", "Hopper", None, "keep@example.test", "existing", None),
                ],
            )

        data_migration = self.write_migration(
            2,
            "transform and migrate data",
            [
                {
                    "type": "transform_data",
                    "table": "users",
                    "transformations": [
                        {"column": "full_name", "expression": "first_name || ' ' || last_name"},
                        {"column": "full_name", "expression": "full_name || '!'"},
                        {"column": "initial", "expression": "substr(first_name, 1, 1)"},
                    ],
                },
                {
                    "type": "migrate_column_data",
                    "table": "users",
                    "from_column": "old_email",
                    "to_column": "email",
                    "default_value": "missing@example.test",
                },
                {
                    "type": "backfill_data",
                    "table": "users",
                    "column": "status",
                    "value": "'active'",
                    "where": "status IS NULL",
                },
                {
                    "type": "backfill_data",
                    "table": "users",
                    "column": "score",
                    "value": 42,
                    "where": "score IS NULL",
                },
            ],
        )
        result = self.run_tool(data_migration)
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(
            [event["type"] for event in events[:-1]],
            ["transform_data", "migrate_column_data", "backfill_data", "backfill_data"],
        )
        self.assertEqual(events[-1], {"event": "migration_complete", "version": 2, "operations_count": 4})

        with sqlite3.connect(self.database) as connection:
            rows = connection.execute(
                "SELECT full_name, initial, email, status, score FROM users ORDER BY id"
            ).fetchall()
            self.assertEqual(
                rows,
                [
                    ("Ada Lovelace!", "A", "ada@example.test", "active", 42),
                    ("Grace Hopper!", "G", "missing@example.test", "existing", 42),
                ],
            )

        rollback = self.write_migration(
            3,
            "invalid data operation rolls back added target",
            [
                {
                    "type": "transform_data",
                    "table": "users",
                    "transformations": [{"column": "temporary", "expression": "first_name"}],
                },
                {"type": "backfill_data", "table": "users", "column": "missing", "value": "'x'"},
            ],
        )
        result = self.run_tool(rollback)
        self.assertEqual(result.returncode, 1)
        self.assertIn("column 'missing' does not exist", result.stderr)
        self.assertEqual(result.stdout, "")
        with sqlite3.connect(self.database) as connection:
            self.assertNotIn("temporary", [row[1] for row in connection.execute("PRAGMA table_info(users)")])
            self.assertIsNone(connection.execute("SELECT 1 FROM _migrations WHERE version = 3").fetchone())

    def test_foreign_keys_indexes_and_check_constraints(self) -> None:
        initial = self.write_migration(
            1,
            "create relational fixture",
            [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
                        {"name": "name", "type": "TEXT", "not_null": True},
                        {"name": "age", "type": "INTEGER", "not_null": True},
                        {"name": "note", "type": "TEXT", "default": "'it''s fine'"},
                    ],
                },
                {
                    "type": "create_table",
                    "table": "posts",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
                        {"name": "user_id", "type": "INTEGER", "not_null": True},
                        {"name": "title", "type": "TEXT", "not_null": True},
                    ],
                },
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Ada", 36))
            connection.execute("INSERT INTO posts (user_id, title) VALUES (?, ?)", (1, "Notes"))

        add_relational_features = self.write_migration(
            2,
            "add indexes and constraints",
            [
                {
                    "type": "create_index",
                    "name": "idx_users_name",
                    "table": "users",
                    "columns": ["name"],
                    "unique": True,
                },
                {
                    "type": "add_check_constraint",
                    "table": "users",
                    "name": "chk_users_age",
                    "expression": "age >= 0 AND age <= 150",
                },
                {
                    "type": "add_foreign_key",
                    "table": "posts",
                    "name": "fk_posts_user_id",
                    "columns": ["user_id"],
                    "references": {"table": "users", "columns": ["id"]},
                    "on_delete": "CASCADE",
                    "on_update": "RESTRICT",
                },
                {
                    "type": "create_index",
                    "name": "idx_posts_user_title",
                    "table": "posts",
                    "columns": ["user_id", "title"],
                    "unique": False,
                },
            ],
        )
        result = self.run_tool(add_relational_features)
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(
            [event["type"] for event in events[:-1]],
            ["create_index", "add_check_constraint", "add_foreign_key", "create_index"],
        )
        self.assertEqual(events[1]["name"], "chk_users_age")
        self.assertEqual(events[2]["name"], "fk_posts_user_id")
        with sqlite3.connect(self.database) as connection:
            self.assertIsNotNone(
                connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_users_name'").fetchone()
            )
            self.assertIsNotNone(
                connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_posts_user_title'").fetchone()
            )
            foreign_keys = connection.execute("PRAGMA foreign_key_list(posts)").fetchall()
            self.assertEqual(len(foreign_keys), 1)
            self.assertEqual(foreign_keys[0][2:6], ("users", "user_id", "id", "RESTRICT"))
            self.assertEqual(foreign_keys[0][6], "CASCADE")
            self.assertEqual(connection.execute("SELECT note FROM users").fetchone()[0], "it's fine")

        invalid_foreign_key_data = self.write_migration(
            3,
            "foreign key data is enforced",
            [{"type": "backfill_data", "table": "posts", "column": "user_id", "value": 999}],
        )
        result = self.run_tool(invalid_foreign_key_data)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FOREIGN KEY constraint failed", result.stderr)
        self.assertEqual(result.stdout, "")

        invalid_check_data = self.write_migration(
            3,
            "check data is enforced",
            [{"type": "backfill_data", "table": "users", "column": "age", "value": 200}],
        )
        result = self.run_tool(invalid_check_data)
        self.assertEqual(result.returncode, 1)
        self.assertIn("CHECK constraint failed", result.stderr)
        self.assertEqual(result.stdout, "")

        remove_relational_features = self.write_migration(
            4,
            "remove foreign key check and index",
            [
                {"type": "drop_foreign_key", "table": "posts", "name": "fk_posts_user_id"},
                {"type": "drop_check_constraint", "table": "users", "name": "chk_users_age"},
                {"type": "drop_index", "name": "idx_posts_user_title"},
            ],
        )
        result = self.run_tool(remove_relational_features)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            [json.loads(line)["type"] for line in result.stdout.splitlines()[:-1]],
            ["drop_foreign_key", "drop_check_constraint", "drop_index"],
        )
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_key_list(posts)").fetchall(), [])
            self.assertIsNone(
                connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_posts_user_title'").fetchone()
            )
            # The users index survives the check-constraint table rebuild.
            self.assertIsNotNone(
                connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_users_name'").fetchone()
            )

        unrestricted = self.write_migration(
            5,
            "removed constraints no longer reject values",
            [
                {"type": "backfill_data", "table": "posts", "column": "user_id", "value": 999},
                {"type": "backfill_data", "table": "users", "column": "age", "value": 200},
            ],
        )
        self.assertEqual(self.run_tool(unrestricted).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT user_id FROM posts").fetchone()[0], 999)
            self.assertEqual(connection.execute("SELECT age FROM users").fetchone()[0], 200)

        duplicate_index = self.write_migration(
            6,
            "duplicate index rejected",
            [{"type": "create_index", "name": "idx_users_name", "table": "users", "columns": ["name"]}],
        )
        result = self.run_tool(duplicate_index)
        self.assertEqual(result.returncode, 1)
        self.assertIn("index 'idx_users_name' already exists", result.stderr)

    def test_composite_foreign_key(self) -> None:
        initial = self.write_migration(
            1,
            "create composite foreign key fixture",
            [
                {
                    "type": "create_table",
                    "table": "parents",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "code", "type": "INTEGER", "not_null": True},
                        {"name": "label", "type": "TEXT", "not_null": True},
                    ],
                },
                {
                    "type": "create_table",
                    "table": "children",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "parent_code", "type": "INTEGER"},
                        {"name": "parent_label", "type": "TEXT"},
                    ],
                },
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO parents VALUES (1, 7, 'primary')")
            connection.execute("INSERT INTO children VALUES (1, 7, 'primary')")

        add_composite_key = self.write_migration(
            2,
            "add composite relationship",
            [
                {
                    "type": "create_index",
                    "name": "idx_parents_code_label",
                    "table": "parents",
                    "columns": ["code", "label"],
                    "unique": True,
                },
                {
                    "type": "add_foreign_key",
                    "table": "children",
                    "name": "fk_children_parent_pair",
                    "columns": ["parent_code", "parent_label"],
                    "references": {"table": "parents", "columns": ["code", "label"]},
                    "on_delete": "SET NULL",
                },
            ],
        )
        result = self.run_tool(add_composite_key)
        self.assertEqual(result.returncode, 0, result.stderr)
        with sqlite3.connect(self.database) as connection:
            foreign_keys = connection.execute("PRAGMA foreign_key_list(children)").fetchall()
            self.assertEqual(len(foreign_keys), 2)
            self.assertEqual({row[2] for row in foreign_keys}, {"parents"})
            self.assertEqual({row[6] for row in foreign_keys}, {"SET NULL"})

        circular_key = self.write_migration(
            3,
            "circular relationship rejected",
            [
                {
                    "type": "add_foreign_key",
                    "table": "parents",
                    "name": "fk_parents_child_id",
                    "columns": ["id"],
                    "references": {"table": "children", "columns": ["id"]},
                }
            ],
        )
        result = self.run_tool(circular_key)
        self.assertEqual(result.returncode, 1)
        self.assertIn("circular foreign key dependency", result.stderr)

        invalid_pair = self.write_migration(
            3,
            "composite relationship is enforced",
            [{"type": "backfill_data", "table": "children", "column": "parent_code", "value": 8}],
        )
        result = self.run_tool(invalid_pair)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FOREIGN KEY constraint failed", result.stderr)

    def test_new_constraints_reject_existing_invalid_data(self) -> None:
        initial = self.write_migration(
            1,
            "create invalid-data fixture",
            [
                {
                    "type": "create_table",
                    "table": "parents",
                    "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}],
                },
                {
                    "type": "create_table",
                    "table": "children",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "parent_id", "type": "INTEGER"},
                    ],
                },
                {
                    "type": "create_table",
                    "table": "measurements",
                    "columns": [{"name": "value", "type": "INTEGER"}],
                },
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO children VALUES (1, 99)")
            connection.execute("INSERT INTO measurements VALUES (-1)")

        foreign_key = self.write_migration(
            2,
            "invalid relationship rejected before rebuild",
            [
                {
                    "type": "add_foreign_key",
                    "table": "children",
                    "name": "fk_children_parent",
                    "columns": ["parent_id"],
                    "references": {"table": "parents", "columns": ["id"]},
                }
            ],
        )
        result = self.run_tool(foreign_key)
        self.assertEqual(result.returncode, 1)
        self.assertIn("foreign key violation: referenced row in 'parents' table does not exist", result.stderr)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_key_list(children)").fetchall(), [])
            self.assertIsNone(connection.execute("SELECT 1 FROM _migrations WHERE version = 2").fetchone())

        check = self.write_migration(
            3,
            "invalid check data rejected before rebuild",
            [
                {
                    "type": "add_check_constraint",
                    "table": "measurements",
                    "name": "chk_measurements_nonnegative",
                    "expression": "value >= 0",
                }
            ],
        )
        result = self.run_tool(check)
        self.assertEqual(result.returncode, 1)
        self.assertIn("check constraint violation: chk_measurements_nonnegative", result.stderr)
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(connection.execute("SELECT 1 FROM _migrations WHERE version = 3").fetchone())

    def test_parent_table_rebuild_preserves_existing_foreign_keys(self) -> None:
        initial = self.write_migration(
            1,
            "create parent rebuild fixture",
            [
                {
                    "type": "create_table",
                    "table": "parents",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "name", "type": "TEXT", "not_null": True},
                    ],
                },
                {
                    "type": "create_table",
                    "table": "children",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "parent_id", "type": "INTEGER", "not_null": True},
                    ],
                },
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO parents VALUES (1, 'parent')")
            connection.execute("INSERT INTO children VALUES (1, 1)")

        relationship = self.write_migration(
            2,
            "add child relationship",
            [
                {
                    "type": "add_foreign_key",
                    "table": "children",
                    "name": "fk_children_parent",
                    "columns": ["parent_id"],
                    "references": {"table": "parents", "columns": ["id"]},
                }
            ],
        )
        self.assertEqual(self.run_tool(relationship).returncode, 0)
        parent_check = self.write_migration(
            3,
            "rebuild parent with child relationship",
            [
                {
                    "type": "add_check_constraint",
                    "table": "parents",
                    "name": "chk_parents_name",
                    "expression": "length(name) > 0",
                }
            ],
        )
        result = self.run_tool(parent_check)
        self.assertEqual(result.returncode, 0, result.stderr)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM children").fetchone()[0], 1)
            self.assertEqual(len(connection.execute("PRAGMA foreign_key_list(children)").fetchall()), 1)

    def test_automatic_rollback_default_and_to_version(self) -> None:
        first = self.write_migration(
            1,
            "create users",
            [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}],
                }
            ],
        )
        second = self.write_migration(
            2,
            "add age",
            [
                {
                    "type": "add_column",
                    "table": "users",
                    "column": {"name": "age", "type": "INTEGER", "default": "0"},
                }
            ],
        )
        third = self.write_migration(
            3,
            "create posts",
            [
                {
                    "type": "create_table",
                    "table": "posts",
                    "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}],
                }
            ],
        )
        fourth = self.write_migration(
            4,
            "index users",
            [{"type": "create_index", "name": "idx_users_id", "table": "users", "columns": ["id"]}],
        )
        for migration in (first, second, third, fourth):
            self.assertEqual(self.run_tool(migration).returncode, 0)

        with sqlite3.connect(self.database) as connection:
            history = json.loads(connection.execute("SELECT operations FROM _migrations WHERE version = 2").fetchone()[0])
            self.assertEqual(history[0]["type"], "add_column")

        result = self.run_rollback()
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(events[0], {"event": "rollback_started", "version": 4, "description": "index users"})
        self.assertEqual(events[1]["event"], "operation_rolled_back")
        self.assertEqual(events[1]["type"], "create_index")
        self.assertEqual(events[-1], {"event": "rollback_finished", "versions_rolled_back": [4], "final_version": 3})
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_users_id'").fetchone())

        result = self.run_rollback("--to-version", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([event["version"] for event in events if event["event"] == "rollback_started"], [3, 2])
        self.assertEqual(events[-1], {"event": "rollback_finished", "versions_rolled_back": [3, 2], "final_version": 1})
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'posts'").fetchone())
            self.assertEqual([row[1] for row in connection.execute("PRAGMA table_info(users)")], ["id"])
            self.assertEqual([row[0] for row in connection.execute("SELECT version FROM _migrations")], [1])

    def test_automatic_rollback_restores_dropped_column_and_data_migration(self) -> None:
        initial = self.write_migration(
            1,
            "create users with old email",
            [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "old_email", "type": "TEXT", "default": "'unknown'"},
                    ],
                }
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO users VALUES (1, 'ada@example.test')")

        rename = self.write_migration(
            2,
            "rename email",
            [
                {
                    "type": "add_column",
                    "table": "users",
                    "column": {"name": "email", "type": "TEXT"},
                },
                {
                    "type": "migrate_column_data",
                    "table": "users",
                    "from_column": "old_email",
                    "to_column": "email",
                },
                {"type": "drop_column", "table": "users", "column": "old_email"},
            ],
        )
        self.assertEqual(self.run_tool(rename).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            stored = json.loads(connection.execute("SELECT operations FROM _migrations WHERE version = 2").fetchone()[0])
            self.assertEqual(stored[-1]["original_definition"]["name"], "old_email")
            self.assertIn("original_sql_definition", stored[-1])
            self.assertEqual(connection.execute("SELECT email FROM users").fetchone()[0], "ada@example.test")

        result = self.run_rollback()
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(
            [event["type"] for event in events if event["event"] == "operation_rolled_back"],
            ["drop_column", "migrate_column_data", "add_column"],
        )
        with sqlite3.connect(self.database) as connection:
            self.assertEqual([row[1] for row in connection.execute("PRAGMA table_info(users)")], ["id", "old_email"])
            self.assertEqual(connection.execute("SELECT old_email FROM users").fetchone()[0], "ada@example.test")
            self.assertIsNone(connection.execute("SELECT 1 FROM _migrations WHERE version = 2").fetchone())

    def test_explicit_and_nonreversible_rollbacks(self) -> None:
        initial = self.write_migration(
            1,
            "create source columns",
            [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [
                        {"name": "first_name", "type": "TEXT"},
                        {"name": "last_name", "type": "TEXT"},
                    ],
                }
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO users VALUES ('Ada', 'Lovelace')")

        explicit = self.write_migration(
            2,
            "compute full name",
            [
                {"type": "add_column", "table": "users", "column": {"name": "full_name", "type": "TEXT"}},
                {
                    "type": "transform_data",
                    "table": "users",
                    "transformations": [{"column": "full_name", "expression": "first_name || ' ' || last_name"}],
                },
            ],
        )
        explicit_payload = json.loads(explicit.read_text(encoding="utf-8"))
        explicit_payload["rollback_operations"] = [
            {"type": "drop_column", "table": "users", "column": "full_name"}
        ]
        explicit.write_text(json.dumps(explicit_payload), encoding="utf-8")
        self.assertEqual(self.run_tool(explicit).returncode, 0)
        result = self.run_rollback()
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([event["type"] for event in events if event["event"] == "operation_rolled_back"], ["drop_column"])
        with sqlite3.connect(self.database) as connection:
            self.assertNotIn("full_name", [row[1] for row in connection.execute("PRAGMA table_info(users)")])

        nonreversible = self.write_migration(
            3,
            "backfill status without rollback",
            [
                {"type": "add_column", "table": "users", "column": {"name": "status", "type": "TEXT"}},
                {"type": "backfill_data", "table": "users", "column": "status", "value": "'active'"},
            ],
        )
        self.assertEqual(self.run_tool(nonreversible).returncode, 0)
        result = self.run_rollback()
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot rollback version 3: missing rollback_operations for backfill_data", result.stderr)
        self.assertEqual(result.stdout, "")
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT status FROM users").fetchone()[0], "active")
            self.assertIsNotNone(connection.execute("SELECT 1 FROM _migrations WHERE version = 3").fetchone())

    def test_rollback_dependencies_and_errors(self) -> None:
        empty = self.run_rollback()
        self.assertEqual(empty.returncode, 1)
        self.assertIn("no migrations to rollback", empty.stderr)

        parent = self.write_migration(
            1,
            "create parent",
            [{"type": "create_table", "table": "parents", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}],
        )
        child = self.write_migration(
            2,
            "create child",
            [
                {
                    "type": "create_table",
                    "table": "children",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "parent_id", "type": "INTEGER"},
                    ],
                }
            ],
        )
        relationship = self.write_migration(
            3,
            "add relationship",
            [
                {
                    "type": "add_foreign_key",
                    "table": "children",
                    "name": "fk_children_parent",
                    "columns": ["parent_id"],
                    "references": {"table": "parents", "columns": ["id"]},
                }
            ],
        )
        for migration in (parent, child, relationship):
            self.assertEqual(self.run_tool(migration).returncode, 0)
        missing = self.run_rollback("--to-version", "99")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("version 99 not found", missing.stderr)

        result = self.run_rollback("--count", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), {"event": "rollback_finished", "versions_rolled_back": [3, 2], "final_version": 1})
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'children'").fetchone())
            self.assertIsNotNone(connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'parents'").fetchone())

    def test_automatic_rollback_restores_dropped_constraints_and_index(self) -> None:
        initial = self.write_migration(
            1,
            "create constraint rollback fixture",
            [
                {
                    "type": "create_table",
                    "table": "parents",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "age", "type": "INTEGER"},
                    ],
                },
                {
                    "type": "create_table",
                    "table": "children",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "parent_id", "type": "INTEGER"},
                    ],
                },
            ],
        )
        self.assertEqual(self.run_tool(initial).returncode, 0)
        add_features = self.write_migration(
            2,
            "add constraint rollback features",
            [
                {
                    "type": "add_check_constraint",
                    "table": "parents",
                    "name": "chk_parents_age",
                    "expression": "age IS NULL OR age >= 0",
                },
                {
                    "type": "add_foreign_key",
                    "table": "children",
                    "name": "fk_children_parent",
                    "columns": ["parent_id"],
                    "references": {"table": "parents", "columns": ["id"]},
                },
                {
                    "type": "create_index",
                    "name": "idx_children_parent",
                    "table": "children",
                    "columns": ["parent_id"],
                },
            ],
        )
        self.assertEqual(self.run_tool(add_features).returncode, 0)
        remove_features = self.write_migration(
            3,
            "remove constraint rollback features",
            [
                {"type": "drop_foreign_key", "table": "children", "name": "fk_children_parent"},
                {"type": "drop_index", "name": "idx_children_parent"},
                {"type": "drop_check_constraint", "table": "parents", "name": "chk_parents_age"},
            ],
        )
        self.assertEqual(self.run_tool(remove_features).returncode, 0)
        result = self.run_rollback()
        self.assertEqual(result.returncode, 0, result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(
            [event["type"] for event in events if event["event"] == "operation_rolled_back"],
            ["drop_check_constraint", "drop_index", "drop_foreign_key"],
        )
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(len(connection.execute("PRAGMA foreign_key_list(children)").fetchall()), 1)
            self.assertIsNotNone(
                connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_children_parent'").fetchone()
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO parents VALUES (1, -1)")

    def test_dependency_validation_and_batch_application(self) -> None:
        migrations = self.directory / "migrations"
        first = self.write_directory_migration(
            migrations,
            1,
            "create users",
            [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}],
                }
            ],
        )
        self.write_directory_migration(
            migrations,
            2,
            "create posts",
            [
                {
                    "type": "create_table",
                    "table": "posts",
                    "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}],
                }
            ],
            depends_on=[1],
        )
        third = self.write_directory_migration(
            migrations,
            3,
            "index posts",
            [{"type": "create_index", "name": "idx_posts_id", "table": "posts", "columns": ["id"]}],
            depends_on=[1, 2],
        )

        standalone_validation = self.run_command("validate", str(third))
        self.assertEqual(standalone_validation.returncode, 0, standalone_validation.stderr)
        self.assertEqual(
            [json.loads(line) for line in standalone_validation.stdout.splitlines()],
            [
                {"event": "validation_started", "migration_file": "migration_v3.json"},
                {
                    "event": "dependency_check",
                    "version": 3,
                    "depends_on": [1, 2],
                    "status": "warning",
                    "message": "cannot verify dependencies without --migrations-dir",
                },
                {"event": "validation_complete", "version": 3, "status": "valid"},
            ],
        )
        self.assertFalse(self.database.exists())

        validation = self.run_command("validate", str(third), "--migrations-dir", str(migrations))
        self.assertEqual(validation.returncode, 0, validation.stderr)
        self.assertEqual(
            [json.loads(line) for line in validation.stdout.splitlines()],
            [
                {"event": "validation_started", "migration_file": "migration_v3.json"},
                {"event": "dependency_check", "version": 3, "depends_on": [1, 2], "status": "ok"},
                {"event": "validation_complete", "version": 3, "status": "valid"},
            ],
        )
        self.assertFalse(self.database.exists())

        applied = self.run_command("migrate-all", "--migrations-dir", str(migrations), str(self.database))
        self.assertEqual(applied.returncode, 0, applied.stderr)
        events = [json.loads(line) for line in applied.stdout.splitlines()]
        self.assertEqual(events[0], {"event": "scan_started", "directory": str(migrations)})
        self.assertEqual(
            [event["version"] for event in events if event["event"] == "migration_discovered"],
            [1, 2, 3],
        )
        self.assertIn({"event": "dependency_resolved", "order": [1, 2, 3]}, events)
        self.assertEqual(
            [event["version"] for event in events if event["event"] == "migration_started"],
            [1, 2, 3],
        )
        self.assertEqual(
            events[-1],
            {"event": "batch_complete", "migrations_applied": 3, "migrations_skipped": 0, "final_version": 3},
        )
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(
                connection.execute("SELECT depends_on FROM _migrations WHERE version = 3").fetchone()[0],
                "[1, 2]",
            )

        skipped = self.run_command("migrate-all", "--migrations-dir", str(migrations), str(self.database))
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertEqual(
            json.loads(skipped.stdout.splitlines()[-1]),
            {"event": "batch_complete", "migrations_applied": 0, "migrations_skipped": 3, "final_version": 3},
        )
        self.assertEqual(
            skipped.stderr.count("already applied, skipping"),
            3,
        )
        self.assertTrue(first.exists())

    def test_dependency_validation_errors_and_direct_transitive_enforcement(self) -> None:
        circular_directory = self.directory / "circular"
        circular_first = self.write_directory_migration(
            circular_directory, 1, "first", [], depends_on=[3]
        )
        self.write_directory_migration(circular_directory, 2, "second", [], depends_on=[1])
        self.write_directory_migration(circular_directory, 3, "third", [], depends_on=[2])
        circular = self.run_command(
            "validate", str(circular_first), "--migrations-dir", str(circular_directory)
        )
        self.assertEqual(circular.returncode, 1)
        circular_events = [json.loads(line) for line in circular.stdout.splitlines()]
        self.assertEqual(
            circular_events[-2:],
            [
                {"event": "circular_dependency_detected", "cycle": [1, 3, 2, 1], "status": "error"},
                {"event": "validation_complete", "version": 1, "status": "invalid"},
            ],
        )
        self.assertIn("circular dependency detected: cycle [1, 3, 2, 1]", circular.stderr)
        self.assertFalse(self.database.exists())

        missing_directory = self.directory / "missing"
        missing = self.write_directory_migration(missing_directory, 5, "missing", [], depends_on=[10])
        missing_result = self.run_command(
            "validate", str(missing), "--migrations-dir", str(missing_directory)
        )
        self.assertEqual(missing_result.returncode, 1)
        self.assertIn("dependency version 10 not found", missing_result.stderr)

        future_directory = self.directory / "future"
        future = self.write_directory_migration(future_directory, 5, "future", [], depends_on=[6])
        self.write_directory_migration(future_directory, 6, "later", [])
        future_result = self.run_command(
            "validate", str(future), "--migrations-dir", str(future_directory)
        )
        self.assertEqual(future_result.returncode, 1)
        self.assertIn("migration version 5 cannot depend on future version 6", future_result.stderr)

        first = self.write_migration(
            1,
            "create dependency source",
            [
                {
                    "type": "create_table",
                    "table": "dependency_source",
                    "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}],
                }
            ],
        )
        second = self.write_migration(2, "depends on first", [], depends_on=[1])
        third = self.write_migration(3, "depends on second", [], depends_on=[2])
        blocked = self.run_tool(third)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("dependency version 2 not found", blocked.stderr)
        self.assertEqual(self.run_tool(first).returncode, 0)
        blocked = self.run_tool(third)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("dependency version 2 not found", blocked.stderr)
        self.assertEqual(self.run_tool(second).returncode, 0)
        self.assertEqual(self.run_tool(third).returncode, 0)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(
                [row[0] for row in connection.execute("SELECT version FROM _migrations ORDER BY version")],
                [1, 2, 3],
            )

    def test_documented_uv_command(self) -> None:
        migration = self.write_migration(
            1,
            "run through uv",
            [
                {
                    "type": "create_table",
                    "table": "events",
                    "columns": [{"name": "message", "type": "TEXT"}],
                }
            ],
        )
        result = subprocess.run(
            [
                "uv",
                "run",
                "--project",
                "/app",
                "migration_tool.py",
                "migrate",
                str(migration),
                str(self.database),
            ],
            cwd="/app",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1]), {"event": "migration_complete", "version": 1, "operations_count": 1})
        rollback = subprocess.run(
            ["uv", "run", "--project", "/app", "migration_tool.py", "rollback", str(self.database)],
            cwd="/app",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(rollback.returncode, 0, rollback.stderr)
        self.assertEqual(
            json.loads(rollback.stdout.splitlines()[-1]),
            {"event": "rollback_finished", "versions_rolled_back": [1], "final_version": None},
        )


if __name__ == "__main__":
    unittest.main()
