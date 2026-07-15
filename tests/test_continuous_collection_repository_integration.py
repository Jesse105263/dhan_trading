import os
import unittest
from datetime import datetime, timedelta

from services.continuous_collection_models import CoverageExpectation, ProviderBatch, RetryPolicy
from services.continuous_collection_provider import LocalFixtureCollectionProvider
from services.continuous_collection_repository import ContinuousCollectionRepository
from services.continuous_collection_service import ContinuousCollectionService
from services.database import get_connection
from services.historical_data_models import HistoricalDataSource
from services.historical_data_repository import HistoricalDataRepository
from services.historical_data_service import HistoricalDataService
from tests.test_historical_data_foundation import fixture, envelope, policy


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS") == "1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class ContinuousCollectionRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,7,15,16,0); self.repository=ContinuousCollectionRepository()
        payload=envelope(fixture(),"v32-collection").payload
        provider=LocalFixtureCollectionProvider({"*":ProviderBatch(payload,"application/json","fixture-v1",self.now,self.now,("TESTCO",))})
        self.source=HistoricalDataSource("V32_TEST","LOCAL","CONTINUOUS_COLLECTION","LOCAL_FIXTURE","integration-test")
        self.service=ContinuousCollectionService(self.repository,HistoricalDataService(HistoricalDataRepository(),clock=lambda:self.now),{"V32_TEST_PROVIDER":provider},clock=lambda:self.now)

    def tearDown(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM continuous_reconciliation_results WHERE work_id IN (SELECT work_id FROM continuous_collection_work_items WHERE provider_code='V32_TEST_PROVIDER')")
                cursor.execute("DELETE FROM continuous_data_quality_incidents WHERE work_id IN (SELECT work_id FROM continuous_collection_work_items WHERE provider_code='V32_TEST_PROVIDER')")
                cursor.execute("ALTER TABLE continuous_collection_attempts DISABLE TRIGGER continuous_attempt_immutable")
                cursor.execute("DELETE FROM continuous_collection_attempts WHERE work_id IN (SELECT work_id FROM continuous_collection_work_items WHERE provider_code='V32_TEST_PROVIDER')")
                cursor.execute("ALTER TABLE continuous_collection_attempts ENABLE TRIGGER continuous_attempt_immutable")
                cursor.execute("UPDATE continuous_repair_jobs SET work_id=NULL WHERE gap_id IN (SELECT gap_id FROM continuous_coverage_gaps WHERE provider_code='V32_TEST_PROVIDER')")
                cursor.execute("DELETE FROM continuous_collection_work_items WHERE provider_code='V32_TEST_PROVIDER'")
                cursor.execute("DELETE FROM continuous_repair_jobs WHERE gap_id IN (SELECT gap_id FROM continuous_coverage_gaps WHERE provider_code='V32_TEST_PROVIDER')")
                cursor.execute("DELETE FROM continuous_coverage_gaps WHERE provider_code='V32_TEST_PROVIDER'")
                cursor.execute("DELETE FROM continuous_provider_quota_state WHERE provider_code='V32_TEST_PROVIDER'")
                cursor.execute("SELECT source_id FROM historical_data_sources WHERE provider_code='V32_TEST'"); row=cursor.fetchone()
                if row:
                    sid=row[0]
                    cursor.execute("DELETE FROM historical_quality_incidents WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,))
                    cursor.execute("DELETE FROM corporate_action_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,))
                    cursor.execute("DELETE FROM historical_bar_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,))
                    cursor.execute("DELETE FROM source_instrument_mappings WHERE source_id=%s",(sid,))
                    cursor.execute("DELETE FROM canonical_instrument_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,))
                    cursor.execute("DELETE FROM canonical_instruments WHERE identity_key LIKE 'NSE|%%|TESTCO%%'")
                    cursor.execute("DELETE FROM historical_raw_manifests WHERE source_id=%s",(sid,)); cursor.execute("DELETE FROM historical_raw_payloads WHERE source_id=%s",(sid,))
                    cursor.execute("DELETE FROM historical_retention_policies WHERE source_id=%s",(sid,)); cursor.execute("DELETE FROM historical_data_sources WHERE source_id=%s",(sid,))
            connection.commit()

    def work(self):
        return self.service.make_work(provider_code="V32_TEST_PROVIDER",dataset_type="OPTION_CONTRACT_BARS",scope=("TESTCO",),requested_start=self.now,requested_end=self.now,resolution="1D",session="POST_CLOSE",retry_policy=RetryPolicy(max_attempts=2,initial_delay_seconds=0))

    def test_persistence_attempt_lineage_idempotency_and_metrics(self):
        work=self.work(); self.assertTrue(self.service.schedule(work)); self.assertFalse(self.service.schedule(work))
        result=self.service.execute_pending(owner="integration",limit=1,source=self.source,policy=policy())
        self.assertEqual(result.completed,1)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT status,attempt_count FROM continuous_collection_work_items WHERE work_id=%s",(work.work_id,)); self.assertEqual(cursor.fetchone(),("COMPLETED",1))
                cursor.execute("SELECT payload_manifest_id,succeeded_scope FROM continuous_collection_attempts WHERE work_id=%s",(work.work_id,)); attempt=cursor.fetchone()
                self.assertIsNotNone(attempt[0]); self.assertEqual(attempt[1],["TESTCO"])
                cursor.execute("SELECT COUNT(*) FROM historical_bar_revisions WHERE instrument_id=%s",(fixture()["instruments"][1]["instrument_id"],)); self.assertEqual(cursor.fetchone()[0],1)
        health=self.service.health().metrics; self.assertGreaterEqual(health["completed_jobs"],1)

    def test_gap_and_repair_are_idempotent(self):
        base=fixture()["instruments"][1]["instrument_id"]
        foundation=HistoricalDataService(HistoricalDataRepository(),clock=lambda:self.now)
        foundation.import_payload(self.source,policy(),envelope(fixture(),"v32-gap-base"),LocalFixtureCollectionProviderAdapter())
        expected=datetime(2026,7,14,4,0)
        request=CoverageExpectation("V32_TEST_PROVIDER","OPTION_CONTRACT_BARS",__import__('uuid').UUID(base),expected.date(),"1D",(expected,))
        self.assertEqual(len(self.service.detect_gaps(request)),1); self.assertEqual(self.service.detect_gaps(request),())
        self.assertEqual(self.service.schedule_repairs(),1); self.assertEqual(self.service.schedule_repairs(),0)


from services.historical_data_provider import LocalJsonHistoricalDataAdapter as LocalFixtureCollectionProviderAdapter

if __name__ == "__main__": unittest.main()
