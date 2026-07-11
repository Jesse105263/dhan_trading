from datetime import datetime
from typing import Any
from uuid import uuid4

from services.stage import Stage


class Pipeline:
    def __init__(self, stages: list[Stage]):
        self.stages = stages
        self.context: dict[str, Any] = {}
        self.started_at: datetime | None = None

    def start(self) -> None:
        self.started_at = datetime.now()

        self.context["run_id"] = str(uuid4())
        self.context["pipeline_started_at"] = self.started_at

        print("=" * 60)
        print("DHAN TRADING PLATFORM")
        print("=" * 60)
        print(f"Run ID: {self.context['run_id']}")
        print(f"Started: {self.started_at}")
        print()

        try:
            for stage in self.stages:
                stage.execute(self.context)
        except Exception:
            self.context["pipeline_status"] = "FAILED"
            raise
        else:
            self.context["pipeline_status"] = "COMPLETED"
        finally:
            self.finish()

    def finish(self) -> None:
        if self.started_at is None:
            raise RuntimeError("Pipeline was not started.")

        finished_at = datetime.now()
        duration = finished_at - self.started_at

        self.context["pipeline_finished_at"] = finished_at
        self.context["pipeline_duration"] = duration

        print()
        print("=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"Run ID: {self.context['run_id']}")
        print(
            "Status: "
            f"{self.context.get('pipeline_status', 'UNKNOWN')}"
        )
        print(f"Finished: {finished_at}")
        print(f"Duration: {duration}")