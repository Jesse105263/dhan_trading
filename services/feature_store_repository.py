from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from services.database import get_connection


class FeatureStoreRepository:
    """Persistence boundary for versioned feature vectors and their exact lineage."""

    def source_observations(self, limit: int, after_at=None, after_id=None) -> list[dict[str, Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT to_jsonb(a) AS analytics, to_jsonb(c) AS changes,
                              to_jsonb(r) AS ranking
                       FROM option_chain_analytics a
                       LEFT JOIN option_analytics_changes c ON c.current_analytics_id=a.analytics_id
                       LEFT JOIN LATERAL (
                           SELECT ranking.* FROM option_rankings ranking
                           JOIN option_ranking_runs run USING (ranking_run_id)
                           WHERE ranking.analytics_id=a.analytics_id
                           ORDER BY run.calculated_at DESC, ranking.ranking_id DESC LIMIT 1
                       ) r ON TRUE
                       WHERE (%s::timestamp IS NULL OR (a.source_captured_at, a.analytics_id) > (%s, %s))
                       ORDER BY a.source_captured_at, a.analytics_id LIMIT %s""",
                    (after_at, after_at, after_id, limit),
                )
                columns = [column.name for column in cursor.description or ()]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def upsert_vector(self, vector: dict[str, Any], values: list[dict[str, Any]]) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO feature_store_vectors
                       (vector_id, analytics_id, change_id, ranking_id, underlying_symbol,
                        expiry, observed_at, schema_version, quality_state, feature_count,
                        missing_feature_count, materialized_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (analytics_id, schema_version) DO UPDATE SET
                         change_id=EXCLUDED.change_id, ranking_id=EXCLUDED.ranking_id,
                         quality_state=EXCLUDED.quality_state,
                         feature_count=EXCLUDED.feature_count,
                         missing_feature_count=EXCLUDED.missing_feature_count,
                         materialized_at=EXCLUDED.materialized_at
                       RETURNING vector_id""",
                    tuple(vector[key] for key in (
                        "vector_id", "analytics_id", "change_id", "ranking_id",
                        "underlying_symbol", "expiry", "observed_at", "schema_version",
                        "quality_state", "feature_count", "missing_feature_count", "materialized_at")),
                )
                stored_id = cursor.fetchone()[0]
                cursor.execute("DELETE FROM feature_store_values WHERE vector_id=%s", (stored_id,))
                cursor.executemany(
                    """INSERT INTO feature_store_values
                       (vector_id, feature_name, feature_group, numeric_value,
                        source_relation, source_field) VALUES (%s,%s,%s,%s,%s,%s)""",
                    [(stored_id, value["name"], value["group"], value["value"],
                      value["relation"], value["field"]) for value in values],
                )
            connection.commit()

    def list_vectors(self, symbol: str, expiry: str | None, limit: int) -> list[dict[str, Any]]:
        clauses, parameters = ["v.underlying_symbol=%s"], [symbol]
        if expiry:
            clauses.append("v.expiry=%s")
            parameters.append(expiry)
        parameters.append(limit)
        return self._fetch(
            f"""SELECT v.*, COALESCE(jsonb_object_agg(f.feature_name, f.numeric_value)
                       FILTER (WHERE f.feature_name IS NOT NULL), '{{}}'::jsonb) AS features
                FROM feature_store_vectors v LEFT JOIN feature_store_values f USING (vector_id)
                WHERE {' AND '.join(clauses)} GROUP BY v.vector_id
                ORDER BY v.observed_at DESC, v.vector_id DESC LIMIT %s""", tuple(parameters))

    def get_vector(self, vector_id: UUID) -> dict[str, Any] | None:
        rows = self._fetch(
            """SELECT v.*, COALESCE(jsonb_object_agg(f.feature_name, f.numeric_value)
                      FILTER (WHERE f.feature_name IS NOT NULL), '{}'::jsonb) AS features
               FROM feature_store_vectors v LEFT JOIN feature_store_values f USING (vector_id)
               WHERE v.vector_id=%s GROUP BY v.vector_id""", (vector_id,))
        return rows[0] if rows else None

    @staticmethod
    def _fetch(query: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                columns = [column.name for column in cursor.description or ()]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
