from typing import Any

from services.database import get_connection
from services.stage import Stage


REQUIRED_TABLES = {
    "instruments",
    "underlying_quotes",
    "option_quotes",
    "trade_signals",
    "scanner_snapshots",
}


class DatabaseStage(Stage):
    def __init__(self) -> None:
        super().__init__("Database")

    def run(self, context: dict[str, Any]) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                postgres_version = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                    """
                )

                existing_tables = {
                    row[0]
                    for row in cursor.fetchall()
                }

                missing_tables = REQUIRED_TABLES - existing_tables

                if missing_tables:
                    missing = ", ".join(sorted(missing_tables))

                    raise RuntimeError(
                        f"Missing required database tables: {missing}"
                    )

                cursor.execute("SELECT 1;")
                health_check = cursor.fetchone()[0]

        context["database_connected"] = health_check == 1
        context["postgres_version"] = postgres_version
        context["database_tables"] = sorted(existing_tables)

        print("PostgreSQL connection: OK")
        print(f"Required tables: {len(REQUIRED_TABLES)}")
        print("Schema verification: OK")