import unittest
from datetime import datetime, timedelta

from services.market_workspace_service import WorkspaceQueryError
from services.symbol_workspace_service import SymbolWorkspaceService


class FakeRepository:
    def search(self, query, limit): return [{"underlying_symbol":"RELIANCE","expiries":[]}]
    def intelligence(self, symbol, expiry):
        if symbol == "NONE": return None
        now=datetime(2026,7,14,12)
        return {"symbol":symbol,"expiry":expiry or "2026-07-30","analytics":[{"analytics_id":"a","source_run_id":"c","source_captured_at":now,"calculated_at":now}],"changes":[],"rankings":[{"ranking_id":"r1","rank_position":2,"source_captured_at":now,"calculated_at":now},{"ranking_id":"r0","rank_position":5,"source_captured_at":now-timedelta(days=1),"calculated_at":now-timedelta(days=1)}],"selections":[{"selection_id":"s","calculated_at":now}],"risk":[{"assessment_id":"x","calculated_at":now}],"signals":[{"signal_id":"g","calculated_at":now}],"collections":[{"run_id":"c","requested_at":now}],"related":[]}

class SymbolWorkspaceServiceTest(unittest.TestCase):
    def setUp(self): self.service=SymbolWorkspaceService(FakeRepository(),clock=lambda:datetime(2026,7,14,12))
    def test_search_validation(self):
        self.assertEqual(self.service.search("rel",10)["count"],1)
        with self.assertRaises(WorkspaceQueryError): self.service.search("x",26)
    def test_workspace_timeline_movement_and_empty(self):
        result=self.service.intelligence("reliance","2026-07-30")
        self.assertEqual(result["rank_movement"],3)
        self.assertEqual({event["type"] for event in result["timeline"]},{"collection","analytics","ranking","selection","risk","signal"})
        self.assertIsNone(self.service.intelligence("NONE",None))
    def test_invalid_expiry(self):
        with self.assertRaises(WorkspaceQueryError): self.service.intelligence("REL","bad")
