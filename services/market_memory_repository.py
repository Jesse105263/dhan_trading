from __future__ import annotations

from typing import Any
from uuid import UUID

from services.database import get_connection


class MarketMemoryRepository:
    """SELECT-only access to immutable, already-persisted market observations."""

    def snapshots(
        self,
        symbol: str,
        expiry: str | None,
        start: str | None,
        end: str | None,
        limit: int,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["a.underlying_symbol = %s"]
        parameters: list[Any] = [symbol]
        for predicate, value in (
            ("a.expiry = %s", expiry),
            ("a.source_captured_at >= %s", start),
            ("a.source_captured_at <= %s", end),
            ("a.source_captured_at < %s", before),
        ):
            if value is not None:
                clauses.append(predicate)
                parameters.append(value)
        parameters.append(limit)
        return self._fetch_all(
            f"""SELECT a.*, r.ranking_id, r.ranking_run_id, r.rank_position,
                       r.total_score, r.liquidity_score, r.activity_score,
                       r.volatility_score, r.directional_score,
                       c.change_id, c.previous_analytics_id
                FROM option_chain_analytics a
                LEFT JOIN LATERAL (
                    SELECT ranking.* FROM option_rankings ranking
                    JOIN option_ranking_runs run USING (ranking_run_id)
                    WHERE ranking.analytics_id = a.analytics_id
                    ORDER BY run.calculated_at DESC, ranking.ranking_id DESC LIMIT 1
                ) r ON TRUE
                LEFT JOIN option_analytics_changes c ON c.current_analytics_id = a.analytics_id
                WHERE {' AND '.join(clauses)}
                ORDER BY a.source_captured_at DESC, a.analytics_id DESC
                LIMIT %s""",
            tuple(parameters),
        )

    def snapshot(self, snapshot_id: UUID) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """SELECT a.*, r.ranking_id, r.ranking_run_id, r.rank_position,
                      r.total_score, r.liquidity_score, r.activity_score,
                      r.volatility_score, r.directional_score,
                      c.change_id, c.previous_analytics_id
               FROM option_chain_analytics a
               LEFT JOIN LATERAL (
                   SELECT ranking.* FROM option_rankings ranking
                   JOIN option_ranking_runs run USING (ranking_run_id)
                   WHERE ranking.analytics_id = a.analytics_id
                   ORDER BY run.calculated_at DESC, ranking.ranking_id DESC LIMIT 1
               ) r ON TRUE
               LEFT JOIN option_analytics_changes c ON c.current_analytics_id = a.analytics_id
               WHERE a.analytics_id = %s""",
            (snapshot_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def _fetch_all(query: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                columns = [column.name for column in cursor.description or ()]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
