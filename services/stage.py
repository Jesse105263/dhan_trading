import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


class Stage(ABC):
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    def execute(
        self,
        context: dict[str, Any],
    ) -> None:
        started_at = datetime.now()

        context["current_stage"] = self.name
        context["current_stage_started_at"] = (
            started_at
        )

        logger.info(
            "Stage started | stage=%s",
            self.name,
        )

        try:
            self.run(context)
        except Exception:
            context["failed_stage"] = self.name

            logger.exception(
                "Stage failed | stage=%s",
                self.name,
            )

            raise

        finished_at = datetime.now()
        duration = finished_at - started_at

        context["last_completed_stage"] = (
            self.name
        )
        context["current_stage"] = None
        context["current_stage_finished_at"] = (
            finished_at
        )

        logger.info(
            "Stage completed | stage=%s | "
            "duration=%s",
            self.name,
            duration,
        )

    @abstractmethod
    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        raise NotImplementedError