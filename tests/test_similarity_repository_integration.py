import os
import unittest

from services.similarity_repository import SimilarityRepository
from services.similarity_service import SimilarityService
from services.database import get_connection


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class SimilarityRepositoryIntegrationTest(unittest.TestCase):
    def test_exact_lineage_idempotency_ordering_and_no_source_mutation(self):
        repository=SimilarityRepository(); service=SimilarityService(repository)
        vectors=repository._fetch("SELECT * FROM feature_store_vectors ORDER BY observed_at DESC,vector_id DESC LIMIT 1",())
        if not vectors: self.skipTest("No persisted Feature Store vectors are available.")
        vector=vectors[0]; before=repository._fetch("SELECT COUNT(*) AS count FROM feature_store_vectors",())[0]["count"]
        first=service.analyze(vector["vector_id"],{"limit":"10"},persist=True)
        second=service.analyze(vector["vector_id"],{"limit":"10"},persist=True)
        self.assertEqual(first["run_id"],second["run_id"])
        run=repository.get_run(first["run_id"]); self.assertEqual(run["query_analytics_id"],vector["analytics_id"])
        matches=repository.get_matches(first["run_id"])
        self.assertEqual([row["rank_position"] for row in matches],list(range(1,len(matches)+1)))
        self.assertEqual(repository._fetch("SELECT COUNT(*) AS count FROM feature_store_vectors",())[0]["count"],before)
        with get_connection() as connection:
            with connection.cursor() as cursor: cursor.execute("DELETE FROM similarity_runs WHERE run_id=%s",(first["run_id"],))
            connection.commit()


if __name__=="__main__": unittest.main()
