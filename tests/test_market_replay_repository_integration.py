from __future__ import annotations
import os, unittest
from datetime import datetime

from services.market_replay_models import MarketReplayRequest
from services.market_replay_repository import MarketReplayRepository
from services.market_replay_service import MarketReplayService
from services.database import get_connection

@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS") == "1", "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class MarketReplayRepositoryIntegrationTest(unittest.TestCase):
    def test_replays_latest_production_signal_lineage(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT signal_run_id FROM option_signal_runs ORDER BY calculated_at DESC LIMIT 1")
                row = cursor.fetchone()
        if row is None:
            self.skipTest("No production signal run is available.")
        result = MarketReplayService(MarketReplayRepository()).replay_and_persist(
            MarketReplayRequest(row[0], datetime.now())
        )
        self.assertGreater(result.signal_count, 0)
        self.assertEqual(len(result.events), result.signal_count * 6)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM market_replay_events WHERE replay_run_id=%s", (result.replay_run_id,))
                self.assertEqual(cursor.fetchone()[0], len(result.events))

if __name__ == "__main__": unittest.main()
