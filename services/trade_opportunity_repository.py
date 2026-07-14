from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection


class TradeOpportunityRepository:
    def similarity_runs(self, run_id: UUID | None = None, limit: int = 100) -> list[dict[str, Any]]:
        clause="WHERE r.run_id=%s" if run_id else ""
        parameters=(run_id,) if run_id else (limit,)
        limit_clause="" if run_id else "LIMIT %s"
        return self._fetch(f"""SELECT r.*,v.underlying_symbol,v.expiry,v.observed_at,
            f.numeric_value AS spot_price FROM similarity_runs r
            JOIN feature_store_vectors v ON v.vector_id=r.query_vector_id
            LEFT JOIN feature_store_values f ON f.vector_id=v.vector_id AND f.feature_name='spot_price'
            {clause} ORDER BY r.calculated_at DESC,r.run_id {limit_clause}""",parameters)

    def similarity_matches(self, run_id: UUID) -> list[dict[str, Any]]:
        return self._fetch("""SELECT m.*,o.outcome_type,o.entry_value,o.closing_return,
            o.maximum_favourable_excursion,o.maximum_adverse_excursion,o.won
            FROM similarity_matches m LEFT JOIN historical_outcomes o ON o.outcome_id=m.matched_outcome_id
            WHERE m.run_id=%s ORDER BY m.rank_position""",(run_id,))

    def persist(self, run: dict[str, Any], opportunities: list[dict[str, Any]]) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO trade_opportunity_runs
                  (run_id,model_version,source_run_ids,opportunity_count,eligible_count,calculated_at)
                  VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (run_id) DO UPDATE SET
                  opportunity_count=EXCLUDED.opportunity_count,eligible_count=EXCLUDED.eligible_count,
                  calculated_at=EXCLUDED.calculated_at""",
                  (run["run_id"],run["model_version"],Jsonb(run["source_run_ids"]),run["opportunity_count"],
                   run["eligible_count"],run["calculated_at"]))
                cursor.execute("DELETE FROM trade_opportunities WHERE run_id=%s",(run["run_id"],))
                for item in opportunities:
                    cursor.execute("""INSERT INTO trade_opportunities
                      (opportunity_id,run_id,similarity_run_id,query_vector_id,query_analytics_id,
                       query_ranking_id,underlying_symbol,expiry,observed_at,model_version,state,direction,
                       rank_position,opportunity_score,evidence_quality,match_count,classified_count,
                       entry_zone_low,entry_zone_high,stop_zone,target_zones,expected_value,
                       historical_win_rate,risk_reward,reasons_for,reasons_against)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                      (item["opportunity_id"],run["run_id"],item["similarity_run_id"],item["query_vector_id"],
                       item["query_analytics_id"],item["query_ranking_id"],item["underlying_symbol"],item["expiry"],
                       item["observed_at"],item["model_version"],item["state"],item["direction"],item["rank_position"],
                       item["opportunity_score"],item["evidence_quality"],item["match_count"],item["classified_count"],
                       item["entry_zone_low"],item["entry_zone_high"],item["stop_zone"],Jsonb(item["target_zones"]),
                       item["expected_value"],item["historical_win_rate"],item["risk_reward"],
                       Jsonb(item["reasons_for"]),Jsonb(item["reasons_against"])))
                    cursor.executemany("""INSERT INTO trade_opportunity_evidence
                      (opportunity_id,similarity_match_id,matched_vector_id,matched_outcome_id)
                      VALUES (%s,%s,%s,%s)""",[(item["opportunity_id"],e["similarity_match_id"],
                      e["matched_vector_id"],e["matched_outcome_id"]) for e in item["evidence"]])
            connection.commit()

    def list(self, state: str | None, symbol: str | None, limit: int) -> list[dict[str, Any]]:
        clauses=["TRUE"]; parameters=[]
        if state: clauses.append("o.state=%s"); parameters.append(state)
        if symbol: clauses.append("o.underlying_symbol=%s"); parameters.append(symbol)
        parameters.append(limit)
        return self._fetch(f"""SELECT o.* FROM trade_opportunities o
          WHERE {' AND '.join(clauses)} ORDER BY
          CASE o.state WHEN 'ELIGIBLE' THEN 0 WHEN 'NO_OPPORTUNITY' THEN 1 ELSE 2 END,
          o.opportunity_score DESC NULLS LAST,o.observed_at DESC,o.opportunity_id LIMIT %s""",tuple(parameters))

    def get(self, opportunity_id: UUID) -> dict[str, Any] | None:
        rows=self._fetch("SELECT * FROM trade_opportunities WHERE opportunity_id=%s",(opportunity_id,))
        if not rows: return None
        item=rows[0]; item["evidence"]=self._fetch("""SELECT e.*,m.rank_position,m.similarity_score,
          m.shared_feature_count,v.underlying_symbol,v.expiry,v.observed_at,to_jsonb(o) outcome
          FROM trade_opportunity_evidence e JOIN similarity_matches m ON m.match_id=e.similarity_match_id
          JOIN feature_store_vectors v ON v.vector_id=e.matched_vector_id
          JOIN historical_outcomes o ON o.outcome_id=e.matched_outcome_id
          WHERE e.opportunity_id=%s ORDER BY m.rank_position""",(opportunity_id,))
        return item

    @staticmethod
    def _fetch(query: str, parameters: tuple[Any,...]) -> list[dict[str,Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query,parameters); columns=[column.name for column in cursor.description or ()]
                return [dict(zip(columns,row,strict=True)) for row in cursor.fetchall()]
