from __future__ import annotations

import os
import unittest

from services.read_api_repository import ReadApiRepository


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS") == "1", "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class ReadApiRepositoryIntegrationTest(unittest.TestCase):
    def test_health_and_all_resources_are_queryable(self) -> None:
        repository = ReadApiRepository()
        self.assertEqual(repository.health()["status"], "ok")
        for resource in repository.resources():
            with self.subTest(resource=resource):
                rows = repository.list_latest(resource, 2)
                self.assertLessEqual(len(rows), 2)
                if rows:
                    run_id_name = {
                        "rankings": "ranking_run_id",
                        "selections": "selection_run_id",
                        "risk": "risk_run_id",
                        "signals": "signal_run_id",
                        "replays": "replay_run_id",
                        "backtests": "backtest_run_id",
                    }[resource]
                    detail = repository.get_run(resource, rows[0][run_id_name])
                    self.assertIsNotNone(detail)
                    self.assertIn("items", detail)
