import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from services.similarity_v2_models import SimilarityPolicyV2
from services.similarity_v2_service import SimilarityV2Service


def vector(number, day, values, coverage=Decimal("100")):
    return {"vector_id":UUID(int=number),"schema_version":"canonical-market-features-v2","instrument_id":UUID(int=99),
        "subject_type":"UNDERLYING","interval_code":"15M","anchor_bar_revision_id":UUID(int=100+number),
        "observed_at":datetime(2026,7,day,10),"available_at":datetime(2026,7,day,10,1),"coverage_percentage":coverage,
        "lineage_checksum":str(number).zfill(64),"features":values,"families":{"return_1_bar_pct":"returns","range_pct":"volatility",
        "bid_ask_spread_pct":"liquidity","trend_regime_3":"regime"}}


class Repository:
    def __init__(self):
        self.query=vector(1,15,{"return_1_bar_pct":1,"range_pct":2,"bid_ask_spread_pct":Decimal("0.2"),"trend_regime_3":1})
        self.rows=[vector(2,14,{"return_1_bar_pct":1,"range_pct":2,"bid_ask_spread_pct":Decimal("0.1"),"trend_regime_3":1}),
            vector(3,13,{"return_1_bar_pct":2,"range_pct":3,"bid_ask_spread_pct":Decimal("0.3"),"trend_regime_3":1}),
            vector(4,12,{"return_1_bar_pct":-1,"range_pct":5,"bid_ask_spread_pct":Decimal("0.4"),"trend_regime_3":-1}),
            vector(5,16,{"return_1_bar_pct":1,"range_pct":2,"bid_ask_spread_pct":Decimal("0.1"),"trend_regime_3":1})]
        self.saved=[]; self.outcome_cutoff=None
    def vector(self,identifier): return self.query if identifier==UUID(int=1) else None
    def candidates(self,query,cutoff,policy): return [item for item in self.rows if item["observed_at"]<cutoff and item["available_at"]<=cutoff]
    def outcomes(self,vectors,cutoff): self.outcome_cutoff=cutoff; return {}
    def persist(self,prepared): self.saved.append(prepared)


class SimilarityV2Tests(unittest.TestCase):
    def setUp(self): self.repository=Repository(); self.service=SimilarityV2Service(self.repository,clock=lambda:datetime(2026,7,16))

    def test_models_weights_diagnostics_and_determinism(self):
        for model in ("WEIGHTED_MANHATTAN","WEIGHTED_EUCLIDEAN","COSINE"):
            policy=SimilarityPolicyV2("test-"+model,model,feature_weights={"range_pct":Decimal("2")},minimum_candidates=2)
            first=self.service.materialize(UUID(int=1),policy); second=self.service.materialize(UUID(int=1),policy)
            self.assertEqual(first.run_id,second.run_id); self.assertEqual(first.evidence_state,"SUFFICIENT")
            match=self.repository.saved[-1]["matches"][0]
            self.assertIn("range_pct",match["feature_diagnostics"]); self.assertGreaterEqual(match["evidence_quality_score"],0)
        self.assertEqual(self.repository.outcome_cutoff,self.repository.query["observed_at"])

    def test_regime_liquidity_dynamic_selection_and_insufficient_state(self):
        policy=SimilarityPolicyV2("filtered",selected_features=("return_1_bar_pct","range_pct","trend_regime_3"),
            same_regime=True,minimum_liquidity_value=Decimal("0.25"),minimum_candidates=3)
        result=self.service.materialize(UUID(int=1),policy)
        self.assertEqual(result.evidence_state,"INSUFFICIENT_EVIDENCE"); self.assertEqual(result.match_count,1)
        self.assertEqual(self.repository.saved[-1]["run"]["quality_metrics"]["selected_features"],list(policy.selected_features))

    def test_temporal_cutoff_and_ranking_strategies(self):
        for strategy in ("DISTANCE","EVIDENCE_QUALITY","TEMPORAL_DIVERSITY"):
            result=self.service.materialize(UUID(int=1),SimilarityPolicyV2("rank-"+strategy,ranking_strategy=strategy,minimum_candidates=1))
            self.assertGreater(result.match_count,0)
        with self.assertRaises(ValueError): self.service.materialize(UUID(int=1),SimilarityPolicyV2("bad-cutoff"),cutoff=datetime(2026,7,16))

    def test_policy_validation(self):
        with self.assertRaises(ValueError): SimilarityPolicyV2("bad",distance_model="UNKNOWN")
        with self.assertRaises(ValueError): SimilarityPolicyV2("bad-weight",feature_weights={"x":Decimal(0)})


if __name__=="__main__": unittest.main()
