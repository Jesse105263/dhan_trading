import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.migration_runner import (
    MigrationRunner,
)


class MigrationRunnerTest(unittest.TestCase):
    def test_discovers_migrations_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            migration_directory = Path(directory)

            second = migration_directory / "002_second.sql"
            first = migration_directory / "001_first.sql"

            second.write_text(
                "SELECT 2;",
                encoding="utf-8",
            )
            first.write_text(
                "SELECT 1;",
                encoding="utf-8",
            )

            with patch(
                "services.migration_runner."
                "MIGRATIONS_DIRECTORY",
                migration_directory,
            ):
                migrations = (
                    MigrationRunner
                    ._discover_migrations()
                )

            self.assertEqual(
                [migration.version for migration in migrations],
                ["001", "002"],
            )

            self.assertEqual(
                [migration.filename for migration in migrations],
                [
                    "001_first.sql",
                    "002_second.sql",
                ],
            )

    def test_calculates_migration_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            migration_directory = Path(directory)
            migration_path = (
                migration_directory
                / "001_test.sql"
            )

            content = "SELECT 1;"

            migration_path.write_text(
                content,
                encoding="utf-8",
            )

            expected_checksum = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()

            with patch(
                "services.migration_runner."
                "MIGRATIONS_DIRECTORY",
                migration_directory,
            ):
                migrations = (
                    MigrationRunner
                    ._discover_migrations()
                )

            self.assertEqual(
                migrations[0].checksum,
                expected_checksum,
            )

    def test_rejects_duplicate_versions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            migration_directory = Path(directory)

            (
                migration_directory
                / "001_first.sql"
            ).write_text(
                "SELECT 1;",
                encoding="utf-8",
            )

            (
                migration_directory
                / "001_second.sql"
            ).write_text(
                "SELECT 2;",
                encoding="utf-8",
            )

            with patch(
                "services.migration_runner."
                "MIGRATIONS_DIRECTORY",
                migration_directory,
            ):
                with self.assertRaises(RuntimeError):
                    MigrationRunner._discover_migrations()


if __name__ == "__main__":
    unittest.main()