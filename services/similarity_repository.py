from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection


class SimilarityRepository:
    """Database reads and persistence for reproducible similarity analyses."""

    def get_vector(self, vector_id: UUID) -> dict[str, Any] | None:
        rows = self._fetch(
            """SELECT v.*, COALESCE(jsonb_object_agg(f.feature_name,f.numeric_value)
                       FILTER (WHERE f.feature_name IS NOT NULL),'{}'::jsonb) features
               FROM feature_store_vectors v LEFT JOIN feature_store_values f USING(vector_id)
               WHERE v.vector_id=%s GROUP BY v.vector_id""", (vector_id,))
        return rows[0] if rows else None

    def candidates(self, query: dict[str, Any], cutoff, same_symbol: bool, same_expiry: bool) -> list[dict[str, Any]]:
        clauses = ["v.vector_id<>%s", "v.observed_at<=%s"]
        parameters: list[Any] = [query["vector_id"], cutoff]
        if same_symbol:
            clauses.append("v.underlying_symbol=%s"); parameters.append(query["underlying_symbol"])
        if same_expiry:
            clauses.append("v.expiry=%s"); parameters.append(query["expiry"])
        return self._fetch(
            f"""SELECT v.*, COALESCE(jsonb_object_agg(f.feature_name,f.numeric_value)
                       FILTER (WHERE f.feature_name IS NOT NULL),'{{}}'::jsonb) features
                FROM feature_store_vectors v LEFT JOIN feature_store_values f USING(vector_id)
                WHERE {' AND '.join(clauses)} GROUP BY v.vector_id
                ORDER BY v.observed_at,v.vector_id""", tuple(parameters))

    def outcomes(self, vector_ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
        if not vector_ids: return {}
        rows = self._fetch(
            """SELECT * FROM historical_outcomes WHERE vector_id=ANY(%s)
               ORDER BY vector_id, materialized_at DESC""", (vector_ids,))
        return {row["vector_id"]: row for row in rows}

    def persist(self, run: dict[str, Any], matches: list[dict[str, Any]]) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO similarity_runs
                       (run_id,query_vector_id,query_analytics_id,query_ranking_id,model_version,
                        configuration,filters,result_limit,candidate_count,match_count,evidence_state,calculated_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (run_id) DO UPDATE SET candidate_count=EXCLUDED.candidate_count,
                         match_count=EXCLUDED.match_count,evidence_state=EXCLUDED.evidence_state,
                         calculated_at=EXCLUDED.calculated_at""",
                    (run["run_id"],run["query_vector_id"],run["query_analytics_id"],run["query_ranking_id"],
                     run["model_version"],Jsonb(run["configuration"]),Jsonb(run["filters"]),run["result_limit"],
                     run["candidate_count"],run["match_count"],run["evidence_state"],run["calculated_at"]))
                cursor.execute("DELETE FROM similarity_matches WHERE run_id=%s", (run["run_id"],))
                cursor.executemany(
                    """INSERT INTO similarity_matches
                       (match_id,run_id,rank_position,matched_vector_id,matched_outcome_id,distance,
                        similarity_score,shared_feature_count,missing_feature_count,feature_contributions)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    [(match["match_id"],match["run_id"],match["rank_position"],match["matched_vector_id"],
                      match["matched_outcome_id"],match["distance"],match["similarity_score"],
                      match["shared_feature_count"],match["missing_feature_count"],Jsonb(match["feature_contributions"]))
                     for match in matches])
            connection.commit()

    def get_run(self, run_id: UUID) -> dict[str, Any] | None:
        rows=self._fetch("SELECT * FROM similarity_runs WHERE run_id=%s",(run_id,))
        return rows[0] if rows else None

    def get_matches(self, run_id: UUID) -> list[dict[str, Any]]:
        return self._fetch(
            """SELECT m.*,v.underlying_symbol,v.expiry,v.observed_at,v.analytics_id,v.ranking_id,
                      to_jsonb(o) AS outcome
               FROM similarity_matches m JOIN feature_store_vectors v ON v.vector_id=m.matched_vector_id
               LEFT JOIN historical_outcomes o ON o.outcome_id=m.matched_outcome_id
               WHERE m.run_id=%s ORDER BY m.rank_position""",(run_id,))

    @staticmethod
    def _fetch(query: str, parameters: tuple[Any,...]) -> list[dict[str,Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query,parameters); columns=[column.name for column in cursor.description or ()]
                return [dict(zip(columns,row,strict=True)) for row in cursor.fetchall()]
