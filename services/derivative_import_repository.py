from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from uuid import UUID

from services.database import get_connection


@dataclass(frozen=True)
class DerivativeImportFailure:
    run_id: UUID
    row_number: int | None
    security_id: str | None
    trading_symbol: str | None
    error_type: str
    error_message: str
    occurred_at: datetime


class DerivativeImportRepository:
    def start_run(
        self,
        run_id: UUID,
        started_at: datetime,
        source_url: str | None,
        source_file_name: str | None,
        source_timestamp: datetime | None,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO derivative_import_runs
                    (
                        run_id,
                        status,
                        source_url,
                        source_file_name,
                        source_timestamp,
                        started_at
                    )
                    VALUES (%s, 'RUNNING', %s, %s, %s, %s);
                    """,
                    (
                        run_id,
                        source_url,
                        source_file_name,
                        source_timestamp,
                        started_at,
                    ),
                )
            connection.commit()

    def complete_run(
        self,
        run_id: UUID,
        completed_at: datetime,
        rows_read: int,
        rows_eligible: int,
        contracts_upserted: int,
        contracts_deactivated: int,
        rows_rejected: int,
    ) -> None:
        self._finish_run(
            run_id=run_id,
            status="COMPLETED",
            completed_at=completed_at,
            rows_read=rows_read,
            rows_eligible=rows_eligible,
            contracts_upserted=contracts_upserted,
            contracts_deactivated=contracts_deactivated,
            rows_rejected=rows_rejected,
            error_message=None,
        )

    def fail_run(
        self,
        run_id: UUID,
        completed_at: datetime,
        rows_read: int,
        rows_eligible: int,
        contracts_upserted: int,
        contracts_deactivated: int,
        rows_rejected: int,
        error_message: str,
    ) -> None:
        self._finish_run(
            run_id=run_id,
            status="FAILED",
            completed_at=completed_at,
            rows_read=rows_read,
            rows_eligible=rows_eligible,
            contracts_upserted=contracts_upserted,
            contracts_deactivated=contracts_deactivated,
            rows_rejected=rows_rejected,
            error_message=error_message,
        )

    def insert_failures(
        self,
        failures: Iterable[DerivativeImportFailure],
    ) -> int:
        records = [
            (
                failure.run_id,
                failure.row_number,
                failure.security_id,
                failure.trading_symbol,
                failure.error_type,
                failure.error_message,
                failure.occurred_at,
            )
            for failure in failures
        ]

        if not records:
            return 0

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO derivative_import_failures
                    (
                        run_id,
                        row_number,
                        security_id,
                        trading_symbol,
                        error_type,
                        error_message,
                        occurred_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    records,
                )
            connection.commit()

        return len(records)

    @staticmethod
    def _finish_run(
        run_id: UUID,
        status: str,
        completed_at: datetime,
        rows_read: int,
        rows_eligible: int,
        contracts_upserted: int,
        contracts_deactivated: int,
        rows_rejected: int,
        error_message: str | None,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE derivative_import_runs
                    SET
                        status = %s,
                        completed_at = %s,
                        rows_read = %s,
                        rows_eligible = %s,
                        contracts_upserted = %s,
                        contracts_deactivated = %s,
                        rows_rejected = %s,
                        error_message = %s
                    WHERE run_id = %s;
                    """,
                    (
                        status,
                        completed_at,
                        rows_read,
                        rows_eligible,
                        contracts_upserted,
                        contracts_deactivated,
                        rows_rejected,
                        error_message,
                        run_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError(
                        f"Unable to update derivative import run: {run_id}"
                    )
            connection.commit()
