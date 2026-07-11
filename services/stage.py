from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class Stage(ABC):
    def __init__(self, name: str):
        self.name = name

    def execute(self, context: dict[str, Any]) -> None:
        started_at = datetime.now()

        print(f"[START] {self.name}")

        self.run(context)

        finished_at = datetime.now()
        duration = finished_at - started_at

        print(f"[DONE]  {self.name} ({duration})")

    @abstractmethod
    def run(self, context: dict[str, Any]) -> None:
        raise NotImplementedError