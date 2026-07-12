import os, unittest
from services.database import get_connection
from services.option_contract_selection_repository import OptionContractSelectionRepository

@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class TestRepositoryIntegration(unittest.TestCase):
    def test_repository_queries_latest_production_ranking(self):
        with get_connection() as c:
            with c.cursor() as cur:
                cur.execute("SELECT ranking_run_id FROM option_ranking_runs ORDER BY calculated_at DESC LIMIT 1")
                row=cur.fetchone()
        if row is None: self.skipTest("No ranking run available.")
        ranked=OptionContractSelectionRepository().list_ranked_underlyings(row[0],10)
        self.assertGreaterEqual(len(ranked),1)
        candidates=OptionContractSelectionRepository().list_contract_candidates(ranked[0])
        self.assertGreaterEqual(len(candidates),2)

if __name__=='__main__': unittest.main()
