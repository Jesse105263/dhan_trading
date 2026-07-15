import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from services.feature_store_v2_models import FeatureAnchorV2, FeatureDefinitionV2, FeatureSchemaV2
from services.feature_store_v2_service import FeatureStoreV2Service


class FakeRepository:
    def __init__(self, anchors, histories):
        self._anchors = anchors
        self._histories = histories
        self.saved = []

    def anchors(self, as_of, limit, after_at=None, after_id=None):
        rows = [item for item in self._anchors if item.available_at <= as_of]
        if after_at is not None:
            rows = [item for item in rows if (item.available_at, item.bar_revision_id) > (after_at, after_id)]
        return rows[:limit]

    def history(self, anchor):
        rows = self._histories[anchor.bar_revision_id]
        assert all(item.bar_close_at <= anchor.bar_close_at for item in rows)
        assert all(item.available_at <= anchor.available_at for item in rows)
        return rows

    def persist(self, prepared):
        self.saved.append(prepared)


def make_bar(index, *, instrument_class="EQUITY", expiry=None, volume=True, open_interest=False):
    opened = datetime(2026, 7, 15, 9, 15) + timedelta(minutes=15 * index)
    close = Decimal(100 + index)
    return FeatureAnchorV2(
        UUID(int=1000 + index), UUID(int=2000 + index), UUID(int=3000), instrument_class,
        UUID(int=3001) if instrument_class in {"OPTION", "FUTURE"} else None, "15m", opened.date(), opened,
        opened + timedelta(minutes=15), opened + timedelta(minutes=16), expiry, close - 1, close + 2,
        close - 2, close, Decimal(1000 + index * 100) if volume else None,
        Decimal(500 + index * 10) if open_interest else None, None, None,
    )


class FeatureStoreV2Tests(unittest.TestCase):
    def test_materializes_multiple_families_with_deterministic_lineage(self):
        bars = [make_bar(index) for index in range(6)]
        repository = FakeRepository([bars[-1]], {bars[-1].bar_revision_id: bars})
        service = FeatureStoreV2Service(repository, clock=lambda: datetime(2026, 7, 16))

        first = service.materialize(as_of=datetime(2026, 7, 16), batch_size=2)
        second = service.materialize(as_of=datetime(2026, 7, 16), batch_size=2)

        self.assertEqual(first.run_id, second.run_id)
        self.assertEqual(first.vector_count, 1)
        prepared = repository.saved[0]
        vector, values = prepared["vectors"][0]
        by_name = {item["feature_name"]: item for item in values}
        self.assertEqual(vector["feature_count"], 17)
        self.assertEqual(set(vector["quality_metrics"]["family_coverage"]),
                         {"price", "returns", "volatility", "volume", "derivatives", "liquidity", "temporal", "regime"})
        self.assertEqual(by_name["return_1_bar_pct"]["source_revision_ids"], [str(bars[-2].bar_revision_id), str(bars[-1].bar_revision_id)])
        self.assertIsNotNone(by_name["realized_volatility_5"]["numeric_value"])
        self.assertEqual(by_name["open_interest"]["missing_reason"], "NOT_APPLICABLE_FOR_INSTRUMENT")
        self.assertEqual(prepared["compatible_schema_versions"], ["option-observation-v1"])
        self.assertEqual(prepared["compatible_outcome_models"], ["canonical-path-outcome-v2"])

    def test_sparse_history_preserves_missing_values(self):
        bar = make_bar(0, volume=False)
        repository = FakeRepository([bar], {bar.bar_revision_id: [bar]})
        result = FeatureStoreV2Service(repository, clock=lambda: datetime(2026, 7, 16)).materialize(
            as_of=datetime(2026, 7, 16)
        )
        vector, values = repository.saved[0]["vectors"][0]
        by_name = {item["feature_name"]: item for item in values}
        self.assertEqual(result.partial_count, 1)
        self.assertEqual(vector["quality_state"], "PARTIAL")
        self.assertIsNone(by_name["volume"]["numeric_value"])
        self.assertEqual(by_name["return_3_bar_pct"]["missing_reason"], "INSUFFICIENT_HISTORY")

    def test_derivative_metadata_and_subject_type_are_point_in_time(self):
        expiry = date(2026, 7, 30)
        bars = [make_bar(index, instrument_class="OPTION", expiry=expiry, open_interest=True) for index in range(2)]
        repository = FakeRepository([bars[-1]], {bars[-1].bar_revision_id: bars})
        FeatureStoreV2Service(repository, clock=lambda: datetime(2026, 7, 16)).materialize(as_of=datetime(2026, 7, 16))
        vector, values = repository.saved[0]["vectors"][0]
        by_name = {item["feature_name"]: item for item in values}
        self.assertEqual(vector["subject_type"], "OPTION")
        self.assertEqual(by_name["days_to_expiry"]["numeric_value"], Decimal(15))
        self.assertIsNotNone(by_name["open_interest_change_1_pct"]["numeric_value"])

    def test_definition_policies_and_versions_are_validated(self):
        with self.assertRaises(ValueError):
            FeatureDefinitionV2("x", "family", "formula", "ZERO_FILL", "NONE", 1, "bad")
        definition = FeatureDefinitionV2("x", "family", "formula", "REQUIRED", "NONE", 1, "ok")
        with self.assertRaises(ValueError):
            FeatureSchemaV2("v", (definition, definition))
        self.assertEqual(FeatureStoreV2Service.DEFAULT_SCHEMA.schema_version, "canonical-market-features-v2")


if __name__ == "__main__":
    unittest.main()
