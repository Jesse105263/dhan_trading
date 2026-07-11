import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from services.database import get_connection


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIRECTORY = PROJECT_ROOT / "migrations"


@dataclass(frozen=True)
class Migration:
    version: str
    filename: str
    path: Path
    checksum: str


class MigrationRunner:
    def run(self) -> int:
        self._validate_migrations_directory()
        self._create_migrations_table()

        migrations = self._discover_migrations()
        applied_migrations = self._load_applied_migrations()

        applied_count = 0

        for migration in migrations:
            existing_checksum = applied_migrations.get(
                migration.version
            )

            if existing_checksum is not None:
                if existing_checksum != migration.checksum:
                    raise RuntimeError(
                        "Applied migration was modified: "
                        f"{migration.filename}"
                    )

                logger.info(
                    "Migration already applied | version=%s | file=%s",
                    migration.version,
                    migration.filename,
                )
                continue

            self._apply_migration(migration)
            applied_count += 1

        logger.info(
            "Migration run complete | discovered=%s | applied=%s",
            len(migrations),
            applied_count,
        )

        return applied_count

    @staticmethod
    def _validate_migrations_directory() -> None:
        if not MIGRATIONS_DIRECTORY.exists():
            raise RuntimeError(
                "Migrations directory does not exist: "
                f"{MIGRATIONS_DIRECTORY}"
            )

        if not MIGRATIONS_DIRECTORY.is_dir():
            raise RuntimeError(
                "Migrations path is not a directory: "
                f"{MIGRATIONS_DIRECTORY}"
            )

    @staticmethod
    def _create_migrations_table() -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations
                    (
                        version VARCHAR(100) PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        checksum VARCHAR(64) NOT NULL,
                        applied_at TIMESTAMP NOT NULL
                            DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

            connection.commit()

    @staticmethod
    def _discover_migrations() -> list[Migration]:
        migration_paths = sorted(
            MIGRATIONS_DIRECTORY.glob("*.sql"),
            key=lambda path: path.name,
        )

        migrations: list[Migration] = []
        versions: set[str] = set()

        for path in migration_paths:
            version = path.stem.split("_", maxsplit=1)[0]

            if not version:
                raise RuntimeError(
                    f"Invalid migration filename: {path.name}"
                )

            if version in versions:
                raise RuntimeError(
                    f"Duplicate migration version: {version}"
                )

            content = path.read_bytes()
            checksum = hashlib.sha256(content).hexdigest()

            migrations.append(
                Migration(
                    version=version,
                    filename=path.name,
                    path=path,
                    checksum=checksum,
                )
            )

            versions.add(version)

        if not migrations:
            raise RuntimeError(
                "No SQL migration files were found."
            )

        return migrations

    @staticmethod
    def _load_applied_migrations() -> dict[str, str]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        version,
                        checksum
                    FROM schema_migrations
                    ORDER BY version;
                    """
                )

                rows = cursor.fetchall()

        return {
            str(row[0]): str(row[1])
            for row in rows
        }

    @staticmethod
    def _apply_migration(
        migration: Migration,
    ) -> None:
        sql = migration.path.read_text(
            encoding="utf-8"
        )

        if not sql.strip():
            raise RuntimeError(
                "Migration file is empty: "
                f"{migration.filename}"
            )

        logger.info(
            "Applying migration | version=%s | file=%s",
            migration.version,
            migration.filename,
        )

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)

                    cursor.execute(
                        """
                        INSERT INTO schema_migrations
                        (
                            version,
                            filename,
                            checksum,
                            applied_at
                        )
                        VALUES
                        (%s, %s, %s, %s);
                        """,
                        (
                            migration.version,
                            migration.filename,
                            migration.checksum,
                            datetime.now(),
                        ),
                    )

                connection.commit()
            except Exception:
                connection.rollback()
                raise

        logger.info(
            "Migration applied | version=%s | file=%s",
            migration.version,
            migration.filename,
        )


def main() -> None:
    runner = MigrationRunner()
    applied_count = runner.run()

    print(
        "✅ Database migrations complete "
        f"(new migrations applied: {applied_count})"
    )


if __name__ == "__main__":
    main()