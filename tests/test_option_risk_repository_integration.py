from __future__ import annotations

import os
import unittest
from decimal import Decimal

from services.database import get_connection
from services.option_risk_repository import OptionRiskRepository


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class OptionRiskRepositoryIntegrationTest(unittest.TestCase):
    def test_reads_latest_production_selection(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT selection_run_id FROM option_contract_selection_runs ORDER BY calculated_at DESC LIMIT 1"
                )
                row = cursor.fetchone()
        if row is None:
            self.skipTest("No option contract selection run available.")
        selections = OptionRiskRepository().list_selected_contracts(row[0])
        self.assertGreaterEqual(len(selections), 1)
        self.assertGreater(selections[0].premium_per_lot, Decimal("0"))
        self.assertGreater(selections[0].lot_size, 0)


if __name__ == "__main__":
    unittest.main()
