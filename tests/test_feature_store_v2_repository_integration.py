import json
import os
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from services.database import get_connection
from services.feature_store_v2_repository import FeatureStoreV2Repository
from services.feature_store_v2_service import FeatureStoreV2Service
from services.historical_data_models import HistoricalDataSource, RawPayloadEnvelope
from services.historical_data_provider import LocalJsonHistoricalDataAdapter
from services.historical_data_repository import HistoricalDataRepository
from services.historical_data_service import HistoricalDataService
from tests.test_historical_data_foundation import policy


INSTRUMENT = UUID("a4444444-4444-4444-8444-444444444444")


def payload(*, revised_close=None, revised_available=None):
    bars = []
    for index in range(6):
        opened = datetime(2026, 7, 15, 9, 15) + timedelta(minutes=15 * index)
        close = str(100 + index)
        available = opened + timedelta(minutes=16)
        if revised_close is not None and index == 5:
            close = revised_close
            available = datetime.fromisoformat(revised_available)
        bars.append({
            "instrument_id": str(INSTRUMENT), "interval_code": "15M",
            "bar_open_at": opened.isoformat(), "bar_close_at": (opened + timedelta(minutes=15)).isoformat(),
            "session_date": "2026-07-15", "adjustment_state": "RAW", "open_price": close,
            "high_price": str(Decimal(close) + 2), "low_price": str(Decimal(close) - 2), "close_price": close,
            "volume": str(1000 + index * 100), "event_at": (opened + timedelta(minutes=15)).isoformat(),
            "available_at": available.isoformat(),
        })
    if revised_close is not None:
        bars = bars[-1:]
    return {
        "instruments": [{"instrument_id": str(INSTRUMENT), "identity_key": "V34|NSE|EQUITY|TEST",
            "instrument_class": "EQUITY", "exchange": "NSE", "segment": "NSE_EQ", "trading_symbol": "V34TEST",
            "valid_from": "2026-01-01T00:00:00", "available_at": "2026-01-01T00:00:00"}],
        "mappings": [], "bars": bars, "corporate_actions": [],
    }


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS") == "1", "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class FeatureStoreV2RepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.source = HistoricalDataSource("V34_TEST", "LOCAL", "FEATURE_STORE_V2", "LOCAL_FIXTURE", "integration")
        self.foundation = HistoricalDataService(HistoricalDataRepository(), clock=lambda: datetime(2026, 7, 16))
        self._import(payload(), "base")

    def _import(self, data, batch):
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        envelope = RawPayloadEnvelope(batch, "fixture-v1", "application/json", raw, datetime(2026, 7, 16), datetime(2026, 7, 16))
        return self.foundation.import_payload(self.source, policy(), envelope, LocalJsonHistoricalDataAdapter())

    def tearDown(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE feature_values_v2 DISABLE TRIGGER feature_values_v2_immutable")
                cursor.execute("ALTER TABLE feature_vectors_v2 DISABLE TRIGGER feature_vectors_v2_immutable")
                cursor.execute("DELETE FROM feature_values_v2 WHERE vector_id IN (SELECT vector_id FROM feature_vectors_v2 WHERE instrument_id=%s)", (INSTRUMENT,))
                cursor.execute("DELETE FROM feature_vectors_v2 WHERE instrument_id=%s", (INSTRUMENT,))
                cursor.execute("ALTER TABLE feature_vectors_v2 ENABLE TRIGGER feature_vectors_v2_immutable")
                cursor.execute("ALTER TABLE feature_values_v2 ENABLE TRIGGER feature_values_v2_immutable")
                cursor.execute("DELETE FROM feature_materialization_runs_v2 WHERE schema_version='canonical-market-features-v2'")
                cursor.execute("DELETE FROM feature_definitions_v2 WHERE schema_version='canonical-market-features-v2'")
                cursor.execute("DELETE FROM feature_schema_versions_v2 WHERE schema_version='canonical-market-features-v2'")
                cursor.execute("SELECT source_id FROM historical_data_sources WHERE provider_code='V34_TEST'")
                row = cursor.fetchone()
                if row:
                    source_id = row[0]
                    cursor.execute("DELETE FROM historical_bar_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)", (source_id,))
                    cursor.execute("DELETE FROM canonical_instrument_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)", (source_id,))
                    cursor.execute("DELETE FROM canonical_instruments WHERE instrument_id=%s", (INSTRUMENT,))
                    cursor.execute("DELETE FROM historical_raw_manifests WHERE source_id=%s", (source_id,))
                    cursor.execute("DELETE FROM historical_raw_payloads WHERE source_id=%s", (source_id,))
                    cursor.execute("DELETE FROM historical_retention_policies WHERE source_id=%s", (source_id,))
                    cursor.execute("DELETE FROM historical_data_sources WHERE source_id=%s", (source_id,))
            connection.commit()

    def test_persistence_lineage_idempotency_and_no_future_leakage(self):
        service = FeatureStoreV2Service(FeatureStoreV2Repository(), clock=lambda: datetime(2026, 7, 16))
        first = service.materialize(as_of=datetime(2026, 7, 15, 11))
        second = service.materialize(as_of=datetime(2026, 7, 15, 11))
        self.assertEqual(first.run_id, second.run_id)
        self.assertEqual(first.vector_count, 6)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*),COUNT(DISTINCT anchor_bar_revision_id),COUNT(DISTINCT lineage_checksum) FROM feature_vectors_v2 WHERE instrument_id=%s", (INSTRUMENT,))
                self.assertEqual(cursor.fetchone(), (6, 6, 6))
                cursor.execute("SELECT v.observed_at,x.source_revision_ids FROM feature_values_v2 x JOIN feature_vectors_v2 v USING(vector_id) WHERE v.instrument_id=%s AND x.feature_name='return_3_bar_pct' ORDER BY v.observed_at", (INSTRUMENT,))
                rows = cursor.fetchall()
                self.assertEqual(len(rows[0][1]), 1)
                self.assertEqual(len(rows[-1][1]), 4)
                source_ids = rows[-1][1]
                cursor.execute("SELECT COUNT(*) FROM historical_bar_revisions WHERE bar_revision_id=ANY(%s::uuid[]) AND bar_close_at>%s", (source_ids, rows[-1][0]))
                self.assertEqual(cursor.fetchone()[0], 0)

    def test_revision_selection_is_bounded_by_as_of(self):
        self._import(payload(revised_close="150", revised_available="2026-07-16T09:30:00"), "late")
        repository = FeatureStoreV2Repository()
        old = repository.anchors(datetime(2026, 7, 15, 11), 20)
        current = repository.anchors(datetime(2026, 7, 17), 20)
        old_last = [item for item in old if item.instrument_id == INSTRUMENT][-1]
        current_last = [item for item in current if item.instrument_id == INSTRUMENT][-1]
        self.assertEqual(old_last.close_price, Decimal("105"))
        self.assertEqual(current_last.close_price, Decimal("150"))
        self.assertNotEqual(old_last.bar_revision_id, current_last.bar_revision_id)


if __name__ == "__main__":
    unittest.main()
