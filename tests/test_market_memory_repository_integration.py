import os
import unittest

from services.market_memory_repository import MarketMemoryRepository


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS") == "1", "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class MarketMemoryRepositoryIntegrationTest(unittest.TestCase):
    def test_read_projection_preserves_persisted_order_and_lineage(self):
        repository = MarketMemoryRepository()
        symbols = repository._fetch_all(
            "SELECT underlying_symbol FROM option_chain_analytics GROUP BY underlying_symbol ORDER BY underlying_symbol LIMIT 1", ()
        )
        if not symbols:
            self.assertEqual(symbols, [])
            return
        rows = repository.snapshots(symbols[0]["underlying_symbol"], None, None, None, 20)
        self.assertLessEqual(len(rows), 20)
        observed = [(row["source_captured_at"], str(row["analytics_id"])) for row in rows]
        self.assertEqual(observed, sorted(observed, reverse=True))
        detail = repository.snapshot(rows[0]["analytics_id"])
        self.assertEqual(detail["source_run_id"], rows[0]["source_run_id"])
        self.assertEqual(detail["underlying_symbol"], rows[0]["underlying_symbol"])
