from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

import psycopg

from services.historical_outcome_repository import HistoricalOutcomeRepository
from services.market_workspace_service import WorkspaceQueryError, WorkspaceUnavailable


class HistoricalOutcomeService:
    MODEL_VERSION="underlying-through-expiry-v1"
    NAMESPACE=UUID("8af78d79-c723-4fe0-a843-c1973fae8c3c")
    TYPES=("NO_FUTURE_DATA","PARTIAL","EXPIRY_COMPLETE")

    def __init__(self,repository=None,clock=datetime.now):
        self.repository=repository or HistoricalOutcomeRepository(); self.clock=clock

    def materialize(self,limit:int|None=None,batch_size:int=500)->dict[str,int]:
        if limit is not None and limit<1: raise ValueError("limit must be greater than zero.")
        if not 1<=batch_size<=1000: raise ValueError("batch_size must be between 1 and 1000.")
        total=0; after_at=after_id=None
        while limit is None or total<limit:
            size=min(batch_size,limit-total) if limit is not None else batch_size
            sources=self.repository.source_vectors(size,after_at,after_id)
            if not sources: break
            for source in sources: self.repository.upsert(self._calculate(source,self.repository.future_vectors(source)))
            total+=len(sources); after_at=sources[-1]["observed_at"]; after_id=sources[-1]["vector_id"]
            if len(sources)<size: break
        return {"source_count":total,"materialized_count":total}

    def list(self,query:dict[str,str],ascending=False)->dict[str,Any]:
        filters,limit=self._filters(query)
        try: rows=self.repository.list_outcomes(filters,limit,ascending)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Historical outcomes are unavailable.") from exc
        return {"data":rows,"count":len(rows),"limit":limit,"model_version":self.MODEL_VERSION}

    def detail(self,outcome_id:UUID):
        try: return self.repository.get_outcome(outcome_id)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Historical outcomes are unavailable.") from exc

    def statistics(self,query:dict[str,str])->dict[str,Any]:
        filters,_=self._filters(query)
        try: data=self.repository.statistics(filters)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Historical outcomes are unavailable.") from exc
        return {"data":data,"model_version":self.MODEL_VERSION}

    def _calculate(self,source,futures):
        entry=source.get("spot_price"); valid=[row for row in futures if row.get("spot_price") is not None]
        terminal=valid[-1] if valid else None
        complete=terminal is not None and terminal["observed_at"].date()==source["expiry"]
        outcome_type="EXPIRY_COMPLETE" if complete else "PARTIAL" if terminal else "NO_FUTURE_DATA"
        terminal_value=terminal["spot_price"] if terminal else None
        def pct(value): return ((Decimal(value)-Decimal(entry))/Decimal(entry))*100 if entry is not None and value is not None and Decimal(entry)!=0 else None
        closing=pct(terminal_value)
        prices=[Decimal(entry),*(Decimal(row["spot_price"]) for row in valid)] if entry is not None and valid else []
        mfe=max(Decimal(0),pct(max(prices))) if prices else None
        mae=min(Decimal(0),pct(min(prices))) if prices else None
        return {"outcome_id":uuid5(self.NAMESPACE,f"{self.MODEL_VERSION}:{source['vector_id']}"),
          "vector_id":source["vector_id"],"analytics_id":source["analytics_id"],"ranking_id":source["ranking_id"],
          "terminal_vector_id":terminal["vector_id"] if terminal else None,"underlying_symbol":source["underlying_symbol"],
          "expiry":source["expiry"],"observed_at":source["observed_at"],"terminal_observed_at":terminal["observed_at"] if terminal else None,
          "model_version":self.MODEL_VERSION,"outcome_type":outcome_type,"entry_value":entry,"terminal_value":terminal_value,
          "forward_return":closing,"maximum_favourable_excursion":mfe,"maximum_adverse_excursion":mae,
          "holding_duration_seconds":int((terminal["observed_at"]-source["observed_at"]).total_seconds()) if terminal else None,
          "expiry_outcome":closing if complete else None,"peak_gain":max(prices)-Decimal(entry) if prices else None,
          "peak_loss":min(prices)-Decimal(entry) if prices else None,"closing_return":closing,
          "won":closing>0 if complete and closing is not None else None,"future_observation_count":len(valid),"materialized_at":self.clock()}

    def _filters(self,query):
        filters={}
        symbol=query.get("symbol")
        if symbol:
            symbol=symbol.strip().upper()
            if len(symbol)>30: raise WorkspaceQueryError("symbol must contain at most 30 characters.")
            filters["symbol"]=symbol
        expiry=query.get("expiry")
        if expiry:
            try: date.fromisoformat(expiry)
            except ValueError as exc: raise WorkspaceQueryError("expiry must be an ISO date.") from exc
            filters["expiry"]=expiry
        for name in ("from","to"):
            value=query.get(name)
            if value:
                try: datetime.fromisoformat(value.replace("Z","+00:00"))
                except ValueError as exc: raise WorkspaceQueryError(f"{name} must be an ISO timestamp.") from exc
                filters[name]=value
        outcome_type=query.get("outcome_type")
        if outcome_type:
            outcome_type=outcome_type.upper()
            if outcome_type not in self.TYPES: raise WorkspaceQueryError(f"outcome_type must be one of: {', '.join(self.TYPES)}.")
            filters["outcome_type"]=outcome_type
        try: limit=int(query.get("limit","50"))
        except ValueError as exc: raise WorkspaceQueryError("limit must be an integer.") from exc
        if not 1<=limit<=200: raise WorkspaceQueryError("limit must be between 1 and 200.")
        return filters,limit
