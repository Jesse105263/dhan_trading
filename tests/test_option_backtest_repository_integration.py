from __future__ import annotations

import os
import unittest
from datetime import datetime
from uuid import UUID

from services.database import get_connection
from services.option_backtest_models import OptionBacktestRequest
from services.option_backtest_repository import OptionBacktestRepository
from services.option_backtest_service import OptionBacktestService


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class OptionBacktestRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT signal_run_id
                    FROM option_signal_runs
                    ORDER BY calculated_at DESC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row is None:
                    self.skipTest("No production signal run is available.")
                self.signal_run_id = UUID(str(row[0]))
                cursor.execute(
                    "DELETE FROM option_backtest_runs WHERE signal_run_id = %s",
                    (self.signal_run_id,),
                )
            connection.commit()

    def tearDown(self):
        if not hasattr(self, "signal_run_id"):
            return
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM option_backtest_runs WHERE signal_run_id = %s",
                    (self.signal_run_id,),
                )
            connection.commit()

    def test_reads_signal_lineage_and_persists_backtest(self):
        repository = OptionBacktestRepository()
        signals = repository.list_signals(self.signal_run_id)
        self.assertGreater(len(signals), 0)
        result = OptionBacktestService(repository).run_and_persist(
            OptionBacktestRequest(self.signal_run_id, datetime.now())
        )
        self.assertEqual(result.signal_count, len(signals))
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM option_backtest_trades WHERE backtest_run_id = %s",
                    (result.backtest_run_id,),
                )
                self.assertEqual(cursor.fetchone()[0], len(signals))


if __name__ == "__main__":
    unittest.main()
