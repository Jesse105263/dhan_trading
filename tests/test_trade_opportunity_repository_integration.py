import os,unittest
from services.database import get_connection
from services.trade_opportunity_repository import TradeOpportunityRepository
from services.trade_opportunity_service import TradeOpportunityService

@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class TradeOpportunityRepositoryIntegrationTest(unittest.TestCase):
    def test_idempotent_materialization_lineage_and_source_immutability(self):
        repository=TradeOpportunityRepository(); sources=repository.similarity_runs(limit=1)
        if not sources: self.skipTest("No persisted similarity run is available.")
        before=repository._fetch("SELECT COUNT(*) count FROM feature_store_vectors",())[0]["count"]
        service=TradeOpportunityService(repository); first=service.materialize(sources[0]["run_id"]); second=service.materialize(sources[0]["run_id"])
        self.assertEqual(first["run_id"],second["run_id"])
        rows=repository.list(None,None,10); self.assertTrue(rows)
        detail=repository.get(rows[0]["opportunity_id"]); self.assertEqual(detail["similarity_run_id"],sources[0]["run_id"])
        self.assertEqual(repository._fetch("SELECT COUNT(*) count FROM feature_store_vectors",())[0]["count"],before)
        with get_connection() as connection:
            with connection.cursor() as cursor: cursor.execute("DELETE FROM trade_opportunity_runs WHERE run_id=%s",(first["run_id"],))
            connection.commit()
