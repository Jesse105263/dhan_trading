import unittest
from datetime import date,datetime
from decimal import Decimal
from uuid import UUID

from services.market_workspace_service import WorkspaceQueryError
from services.trade_opportunity_service import TradeOpportunityService

RUN=UUID("11111111-1111-4111-8111-111111111111")


class Repository:
    def __init__(self,count=5,positive=True): self.count=count; self.positive=positive; self.persisted=None
    def similarity_runs(self,run_id,limit): return [{"run_id":RUN,"query_vector_id":RUN,"query_analytics_id":RUN,
      "query_ranking_id":None,"underlying_symbol":"ABC","expiry":date(2026,8,27),
      "observed_at":datetime(2026,7,15,12),"spot_price":Decimal(100)}]
    def similarity_matches(self,run_id):
        rows=[]
        for index in range(self.count):
            value=Decimal(index+1) if self.positive else Decimal(-index-1)
            rows.append({"match_id":UUID(f"00000000-0000-4000-8000-{index+1:012d}"),
              "matched_vector_id":UUID(f"10000000-0000-4000-8000-{index+1:012d}"),
              "matched_outcome_id":UUID(f"20000000-0000-4000-8000-{index+1:012d}"),
              "outcome_type":"EXPIRY_COMPLETE","won":self.positive,"closing_return":value,
              "maximum_favourable_excursion":Decimal(2*(index+1)),
              "maximum_adverse_excursion":Decimal(-5+index),"similarity_score":Decimal("0.8"),
              "shared_feature_count":10})
        return rows
    def persist(self,run,items): self.persisted=(run,items)
    def list(self,state,symbol,limit): return []
    def get(self,identifier): return None


class TradeOpportunityServiceTest(unittest.TestCase):
    def test_calculates_traceable_zones_expected_value_and_rank(self):
        repository=Repository(); result=TradeOpportunityService(repository).materialize(RUN)
        item=repository.persisted[1][0]
        self.assertEqual(result["eligible_count"],1); self.assertEqual(item["state"],"ELIGIBLE")
        self.assertEqual(item["entry_zone_low"],Decimal(96)); self.assertEqual(item["entry_zone_high"],Decimal(100))
        self.assertEqual(item["stop_zone"],Decimal(95)); self.assertEqual(item["target_zones"],[Decimal(106),Decimal(108)])
        self.assertEqual(item["expected_value"],Decimal(3)); self.assertEqual(item["historical_win_rate"],Decimal(1))
        self.assertEqual(len(item["evidence"]),5); self.assertIsNotNone(item["risk_reward"])
    def test_insufficient_evidence_never_fabricates_fields(self):
        repository=Repository(count=4); TradeOpportunityService(repository).materialize(RUN)
        item=repository.persisted[1][0]
        self.assertEqual(item["state"],"INSUFFICIENT_EVIDENCE")
        for field in ("entry_zone_low","stop_zone","expected_value","historical_win_rate","risk_reward","opportunity_score"):
            self.assertIsNone(item[field])
    def test_non_positive_history_is_not_an_opportunity(self):
        repository=Repository(positive=False); TradeOpportunityService(repository).materialize(RUN)
        item=repository.persisted[1][0]
        self.assertEqual(item["state"],"NO_OPPORTUNITY"); self.assertIsNone(item["entry_zone_low"])
        self.assertLess(item["expected_value"],0)
    def test_deterministic_ids_and_validation(self):
        repository=Repository(); service=TradeOpportunityService(repository)
        first=service.materialize(RUN)["run_id"]; second=service.materialize(RUN)["run_id"]
        self.assertEqual(first,second)
        with self.assertRaises(ValueError): service.materialize(limit=0)
        for query in ({"limit":"bad"},{"limit":"201"},{"state":"bad"}):
            with self.assertRaises(WorkspaceQueryError): service.list(query)


if __name__=="__main__": unittest.main()
