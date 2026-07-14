from __future__ import annotations

from typing import Any

from services.database import get_connection


class SymbolWorkspaceRepository:
    """SELECT-only symbol intelligence projections."""

    def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        return self._fetch_all(
            """SELECT underlying_symbol, MAX(source_captured_at) AS latest_captured_at,
                      ARRAY_AGG(DISTINCT expiry ORDER BY expiry) AS expiries
               FROM option_chain_analytics WHERE underlying_symbol ILIKE %s
               GROUP BY underlying_symbol ORDER BY underlying_symbol LIMIT %s""",
            (f"%{query}%", limit),
        )

    def intelligence(self, symbol: str, expiry: str | None) -> dict[str, Any] | None:
        selected_expiry = expiry
        if selected_expiry is None:
            row = self._optional(
                """SELECT expiry FROM option_chain_analytics WHERE underlying_symbol=%s
                   ORDER BY source_captured_at DESC, analytics_id DESC LIMIT 1""", (symbol,)
            )
            if row is None:
                return None
            selected_expiry = str(row["expiry"])
        analytics = self._fetch_all(
            """SELECT * FROM option_chain_analytics WHERE underlying_symbol=%s AND expiry=%s
               ORDER BY source_captured_at DESC, analytics_id DESC LIMIT 50""", (symbol, selected_expiry)
        )
        if not analytics:
            return None
        params = (symbol, selected_expiry)
        return {
            "symbol": symbol,
            "expiry": selected_expiry,
            "analytics": analytics,
            "changes": self._fetch_all(
                """SELECT * FROM option_analytics_changes WHERE underlying_symbol=%s AND expiry=%s
                   ORDER BY current_captured_at DESC, change_id DESC LIMIT 50""", params),
            "rankings": self._fetch_all(
                """SELECT r.*, rr.calculated_at FROM option_rankings r
                   JOIN option_ranking_runs rr USING (ranking_run_id)
                   WHERE r.underlying_symbol=%s AND r.expiry=%s
                   ORDER BY rr.calculated_at DESC, r.ranking_id DESC LIMIT 50""", params),
            "selections": self._fetch_all(
                """SELECT s.*, sr.calculated_at FROM option_contract_selections s
                   JOIN option_contract_selection_runs sr USING (selection_run_id)
                   WHERE s.underlying_symbol=%s AND s.expiry=%s
                   ORDER BY sr.calculated_at DESC, s.selection_id DESC LIMIT 50""", params),
            "risk": self._fetch_all(
                """SELECT a.*, rr.calculated_at FROM option_risk_assessments a
                   JOIN option_risk_assessment_runs rr USING (risk_run_id)
                   WHERE a.underlying_symbol=%s AND a.expiry=%s
                   ORDER BY rr.calculated_at DESC, a.assessment_id DESC LIMIT 50""", params),
            "signals": self._fetch_all(
                """SELECT s.*, sr.calculated_at FROM option_signals s
                   JOIN option_signal_runs sr USING (signal_run_id)
                   WHERE s.underlying_symbol=%s AND s.expiry=%s
                   ORDER BY sr.calculated_at DESC, s.signal_id DESC LIMIT 50""", params),
            "collections": self._fetch_all(
                """SELECT run_id, status, requested_at, completed_at, spot_price,
                          strikes_received, quotes_received, quotes_inserted
                   FROM option_chain_runs WHERE underlying_symbol=%s AND expiry=%s
                   ORDER BY requested_at DESC, run_id DESC LIMIT 50""", params),
            "related": self._fetch_all(
                """SELECT DISTINCT ON (r.expiry) r.ranking_id, r.ranking_run_id,
                          r.expiry, r.rank_position, r.total_score, r.source_captured_at
                   FROM option_rankings r JOIN option_ranking_runs rr USING (ranking_run_id)
                   WHERE r.underlying_symbol=%s
                   ORDER BY r.expiry, rr.calculated_at DESC, r.ranking_id DESC""", (symbol,)),
        }

    @staticmethod
    def _fetch_all(query: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                columns = [column.name for column in cursor.description or ()]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    @classmethod
    def _optional(cls, query: str, parameters: tuple[Any, ...]) -> dict[str, Any] | None:
        rows = cls._fetch_all(query, parameters)
        return rows[0] if rows else None
