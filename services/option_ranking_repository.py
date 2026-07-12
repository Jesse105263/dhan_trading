from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.option_ranking_models import OptionRanking, OptionRankingCandidate, OptionRankingResult


class OptionRankingRepository:
    def list_latest_candidates(self, as_of: datetime) -> list[OptionRankingCandidate]:
        query = """
        SELECT DISTINCT ON (a.underlying_symbol, a.expiry)
               a.analytics_id, c.change_id, a.underlying_symbol, a.expiry,
               a.source_captured_at, a.liquidity_coverage, a.price_coverage,
               c.total_call_oi_change, c.total_put_oi_change,
               c.atm_straddle_change, c.atm_mean_iv_change,
               a.total_pcr, c.total_pcr_change, a.spot_price,
               a.call_oi_wall_strike, a.put_oi_wall_strike
        FROM option_chain_analytics a
        JOIN option_analytics_changes c ON c.current_analytics_id = a.analytics_id
        WHERE a.source_captured_at <= %s
        ORDER BY a.underlying_symbol, a.expiry, a.source_captured_at DESC, a.analytics_id DESC;
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (as_of,))
                rows = cursor.fetchall()
        result = []
        for row in rows:
            values = list(row)
            for index in (5, 6, 9, 10, 11, 12, 13, 14, 15):
                if values[index] is not None:
                    values[index] = Decimal(values[index])
            result.append(OptionRankingCandidate(*values))
        return result

    def persist(self, result: OptionRankingResult) -> OptionRankingResult:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO option_ranking_runs
                    (ranking_run_id, as_of, calculated_at, eligible_count, methodology_version)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (result.ranking_run_id, result.as_of, result.calculated_at,
                     len(result.rankings), result.methodology_version),
                )
                for ranking in result.rankings:
                    cursor.execute(
                        """
                        INSERT INTO option_rankings
                        (ranking_id, ranking_run_id, analytics_id, change_id,
                         underlying_symbol, expiry, source_captured_at, rank_position,
                         total_score, liquidity_score, activity_score, volatility_score,
                         directional_score, explanation)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                        """,
                        (ranking.ranking_id, ranking.ranking_run_id, ranking.analytics_id,
                         ranking.change_id, ranking.underlying_symbol, ranking.expiry,
                         ranking.source_captured_at, ranking.rank_position, ranking.total_score,
                         ranking.liquidity_score, ranking.activity_score,
                         ranking.volatility_score, ranking.directional_score,
                         Jsonb(ranking.explanation)),
                    )
            connection.commit()
        return result
