import os,unittest
from services.database import get_connection
from services.historical_outcome_repository import HistoricalOutcomeRepository
from services.historical_outcome_service import HistoricalOutcomeService

@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class HistoricalOutcomeRepositoryIntegrationTest(unittest.TestCase):
    def test_idempotent_materialization_lineage_and_statistics(self):
        repository=HistoricalOutcomeRepository(); service=HistoricalOutcomeService(repository)
        before=repository._fetch("SELECT COUNT(*) AS count FROM feature_store_vectors",())[0]["count"]
        service.materialize(); service.materialize()
        outcomes=repository._fetch("SELECT * FROM historical_outcomes",())
        self.assertEqual(len(outcomes),before)
        if outcomes:
            detail=repository.get_outcome(outcomes[0]["outcome_id"]); self.assertEqual(detail["vector_id"],outcomes[0]["vector_id"])
        stats=repository.statistics({}); self.assertEqual(stats["outcome_count"],before)
