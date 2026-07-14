from __future__ import annotations

import unittest
from unittest.mock import Mock
from uuid import UUID

from services.trading_analyst import AnalystRequest, TradingAnalystEvidenceService, TradingAnalystService


ID = UUID("11111111-1111-4111-8111-111111111111")
SECOND = UUID("22222222-2222-4222-8222-222222222222")


def opportunity(identifier=ID, state="ELIGIBLE"):
    eligible = state == "ELIGIBLE"
    return {
        "opportunity_id": identifier, "similarity_run_id": ID, "query_vector_id": ID,
        "query_analytics_id": ID, "query_ranking_id": SECOND, "underlying_symbol": "ABC",
        "expiry": "2026-08-27", "observed_at": "2026-07-15T10:00:00", "state": state,
        "direction": "LONG" if eligible else None, "opportunity_score": 75 if eligible else None,
        "evidence_quality": 0.8, "match_count": 8, "classified_count": 5,
        "entry_zone_low": 96 if eligible else None, "entry_zone_high": 100 if eligible else None,
        "stop_zone": 94 if eligible else None, "target_zones": [106, 110] if eligible else [],
        "historical_win_rate": 0.8 if eligible else None, "expected_value": 3 if eligible else None,
        "risk_reward": 2 if eligible else None, "reasons_for": ["Persisted support"],
        "reasons_against": ["No guarantee"], "evidence": [{"similarity_match_id": SECOND,
        "matched_vector_id": SECOND, "matched_outcome_id": SECOND, "outcome": {"won": True}}],
    }


class DetailService:
    def __init__(self, value): self.value=value; self.calls=0
    def detail(self, identifier): self.calls+=1; return self.value


class Similarity:
    def run(self, identifier, matches=False): return {"run_id": identifier, "matches": []}


class Events:
    def opportunity_context(self, identifier): return {"events": [], "reasons_for": [], "reasons_against": []}


class Provider:
    name="provider"
    def __init__(self, error=None): self.calls=0; self.error=error
    def answer(self, question, evidence):
        self.calls+=1
        if self.error: raise self.error
        return "Provider interpretation"


def evidence_service(value):
    return TradingAnalystEvidenceService(DetailService(value), DetailService({"features": {"spot_price": 100}}), DetailService({"features": {}}), Similarity(), Events())


class TradingAnalystTest(unittest.TestCase):
    def test_packet_has_exact_lineage_and_missing_context_markers(self):
        packet=evidence_service(opportunity()).assemble(ID)
        self.assertEqual(packet["schema_version"],"trading-analyst-evidence-v1")
        self.assertEqual(packet["lineage"]["query_vector_id"],ID)
        self.assertTrue(any(c["type"]=="historical_outcome" for c in packet["citations"]))
        self.assertIn("No linked news",packet["limitations"][-1])

    def test_local_answer_and_insufficient_evidence(self):
        result=TradingAnalystService(evidence_service(opportunity())).ask(AnalystRequest("Explain",(ID,)))
        self.assertIn("Facts",result["answer"]); self.assertIn("underlying reference",result["answer"])
        result=TradingAnalystService(evidence_service(opportunity(state="INSUFFICIENT_EVIDENCE"))).ask(AnalystRequest("Explain",(ID,)))
        self.assertIn("INSUFFICIENT_EVIDENCE",result["answer"])
        self.assertNotIn("entry 96",result["answer"])

    def test_refusal_precedes_retrieval_and_provider(self):
        evidence=evidence_service(opportunity()); provider=Provider()
        result=TradingAnalystService(evidence,provider).ask(AnalystRequest("Place an order",(ID,)))
        self.assertEqual(result["status"],"REFUSED"); self.assertEqual(provider.calls,0)
        self.assertEqual(evidence.opportunities.calls,0)

    def test_provider_failure_falls_back_and_is_sanitized(self):
        result=TradingAnalystService(evidence_service(opportunity()),Provider(RuntimeError("api_key=secret failed"))).ask(AnalystRequest("Explain",(ID,)))
        self.assertEqual(result["provider"],"provider+local-fallback")
        self.assertNotIn("secret",result["model_error"])
        self.assertIn("Facts",result["answer"])

    def test_compare_and_request_validation(self):
        service=evidence_service(opportunity())
        result=TradingAnalystService(service).ask(AnalystRequest("Compare",(ID,SECOND)))
        self.assertIn("Comparison",result["answer"])
        for request in (AnalystRequest("",(ID,)),AnalystRequest("x",()),AnalystRequest("x",(ID,ID))):
            with self.assertRaises(ValueError): request.normalized()


if __name__ == "__main__": unittest.main()
