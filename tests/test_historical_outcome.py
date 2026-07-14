import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
from services.historical_outcome_service import HistoricalOutcomeService
from services.market_workspace_service import WorkspaceQueryError

class Repository:
    def __init__(self,futures): self.futures=futures; self.saved=[]
    def source_vectors(self,limit,after_at=None,after_id=None):
        if after_at is not None:return []
        return [{"vector_id":UUID("11111111-1111-4111-8111-111111111111"),"analytics_id":UUID("22222222-2222-4222-8222-222222222222"),"ranking_id":None,"underlying_symbol":"REL","expiry":date(2026,7,30),"observed_at":datetime(2026,7,28,10),"spot_price":Decimal("100")}][:limit]
    def future_vectors(self,source):return self.futures
    def upsert(self,outcome):self.saved.append(outcome)
    def list_outcomes(self,filters,limit,ascending=False):return self.saved[:limit]
    def get_outcome(self,outcome_id):return self.saved[0] if self.saved else None
    def statistics(self,filters):return {"outcome_count":len(self.saved)}

class HistoricalOutcomeServiceTest(unittest.TestCase):
    def future(self,identifier,time,price):return {"vector_id":UUID(identifier),"observed_at":time,"spot_price":Decimal(price)}
    def test_complete_objective_outcome(self):
        futures=[self.future("33333333-3333-4333-8333-333333333333",datetime(2026,7,29,10),"90"),self.future("44444444-4444-4444-8444-444444444444",datetime(2026,7,30,10),"120")]
        repo=Repository(futures); service=HistoricalOutcomeService(repo,clock=lambda:datetime(2026,8,1))
        service.materialize(); result=repo.saved[0]
        self.assertEqual(result["outcome_type"],"EXPIRY_COMPLETE"); self.assertEqual(result["closing_return"],Decimal("20") )
        self.assertEqual(result["maximum_favourable_excursion"],Decimal("20")); self.assertEqual(result["maximum_adverse_excursion"],Decimal("-10"))
        self.assertTrue(result["won"]); self.assertEqual(result["future_observation_count"],2)
    def test_partial_and_missing_are_not_classified(self):
        partial=Repository([self.future("33333333-3333-4333-8333-333333333333",datetime(2026,7,29,10),"110")]); service=HistoricalOutcomeService(partial)
        service.materialize(); self.assertEqual(partial.saved[0]["outcome_type"],"PARTIAL"); self.assertIsNone(partial.saved[0]["won"]); self.assertIsNone(partial.saved[0]["expiry_outcome"])
        empty=Repository([]); HistoricalOutcomeService(empty).materialize(); self.assertEqual(empty.saved[0]["outcome_type"],"NO_FUTURE_DATA"); self.assertIsNone(empty.saved[0]["closing_return"]); self.assertIsNone(empty.saved[0]["maximum_favourable_excursion"]); self.assertIsNone(empty.saved[0]["peak_gain"])
    def test_deterministic_id_idempotent_batches_and_filters(self):
        repo=Repository([]); service=HistoricalOutcomeService(repo); service.materialize(); first=repo.saved[-1]["outcome_id"]; service.materialize(); self.assertEqual(first,repo.saved[-1]["outcome_id"])
        self.assertEqual(service.list({"symbol":"rel"})["count"],2); self.assertEqual(service.statistics({})["data"]["outcome_count"],2)
        for query in ({"limit":"0"},{"expiry":"bad"},{"from":"bad"},{"outcome_type":"guess"}):
            with self.subTest(query=query),self.assertRaises(WorkspaceQueryError):service.list(query)
