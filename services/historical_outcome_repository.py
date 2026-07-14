from __future__ import annotations

from typing import Any
from uuid import UUID

from services.database import get_connection


class HistoricalOutcomeRepository:
    def source_vectors(self, limit: int, after_at=None, after_id=None) -> list[dict[str, Any]]:
        return self._fetch(
            """SELECT v.*, f.numeric_value AS spot_price
               FROM feature_store_vectors v
               LEFT JOIN feature_store_values f ON f.vector_id=v.vector_id AND f.feature_name='spot_price'
               WHERE (%s::timestamp IS NULL OR (v.observed_at,v.vector_id)>(%s,%s))
               ORDER BY v.observed_at,v.vector_id LIMIT %s""",
            (after_at, after_at, after_id, limit),
        )

    def future_vectors(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        return self._fetch(
            """SELECT v.vector_id,v.observed_at,f.numeric_value AS spot_price
               FROM feature_store_vectors v
               LEFT JOIN feature_store_values f ON f.vector_id=v.vector_id AND f.feature_name='spot_price'
               WHERE v.underlying_symbol=%s AND v.expiry=%s
                 AND (v.observed_at,v.vector_id)>(%s,%s)
                 AND v.observed_at::date<=v.expiry
               ORDER BY v.observed_at,v.vector_id""",
            (source["underlying_symbol"], source["expiry"], source["observed_at"], source["vector_id"]),
        )

    def upsert(self, outcome: dict[str, Any]) -> None:
        keys = tuple(outcome)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""INSERT INTO historical_outcomes ({','.join(keys)})
                        VALUES ({','.join(['%s']*len(keys))})
                        ON CONFLICT (vector_id,model_version) DO UPDATE SET
                        terminal_vector_id=EXCLUDED.terminal_vector_id,
                        terminal_observed_at=EXCLUDED.terminal_observed_at,
                        outcome_type=EXCLUDED.outcome_type,entry_value=EXCLUDED.entry_value,
                        terminal_value=EXCLUDED.terminal_value,forward_return=EXCLUDED.forward_return,
                        maximum_favourable_excursion=EXCLUDED.maximum_favourable_excursion,
                        maximum_adverse_excursion=EXCLUDED.maximum_adverse_excursion,
                        holding_duration_seconds=EXCLUDED.holding_duration_seconds,
                        expiry_outcome=EXCLUDED.expiry_outcome,peak_gain=EXCLUDED.peak_gain,
                        peak_loss=EXCLUDED.peak_loss,closing_return=EXCLUDED.closing_return,
                        won=EXCLUDED.won,future_observation_count=EXCLUDED.future_observation_count,
                        materialized_at=EXCLUDED.materialized_at""",
                    tuple(outcome.values()),
                )
            connection.commit()

    def list_outcomes(self, filters: dict[str, Any], limit: int, ascending: bool = False) -> list[dict[str, Any]]:
        clauses, parameters = ["TRUE"], []
        for field, predicate in (("symbol","underlying_symbol=%s"),("expiry","expiry=%s"),
                                 ("from","observed_at>=%s"),("to","observed_at<=%s"),
                                 ("outcome_type","outcome_type=%s")):
            if filters.get(field) is not None:
                clauses.append(predicate); parameters.append(filters[field])
        parameters.append(limit)
        direction = "ASC" if ascending else "DESC"
        return self._fetch(f"SELECT * FROM historical_outcomes WHERE {' AND '.join(clauses)} ORDER BY observed_at {direction},outcome_id {direction} LIMIT %s", tuple(parameters))

    def get_outcome(self, outcome_id: UUID) -> dict[str, Any] | None:
        rows=self._fetch("SELECT * FROM historical_outcomes WHERE outcome_id=%s",(outcome_id,))
        return rows[0] if rows else None

    def statistics(self, filters: dict[str, Any]) -> dict[str, Any]:
        clauses, parameters = ["TRUE"], []
        for field, predicate in (("symbol","underlying_symbol=%s"),("expiry","expiry=%s"),
                                 ("from","observed_at>=%s"),("to","observed_at<=%s"),
                                 ("outcome_type","outcome_type=%s")):
            if filters.get(field) is not None: clauses.append(predicate); parameters.append(filters[field])
        rows=self._fetch(f"""SELECT COUNT(*) AS outcome_count,COUNT(won) AS classified_count,
            AVG(CASE WHEN won THEN 1.0 ELSE 0.0 END) FILTER (WHERE won IS NOT NULL) AS win_rate,
            AVG(closing_return) AS average_return,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY closing_return) AS median_return,
            AVG(maximum_favourable_excursion) AS average_mfe,
            AVG(maximum_adverse_excursion) AS average_mae,
            MAX(closing_return) AS best_outcome,MIN(closing_return) AS worst_outcome
            FROM historical_outcomes WHERE {' AND '.join(clauses)}""",tuple(parameters))
        return rows[0]

    @staticmethod
    def _fetch(query: str, parameters: tuple[Any,...]) -> list[dict[str,Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query,parameters); columns=[column.name for column in cursor.description or ()]
                return [dict(zip(columns,row,strict=True)) for row in cursor.fetchall()]
