import json, os, unittest
from datetime import datetime, timedelta
from uuid import UUID

from services.database import get_connection
from services.feature_store_v2_service import FeatureStoreV2Service
from services.historical_data_models import HistoricalDataSource, RawPayloadEnvelope
from services.historical_data_provider import LocalJsonHistoricalDataAdapter
from services.historical_data_repository import HistoricalDataRepository
from services.historical_data_service import HistoricalDataService
from services.similarity_v2_models import SimilarityPolicyV2
from services.similarity_v2_repository import SimilarityV2Repository
from services.similarity_v2_service import SimilarityV2Service
from tests.test_historical_data_foundation import policy as retention_policy


INSTRUMENT=UUID("a5555555-5555-4555-8555-555555555555")


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class SimilarityV2RepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        source=HistoricalDataSource("V35_TEST","LOCAL","SIMILARITY_V2","LOCAL_FIXTURE","integration")
        bars=[]
        for index in range(7):
            opened=datetime(2026,7,8+index,9,15); close=str(100+index)
            bars.append({"instrument_id":str(INSTRUMENT),"interval_code":"1D","bar_open_at":opened.isoformat(),
                "bar_close_at":(opened+timedelta(hours=6)).isoformat(),"session_date":opened.date().isoformat(),"adjustment_state":"RAW",
                "open_price":close,"high_price":str(102+index),"low_price":str(98+index),"close_price":close,"volume":str(1000+index*100),
                "event_at":(opened+timedelta(hours=6)).isoformat(),"available_at":(opened+timedelta(hours=7)).isoformat()})
        data={"instruments":[{"instrument_id":str(INSTRUMENT),"identity_key":"V35|NSE|EQUITY|TEST","instrument_class":"EQUITY",
            "exchange":"NSE","segment":"NSE_EQ","trading_symbol":"V35TEST","valid_from":"2026-01-01T00:00:00","available_at":"2026-01-01T00:00:00"}],
            "mappings":[],"bars":bars,"corporate_actions":[]}
        raw=json.dumps(data,sort_keys=True,separators=(",",":")).encode()
        HistoricalDataService(HistoricalDataRepository(),clock=lambda:datetime(2026,7,16)).import_payload(source,retention_policy(),
            RawPayloadEnvelope("v35", "fixture-v1","application/json",raw,datetime(2026,7,16),datetime(2026,7,16)),LocalJsonHistoricalDataAdapter())
        FeatureStoreV2Service(clock=lambda:datetime(2026,7,16)).materialize(as_of=datetime(2026,7,16))

    def tearDown(self):
        with get_connection() as c:
            with c.cursor() as q:
                q.execute("ALTER TABLE similarity_matches_v2 DISABLE TRIGGER similarity_matches_v2_immutable"); q.execute("ALTER TABLE similarity_runs_v2 DISABLE TRIGGER similarity_runs_v2_immutable")
                q.execute("DELETE FROM similarity_matches_v2 WHERE run_id IN (SELECT run_id FROM similarity_runs_v2 WHERE model_version LIKE 'v35-test%')")
                q.execute("DELETE FROM similarity_runs_v2 WHERE model_version LIKE 'v35-test%'"); q.execute("DELETE FROM similarity_models_v2 WHERE model_version LIKE 'v35-test%'")
                q.execute("ALTER TABLE similarity_runs_v2 ENABLE TRIGGER similarity_runs_v2_immutable"); q.execute("ALTER TABLE similarity_matches_v2 ENABLE TRIGGER similarity_matches_v2_immutable")
                q.execute("ALTER TABLE feature_values_v2 DISABLE TRIGGER feature_values_v2_immutable"); q.execute("ALTER TABLE feature_vectors_v2 DISABLE TRIGGER feature_vectors_v2_immutable")
                q.execute("DELETE FROM feature_values_v2 WHERE vector_id IN (SELECT vector_id FROM feature_vectors_v2 WHERE instrument_id=%s)",(INSTRUMENT,)); q.execute("DELETE FROM feature_vectors_v2 WHERE instrument_id=%s",(INSTRUMENT,))
                q.execute("ALTER TABLE feature_vectors_v2 ENABLE TRIGGER feature_vectors_v2_immutable"); q.execute("ALTER TABLE feature_values_v2 ENABLE TRIGGER feature_values_v2_immutable")
                q.execute("SELECT source_id FROM historical_data_sources WHERE provider_code='V35_TEST'"); row=q.fetchone()
                if row:
                    sid=row[0]; q.execute("DELETE FROM historical_bar_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,)); q.execute("DELETE FROM canonical_instrument_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,)); q.execute("DELETE FROM canonical_instruments WHERE instrument_id=%s",(INSTRUMENT,)); q.execute("DELETE FROM historical_raw_manifests WHERE source_id=%s",(sid,)); q.execute("DELETE FROM historical_raw_payloads WHERE source_id=%s",(sid,)); q.execute("DELETE FROM historical_retention_policies WHERE source_id=%s",(sid,)); q.execute("DELETE FROM historical_data_sources WHERE source_id=%s",(sid,))
            c.commit()

    def test_idempotent_persistence_exact_lineage_and_temporal_cutoff(self):
        repository=SimilarityV2Repository(); vectors=repository._dicts("SELECT vector_id,observed_at FROM feature_vectors_v2 WHERE instrument_id=%s ORDER BY observed_at",(INSTRUMENT,))
        query=vectors[-1]; policy=SimilarityPolicyV2("v35-test-manhattan",minimum_candidates=3,minimum_shared_features=3)
        service=SimilarityV2Service(repository,clock=lambda:datetime(2026,7,16)); first=service.materialize(query["vector_id"],policy); second=service.materialize(query["vector_id"],policy)
        self.assertEqual(first.run_id,second.run_id); self.assertEqual(first.evidence_state,"SUFFICIENT")
        with get_connection() as c:
            with c.cursor() as q:
                q.execute("SELECT COUNT(*),COUNT(DISTINCT matched_vector_id),MIN(lineage_checksum) FROM similarity_matches_v2 WHERE run_id=%s",(first.run_id,)); count,distinct_count,checksum=q.fetchone(); self.assertEqual(count,distinct_count); self.assertEqual(len(checksum),64)
                q.execute("SELECT COUNT(*) FROM similarity_matches_v2 m JOIN feature_vectors_v2 v ON v.vector_id=m.matched_vector_id JOIN similarity_runs_v2 r ON r.run_id=m.run_id WHERE m.run_id=%s AND (v.observed_at>=r.cutoff_at OR v.available_at>r.cutoff_at)",(first.run_id,)); self.assertEqual(q.fetchone()[0],0)


if __name__=="__main__": unittest.main()
