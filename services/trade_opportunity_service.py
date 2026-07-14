from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

import psycopg

from services.market_workspace_service import WorkspaceQueryError, WorkspaceUnavailable
from services.trade_opportunity_repository import TradeOpportunityRepository


class TradeOpportunityService:
    MODEL_VERSION="historical-long-opportunity-v1"
    NAMESPACE=UUID("df1f89f0-b8eb-4ae7-88d7-7a99fe284bf8")
    MINIMUM_CLASSIFIED=5
    STATES=("ELIGIBLE","INSUFFICIENT_EVIDENCE","NO_OPPORTUNITY")

    def __init__(self,repository=None,clock=datetime.now):
        self.repository=repository or TradeOpportunityRepository(); self.clock=clock

    def materialize(self,similarity_run_id:UUID|None=None,limit:int=100)->dict[str,Any]:
        if not 1<=limit<=500: raise ValueError("limit must be between 1 and 500.")
        sources=self.repository.similarity_runs(similarity_run_id,limit)
        if similarity_run_id and not sources: return {"run_id":None,"opportunity_count":0,"eligible_count":0}
        items=[self._calculate(source,self.repository.similarity_matches(source["run_id"])) for source in sources]
        items.sort(key=lambda item:(0 if item["state"]=="ELIGIBLE" else 1 if item["state"]=="NO_OPPORTUNITY" else 2,
          -(item["opportunity_score"] or Decimal(0)),-item["observed_at"].timestamp(),str(item["opportunity_id"])))
        for rank,item in enumerate(items,1): item["rank_position"]=rank
        source_ids=sorted(str(source["run_id"]) for source in sources)
        signature=json.dumps({"model":self.MODEL_VERSION,"source_run_ids":source_ids},sort_keys=True)
        run={"run_id":uuid5(self.NAMESPACE,signature),"model_version":self.MODEL_VERSION,
          "source_run_ids":source_ids,"opportunity_count":len(items),
          "eligible_count":sum(item["state"]=="ELIGIBLE" for item in items),"calculated_at":self.clock()}
        self.repository.persist(run,items)
        return {key:run[key] for key in ("run_id","opportunity_count","eligible_count")}

    def list(self,query:dict[str,str])->dict[str,Any]:
        state=query.get("state") or None
        if state:
            state=state.upper()
            if state not in self.STATES: raise WorkspaceQueryError(f"state must be one of: {', '.join(self.STATES)}.")
        symbol=(query.get("symbol") or "").strip().upper() or None
        if symbol and len(symbol)>30: raise WorkspaceQueryError("symbol must contain at most 30 characters.")
        try: limit=int(query.get("limit","50"))
        except ValueError as exc: raise WorkspaceQueryError("limit must be an integer.") from exc
        if not 1<=limit<=200: raise WorkspaceQueryError("limit must be between 1 and 200.")
        try: rows=self.repository.list(state,symbol,limit)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Trade opportunities are unavailable.") from exc
        return {"data":rows,"count":len(rows),"limit":limit,"model_version":self.MODEL_VERSION}

    def detail(self,opportunity_id:UUID):
        try: return self.repository.get(opportunity_id)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Trade opportunities are unavailable.") from exc

    def _calculate(self,source,matches):
        classified=[m for m in matches if m.get("outcome_type")=="EXPIRY_COMPLETE" and m.get("won") is not None
          and all(m.get(field) is not None for field in ("closing_return","maximum_favourable_excursion","maximum_adverse_excursion"))]
        similarities=[Decimal(m["similarity_score"]) for m in classified]
        shared=[Decimal(m["shared_feature_count"]) for m in classified]
        evidence_quality=min(Decimal(1),Decimal(len(classified))/Decimal(20))*Decimal("0.5")
        if classified:
            evidence_quality+=sum(similarities)/len(similarities)*Decimal("0.3")
            evidence_quality+=min(Decimal(1),(sum(shared)/len(shared))/Decimal(12))*Decimal("0.2")
        base={"opportunity_id":uuid5(self.NAMESPACE,f"{self.MODEL_VERSION}:{source['run_id']}"),
          "similarity_run_id":source["run_id"],"query_vector_id":source["query_vector_id"],
          "query_analytics_id":source["query_analytics_id"],"query_ranking_id":source["query_ranking_id"],
          "underlying_symbol":source["underlying_symbol"],"expiry":source["expiry"],"observed_at":source["observed_at"],
          "model_version":self.MODEL_VERSION,"evidence_quality":evidence_quality,"match_count":len(matches),
          "classified_count":len(classified),"rank_position":0,"evidence":[{"similarity_match_id":m["match_id"],
          "matched_vector_id":m["matched_vector_id"],"matched_outcome_id":m["matched_outcome_id"]} for m in classified]}
        empty={"direction":None,"opportunity_score":None,"entry_zone_low":None,"entry_zone_high":None,
          "stop_zone":None,"target_zones":[],"expected_value":None,"historical_win_rate":None,"risk_reward":None}
        if len(classified)<self.MINIMUM_CLASSIFIED or source.get("spot_price") is None:
            return {**base,**empty,"state":"INSUFFICIENT_EVIDENCE","reasons_for":[],
              "reasons_against":[f"At least {self.MINIMUM_CLASSIFIED} expiry-classified outcomes and a persisted query spot are required."]}
        closing=[Decimal(m["closing_return"]) for m in classified]; mfe=[Decimal(m["maximum_favourable_excursion"]) for m in classified]
        mae=[Decimal(m["maximum_adverse_excursion"]) for m in classified]; spot=Decimal(source["spot_price"])
        expected=sum(closing)/len(closing); win_rate=sum(Decimal(1 if m["won"] else 0) for m in classified)/len(classified)
        entry_low=spot*(Decimal(1)+self._quantile(mae,Decimal("0.25"))/100); entry_high=spot
        stop=spot*(Decimal(1)+self._quantile(mae,Decimal("0.10"))/100)
        targets=[spot*(Decimal(1)+self._quantile(mfe,q)/100) for q in (Decimal("0.50"),Decimal("0.75"))]
        midpoint=(entry_low+entry_high)/2; downside=midpoint-stop; upside=targets[0]-midpoint
        risk_reward=upside/downside if downside>0 and upside>0 else None
        eligible=expected>0 and win_rate>=Decimal("0.5") and risk_reward is not None and stop<entry_low<entry_high<targets[0]<targets[1]
        if not eligible:
            return {**base,**empty,"state":"NO_OPPORTUNITY","expected_value":expected,
              "historical_win_rate":win_rate,"reasons_for":[],"reasons_against":["Persisted evidence does not satisfy the positive-expectancy long-opportunity policy."]}
        score=(sum(similarities)/len(similarities)*Decimal(40)+win_rate*Decimal(30)+
          min(Decimal(1),max(Decimal(0),expected)/Decimal(10))*Decimal(20)+evidence_quality*Decimal(10))
        return {**base,"state":"ELIGIBLE","direction":"LONG","opportunity_score":score,
          "entry_zone_low":entry_low,"entry_zone_high":entry_high,"stop_zone":stop,"target_zones":targets,
          "expected_value":expected,"historical_win_rate":win_rate,"risk_reward":risk_reward,
          "reasons_for":[f"{len(classified)} expiry-classified historical matches.","Positive average closing return and majority historical wins."],
          "reasons_against":["Zones reference underlying spot, not option premium.","Historical evidence does not guarantee future results."]}

    @staticmethod
    def _quantile(values:list[Decimal],quantile:Decimal)->Decimal:
        ordered=sorted(values); index=int((len(ordered)-1)*quantile)
        return ordered[index]
