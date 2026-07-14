from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection


class NewsEventRepository:
    def upsert(self,event:dict[str,Any])->None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO market_events
                  (event_id,schema_version,source,source_event_id,event_type,title,summary,published_at,event_at,
                   is_scheduled,market_wide,source_reference,event_metadata,sanitized_text,raw_source_checksum,
                   deduplication_identity,ingested_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                  ON CONFLICT (event_id) DO UPDATE SET title=EXCLUDED.title,summary=EXCLUDED.summary,
                   published_at=EXCLUDED.published_at,event_at=EXCLUDED.event_at,is_scheduled=EXCLUDED.is_scheduled,
                   market_wide=EXCLUDED.market_wide,source_reference=EXCLUDED.source_reference,
                   event_metadata=EXCLUDED.event_metadata,sanitized_text=EXCLUDED.sanitized_text,
                   raw_source_checksum=EXCLUDED.raw_source_checksum,ingested_at=EXCLUDED.ingested_at""",
                  (event["event_id"],event["schema_version"],event["source"],event["source_event_id"],
                   event["event_type"],event["title"],event["summary"],event["published_at"],event["event_at"],
                   event["is_scheduled"],event["market_wide"],event["source_reference"],Jsonb(event["metadata"]),
                   event["sanitized_text"],event["raw_source_checksum"],event["deduplication_identity"],event["ingested_at"]))
                cursor.execute("DELETE FROM market_event_symbols WHERE event_id=%s",(event["event_id"],))
                cursor.execute("DELETE FROM market_event_sectors WHERE event_id=%s",(event["event_id"],))
                cursor.executemany("INSERT INTO market_event_symbols VALUES (%s,%s)",[(event["event_id"],s) for s in event["symbols"]])
                cursor.executemany("INSERT INTO market_event_sectors VALUES (%s,%s)",[(event["event_id"],s) for s in event["sectors"]])
            connection.commit()

    def events(self)->list[dict[str,Any]]:
        return self._fetch("""SELECT e.*,
          COALESCE((SELECT jsonb_agg(symbol ORDER BY symbol) FROM market_event_symbols s WHERE s.event_id=e.event_id),'[]') symbols,
          COALESCE((SELECT jsonb_agg(sector ORDER BY sector) FROM market_event_sectors s WHERE s.event_id=e.event_id),'[]') sectors
          FROM market_events e ORDER BY COALESCE(e.event_at,e.published_at),e.event_id""",())

    def vectors(self)->list[dict[str,Any]]:
        return self._fetch("""SELECT v.vector_id,v.underlying_symbol,v.expiry,v.observed_at,
          o.outcome_id,o.terminal_observed_at FROM feature_store_vectors v
          LEFT JOIN historical_outcomes o ON o.vector_id=v.vector_id
          ORDER BY v.observed_at,v.vector_id""",())

    def similarity_runs(self)->list[dict[str,Any]]:
        return self._fetch("SELECT run_id,query_vector_id FROM similarity_runs ORDER BY run_id",())

    def opportunities(self)->list[dict[str,Any]]:
        return self._fetch("SELECT opportunity_id,query_vector_id,underlying_symbol,expiry,observed_at FROM trade_opportunities ORDER BY opportunity_id",())

    def replace_vector_links(self,links:list[dict[str,Any]])->None:
        self._replace("market_event_vector_context","""INSERT INTO market_event_vector_context
          (event_id,vector_id,outcome_id,context_type,predictive_eligible,seconds_from_observation)
          VALUES (%s,%s,%s,%s,%s,%s)""",[(x["event_id"],x["vector_id"],x["outcome_id"],x["context_type"],x["predictive_eligible"],x["seconds"]) for x in links])

    def replace_similarity_links(self,links:list[tuple])->None:
        self._replace("market_event_similarity_context","INSERT INTO market_event_similarity_context VALUES (%s,%s,%s)",links)

    def replace_opportunity_links(self,links:list[dict[str,Any]])->None:
        self._replace("market_event_opportunity_context","""INSERT INTO market_event_opportunity_context
          (event_id,opportunity_id,context_type,seconds_from_observation) VALUES (%s,%s,%s,%s)""",
          [(x["event_id"],x["opportunity_id"],x["context_type"],x["seconds"]) for x in links])

    def list(self,filters:dict[str,Any],limit:int)->list[dict[str,Any]]:
        clauses=["TRUE"]; parameters=[]
        if filters.get("symbol"): clauses.append("(e.market_wide OR EXISTS(SELECT 1 FROM market_event_symbols s WHERE s.event_id=e.event_id AND s.symbol=%s))"); parameters.append(filters["symbol"])
        if filters.get("sector"): clauses.append("EXISTS(SELECT 1 FROM market_event_sectors s WHERE s.event_id=e.event_id AND s.sector=%s)"); parameters.append(filters["sector"])
        for key,predicate in (("event_type","e.event_type=%s"),("scheduled","e.is_scheduled=%s"),("market_wide","e.market_wide=%s"),("from","COALESCE(e.event_at,e.published_at)>=%s"),("to","COALESCE(e.event_at,e.published_at)<=%s")):
            if key in filters: clauses.append(predicate); parameters.append(filters[key])
        parameters.append(limit)
        return self._fetch(f"""SELECT e.*,
          COALESCE((SELECT jsonb_agg(symbol ORDER BY symbol) FROM market_event_symbols s WHERE s.event_id=e.event_id),'[]') symbols,
          COALESCE((SELECT jsonb_agg(sector ORDER BY sector) FROM market_event_sectors s WHERE s.event_id=e.event_id),'[]') sectors
          FROM market_events e WHERE {' AND '.join(clauses)}
          ORDER BY COALESCE(e.event_at,e.published_at) DESC,e.event_id DESC LIMIT %s""",tuple(parameters))

    def get(self,event_id:UUID)->dict[str,Any]|None:
        rows=self._fetch("""SELECT e.*,
          COALESCE((SELECT jsonb_agg(symbol ORDER BY symbol) FROM market_event_symbols s WHERE s.event_id=e.event_id),'[]') symbols,
          COALESCE((SELECT jsonb_agg(sector ORDER BY sector) FROM market_event_sectors s WHERE s.event_id=e.event_id),'[]') sectors
          FROM market_events e WHERE e.event_id=%s""",(event_id,))
        return rows[0] if rows else None

    def vector_context(self,vector_id:UUID)->list[dict[str,Any]]:
        return self._fetch("""SELECT c.*,to_jsonb(e) event,
          COALESCE((SELECT jsonb_agg(symbol ORDER BY symbol) FROM market_event_symbols s WHERE s.event_id=e.event_id),'[]') symbols
          FROM market_event_vector_context c JOIN market_events e USING(event_id)
          WHERE c.vector_id=%s ORDER BY COALESCE(e.event_at,e.published_at),e.event_id,c.context_type""",(vector_id,))

    def opportunity_context(self,opportunity_id:UUID)->list[dict[str,Any]]:
        return self._fetch("""SELECT c.*,to_jsonb(e) event,
          COALESCE((SELECT jsonb_agg(symbol ORDER BY symbol) FROM market_event_symbols s WHERE s.event_id=e.event_id),'[]') symbols
          FROM market_event_opportunity_context c JOIN market_events e USING(event_id)
          WHERE c.opportunity_id=%s ORDER BY CASE c.context_type WHEN 'UPCOMING_RISK' THEN 0 ELSE 1 END,
          abs(c.seconds_from_observation),e.event_id""",(opportunity_id,))

    def opportunity_exists(self,opportunity_id:UUID)->bool:
        return bool(self._fetch("SELECT 1 present FROM trade_opportunities WHERE opportunity_id=%s",(opportunity_id,)))

    def vector_exists(self,vector_id:UUID)->bool:
        return bool(self._fetch("SELECT 1 present FROM feature_store_vectors WHERE vector_id=%s",(vector_id,)))

    @staticmethod
    def _replace(table:str,query:str,rows:list[tuple])->None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table}")
                if rows: cursor.executemany(query,rows)
            connection.commit()

    @staticmethod
    def _fetch(query:str,parameters:tuple[Any,...])->list[dict[str,Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query,parameters); columns=[column.name for column in cursor.description or ()]
                return [dict(zip(columns,row,strict=True)) for row in cursor.fetchall()]
