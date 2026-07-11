from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from services.database import get_connection


@dataclass(frozen=True)
class ScannerSnapshot:
    run_id: str
    symbol: str
    spot_price: float
    volume: int | None
    underlying_oi: int | None
    source_quote_timestamp: datetime
    snapshot_time: datetime


class SnapshotRepository:
    def start_run(
        self,
        run_id: str,
        started_at: datetime,
        quote_timestamp: datetime,
        instrument_count: int,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pipeline_runs
                    (
                        run_id,
                        status,
                        started_at,
                        quote_timestamp,
                        instrument_count,
                        snapshot_count
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        started_at = EXCLUDED.started_at,
                        quote_timestamp = EXCLUDED.quote_timestamp,
                        instrument_count = EXCLUDED.instrument_count,
                        snapshot_count = EXCLUDED.snapshot_count;
                    """,
                    (
                        run_id,
                        "RUNNING",
                        started_at,
                        quote_timestamp,
                        instrument_count,
                        0,
                    ),
                )

            connection.commit()

    def complete_run(
        self,
        run_id: str,
        completed_at: datetime,
        snapshot_count: int,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = %s,
                        completed_at = %s,
                        snapshot_count = %s
                    WHERE run_id = %s;
                    """,
                    (
                        "SNAPSHOT_COMPLETE",
                        completed_at,
                        snapshot_count,
                        run_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Unable to complete pipeline run: "
                        f"{run_id}"
                    )

            connection.commit()

    def bulk_insert(
        self,
        snapshots: Iterable[ScannerSnapshot],
    ) -> int:
        records = [
            (
                snapshot.run_id,
                snapshot.symbol,
                snapshot.spot_price,
                snapshot.volume,
                snapshot.underlying_oi,
                snapshot.source_quote_timestamp,
                snapshot.snapshot_time,
            )
            for snapshot in snapshots
        ]

        if not records:
            return 0

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO scanner_snapshots
                    (
                        run_id,
                        symbol,
                        spot_price,
                        volume,
                        underlying_oi,
                        source_quote_timestamp,
                        snapshot_time
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id, symbol)
                    WHERE run_id IS NOT NULL
                    DO UPDATE SET
                        spot_price = EXCLUDED.spot_price,
                        volume = EXCLUDED.volume,
                        underlying_oi = EXCLUDED.underlying_oi,
                        source_quote_timestamp =
                            EXCLUDED.source_quote_timestamp,
                        snapshot_time = EXCLUDED.snapshot_time;
                    """,
                    records,
                )

            connection.commit()

        return len(records)

    def count_for_run(
        self,
        run_id: str,
    ) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM scanner_snapshots
                    WHERE run_id = %s;
                    """,
                    (run_id,),
                )

                result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"Unable to count snapshots for run: {run_id}"
            )

        return int(result[0])