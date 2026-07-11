from dataclasses import dataclass
from datetime import datetime

from services.database import get_connection


@dataclass(frozen=True)
class PipelineFailure:
    run_id: str
    stage_name: str
    error_type: str
    error_message: str
    retryable: bool
    occurred_at: datetime
    symbol: str | None = None


class FailureRepository:
    def insert(
        self,
        failure: PipelineFailure,
    ) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pipeline_failures
                    (
                        run_id,
                        stage_name,
                        symbol,
                        error_type,
                        error_message,
                        retryable,
                        occurred_at
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        failure.run_id,
                        failure.stage_name,
                        failure.symbol,
                        failure.error_type,
                        failure.error_message,
                        failure.retryable,
                        failure.occurred_at,
                    ),
                )

                result = cursor.fetchone()

            connection.commit()

        if result is None:
            raise RuntimeError(
                "Failure record was not created."
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
                    FROM pipeline_failures
                    WHERE run_id = %s;
                    """,
                    (run_id,),
                )

                result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                "Unable to count failures for run: "
                f"{run_id}"
            )

        return int(result[0])