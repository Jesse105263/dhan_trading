from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from uuid import UUID

from services.market_memory_service import MarketMemoryService
from services.market_workspace_service import WorkspaceQueryError


FIRST = UUID("11111111-1111-4111-8111-111111111111")
SECOND = UUID("22222222-2222-4222-8222-222222222222")


class FakeRepository:
    def __init__(self) -> None:
        now = datetime(2026, 7, 14, 12)
        self.rows = [self._row(SECOND, now, "102", "0.8"), self._row(FIRST, now - timedelta(hours=1), "100", "0.6")]

    @staticmethod
    def _row(identifier, captured, spot, score):
        return {
            "analytics_id": identifier, "source_run_id": identifier,
            "underlying_symbol": "RELIANCE", "expiry": "2026-07-30",
            "source_captured_at": captured, "calculated_at": captured,
            "spot_price": spot, "atm_mean_iv": "18", "total_score": score,
            "rank_position": 1, "ranking_id": identifier, "ranking_run_id": identifier,
            "change_id": identifier, "previous_analytics_id": None,
        }

    def snapshots(self, symbol, expiry, start, end, limit, before=None):
        rows = [row for row in self.rows if not before or str(row["source_captured_at"]) < before]
        return rows[:limit]

    def snapshot(self, identifier):
        return next((row for row in self.rows if row["analytics_id"] == identifier), None)


class MarketMemoryServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = MarketMemoryService(FakeRepository(), clock=lambda: datetime(2026, 7, 14, 12))

    def test_ordered_snapshots_latest_previous_and_feature_history(self):
        result = self.service.list({"symbol": "reliance", "limit": "10"})
        self.assertEqual([row["snapshot_id"] for row in result["data"]], [SECOND, FIRST])
        self.assertEqual(self.service.latest({"symbol": "RELIANCE"})["snapshot_id"], SECOND)
        self.assertEqual(self.service.latest({"symbol": "RELIANCE"}, previous=True)["snapshot_id"], FIRST)
        history = self.service.feature_history("total_score", {"symbol": "RELIANCE"})
        self.assertEqual([point["value"] for point in history["data"]], ["0.6", "0.8"])

    def test_comparison_reports_only_changes_and_orders_timestamps(self):
        result = self.service.compare(SECOND, FIRST)
        changes = {change["feature"] for change in result["changes"]}
        self.assertEqual(changes, {"spot_price", "total_score"})
        self.assertEqual(result["previous_snapshot_id"], FIRST)

    def test_validates_filters_feature_and_limit(self):
        for query in ({}, {"symbol": "R", "limit": "0"}, {"symbol": "R", "expiry": "bad"}, {"symbol": "R", "from": "bad"}):
            with self.subTest(query=query), self.assertRaises(WorkspaceQueryError): self.service.list(query)
        with self.assertRaises(WorkspaceQueryError):
            self.service.feature_history("invented_metric", {"symbol": "R"})

    def test_empty_and_not_found(self):
        self.assertIsNone(self.service.detail(UUID("33333333-3333-4333-8333-333333333333")))
