from datetime import datetime
from typing import Any

from services.feature_repository import (
    FeatureInput,
    FeatureRepository,
    MarketFeature,
)
from services.stage import Stage


LOOKBACK_RUNS = 20


class FeatureStage(Stage):
    def __init__(
        self,
        repository: FeatureRepository | None = None,
    ) -> None:
        super().__init__("Feature Engine")

        self.repository = (
            repository
            or FeatureRepository()
        )

    def run(self, context: dict[str, Any]) -> None:
        run_id = context.get("run_id")
        snapshot_count = context.get("snapshot_count")

        if not run_id:
            raise RuntimeError(
                "Pipeline context is missing run_id."
            )

        if snapshot_count is None:
            raise RuntimeError(
                "Pipeline context is missing snapshot_count."
            )

        inputs = self.repository.list_inputs_for_run(
            run_id=run_id,
            lookback_runs=LOOKBACK_RUNS,
        )

        if not inputs:
            raise RuntimeError(
                "No snapshot inputs were found "
                "for feature calculation."
            )

        if len(inputs) != snapshot_count:
            raise RuntimeError(
                "Feature input count does not match "
                "snapshot count. "
                f"Snapshots: {snapshot_count}, "
                f"Feature inputs: {len(inputs)}"
            )

        calculated_at = datetime.now()

        features = [
            self._build_feature(
                run_id=run_id,
                feature_input=feature_input,
                calculated_at=calculated_at,
            )
            for feature_input in inputs
        ]

        upserted_count = self.repository.bulk_upsert(
            features
        )

        persisted_count = self.repository.count_for_run(
            run_id
        )

        if persisted_count != snapshot_count:
            raise RuntimeError(
                "Feature persistence validation failed. "
                f"Expected: {snapshot_count}, "
                f"Persisted: {persisted_count}"
            )

        self.repository.complete_run(
            run_id=run_id,
            feature_count=persisted_count,
            completed_at=datetime.now(),
        )

        features_with_history = sum(
            1
            for feature in features
            if feature.history_count > 0
        )

        features_with_relative_volume = sum(
            1
            for feature in features
            if feature.relative_volume is not None
        )

        context["feature_complete"] = True
        context["feature_count"] = persisted_count
        context["feature_calculated_at"] = (
            calculated_at
        )

        print(f"Feature inputs: {len(inputs)}")
        print(f"Features upserted: {upserted_count}")
        print(f"Features persisted: {persisted_count}")
        print(
            "Features with history: "
            f"{features_with_history}"
        )
        print(
            "Features with relative volume: "
            f"{features_with_relative_volume}"
        )

    @staticmethod
    def _build_feature(
        run_id: str,
        feature_input: FeatureInput,
        calculated_at: datetime,
    ) -> MarketFeature:
        price_change = None
        price_change_pct = None

        if feature_input.previous_spot_price is not None:
            price_change = (
                feature_input.spot_price
                - feature_input.previous_spot_price
            )

            if feature_input.previous_spot_price != 0:
                price_change_pct = (
                    price_change
                    / feature_input.previous_spot_price
                ) * 100

        volume_change = None
        volume_change_pct = None

        if (
            feature_input.volume is not None
            and feature_input.previous_volume is not None
        ):
            volume_change = (
                feature_input.volume
                - feature_input.previous_volume
            )

            if feature_input.previous_volume != 0:
                volume_change_pct = (
                    volume_change
                    / feature_input.previous_volume
                ) * 100

        relative_volume = None

        if (
            feature_input.volume is not None
            and feature_input.average_prior_volume
            is not None
            and feature_input.average_prior_volume > 0
        ):
            relative_volume = (
                feature_input.volume
                / feature_input.average_prior_volume
            )

        return MarketFeature(
            run_id=run_id,
            symbol=feature_input.symbol,
            spot_price=feature_input.spot_price,
            previous_spot_price=(
                feature_input.previous_spot_price
            ),
            price_change=price_change,
            price_change_pct=price_change_pct,
            volume=feature_input.volume,
            previous_volume=(
                feature_input.previous_volume
            ),
            volume_change=volume_change,
            volume_change_pct=volume_change_pct,
            average_prior_volume=(
                feature_input.average_prior_volume
            ),
            relative_volume=relative_volume,
            history_count=feature_input.history_count,
            calculated_at=calculated_at,
        )