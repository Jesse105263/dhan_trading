from typing import Any

from services.database_stage import DatabaseStage
from services.pipeline import Pipeline
from services.stage import Stage


class CollectorStage(Stage):
    def __init__(self) -> None:
        super().__init__("Collector")

    def run(self, context: dict[str, Any]) -> None:
        context["collector_complete"] = True


class SnapshotStage(Stage):
    def __init__(self) -> None:
        super().__init__("Snapshot Engine")

    def run(self, context: dict[str, Any]) -> None:
        context["snapshot_complete"] = True


class FeatureStage(Stage):
    def __init__(self) -> None:
        super().__init__("Feature Engine")

    def run(self, context: dict[str, Any]) -> None:
        context["feature_complete"] = True


class RankingStage(Stage):
    def __init__(self) -> None:
        super().__init__("Ranking Engine")

    def run(self, context: dict[str, Any]) -> None:
        context["ranking_complete"] = True


class RiskStage(Stage):
    def __init__(self) -> None:
        super().__init__("Risk Engine")

    def run(self, context: dict[str, Any]) -> None:
        context["risk_complete"] = True


class SignalStage(Stage):
    def __init__(self) -> None:
        super().__init__("Signal Engine")

    def run(self, context: dict[str, Any]) -> None:
        context["signal_complete"] = True


def main() -> None:
    pipeline = Pipeline(
        stages=[
            CollectorStage(),
            SnapshotStage(),
            FeatureStage(),
            RankingStage(),
            RiskStage(),
            SignalStage(),
            DatabaseStage(),
        ]
    )

    pipeline.start()


if __name__ == "__main__":
    main()