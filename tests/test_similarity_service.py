import unittest
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.market_workspace_service import WorkspaceQueryError
from services.similarity_service import SimilarityService


QUERY=UUID("11111111-1111-4111-8111-111111111111")


def vector(identifier, observed, symbol="ABC", expiry="2026-08-27", **features):
    return {"vector_id":UUID(identifier),"analytics_id":UUID(identifier),"ranking_id":None,
      "underlying_symbol":symbol,"expiry":expiry,"observed_at":datetime.fromisoformat(observed),"features":features}


class Repository:
    def __init__(self):
        shared={"atm_distance_pct":1,"total_pcr":1,"nearby_pcr":1,"atm_mean_iv":20,
                "liquidity_coverage":0.8,"time_to_expiry_days":20}
        self.query=vector(str(QUERY),"2026-07-15T12:00:00",**shared)
        self.rows=[
          vector("22222222-2222-4222-8222-222222222222","2026-07-14T12:00:00",**shared),
          vector("33333333-3333-4333-8333-333333333333","2026-07-13T12:00:00",symbol="XYZ",
                 **{**shared,"atm_mean_iv":40,"total_pcr":2}),
          vector("44444444-4444-4444-8444-444444444444","2026-07-16T12:00:00",**shared)]
        self.persisted=None
    def get_vector(self,identifier): return self.query if identifier==QUERY else None
    def candidates(self,query,cutoff,same_symbol,same_expiry):
        return [r for r in self.rows if r["observed_at"]<=cutoff
                and (not same_symbol or r["underlying_symbol"]==query["underlying_symbol"])
                and (not same_expiry or r["expiry"]==query["expiry"])]
    def outcomes(self,ids):
        return {ids[0]:{"outcome_id":UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),"won":True,
          "closing_return":Decimal("2"),"maximum_favourable_excursion":Decimal("3"),
          "maximum_adverse_excursion":Decimal("-1")}} if ids else {}
    def persist(self,run,matches): self.persisted=(run,matches)
    def get_run(self,run_id): return None


class SimilarityServiceTest(unittest.TestCase):
    def setUp(self): self.repository=Repository(); self.service=SimilarityService(self.repository)

    def test_deterministic_ranking_excludes_query_and_future(self):
        first=self.service.analyze(QUERY,{})
        second=self.service.analyze(QUERY,{})
        self.assertEqual(first["run_id"],second["run_id"])
        self.assertEqual([m["vector_id"] for m in first["matches"]],[m["vector_id"] for m in second["matches"]])
        self.assertEqual(first["matches"][0]["similarity_score"],Decimal("1"))
        self.assertNotIn(UUID("44444444-4444-4444-8444-444444444444"),[m["vector_id"] for m in first["matches"]])

    def test_nulls_are_skipped_and_overlap_is_required(self):
        self.repository.rows[0]["features"]={"atm_distance_pct":1}
        result=self.service.analyze(QUERY,{})
        self.assertNotIn(self.repository.rows[0]["vector_id"],[m["vector_id"] for m in result["matches"]])

    def test_filters_and_cutoff(self):
        self.repository.rows[0]["expiry"]="2026-09-24"
        self.repository.rows.append(vector("55555555-5555-4555-8555-555555555555","2026-07-12T12:00:00",
          **self.repository.query["features"]))
        result=self.service.analyze(QUERY,{"same_symbol":"true","same_expiry":"true","limit":"1"})
        self.assertEqual(result["match_count"],1)
        with self.assertRaises(WorkspaceQueryError):
            self.service.analyze(QUERY,{"historical_cutoff":"2026-07-16T00:00:00"})

    def test_outcomes_are_attached_and_insufficient_evidence_is_explicit(self):
        result=self.service.analyze(QUERY,{})
        self.assertEqual(result["statistics"]["classified_count"],1)
        self.assertEqual(result["evidence_state"],"INSUFFICIENT")

    def test_persistence_is_idempotent_by_deterministic_ids(self):
        result=self.service.analyze(QUERY,{},persist=True)
        run,matches=self.repository.persisted
        self.assertEqual(run["run_id"],result["run_id"])
        self.assertEqual(matches[0]["match_id"],self.service.analyze(QUERY,{},persist=True) and self.repository.persisted[1][0]["match_id"])

    def test_invalid_options(self):
        for query in ({"limit":"0"},{"same_symbol":"yes"},{"model_version":"other"}):
            with self.assertRaises(WorkspaceQueryError): self.service.analyze(QUERY,query)

    def test_model_metadata_exposes_exact_allow_list_and_weights(self):
        model=self.service.models()["data"][0]
        self.assertEqual({row["name"] for row in model["features"]},set(self.service.FEATURES))
        self.assertEqual(next(row["weight"] for row in model["features"] if row["name"]=="atm_mean_iv"),1.5)
        self.assertFalse(model["outcomes_used_as_inputs"])


if __name__=="__main__": unittest.main()
