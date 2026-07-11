from datetime import datetime

from services.database import get_connection


class PipelineRunRepository:
    def start_run(
        self,
        run_id: str,
        started_at: datetime,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pipeline_runs
                    (
                        run_id,
                        status,
                        started_at
                    )
                    VALUES
                    (%s, %s, %s)
                    ON CONFLICT (run_id)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        started_at = EXCLUDED.started_at,
                        completed_at = NULL;
                    """,
                    (
                        run_id,
                        "RUNNING",
                        started_at,
                    ),
                )

            connection.commit()

    def complete_run(
        self,
        run_id: str,
        completed_at: datetime,
    ) -> None:
        self._update_status(
            run_id=run_id,
            status="COMPLETED",
            completed_at=completed_at,
        )

    def fail_run(
        self,
        run_id: str,
        completed_at: datetime,
    ) -> None:
        self._update_status(
            run_id=run_id,
            status="FAILED",
            completed_at=completed_at,
        )

    @staticmethod
    def _update_status(
        run_id: str,
        status: str,
        completed_at: datetime,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = %s,
                        completed_at = %s
                    WHERE run_id = %s;
                    """,
                    (
                        status,
                        completed_at,
                        run_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Unable to update pipeline run: "
                        f"{run_id}"
                    )

            connection.commit()