from typing import Any

from services.database import get_connection
from services.stage import Stage


REQUIRED_TABLES = {
    "instruments",
    "underlying_quotes",
    "option_quotes",
    "trade_signals",
    "pipeline_runs",
    "scanner_snapshots",
    "market_features",
}


class DatabaseStage(Stage):
    def __init__(self) -> None:
        super().__init__("Database")

    def run(self, context: dict[str, Any]) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                postgres_version = cursor.fetchone()

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

                missing_tables = (
                    REQUIRED_TABLES
                    - existing_tables
                )

                if missing_tables:
                    missing = ", ".join(
                        sorted(missing_tables)
                    )

                    raise RuntimeError(
                        "Missing required database tables: "
                        f"{missing}"
                    )

                cursor.execute("SELECT 1;")
                health_result = cursor.fetchone()

        if postgres_version is None:
            raise RuntimeError(
                "Unable to read PostgreSQL version."
            )

        if health_result is None:
            raise RuntimeError(
                "PostgreSQL health check returned no result."
            )

        context["database_connected"] = (
            health_result[0] == 1
        )
        context["postgres_version"] = (
            postgres_version[0]
        )
        context["database_tables"] = sorted(
            existing_tables
        )

        print("PostgreSQL connection: OK")
        print(
            f"Required tables: {len(REQUIRED_TABLES)}"
        )
        print("Schema verification: OK")