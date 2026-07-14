from __future__ import annotations

from typing import Any
from uuid import UUID

from services.database import get_connection


class MarketWorkspaceRepository:
    """Purpose-built, read-only projections for the Version 2 market workspace."""

    def overview(self) -> dict[str, Any]:
        return {
            "database_ready": self._fetch_one("SELECT TRUE AS database_ready", ())["database_ready"],
            "latest_option_run": self._fetch_optional(
                """SELECT run_id, underlying_symbol, expiry, completed_at
                   FROM option_chain_runs WHERE status='COMPLETED'
                   ORDER BY completed_at DESC NULLS LAST, run_id DESC LIMIT 1""", ()
            ),
            "latest_ranking_run": self._fetch_optional(
                """SELECT ranking_run_id, calculated_at, eligible_count
                   FROM option_ranking_runs ORDER BY calculated_at DESC, ranking_run_id DESC LIMIT 1""", ()
            ),
            "counts": self._fetch_one(
                """WITH latest AS (
                       SELECT ranking_run_id FROM option_ranking_runs
                       ORDER BY calculated_at DESC, ranking_run_id DESC LIMIT 1
                   ), ranked AS (
                       SELECT ranking_id FROM option_rankings r JOIN latest l USING (ranking_run_id)
                   )
                   SELECT
                     (SELECT COUNT(*) FROM ranked) AS ranked,
                     (SELECT COUNT(DISTINCT s.selection_id) FROM option_contract_selections s JOIN ranked r USING (ranking_id)) AS selections,
                     (SELECT COUNT(*) FROM option_risk_assessments a JOIN ranked r USING (ranking_id) WHERE a.approved) AS risk_approved,
                     (SELECT COUNT(*) FROM option_risk_assessments a JOIN ranked r USING (ranking_id) WHERE NOT a.approved) AS risk_rejected,
                     (SELECT COUNT(*) FROM option_signals s JOIN ranked r USING (ranking_id)) AS signals""", ()
            ),
            "failures": self._fetch_all(
                """SELECT id, run_id, stage_name, symbol, error_type, error_message,
                          retryable, occurred_at
                   FROM pipeline_failures ORDER BY occurred_at DESC, id DESC LIMIT 5""", ()
            ),
        }

    def list_opportunities(
        self, *, symbol: str | None, expiry: str | None, minimum_score: Any | None,
        selection: bool | None, risk_approved: bool | None, signal: bool | None,
        freshness: str | None, current_cutoff: Any, aging_cutoff: Any,
        sort: str, direction: str, limit: int, offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = []
        parameters: list[Any] = []
        if symbol:
            conditions.append("r.underlying_symbol ILIKE %s")
            parameters.append(f"%{symbol}%")
        if expiry:
            conditions.append("r.expiry = %s")
            parameters.append(expiry)
        if minimum_score is not None:
            conditions.append("r.total_score >= %s")
            parameters.append(minimum_score)
        if freshness == "current":
            conditions.append("r.source_captured_at >= %s")
            parameters.append(current_cutoff)
        elif freshness == "aging":
            conditions.append("r.source_captured_at < %s AND r.source_captured_at >= %s")
            parameters.extend((current_cutoff, aging_cutoff))
        elif freshness == "stale":
            conditions.append("r.source_captured_at < %s")
            parameters.append(aging_cutoff)
        availability = {
            "selection": "EXISTS (SELECT 1 FROM option_contract_selections s WHERE s.ranking_id=r.ranking_id)",
            "risk": "EXISTS (SELECT 1 FROM option_risk_assessments a WHERE a.ranking_id=r.ranking_id AND a.approved)",
            "signal": "EXISTS (SELECT 1 FROM option_signals g WHERE g.ranking_id=r.ranking_id)",
        }
        for value, expression in ((selection, availability["selection"]), (risk_approved, availability["risk"]), (signal, availability["signal"])):
            if value is not None:
                conditions.append(expression if value else f"NOT {expression}")
        where = " AND " + " AND ".join(conditions) if conditions else ""
        base = f"""FROM option_rankings r
                   JOIN (SELECT ranking_run_id, calculated_at FROM option_ranking_runs
                         ORDER BY calculated_at DESC, ranking_run_id DESC LIMIT 1) latest
                     USING (ranking_run_id)
                   WHERE TRUE {where}"""
        total = self._fetch_one(f"SELECT COUNT(*) AS total {base}", tuple(parameters))["total"]
        order_columns = {"rank": "r.rank_position", "score": "r.total_score", "captured_at": "r.source_captured_at", "symbol": "r.underlying_symbol"}
        query = f"""SELECT r.ranking_id, r.ranking_run_id, r.analytics_id, r.change_id,
                           r.underlying_symbol, r.expiry, r.source_captured_at,
                           r.rank_position, r.total_score, r.liquidity_score,
                           r.activity_score, r.volatility_score, r.directional_score,
                           r.explanation, latest.calculated_at,
                           {availability['selection']} AS selection_available,
                           {availability['risk']} AS risk_approved,
                           {availability['signal']} AS signal_available
                    {base} ORDER BY {order_columns[sort]} {direction.upper()},
                    r.ranking_id ASC LIMIT %s OFFSET %s"""
        return self._fetch_all(query, tuple(parameters + [limit, offset])), int(total)

    def get_opportunity(self, ranking_id: UUID) -> dict[str, Any] | None:
        return self._fetch_optional(
            """SELECT r.ranking_id, r.ranking_run_id, r.analytics_id, r.change_id,
                      r.underlying_symbol, r.expiry, r.source_captured_at, r.rank_position,
                      r.total_score, r.liquidity_score, r.activity_score,
                      r.volatility_score, r.directional_score, r.explanation,
                      rr.calculated_at,
                      s.selection_id, s.selection_run_id, s.option_type,
                      s.trading_symbol, s.strike, s.contract_score,
                      a.assessment_id, a.risk_run_id, a.approved, a.rejection_code,
                      g.signal_id, g.signal_run_id, g.action, g.direction
               FROM option_rankings r JOIN option_ranking_runs rr USING (ranking_run_id)
               LEFT JOIN LATERAL (SELECT * FROM option_contract_selections
                   WHERE ranking_id=r.ranking_id ORDER BY created_at DESC, selection_id LIMIT 1) s ON TRUE
               LEFT JOIN LATERAL (SELECT * FROM option_risk_assessments
                   WHERE ranking_id=r.ranking_id ORDER BY created_at DESC, assessment_id LIMIT 1) a ON TRUE
               LEFT JOIN LATERAL (SELECT * FROM option_signals
                   WHERE ranking_id=r.ranking_id ORDER BY created_at DESC, signal_id LIMIT 1) g ON TRUE
               WHERE r.ranking_id=%s""", (ranking_id,)
        )

    @staticmethod
    def _fetch_all(query: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                columns = [column.name for column in cursor.description or ()]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    @classmethod
    def _fetch_one(cls, query: str, parameters: tuple[Any, ...]) -> dict[str, Any]:
        rows = cls._fetch_all(query, parameters)
        if not rows:
            raise RuntimeError("Read projection returned no row.")
        return rows[0]

    @classmethod
    def _fetch_optional(cls, query: str, parameters: tuple[Any, ...]) -> dict[str, Any] | None:
        rows = cls._fetch_all(query, parameters)
        return rows[0] if rows else None
