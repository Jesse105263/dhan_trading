from typing import Any

from app.logging_config import configure_logging
from services.collector import CollectorStage
from services.database_stage import DatabaseStage
from services.feature_engine import FeatureStage
from services.pipeline import Pipeline
from services.snapshot_engine import SnapshotStage
from services.stage import Stage


class RankingStage(Stage):
    def __init__(self) -> None:
        super().__init__("Ranking Engine")

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        context["ranking_complete"] = True


class RiskStage(Stage):
    def __init__(self) -> None:
        super().__init__("Risk Engine")

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        context["risk_complete"] = True


class SignalStage(Stage):
    def __init__(self) -> None:
        super().__init__("Signal Engine")

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        context["signal_complete"] = True


def main() -> None:
    configure_logging()

    pipeline = Pipeline(
        stages=[
            DatabaseStage(),
            CollectorStage(),
            SnapshotStage(),
            FeatureStage(),
            RankingStage(),
            RiskStage(),
            SignalStage(),
        ]
    )

    pipeline.start()


if __name__ == "__main__":
    main()