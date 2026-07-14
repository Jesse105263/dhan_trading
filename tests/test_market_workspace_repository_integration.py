from __future__ import annotations

import os
import unittest

from services.market_workspace_repository import MarketWorkspaceRepository


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS") == "1", "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class MarketWorkspaceRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = MarketWorkspaceRepository()

    def test_overview_and_empty_safe_projection(self) -> None:
        overview = self.repository.overview()
        self.assertTrue(overview["database_ready"])
        self.assertEqual(set(overview["counts"]), {"ranked", "selections", "risk_approved", "risk_rejected", "signals"})
        rows, total = self.repository.list_opportunities(symbol="V2_NO_SUCH_SYMBOL", expiry=None, minimum_score=None, selection=None, risk_approved=None, signal=None, freshness=None, current_cutoff=None, aging_cutoff=None, sort="rank", direction="asc", limit=5, offset=0)
        self.assertEqual(rows, [])
        self.assertEqual(total, 0)

    def test_latest_projection_is_ordered_bounded_and_preserves_lineage(self) -> None:
        rows, total = self.repository.list_opportunities(symbol=None, expiry=None, minimum_score=None, selection=None, risk_approved=None, signal=None, freshness=None, current_cutoff=None, aging_cutoff=None, sort="rank", direction="asc", limit=5, offset=0)
        self.assertLessEqual(len(rows), 5)
        self.assertGreaterEqual(total, len(rows))
        self.assertEqual([row["rank_position"] for row in rows], sorted(row["rank_position"] for row in rows))
        if rows:
            detail = self.repository.get_opportunity(rows[0]["ranking_id"])
            self.assertIsNotNone(detail)
            self.assertEqual(detail["ranking_id"], rows[0]["ranking_id"])
            self.assertEqual(detail["ranking_run_id"], rows[0]["ranking_run_id"])
