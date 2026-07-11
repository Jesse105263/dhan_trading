import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from services.error_sanitizer import (
    classify_retryable,
    sanitize_error_message,
)
from services.failure_repository import (
    FailureRepository,
    PipelineFailure,
)
from services.metrics_repository import (
    MetricsRepository,
    StageMetric,
)
from services.pipeline_run_repository import (
    PipelineRunRepository,
)
from services.stage import Stage


logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        stages: list[Stage],
        run_repository: PipelineRunRepository | None = None,
        failure_repository: FailureRepository | None = None,
        metrics_repository: MetricsRepository | None = None,
    ) -> None:
        self.stages = stages
        self.context: dict[str, Any] = {}
        self.started_at: datetime | None = None

        self.run_repository = (
            run_repository
            or PipelineRunRepository()
        )

        self.failure_repository = (
            failure_repository
            or FailureRepository()
        )

        self.metrics_repository = (
            metrics_repository
            or MetricsRepository()
        )

    def start(self) -> None:
        self.started_at = datetime.now()
        run_id = str(uuid4())

        self.context["run_id"] = run_id
        self.context["pipeline_started_at"] = self.started_at
        self.context["pipeline_status"] = "RUNNING"

        self.run_repository.start_run(
            run_id=run_id,
            started_at=self.started_at,
        )

        logger.info(
            "Pipeline started | run_id=%s",
            run_id,
        )

        try:
            for stage in self.stages:
                self._execute_stage(
                    stage=stage,
                    run_id=run_id,
                )

        except Exception as error:
            failed_at = datetime.now()
            failed_stage = str(
                self.context.get(
                    "failed_stage",
                    self.context.get(
                        "current_stage",
                        "UNKNOWN",
                    ),
                )
            )

            sanitized_message = sanitize_error_message(
                str(error)
            )

            failure = PipelineFailure(
                run_id=run_id,
                stage_name=failed_stage,
                error_type=type(error).__name__,
                error_message=sanitized_message,
                retryable=classify_retryable(error),
                occurred_at=failed_at,
                symbol=self._extract_symbol(),
            )

            try:
                failure_id = (
                    self.failure_repository
                    .insert(failure)
                )
                self.context["failure_id"] = failure_id
            except Exception:
                logger.exception(
                    "Unable to persist pipeline failure "
                    "| run_id=%s",
                    run_id,
                )

            self.context["pipeline_status"] = "FAILED"
            self.context["pipeline_finished_at"] = failed_at

            self.run_repository.fail_run(
                run_id=run_id,
                completed_at=failed_at,
            )

            logger.exception(
                "Pipeline failed | run_id=%s | stage=%s",
                run_id,
                failed_stage,
            )

            raise

        else:
            completed_at = datetime.now()

            self.context["pipeline_status"] = "COMPLETED"
            self.context["pipeline_finished_at"] = completed_at

            self.run_repository.complete_run(
                run_id=run_id,
                completed_at=completed_at,
            )

            logger.info(
                "Pipeline completed | run_id=%s",
                run_id,
            )

        finally:
            self.finish()

    def _execute_stage(
        self,
        stage: Stage,
        run_id: str,
    ) -> None:
        started_at = datetime.now()

        try:
            stage.execute(self.context)
        except Exception:
            completed_at = datetime.now()

            self._persist_stage_metric(
                run_id=run_id,
                stage_name=stage.name,
                status="FAILED",
                started_at=started_at,
                completed_at=completed_at,
            )

            raise

        completed_at = datetime.now()

        self._persist_stage_metric(
            run_id=run_id,
            stage_name=stage.name,
            status="COMPLETED",
            started_at=started_at,
            completed_at=completed_at,
        )

    def _persist_stage_metric(
        self,
        run_id: str,
        stage_name: str,
        status: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> None:
        metric_data = self.context.get(
            "stage_metric_data",
            {},
        )

        source_timestamp = metric_data.get(
            "source_timestamp"
        )

        freshness_seconds = None

        if isinstance(source_timestamp, datetime):
            freshness_seconds = max(
                0.0,
                (
                    completed_at
                    - source_timestamp
                ).total_seconds(),
            )

        duration_ms = int(
            (
                completed_at
                - started_at
            ).total_seconds()
            * 1000
        )

        metric = StageMetric(
            run_id=run_id,
            stage_name=stage_name,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            records_requested=self._safe_int(
                metric_data.get(
                    "records_requested"
                )
            ),
            records_received=self._safe_int(
                metric_data.get(
                    "records_received"
                )
            ),
            records_written=self._safe_int(
                metric_data.get(
                    "records_written"
                )
            ),
            source_timestamp=source_timestamp,
            data_freshness_seconds=(
                freshness_seconds
            ),
        )

        try:
            self.metrics_repository.insert(
                metric
            )
        except Exception:
            logger.exception(
                "Unable to persist stage metric "
                "| run_id=%s | stage=%s",
                run_id,
                stage_name,
            )

    def finish(self) -> None:
        if self.started_at is None:
            raise RuntimeError(
                "Pipeline was not started."
            )

        finished_at = self.context.get(
            "pipeline_finished_at",
            datetime.now(),
        )

        duration = finished_at - self.started_at

        self.context["pipeline_duration"] = duration

        logger.info(
            "Pipeline summary | run_id=%s | "
            "status=%s | duration=%s",
            self.context.get("run_id"),
            self.context.get(
                "pipeline_status",
                "UNKNOWN",
            ),
            duration,
        )

    def _extract_symbol(
        self,
    ) -> str | None:
        symbol = self.context.get(
            "current_symbol"
        )

        if symbol is None:
            return None

        cleaned = str(symbol).strip().upper()

        return cleaned or None

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None