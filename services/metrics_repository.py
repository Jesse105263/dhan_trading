from dataclasses import dataclass
from datetime import datetime

from services.database import get_connection


@dataclass(frozen=True)
class StageMetric:
    run_id: str
    stage_name: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    records_requested: int | None
    records_received: int | None
    records_written: int | None
    source_timestamp: datetime | None
    data_freshness_seconds: float | None


class MetricsRepository:
    def insert(
        self,
        metric: StageMetric,
    ) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO stage_metrics
                    (
                        run_id,
                        stage_name,
                        status,
                        started_at,
                        completed_at,
                        duration_ms,
                        records_requested,
                        records_received,
                        records_written,
                        source_timestamp,
                        data_freshness_seconds
                    )
                    VALUES
                    (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    RETURNING id;
                    """,
                    (
                        metric.run_id,
                        metric.stage_name,
                        metric.status,
                        metric.started_at,
                        metric.completed_at,
                        metric.duration_ms,
                        metric.records_requested,
                        metric.records_received,
                        metric.records_written,
                        metric.source_timestamp,
                        metric.data_freshness_seconds,
                    ),
                )

                result = cursor.fetchone()

            connection.commit()

        if result is None:
            raise RuntimeError(
                "Stage metric was not created."
            )

        return int(result[0])

    def count_for_run(
        self,
        run_id: str,
    ) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM stage_metrics
                    WHERE run_id = %s;
                    """,
                    (run_id,),
                )

                result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"Unable to count metrics for run: {run_id}"
            )

        return int(result[0])