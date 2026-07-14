from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from statistics import median
from typing import Any
from uuid import UUID, uuid5

import psycopg

from services.market_workspace_service import WorkspaceQueryError, WorkspaceUnavailable
from services.similarity_repository import SimilarityRepository


class SimilarityService:
    MODEL_VERSION = "option-observation-similarity-v1"
    NAMESPACE = UUID("325dd264-6504-46d1-a690-7689595ddbca")
    FEATURES = {
        "atm_distance_pct": Decimal("1.0"),
        "total_pcr": Decimal("1.0"),
        "nearby_pcr": Decimal("1.0"),
        "atm_mean_iv": Decimal("1.5"),
        "nearby_mean_iv": Decimal("1.0"),
        "liquidity_coverage": Decimal("1.5"),
        "price_coverage": Decimal("1.0"),
        "spot_price_change": Decimal("1.0"),
        "atm_straddle_change": Decimal("1.0"),
        "total_pcr_change": Decimal("1.0"),
        "atm_mean_iv_change": Decimal("1.0"),
        "time_to_expiry_days": Decimal("1.0"),
    }
    MINIMUM_SHARED_FEATURES = 5
    MAX_LIMIT = 100
    MINIMUM_CLASSIFIED_OUTCOMES = 3

    def __init__(self, repository=None, clock=datetime.now):
        self.repository = repository or SimilarityRepository(); self.clock = clock

    def models(self) -> dict[str, Any]:
        return {"data": [{"model_version": self.MODEL_VERSION, "method": "min-max normalized weighted Manhattan distance",
          "features": [{"name": name, "weight": float(weight)} for name, weight in self.FEATURES.items()],
          "minimum_shared_features": self.MINIMUM_SHARED_FEATURES,
          "outcomes_used_as_inputs": False}]}

    def analyze(self, vector_id: UUID, query: dict[str, str], persist: bool = False) -> dict[str, Any] | None:
        options = self._options(query)
        try:
            source = self.repository.get_vector(vector_id)
            if source is None: return None
            cutoff = options["historical_cutoff"] or source["observed_at"]
            if cutoff > source["observed_at"]:
                raise WorkspaceQueryError("historical_cutoff cannot be later than the query observation.")
            candidates = self.repository.candidates(source, cutoff, options["same_symbol"], options["same_expiry"])
            ranked = self._rank(source, candidates)[:options["limit"]]
            # Outcomes are deliberately fetched only after ranking has completed.
            outcomes = self.repository.outcomes([row["vector_id"] for row in ranked])
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Similarity evidence is unavailable.") from exc
        filters = {"same_symbol": options["same_symbol"], "same_expiry": options["same_expiry"],
                   "historical_cutoff": cutoff.isoformat()}
        signature = json.dumps({"vector_id": str(vector_id), "model": self.MODEL_VERSION,
          "filters": filters, "limit": options["limit"]}, sort_keys=True)
        run_id = uuid5(self.NAMESPACE, signature)
        matches=[]
        for rank,row in enumerate(ranked,1):
            outcome=outcomes.get(row["vector_id"])
            matches.append({**row,"rank":rank,"outcome":outcome,
              "outcome_id":outcome.get("outcome_id") if outcome else None})
        statistics=self._statistics(matches)
        evidence_state="SUFFICIENT" if statistics["classified_count"]>=self.MINIMUM_CLASSIFIED_OUTCOMES else "INSUFFICIENT"
        result={"run_id":run_id,"model_version":self.MODEL_VERSION,"query_vector":self._lineage(source),
          "filters":filters,"candidate_count":len(candidates),"match_count":len(matches),
          "evidence_state":evidence_state,"matches":matches,"statistics":statistics}
        if persist:
            now=self.clock(); configuration=self.models()["data"][0]
            run={"run_id":run_id,"query_vector_id":vector_id,"query_analytics_id":source["analytics_id"],
              "query_ranking_id":source.get("ranking_id"),"model_version":self.MODEL_VERSION,
              "configuration":configuration,"filters":filters,"result_limit":options["limit"],
              "candidate_count":len(candidates),"match_count":len(matches),"evidence_state":evidence_state,
              "calculated_at":now}
            stored=[]
            for match in matches:
                stored.append({"match_id":uuid5(self.NAMESPACE,f"{run_id}:{match['vector_id']}"),"run_id":run_id,
                  "rank_position":match["rank"],"matched_vector_id":match["vector_id"],
                  "matched_outcome_id":match["outcome_id"],"distance":match["distance"],
                  "similarity_score":match["similarity_score"],"shared_feature_count":match["shared_feature_count"],
                  "missing_feature_count":match["missing_feature_count"],
                  "feature_contributions":match["feature_contributions"]})
            self.repository.persist(run,stored)
        return result

    def run(self, run_id: UUID, matches=False):
        try:
            run=self.repository.get_run(run_id)
            if run is not None and matches: run={**run,"matches":self.repository.get_matches(run_id)}
            return run
        except psycopg.Error as exc: raise WorkspaceUnavailable("Similarity evidence is unavailable.") from exc

    def _rank(self, source, candidates):
        pools={name:[Decimal(row["features"][name]) for row in [source,*candidates]
                     if row.get("features",{}).get(name) is not None] for name in self.FEATURES}
        ranges={name:(min(values),max(values)) for name,values in pools.items() if values}
        ranked=[]
        for candidate in candidates:
            contributions={}; weighted=Decimal(0); weights=Decimal(0); shared=0
            for name,weight in self.FEATURES.items():
                left=source["features"].get(name); right=candidate["features"].get(name)
                if left is None or right is None: continue
                shared+=1; low,high=ranges[name]
                delta=Decimal(0) if high==low else abs(Decimal(left)-Decimal(right))/(high-low)
                contribution=delta*weight; contributions[name]={"distance":float(delta),"weight":float(weight),"weighted_distance":float(contribution)}
                weighted+=contribution; weights+=weight
            if shared<self.MINIMUM_SHARED_FEATURES or weights==0: continue
            distance=weighted/weights
            ranked.append({**self._lineage(candidate),"distance":distance,
              "similarity_score":max(Decimal(0),Decimal(1)-distance),"shared_feature_count":shared,
              "missing_feature_count":len(self.FEATURES)-shared,"feature_contributions":contributions})
        return sorted(ranked,key=lambda row:(row["distance"],row["observed_at"],str(row["vector_id"])))

    @staticmethod
    def _lineage(row):
        return {key:row.get(key) for key in ("vector_id","analytics_id","ranking_id","underlying_symbol","expiry","observed_at")}

    def _statistics(self,matches):
        outcomes=[m["outcome"] for m in matches if m["outcome"]]
        classified=[o for o in outcomes if o.get("won") is not None]
        returns=[Decimal(o["closing_return"]) for o in outcomes if o.get("closing_return") is not None]
        values=lambda field:[Decimal(o[field]) for o in outcomes if o.get(field) is not None]
        average=lambda rows:sum(rows)/len(rows) if rows else None
        mfes=values("maximum_favourable_excursion"); maes=values("maximum_adverse_excursion")
        return {"match_count":len(matches),"usable_outcome_count":len(outcomes),"classified_count":len(classified),
          "historical_win_rate":average([Decimal(1 if o["won"] else 0) for o in classified]),
          "average_closing_return":average(returns),"median_closing_return":median(returns) if returns else None,
          "average_mfe":average(mfes),"average_mae":average(maes),"best_outcome":max(returns) if returns else None,
          "worst_outcome":min(returns) if returns else None}

    def _options(self,query):
        try: limit=int(query.get("limit","20"))
        except ValueError as exc: raise WorkspaceQueryError("limit must be an integer.") from exc
        if not 1<=limit<=self.MAX_LIMIT: raise WorkspaceQueryError(f"limit must be between 1 and {self.MAX_LIMIT}.")
        def boolean(name):
            value=query.get(name,"false").lower()
            if value not in ("true","false"): raise WorkspaceQueryError(f"{name} must be true or false.")
            return value=="true"
        cutoff=None
        if query.get("historical_cutoff"):
            try: cutoff=datetime.fromisoformat(query["historical_cutoff"].replace("Z","+00:00")).replace(tzinfo=None)
            except ValueError as exc: raise WorkspaceQueryError("historical_cutoff must be an ISO timestamp.") from exc
        model=query.get("model_version",self.MODEL_VERSION)
        if model!=self.MODEL_VERSION: raise WorkspaceQueryError(f"model_version must be {self.MODEL_VERSION}.")
        return {"limit":limit,"same_symbol":boolean("same_symbol"),"same_expiry":boolean("same_expiry"),"historical_cutoff":cutoff}
