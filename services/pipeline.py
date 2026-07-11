from datetime import datetime
from typing import Any

from services.stage import Stage


class Pipeline:
    def __init__(self, stages: list[Stage]):
        self.stages = stages
        self.context: dict[str, Any] = {}
        self.started_at: datetime | None = None

    def start(self) -> None:
        self.started_at = datetime.now()

        print("=" * 60)
        print("DHAN TRADING PLATFORM")
        print("=" * 60)
        print(f"Started: {self.started_at}")
        print()

        for stage in self.stages:
            stage.execute(self.context)

        self.finish()

    def finish(self) -> None:
        if self.started_at is None:
            raise RuntimeError("Pipeline was not started.")

        finished_at = datetime.now()
        duration = finished_at - self.started_at

        print()
        print("=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"Finished: {finished_at}")
        print(f"Duration: {duration}")