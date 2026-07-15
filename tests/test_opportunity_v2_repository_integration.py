import os,unittest
from datetime import datetime
from uuid import UUID
from services.database import get_connection
from services.opportunity_v2_models import OpportunityPolicyV2
from services.opportunity_v2_repository import OpportunityV2Repository
from services.opportunity_v2_service import OpportunityV2Service
from services.similarity_v2_models import SimilarityPolicyV2
from services.similarity_v2_repository import SimilarityV2Repository
from services.similarity_v2_service import SimilarityV2Service
from tests.test_similarity_v2_repository_integration import INSTRUMENT,SimilarityV2RepositoryIntegrationTest

@unittest.skipUnless(os.getenv('RUN_DB_INTEGRATION_TESTS')=='1','Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.')
class OpportunityV2RepositoryIntegrationTest(unittest.TestCase):
 def setUp(self):self.fixture=SimilarityV2RepositoryIntegrationTest('test_idempotent_persistence_exact_lineage_and_temporal_cutoff');self.fixture.setUp()
 def tearDown(self):
  with get_connection() as c:
   with c.cursor() as q:
    q.execute('ALTER TABLE opportunity_evidence_v2 DISABLE TRIGGER opportunity_evidence_v2_immutable');q.execute('ALTER TABLE opportunity_candidates_v2 DISABLE TRIGGER opportunity_candidates_v2_immutable');q.execute('ALTER TABLE opportunity_runs_v2 DISABLE TRIGGER opportunity_runs_v2_immutable')
    q.execute("DELETE FROM opportunity_evidence_v2 WHERE candidate_id IN (SELECT candidate_id FROM opportunity_candidates_v2 WHERE strategy_code='V35_TEST')");q.execute("DELETE FROM opportunity_candidates_v2 WHERE strategy_code='V35_TEST'");q.execute("DELETE FROM opportunity_runs_v2 WHERE policy_version='v35-test-opportunity'");q.execute("DELETE FROM opportunity_policies_v2 WHERE policy_version='v35-test-opportunity'")
    q.execute('ALTER TABLE opportunity_runs_v2 ENABLE TRIGGER opportunity_runs_v2_immutable');q.execute('ALTER TABLE opportunity_candidates_v2 ENABLE TRIGGER opportunity_candidates_v2_immutable');q.execute('ALTER TABLE opportunity_evidence_v2 ENABLE TRIGGER opportunity_evidence_v2_immutable')
   c.commit()
  self.fixture.tearDown()
 def test_idempotent_abstention_persistence_and_exact_lineage(self):
  sr=SimilarityV2Repository();vectors=sr._dicts('SELECT vector_id FROM feature_vectors_v2 WHERE instrument_id=%s ORDER BY observed_at',(INSTRUMENT,));sim=SimilarityV2Service(sr,clock=lambda:datetime(2026,7,16)).materialize(vectors[-1]['vector_id'],SimilarityPolicyV2('v35-test-manhattan',minimum_candidates=3))
  policy=OpportunityPolicyV2('v35-test-opportunity','V35_TEST','LONG_CALL','SESSION','2026-06-30');service=OpportunityV2Service(OpportunityV2Repository(),clock=lambda:datetime(2026,7,16));a=service.materialize(sim.run_id,policy);b=service.materialize(sim.run_id,policy)
  self.assertEqual(a.run_id,b.run_id);self.assertEqual(a.state,'INSUFFICIENT_EVIDENCE')
  with get_connection() as c:
   with c.cursor() as q:q.execute('SELECT entry_zone_low,historical_win_rate,lineage_checksum FROM opportunity_candidates_v2 WHERE candidate_id=%s',(a.candidate_id,));row=q.fetchone();self.assertIsNone(row[0]);self.assertIsNone(row[1]);self.assertEqual(len(row[2]),64)
if __name__=='__main__':unittest.main()
