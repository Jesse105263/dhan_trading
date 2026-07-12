from __future__ import annotations

import os
import unittest
from datetime import datetime
from uuid import UUID

from services.database import get_connection
from services.option_signal_models import OptionSignalRequest
from services.option_signal_repository import OptionSignalRepository
from services.option_signal_service import OptionSignalService


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class OptionSignalRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT risk_run_id
                    FROM option_risk_assessment_runs
                    WHERE approved_contract_count > 0
                    ORDER BY calculated_at DESC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row is None:
                    self.skipTest("No production risk run with approved contracts.")
                self.risk_run_id = UUID(str(row[0]))
                cursor.execute("DELETE FROM option_signal_runs WHERE risk_run_id = %s", (self.risk_run_id,))
            connection.commit()

    def tearDown(self):
        if not hasattr(self, "risk_run_id"):
            return
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM option_signal_runs WHERE risk_run_id = %s", (self.risk_run_id,))
            connection.commit()

    def test_reads_approved_lineage_and_persists_signals(self):
        repository = OptionSignalRepository()
        candidates = repository.list_approved_candidates(self.risk_run_id)
        self.assertGreater(len(candidates), 0)
        result = OptionSignalService(repository).generate_and_persist(
            OptionSignalRequest(self.risk_run_id, datetime.now())
        )
        self.assertEqual(len(result.signals), len(candidates))
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM option_signals WHERE signal_run_id = %s",
                    (result.signal_run_id,),
                )
                self.assertEqual(cursor.fetchone()[0], len(result.signals))


if __name__ == "__main__":
    unittest.main()
