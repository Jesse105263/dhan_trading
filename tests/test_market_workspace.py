from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.market_workspace_service import MarketWorkspaceService, WorkspaceQueryError


class FakeWorkspaceRepository:
    def __init__(self) -> None:
        self.now = datetime(2026, 7, 14, 12)
        self.item_id = uuid4()
        self.rows = [{
            "ranking_id": self.item_id, "ranking_run_id": uuid4(), "analytics_id": uuid4(),
            "change_id": uuid4(), "underlying_symbol": "RELIANCE", "expiry": "2026-07-30",
            "source_captured_at": self.now - timedelta(minutes=10), "rank_position": 1,
            "total_score": Decimal("0.88"), "liquidity_score": Decimal("0.9"),
            "activity_score": Decimal("0.8"), "volatility_score": Decimal("0.7"),
            "directional_score": Decimal("0.6"), "explanation": {},
            "calculated_at": self.now, "selection_available": True,
            "risk_approved": True, "signal_available": False,
        }]
        self.last = None

    def overview(self):
        return {"database_ready": True, "latest_option_run": {"completed_at": self.now - timedelta(minutes=10)}, "latest_ranking_run": {"calculated_at": self.now, "eligible_count": 1}, "counts": {"ranked": 1, "selections": 1, "risk_approved": 1, "risk_rejected": 0, "signals": 0}, "failures": []}

    def list_opportunities(self, **kwargs):
        self.last = kwargs
        return self.rows[:kwargs["limit"]], len(self.rows)

    def get_opportunity(self, ranking_id):
        return self.rows[0] if ranking_id == self.item_id else None


class MarketWorkspaceServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeWorkspaceRepository()
        self.service = MarketWorkspaceService(self.repository, clock=lambda: self.repository.now)

    def test_freshness_boundaries(self) -> None:
        self.assertEqual(self.service.freshness(None), "unavailable")
        self.assertEqual(self.service.freshness(self.repository.now - timedelta(minutes=15)), "current")
        self.assertEqual(self.service.freshness(self.repository.now - timedelta(minutes=16)), "aging")
        self.assertEqual(self.service.freshness(self.repository.now - timedelta(minutes=61)), "stale")

    def test_overview_aggregates_persisted_values(self) -> None:
        result = self.service.overview()
        self.assertTrue(result["platform"]["database_ready"])
        self.assertEqual(result["counts"]["ranked"], 1)
        self.assertEqual(result["freshness"]["state"], "current")

    def test_filters_sorting_and_bounded_pagination(self) -> None:
        result = self.service.opportunities({"symbol": "REL", "minimum_score": "0.5", "selection": "true", "sort": "score", "direction": "desc", "limit": "10", "offset": "0"})
        self.assertEqual(result["data"][0]["freshness"], "current")
        self.assertEqual(self.repository.last["symbol"], "REL")
        self.assertEqual(self.repository.last["sort"], "score")
        self.assertEqual(result["page"]["total"], 1)

    def test_rejects_invalid_filters(self) -> None:
        for query in ({"limit": "101"}, {"sort": "profit"}, {"minimum_score": "2"}, {"selection": "yes"}, {"freshness": "live"}):
            with self.subTest(query=query), self.assertRaises(WorkspaceQueryError):
                self.service.opportunities(query)

    def test_empty_and_not_found(self) -> None:
        self.repository.rows = []
        self.assertEqual(self.service.opportunities({})["data"], [])
        self.assertIsNone(self.service.opportunity(uuid4()))
