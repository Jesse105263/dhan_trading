import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from services.pipeline_run_repository import (
    PipelineRunRepository,
)
from services.stage import Stage


logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        stages: list[Stage],
        run_repository: (
            PipelineRunRepository | None
        ) = None,
    ):
        self.stages = stages
        self.context: dict[str, Any] = {}
        self.started_at: datetime | None = None
        self.run_repository = (
            run_repository
            or PipelineRunRepository()
        )

    def start(self) -> None:
        self.started_at = datetime.now()

        run_id = str(uuid4())

        self.context["run_id"] = run_id
        self.context["pipeline_started_at"] = (
            self.started_at
        )
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
                stage.execute(self.context)
        except Exception:
            failed_at = datetime.now()

            self.context["pipeline_status"] = "FAILED"
            self.context["pipeline_finished_at"] = (
                failed_at
            )

            self.run_repository.fail_run(
                run_id=run_id,
                completed_at=failed_at,
            )

            logger.exception(
                "Pipeline failed | run_id=%s",
                run_id,
            )

            raise
        else:
            completed_at = datetime.now()

            self.context["pipeline_status"] = (
                "COMPLETED"
            )
            self.context["pipeline_finished_at"] = (
                completed_at
            )

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