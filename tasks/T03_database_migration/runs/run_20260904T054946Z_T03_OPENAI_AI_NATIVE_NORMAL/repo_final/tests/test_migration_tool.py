"""Visible cumulative tests for the revealed migration checkpoints 1 and 2."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "migration_tool.py"


class MigrationToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temporary_directory.name)
        self.database = self.temp_path / "app.db"
        self.migration_number = 0

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_migration(self, migration: dict[str, Any]) -> subprocess.CompletedProcess[str]:
        self.migration_number += 1
        migration_path = self.temp_path / f"migration-{self.migration_number}.json"
        migration_path.write_text(json.dumps(migration), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(TOOL), "migrate", str(migration_path), str(self.database)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_rollback(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), "rollback", str(self.database), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_validate(self, migration_file: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), "validate", str(migration_file), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_migrate_all(self, directory: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "migrate-all",
                "--migrations-dir",
                str(directory),
                str(self.database),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_directory_migration(
        self, directory: Path, filename: str, migration: dict[str, Any]
    ) -> Path:
        path = directory / filename
        path.write_text(json.dumps(migration), encoding="utf-8")
        return path

    def events(self, completed: subprocess.CompletedProcess[str]) -> list[dict[str, Any]]:
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return [json.loads(line) for line in completed.stdout.splitlines()]

    def migration_rows(self) -> list[tuple[int, str]]:
        with sqlite3.connect(self.database) as connection:
            return connection.execute(
                "SELECT version, description FROM _migrations ORDER BY version"
            ).fetchall()

    def test_checkpoint_one_schema_tracking_skip_and_validation(self) -> None:
        create = {
            "version": 1,
            "description": "create users",
            "operations": [
                {
                    "type": "create_table",
                    "table": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
                        {"name": "email", "type": "TEXT", "not_null": True, "unique": True},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
                    ],
                }
            ],
        }
        self.assertEqual(
            self.events(self.run_migration(create)),
            [
                {"event": "operation_applied", "type": "create_table", "table": "users", "version": 1},
                {"event": "migration_complete", "version": 1, "operations_count": 1},
            ],
        )
        add = {
            "version": 2,
            "description": "add age",
            "operations": [
                {
                    "type": "add_column",
                    "table": "users",
                    "column": {"name": "age", "type": "INTEGER", "default": "0"},
                }
            ],
        }
        self.assertEqual(
            self.events(self.run_migration(add))[0],
            {"event": "operation_applied", "type": "add_column", "table": "users", "column": "age", "version": 2},
        )
        skipped = self.run_migration(add)
        self.assertEqual(skipped.returncode, 0)
        self.assertEqual(
            json.loads(skipped.stdout),
            {"event": "migration_skipped", "version": 2, "reason": "already_applied"},
        )
        self.assertEqual(skipped.stderr, "Warning: Migration version 2 already applied, skipping\n")
        self.assertEqual(self.migration_rows(), [(1, "create users"), (2, "add age")])

        invalid = self.run_migration({"version": 3, "description": "bad"})
        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(invalid.stdout, "")
        self.assertIn("Error: invalid migration schema: missing required field 'operations'", invalid.stderr)

    def test_drop_column_preserves_rows_and_supported_schema(self) -> None:
        create = {
            "version": 1,
            "description": "create products",
            "operations": [
                {
                    "type": "create_table",
                    "table": "products",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
                        {"name": "sku", "type": "TEXT", "not_null": True, "unique": True},
                        {"name": "label", "type": "TEXT", "default": "'anonymous'"},
                        {"name": "obsolete", "type": "TEXT"},
                        {"name": "price", "type": "REAL", "not_null": True, "default": "0"},
                    ],
                }
            ],
        }
        self.events(self.run_migration(create))
        with sqlite3.connect(self.database) as connection:
            connection.executemany(
                "INSERT INTO products (sku, label, obsolete, price) VALUES (?, ?, ?, ?)",
                [("A-1", "Alpha", "old-a", 1.5), ("B-2", "Beta", "old-b", 2.5)],
            )
        drop = {
            "version": 2,
            "description": "remove obsolete",
            "operations": [{"type": "drop_column", "table": "products", "column": "obsolete"}],
        }
        self.assertEqual(
            self.events(self.run_migration(drop))[0],
            {"event": "operation_applied", "type": "drop_column", "table": "products", "column": "obsolete", "version": 2},
        )
        with sqlite3.connect(self.database) as connection:
            rows = connection.execute("SELECT id, sku, label, price FROM products ORDER BY id").fetchall()
            columns = connection.execute("PRAGMA table_info(products)").fetchall()
            source = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'products'"
            ).fetchone()[0]
            indexes = connection.execute("PRAGMA index_list(products)").fetchall()
            temporary_tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE '_migration_tmp_products_%'"
            ).fetchall()
        self.assertEqual(rows, [(1, "A-1", "Alpha", 1.5), (2, "B-2", "Beta", 2.5)])
        self.assertEqual([column[1] for column in columns], ["id", "sku", "label", "price"])
        self.assertEqual(columns[2][4], "'anonymous'")
        self.assertIn("INTEGER PRIMARY KEY AUTOINCREMENT", source.upper())
        self.assertTrue(any(index[2] and index[3] == "u" for index in indexes))
        self.assertEqual(temporary_tables, [])
        self.assertEqual(self.migration_rows(), [(1, "create products"), (2, "remove obsolete")])

    def test_forbidden_drops_do_not_record_failed_versions(self) -> None:
        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create only column table",
                    "operations": [
                        {"type": "create_table", "table": "single_value", "columns": [{"name": "value", "type": "TEXT"}]}
                    ],
                }
            )
        )
        only_column = self.run_migration(
            {"version": 2, "description": "bad only drop", "operations": [{"type": "drop_column", "table": "single_value", "column": "value"}]}
        )
        self.assertEqual(only_column.returncode, 1)
        self.assertIn("cannot drop the only column", only_column.stderr)
        self.events(
            self.run_migration(
                {
                    "version": 3,
                    "description": "create protected table",
                    "operations": [
                        {
                            "type": "create_table",
                            "table": "protected",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "value", "type": "TEXT"},
                            ],
                        }
                    ],
                }
            )
        )
        primary_key = self.run_migration(
            {"version": 4, "description": "bad key drop", "operations": [{"type": "drop_column", "table": "protected", "column": "id"}]}
        )
        self.assertEqual(primary_key.returncode, 1)
        self.assertIn("cannot drop primary key column 'id'", primary_key.stderr)
        self.assertEqual(
            self.migration_rows(),
            [(1, "create only column table"), (3, "create protected table")],
        )

    def test_checkpoint_two_data_operations_are_ordered_and_atomic(self) -> None:
        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create people",
                    "operations": [
                        {
                            "type": "create_table",
                            "table": "people",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "first_name", "type": "TEXT"},
                                {"name": "last_name", "type": "TEXT"},
                                {"name": "full_name", "type": "TEXT"},
                                {"name": "old_email", "type": "TEXT"},
                                {"name": "new_email", "type": "TEXT"},
                                {"name": "status", "type": "TEXT"},
                            ],
                        }
                    ],
                }
            )
        )
        with sqlite3.connect(self.database) as connection:
            connection.executemany(
                "INSERT INTO people VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (1, "Ada", "Lovelace", None, "ada@example.test", "old", None),
                    (2, "Grace", "Hopper", None, None, "old", "keep"),
                ],
            )
        data_migration = {
            "version": 2,
            "description": "transform people",
            "operations": [
                {
                    "type": "transform_data",
                    "table": "people",
                    "transformations": [
                        {"column": "full_name", "expression": "first_name"},
                        {"column": "full_name", "expression": "full_name || ' ' || last_name"},
                    ],
                },
                {
                    "type": "migrate_column_data",
                    "table": "people",
                    "from_column": "old_email",
                    "to_column": "new_email",
                    "default_value": "missing@example.test",
                },
                {
                    "type": "backfill_data",
                    "table": "people",
                    "column": "status",
                    "value": "'active'",
                    "where": "status IS NULL",
                },
            ],
        }
        events = self.events(self.run_migration(data_migration))
        self.assertEqual([event["type"] for event in events[:-1]], ["transform_data", "migrate_column_data", "backfill_data"])
        self.assertEqual(events[-1], {"event": "migration_complete", "version": 2, "operations_count": 3})
        with sqlite3.connect(self.database) as connection:
            rows = connection.execute(
                "SELECT full_name, new_email, status FROM people ORDER BY id"
            ).fetchall()
        self.assertEqual(
            rows,
            [
                ("Ada Lovelace", "ada@example.test", "active"),
                ("Grace Hopper", "missing@example.test", "keep"),
            ],
        )

        failed = self.run_migration(
            {
                "version": 3,
                "description": "must roll back",
                "operations": [
                    {"type": "backfill_data", "table": "people", "column": "status", "value": "'broken'"},
                    {
                        "type": "transform_data",
                        "table": "people",
                        "transformations": [{"column": "missing", "expression": "1"}],
                    },
                ],
            }
        )
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(failed.stdout, "")
        self.assertIn("column 'missing' does not exist", failed.stderr)
        with sqlite3.connect(self.database) as connection:
            statuses = connection.execute("SELECT status FROM people ORDER BY id").fetchall()
        self.assertEqual(statuses, [("active",), ("keep",)])
        self.assertEqual(self.migration_rows(), [(1, "create people"), (2, "transform people")])

    def test_checkpoint_two_validation_and_missing_columns(self) -> None:
        invalid = self.run_migration(
            {
                "version": 1,
                "description": "bad transform",
                "operations": [{"type": "transform_data", "table": "users", "transformations": [{"column": "name"}]}],
            }
        )
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("missing required field 'expression'", invalid.stderr)

        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create users",
                    "operations": [
                        {"type": "create_table", "table": "users", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}
                    ],
                }
            )
        )
        missing = self.run_migration(
            {
                "version": 2,
                "description": "missing target",
                "operations": [
                    {"type": "backfill_data", "table": "users", "column": "status", "value": "'active'"}
                ],
            }
        )
        self.assertEqual(missing.returncode, 1)
        self.assertIn("column 'status' does not exist", missing.stderr)
        self.assertEqual(self.migration_rows(), [(1, "create users")])

    def test_checkpoint_three_foreign_keys_indexes_and_checks(self) -> None:
        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create related tables",
                    "operations": [
                        {
                            "type": "create_table",
                            "table": "users",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "email", "type": "TEXT", "not_null": True, "unique": True},
                            ],
                        },
                        {
                            "type": "create_table",
                            "table": "posts",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "user_id", "type": "INTEGER", "not_null": True},
                                {"name": "title", "type": "TEXT", "not_null": True},
                            ],
                        },
                    ],
                }
            )
        )
        foreign_key = {
            "version": 2,
            "description": "link posts to users",
            "operations": [
                {
                    "type": "add_foreign_key",
                    "table": "posts",
                    "name": "fk_posts_user",
                    "columns": ["user_id"],
                    "references": {"table": "users", "columns": ["id"]},
                    "on_delete": "CASCADE",
                    "on_update": "RESTRICT",
                }
            ],
        }
        foreign_events = self.events(self.run_migration(foreign_key))
        self.assertEqual(
            foreign_events[0],
            {"event": "operation_applied", "type": "add_foreign_key", "table": "posts", "name": "fk_posts_user", "version": 2},
        )
        with sqlite3.connect(self.database) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO users VALUES (1, 'user@example.test')")
            connection.execute("INSERT INTO posts VALUES (1, 1, 'valid')")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO posts VALUES (2, 999, 'invalid')")
            connection.execute("DELETE FROM users WHERE id = 1")
            self.assertEqual(connection.execute("SELECT * FROM posts").fetchall(), [])
            foreign_key_list = connection.execute("PRAGMA foreign_key_list(posts)").fetchall()
        self.assertEqual(foreign_key_list[0][2], "users")
        self.assertEqual(foreign_key_list[0][6], "CASCADE")

        check = {
            "version": 3,
            "description": "require a title",
            "operations": [
                {
                    "type": "add_check_constraint",
                    "table": "posts",
                    "name": "chk_posts_title",
                    "expression": "length(title) > 0",
                }
            ],
        }
        self.events(self.run_migration(check))
        index = {
            "version": 4,
            "description": "index posts",
            "operations": [
                {
                    "type": "create_index",
                    "table": "posts",
                    "name": "idx_posts_user_title",
                    "columns": ["user_id", "title"],
                    "unique": False,
                }
            ],
        }
        self.events(self.run_migration(index))
        with sqlite3.connect(self.database) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO users VALUES (2, 'other@example.test')")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO posts VALUES (3, 2, '')")
            source = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'posts'"
            ).fetchone()[0]
            self.assertIn('CONSTRAINT "chk_posts_title"', source)
            self.assertIsNotNone(
                connection.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = 'idx_posts_user_title'"
                ).fetchone()
            )

        self.events(
            self.run_migration(
                {
                    "version": 5,
                    "description": "remove title check",
                    "operations": [{"type": "drop_check_constraint", "table": "posts", "name": "chk_posts_title"}],
                }
            )
        )
        with sqlite3.connect(self.database) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO posts VALUES (4, 2, '')")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO posts VALUES (5, 999, 'still foreign keyed')")

        duplicate_index = self.run_migration(index | {"version": 6, "description": "duplicate index"})
        self.assertEqual(duplicate_index.returncode, 1)
        self.assertIn("index 'idx_posts_user_title' already exists", duplicate_index.stderr)
        self.events(
            self.run_migration(
                {
                    "version": 7,
                    "description": "drop index",
                    "operations": [{"type": "drop_index", "name": "idx_posts_user_title"}],
                }
            )
        )
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = 'idx_posts_user_title'"
                ).fetchone()
            )

        self.events(
            self.run_migration(
                {
                    "version": 8,
                    "description": "remove foreign key",
                    "operations": [{"type": "drop_foreign_key", "table": "posts", "name": "fk_posts_user"}],
                }
            )
        )
        with sqlite3.connect(self.database) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO posts VALUES (6, 999, 'unconstrained')")

    def test_checkpoint_three_rejects_invalid_existing_data_and_check(self) -> None:
        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create foreign key candidates",
                    "operations": [
                        {"type": "create_table", "table": "parents", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]},
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
                            "table": "ages",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "age", "type": "INTEGER"},
                            ],
                        },
                    ],
                }
            )
        )
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO children VALUES (1, 999)")
            connection.execute("INSERT INTO ages VALUES (1, -1)")
        invalid_foreign_key = self.run_migration(
            {
                "version": 2,
                "description": "invalid existing child",
                "operations": [
                    {
                        "type": "add_foreign_key",
                        "table": "children",
                        "name": "fk_children_parent",
                        "columns": ["parent_id"],
                        "references": {"table": "parents", "columns": ["id"]},
                    }
                ],
            }
        )
        self.assertEqual(invalid_foreign_key.returncode, 1)
        self.assertIn("foreign key violation: referenced row in 'parents'", invalid_foreign_key.stderr)
        invalid_check = self.run_migration(
            {
                "version": 3,
                "description": "invalid existing age",
                "operations": [
                    {
                        "type": "add_check_constraint",
                        "table": "ages",
                        "name": "chk_ages_nonnegative",
                        "expression": "age >= 0",
                    }
                ],
            }
        )
        self.assertEqual(invalid_check.returncode, 1)
        self.assertIn("check constraint violation", invalid_check.stderr)
        self.assertEqual(
            self.migration_rows(),
            [(1, "create foreign key candidates")],
        )

    def test_checkpoint_four_automatic_rollback_and_target_version(self) -> None:
        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create users",
                    "operations": [
                        {
                            "type": "create_table",
                            "table": "users",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "name", "type": "TEXT"},
                            ],
                        }
                    ],
                }
            )
        )
        self.events(
            self.run_migration(
                {
                    "version": 2,
                    "description": "add age",
                    "operations": [
                        {"type": "add_column", "table": "users", "column": {"name": "age", "type": "INTEGER", "default": "0"}}
                    ],
                }
            )
        )
        self.events(
            self.run_migration(
                {
                    "version": 3,
                    "description": "create posts",
                    "operations": [
                        {"type": "create_table", "table": "posts", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}
                    ],
                }
            )
        )
        rollback = self.run_rollback("--to-version", "1")
        events = self.events(rollback)
        self.assertEqual(events[0], {"event": "rollback_started", "version": 3, "description": "create posts"})
        self.assertEqual(
            events[1],
            {"event": "operation_rolled_back", "type": "create_table", "table": "posts", "version": 3},
        )
        self.assertEqual(events[-1], {"event": "rollback_finished", "versions_rolled_back": [3, 2], "final_version": 1})
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(
                [row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()],
                ["id", "name"],
            )
            self.assertIsNone(
                connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'posts'").fetchone()
            )
        self.assertEqual(self.migration_rows(), [(1, "create users")])

    def test_checkpoint_four_explicit_and_data_column_rollback(self) -> None:
        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create contacts",
                    "operations": [
                        {
                            "type": "create_table",
                            "table": "contacts",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "first_name", "type": "TEXT"},
                                {"name": "last_name", "type": "TEXT"},
                                {"name": "email", "type": "TEXT"},
                            ],
                        }
                    ],
                }
            )
        )
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO contacts VALUES (1, 'Ada', 'Lovelace', 'ada@example.test')")
        self.events(
            self.run_migration(
                {
                    "version": 2,
                    "description": "compute full name",
                    "operations": [
                        {"type": "add_column", "table": "contacts", "column": {"name": "full_name", "type": "TEXT"}},
                        {
                            "type": "transform_data",
                            "table": "contacts",
                            "transformations": [{"column": "full_name", "expression": "first_name || ' ' || last_name"}],
                        },
                    ],
                    "rollback_operations": [{"type": "drop_column", "table": "contacts", "column": "full_name"}],
                }
            )
        )
        self.events(
            self.run_migration(
                {
                    "version": 3,
                    "description": "rename email",
                    "operations": [
                        {"type": "add_column", "table": "contacts", "column": {"name": "email_address", "type": "TEXT"}},
                        {"type": "migrate_column_data", "table": "contacts", "from_column": "email", "to_column": "email_address"},
                        {"type": "drop_column", "table": "contacts", "column": "email"},
                    ],
                }
            )
        )
        rollback = self.run_rollback()
        events = self.events(rollback)
        self.assertEqual(
            [event["type"] for event in events if event["event"] == "operation_rolled_back"],
            ["drop_column", "migrate_column_data", "add_column"],
        )
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(
                connection.execute("SELECT email FROM contacts").fetchall(),
                [("ada@example.test",)],
            )
            self.assertNotIn(
                "email_address",
                [row[1] for row in connection.execute("PRAGMA table_info(contacts)").fetchall()],
            )
        self.events(self.run_rollback())
        with sqlite3.connect(self.database) as connection:
            self.assertNotIn(
                "full_name",
                [row[1] for row in connection.execute("PRAGMA table_info(contacts)").fetchall()],
            )
        self.assertEqual(self.migration_rows(), [(1, "create contacts")])

    def test_checkpoint_four_constraint_rollbacks_and_nonreversible_failure(self) -> None:
        self.events(
            self.run_migration(
                {
                    "version": 1,
                    "description": "create tables",
                    "operations": [
                        {"type": "create_table", "table": "parents", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]},
                        {
                            "type": "create_table",
                            "table": "children",
                            "columns": [
                                {"name": "id", "type": "INTEGER", "primary_key": True},
                                {"name": "parent_id", "type": "INTEGER"},
                                {"name": "status", "type": "TEXT"},
                            ],
                        },
                    ],
                }
            )
        )
        self.events(
            self.run_migration(
                {
                    "version": 2,
                    "description": "add constraints",
                    "operations": [
                        {
                            "type": "add_foreign_key",
                            "table": "children",
                            "name": "fk_children_parent",
                            "columns": ["parent_id"],
                            "references": {"table": "parents", "columns": ["id"]},
                        },
                        {"type": "create_index", "table": "children", "name": "idx_children_parent", "columns": ["parent_id"]},
                        {"type": "add_check_constraint", "table": "children", "name": "chk_children_status", "expression": "status IS NULL OR length(status) > 0"},
                    ],
                }
            )
        )
        self.events(self.run_rollback())
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_key_list(children)").fetchall(), [])
            self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'idx_children_parent'").fetchone())
            schema = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'children'").fetchone()[0]
            self.assertNotIn("chk_children_status", schema)

        self.events(
            self.run_migration(
                {
                    "version": 3,
                    "description": "non reversible backfill",
                    "operations": [{"type": "backfill_data", "table": "children", "column": "status", "value": "'active'"}],
                }
            )
        )
        failed = self.run_rollback()
        self.assertEqual(failed.returncode, 1)
        self.assertIn("cannot rollback version 3: missing rollback_operations for backfill_data", failed.stderr)
        self.assertEqual(self.migration_rows(), [(1, "create tables"), (3, "non reversible backfill")])

    def test_checkpoint_five_validate_graphs_without_database_mutation(self) -> None:
        directory = self.temp_path / "migrations"
        directory.mkdir()
        migration_one = self.write_directory_migration(
            directory,
            "migration_v1.json",
            {
                "version": 1,
                "description": "create users",
                "operations": [{"type": "create_table", "table": "users", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}],
            },
        )
        migration_two = self.write_directory_migration(
            directory,
            "migration_v2.json",
            {
                "version": 2,
                "description": "create posts",
                "depends_on": [1],
                "operations": [{"type": "create_table", "table": "posts", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}],
            },
        )
        valid = self.run_validate(migration_two, "--migrations-dir", str(directory))
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(
            [json.loads(line) for line in valid.stdout.splitlines()],
            [
                {"event": "validation_started", "migration_file": "migration_v2.json"},
                {"event": "dependency_check", "version": 2, "depends_on": [1], "status": "ok"},
                {"event": "validation_complete", "version": 2, "status": "valid"},
            ],
        )
        self.assertFalse(self.database.exists())
        no_directory = self.run_validate(migration_two)
        self.assertEqual(no_directory.returncode, 0)
        self.assertEqual(json.loads(no_directory.stdout.splitlines()[1])["status"], "warning")

        self.write_directory_migration(
            directory,
            "migration_v3.json",
            {
                "version": 3,
                "description": "cycle start",
                "depends_on": [5],
                "operations": [{"type": "create_table", "table": "three", "columns": [{"name": "id", "type": "INTEGER"}]}],
            },
        )
        self.write_directory_migration(
            directory,
            "migration_v4.json",
            {
                "version": 4,
                "description": "cycle middle",
                "depends_on": [3],
                "operations": [{"type": "create_table", "table": "four", "columns": [{"name": "id", "type": "INTEGER"}]}],
            },
        )
        migration_five = self.write_directory_migration(
            directory,
            "migration_v5.json",
            {
                "version": 5,
                "description": "cycle end",
                "depends_on": [4],
                "operations": [{"type": "create_table", "table": "five", "columns": [{"name": "id", "type": "INTEGER"}]}],
            },
        )
        circular = self.run_validate(migration_five, "--migrations-dir", str(directory))
        self.assertEqual(circular.returncode, 1)
        circular_events = [json.loads(line) for line in circular.stdout.splitlines()]
        self.assertEqual(circular_events[1]["event"], "circular_dependency_detected")
        self.assertEqual(circular_events[1]["cycle"], [3, 5, 4, 3])
        self.assertIn("Error: circular dependency detected", circular.stderr)
        self.assertTrue(migration_one.exists())

    def test_checkpoint_five_migrate_all_orders_dependencies_and_skips_applied(self) -> None:
        directory = self.temp_path / "batch"
        directory.mkdir()
        self.write_directory_migration(
            directory,
            "z_v4.json",
            {
                "version": 4,
                "description": "add active",
                "depends_on": [2, 3],
                "operations": [{"type": "add_column", "table": "users", "column": {"name": "active", "type": "INTEGER", "default": "1"}}],
            },
        )
        self.write_directory_migration(
            directory,
            "a_v1.json",
            {
                "version": 1,
                "description": "create users",
                "operations": [{"type": "create_table", "table": "users", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}],
            },
        )
        self.write_directory_migration(
            directory,
            "m_v2.json",
            {
                "version": 2,
                "description": "add name",
                "depends_on": [1],
                "operations": [{"type": "add_column", "table": "users", "column": {"name": "name", "type": "TEXT"}}],
            },
        )
        self.write_directory_migration(
            directory,
            "n_v3.json",
            {
                "version": 3,
                "description": "create audit",
                "depends_on": [1],
                "operations": [{"type": "create_table", "table": "audit", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}],
            },
        )
        batch = self.run_migrate_all(directory)
        self.assertEqual(batch.returncode, 0, batch.stderr)
        events = [json.loads(line) for line in batch.stdout.splitlines()]
        self.assertIn({"event": "dependency_resolved", "order": [1, 2, 3, 4]}, events)
        self.assertEqual(events[-1], {"event": "batch_complete", "migrations_applied": 4, "migrations_skipped": 0, "final_version": 4})
        self.assertEqual(self.migration_rows(), [(1, "create users"), (2, "add name"), (3, "create audit"), (4, "add active")])
        repeated = self.run_migrate_all(directory)
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(
            json.loads(repeated.stdout.splitlines()[-1]),
            {"event": "batch_complete", "migrations_applied": 0, "migrations_skipped": 4, "final_version": 4},
        )

    def test_checkpoint_five_single_migration_requires_applied_dependencies(self) -> None:
        dependency = {
            "version": 1,
            "description": "create users",
            "operations": [{"type": "create_table", "table": "users", "columns": [{"name": "id", "type": "INTEGER", "primary_key": True}]}],
        }
        dependent = {
            "version": 2,
            "description": "add name",
            "depends_on": [1],
            "operations": [{"type": "add_column", "table": "users", "column": {"name": "name", "type": "TEXT"}}],
        }
        blocked = self.run_migration(dependent)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("depends on unapplied version 1", blocked.stderr)
        self.events(self.run_migration(dependency))
        self.events(self.run_migration(dependent))


if __name__ == "__main__":
    unittest.main()
