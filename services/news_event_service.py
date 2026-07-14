from __future__ import annotations

import hashlib
import json
from datetime import date,datetime,timedelta
from typing import Any
from uuid import UUID,uuid5

import psycopg

from services.error_sanitizer import sanitize_error_message
from services.market_workspace_service import WorkspaceQueryError,WorkspaceUnavailable
from services.news_event_repository import NewsEventRepository


class NewsEventService:
    SCHEMA_VERSION="market-event-v1"
    NAMESPACE=UUID("cbec9369-95bf-45b7-9a2e-90cf8b5737f7")
    TYPES=("CORPORATE_EARNINGS","CORPORATE_ACTION","EXCHANGE_ANNOUNCEMENT","MACROECONOMIC","RBI","SECTOR","MARKET_WIDE","COMPANY_NEWS")
    BEFORE_WINDOW=timedelta(days=7); EXPIRY_WINDOW=timedelta(days=2); UPCOMING_WINDOW=timedelta(days=14)

    def __init__(self,repository=None,clock=datetime.now): self.repository=repository or NewsEventRepository(); self.clock=clock

    def import_records(self,provider,limit:int=500)->dict[str,int]:
        if not 1<=limit<=5000: raise ValueError("limit must be between 1 and 5000.")
        records=provider.records(limit)
        for record in records: self.repository.upsert(self._normalize(record))
        return {"source_count":len(records),"imported_count":len(records)}

    def link_historical(self,limit:int=5000)->dict[str,int]:
        events=self.repository.events(); vectors=self.repository.vectors()
        if len(vectors)>limit: raise ValueError(f"Feature vector count exceeds the {limit} link limit.")
        links=[]
        for vector in vectors:
            observation=vector["observed_at"]; expiry=datetime.combine(vector["expiry"],datetime.min.time())
            for event in events:
                if not self._relevant(event,vector["underlying_symbol"]): continue
                effective=event["event_at"] or event["published_at"]; published=event["published_at"]
                seconds=int((effective-observation).total_seconds())
                if observation-self.BEFORE_WINDOW<=effective<=observation and published is not None and published<=observation:
                    links.append(self._link(event,vector,"BEFORE_OBSERVATION",True,seconds))
                terminal=vector.get("terminal_observed_at")
                if terminal and observation<effective<=terminal:
                    links.append(self._link(event,vector,"DURING_HOLDING",False,seconds))
                if abs(effective-expiry)<=self.EXPIRY_WINDOW:
                    links.append(self._link(event,vector,"NEAR_EXPIRY",published is not None and published<=observation,seconds))
        self.repository.replace_vector_links(links)
        predictive={(link["event_id"],link["vector_id"]) for link in links if link["predictive_eligible"]}
        similarity=[(event_id,run["run_id"],run["query_vector_id"]) for run in self.repository.similarity_runs()
          for event_id,vector_id in predictive if vector_id==run["query_vector_id"]]
        self.repository.replace_similarity_links(similarity)
        return {"vector_count":len(vectors),"link_count":len(links),"similarity_link_count":len(similarity)}

    def link_opportunities(self,limit:int=1000)->dict[str,int]:
        events=self.repository.events(); opportunities=self.repository.opportunities()
        if len(opportunities)>limit: raise ValueError(f"Opportunity count exceeds the {limit} link limit.")
        links=[]
        for opportunity in opportunities:
            observation=opportunity["observed_at"]
            for event in events:
                if not self._relevant(event,opportunity["underlying_symbol"]): continue
                effective=event["event_at"] or event["published_at"]; published=event["published_at"]
                if published is None or published>observation: continue
                seconds=int((effective-observation).total_seconds())
                if observation-self.BEFORE_WINDOW<=effective<=observation:
                    links.append({"event_id":event["event_id"],"opportunity_id":opportunity["opportunity_id"],"context_type":"RECENT_CONTEXT","seconds":seconds})
                end=min(observation+self.UPCOMING_WINDOW,datetime.combine(opportunity["expiry"],datetime.max.time()))
                if observation<effective<=end:
                    links.append({"event_id":event["event_id"],"opportunity_id":opportunity["opportunity_id"],"context_type":"UPCOMING_RISK","seconds":seconds})
        self.repository.replace_opportunity_links(links)
        return {"opportunity_count":len(opportunities),"link_count":len(links)}

    def list(self,query:dict[str,str])->dict[str,Any]:
        filters,limit=self._filters(query)
        try: rows=self.repository.list(filters,limit)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Persisted event intelligence is unavailable.") from exc
        return {"data":rows,"count":len(rows),"limit":limit,"schema_version":self.SCHEMA_VERSION}

    def detail(self,event_id:UUID):
        try: return self.repository.get(event_id)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Persisted event intelligence is unavailable.") from exc

    def context(self,query:dict[str,str])->dict[str,Any]|None:
        vector_value=query.get("vector_id")
        if vector_value:
            try: vector_id=UUID(vector_value)
            except ValueError as exc: raise WorkspaceQueryError("vector_id must be a valid UUID.") from exc
            try:
                if not self.repository.vector_exists(vector_id): return None
                rows=self.repository.vector_context(vector_id)
            except psycopg.Error as exc: raise WorkspaceUnavailable("Persisted event intelligence is unavailable.") from exc
            counts={name:sum(row["context_type"]==name for row in rows) for name in ("BEFORE_OBSERVATION","DURING_HOLDING","NEAR_EXPIRY")}
            return {"vector_id":vector_id,"events":rows,"counts":counts,"predictive_event_count":sum(row["predictive_eligible"] for row in rows),
              "leakage_policy":"Only events published by the observation timestamp are predictive inputs."}
        if query.get("symbol"): return self.list(query)
        raise WorkspaceQueryError("context requires vector_id or symbol.")

    def opportunity_context(self,opportunity_id:UUID)->dict[str,Any]|None:
        try:
            if not self.repository.opportunity_exists(opportunity_id): return None
            rows=self.repository.opportunity_context(opportunity_id)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Persisted event intelligence is unavailable.") from exc
        upcoming=[row for row in rows if row["context_type"]=="UPCOMING_RISK"]
        reasons_against=[f"Scheduled {row['event']['event_type']} event in {max(0,row['seconds_from_observation']//86400)} days: {row['event']['title']}" for row in upcoming if row["event"]["is_scheduled"]]
        return {"opportunity_id":opportunity_id,"events":rows,"recent_event_count":sum(row["context_type"]=="RECENT_CONTEXT" for row in rows),
          "upcoming_event_count":len(upcoming),"reasons_for":[],"reasons_against":reasons_against,
          "limitations":["Event context does not alter opportunity eligibility, score, entry, stop, targets, win rate, or expected value.","No sentiment or inferred company relationship is used."]}

    def _normalize(self,record):
        required=("source","source_event_id","event_type","title","summary","is_scheduled","market_wide")
        if any(key not in record for key in required): raise ValueError("Event record is missing a required field.")
        event_type=str(record["event_type"]).upper()
        if event_type not in self.TYPES: raise ValueError(f"Unsupported event_type: {event_type}.")
        if not isinstance(record["is_scheduled"],bool) or not isinstance(record["market_wide"],bool):
            raise ValueError("is_scheduled and market_wide must be booleans.")
        published=self._timestamp(record.get("published_at"),"published_at"); event_at=self._timestamp(record.get("event_at"),"event_at")
        if published is None and event_at is None: raise ValueError("published_at or event_at is required.")
        symbols=sorted(set(self._labels(record.get("affected_symbols",[]),"symbol")))
        sectors=sorted(set(self._labels(record.get("affected_sectors",[]),"sector")))
        source=self._text(record["source"],100); source_id=self._text(record["source_event_id"],200)
        title=self._text(record["title"],500); summary=self._text(record["summary"],4000)
        canonical=json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=True)
        checksum=hashlib.sha256(canonical.encode()).hexdigest()
        identity=hashlib.sha256(f"{source}|{source_id}|{event_type}".encode()).hexdigest()
        metadata=self._sanitize_value(record.get("metadata",{}))
        return {"event_id":uuid5(self.NAMESPACE,f"{self.SCHEMA_VERSION}:{identity}"),"schema_version":self.SCHEMA_VERSION,
          "source":source,"source_event_id":source_id,"event_type":event_type,"title":title,"summary":summary,
          "published_at":published,"event_at":event_at,"is_scheduled":bool(record["is_scheduled"]),
          "market_wide":bool(record["market_wide"]),"source_reference":self._text(record.get("source_reference",""),1000) or None,
          "metadata":metadata,"sanitized_text":f"{title}\n{summary}","raw_source_checksum":checksum,
          "deduplication_identity":identity,"ingested_at":self.clock(),"symbols":symbols,"sectors":sectors}

    @staticmethod
    def _link(event,vector,context,predictive,seconds): return {"event_id":event["event_id"],"vector_id":vector["vector_id"],"outcome_id":vector.get("outcome_id"),"context_type":context,"predictive_eligible":predictive,"seconds":seconds}
    @staticmethod
    def _relevant(event,symbol): return bool(event["market_wide"] or symbol in event["symbols"])
    @staticmethod
    def _timestamp(value,name):
        if value in (None,""): return None
        try: return datetime.fromisoformat(str(value).replace("Z","+00:00")).replace(tzinfo=None)
        except ValueError as exc: raise ValueError(f"{name} must be an ISO timestamp.") from exc
    @staticmethod
    def _text(value,limit): return sanitize_error_message(str(value))[:limit] if str(value).strip() else ""
    @staticmethod
    def _labels(values,name):
        if not isinstance(values,list): raise ValueError(f"affected_{name}s must be an array.")
        result=[]
        for value in values:
            label=str(value).strip().upper()
            if not label or len(label)>100: raise ValueError(f"Invalid affected {name}.")
            result.append(label)
        return result
    def _sanitize_value(self,value):
        if isinstance(value,dict): return {str(k)[:100]:self._sanitize_value(v) for k,v in value.items() if str(k).lower() not in ("password","api_key","access_token","authorization")}
        if isinstance(value,list): return [self._sanitize_value(v) for v in value[:100]]
        if isinstance(value,str): return self._text(value,1000)
        if value is None or isinstance(value,(bool,int,float)): return value
        return self._text(value,1000)

    def _filters(self,query):
        filters={}
        for key in ("symbol","sector"):
            if query.get(key):
                value=query[key].strip().upper()
                if not value or len(value)>100: raise WorkspaceQueryError(f"{key} must contain 1 to 100 characters.")
                filters[key]=value
        if query.get("event_type"):
            value=query["event_type"].upper()
            if value not in self.TYPES: raise WorkspaceQueryError(f"event_type must be one of: {', '.join(self.TYPES)}.")
            filters["event_type"]=value
        for key in ("scheduled","market_wide"):
            if key in query:
                value=query[key].lower()
                if value not in ("true","false"): raise WorkspaceQueryError(f"{key} must be true or false.")
                filters[key]=value=="true"
        for key in ("from","to"):
            if query.get(key):
                try: filters[key]=datetime.fromisoformat(query[key].replace("Z","+00:00")).replace(tzinfo=None)
                except ValueError as exc: raise WorkspaceQueryError(f"{key} must be an ISO timestamp.") from exc
        try: limit=int(query.get("limit","50"))
        except ValueError as exc: raise WorkspaceQueryError("limit must be an integer.") from exc
        if not 1<=limit<=200: raise WorkspaceQueryError("limit must be between 1 and 200.")
        return filters,limit
