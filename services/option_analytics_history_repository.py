from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from services.database import get_connection
from services.option_analytics_history_models import (
    OptionAnalyticsChange,
    OptionAnalyticsPair,
)
from services.option_analytics_models import OptionChainAnalytics


class OptionAnalyticsHistoryNotFoundError(LookupError):
    pass


class OptionAnalyticsHistoryRepository:
    _SELECT = """
        SELECT analytics_id, source_run_id, underlying_symbol, expiry,
               source_captured_at, calculated_at, spot_price, atm_strike,
               atm_distance, atm_distance_pct, atm_call_price, atm_put_price,
               atm_straddle_cost, total_call_oi, total_put_oi, total_pcr,
               nearby_call_oi, nearby_put_oi, nearby_pcr, atm_call_iv,
               atm_put_iv, atm_mean_iv, nearby_call_mean_iv,
               nearby_put_mean_iv, nearby_mean_iv, call_oi_wall_strike,
               call_oi_wall_value, put_oi_wall_strike, put_oi_wall_value,
               minimum_strike, maximum_strike, strike_count,
               nearby_strike_count, quote_count, priced_quote_count,
               liquid_quote_count, price_coverage, liquidity_coverage
        FROM option_chain_analytics
    """

    def list_history(self, underlying_symbol: str, expiry, limit: int = 100) -> list[OptionChainAnalytics]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    self._SELECT + """
                    WHERE underlying_symbol = %s AND expiry = %s
                    ORDER BY source_captured_at ASC, analytics_id ASC
                    LIMIT %s;
                    """,
                    (underlying_symbol.strip().upper(), expiry, limit),
                )
                rows = cursor.fetchall()
        return [self._map(row) for row in rows]

    def get_consecutive_pair(self, current_analytics_id: UUID) -> OptionAnalyticsPair:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    self._SELECT + " WHERE analytics_id = %s;",
                    (current_analytics_id,),
                )
                current_row = cursor.fetchone()
                if current_row is None:
                    raise OptionAnalyticsHistoryNotFoundError(
                        f"Current analytics snapshot not found: {current_analytics_id}."
                    )
                current = self._map(current_row)
                cursor.execute(
                    self._SELECT + """
                    WHERE underlying_symbol = %s
                      AND expiry = %s
                      AND (source_captured_at, analytics_id) < (%s, %s)
                    ORDER BY source_captured_at DESC, analytics_id DESC
                    LIMIT 1;
                    """,
                    (
                        current.underlying_symbol,
                        current.expiry,
                        current.source_captured_at,
                        current.analytics_id,
                    ),
                )
                previous_row = cursor.fetchone()
        if previous_row is None:
            raise OptionAnalyticsHistoryNotFoundError(
                "No previous comparable analytics snapshot exists."
            )
        return OptionAnalyticsPair(previous=self._map(previous_row), current=current)

    def upsert_change(self, change: OptionAnalyticsChange) -> OptionAnalyticsChange:
        values = tuple(change.__dict__.values())
        columns = ", ".join(change.__dict__.keys())
        placeholders = ", ".join(["%s"] * len(values))
        updates = ", ".join(
            f"{name} = EXCLUDED.{name}"
            for name in change.__dict__.keys()
            if name not in {"change_id", "current_analytics_id"}
        )
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO option_analytics_changes ({columns})
                    VALUES ({placeholders})
                    ON CONFLICT (current_analytics_id) DO UPDATE SET {updates}
                    RETURNING change_id;
                    """,
                    values,
                )
                stored_id = cursor.fetchone()[0]
            connection.commit()
        if stored_id == change.change_id:
            return change
        return OptionAnalyticsChange(**{**change.__dict__, "change_id": stored_id})

    @staticmethod
    def _map(row) -> OptionChainAnalytics:
        decimal_indexes = {
            6, 7, 8, 9, 10, 11, 12, 15, 18, 19, 20, 21, 22, 23, 24,
            25, 27, 29, 30, 36, 37,
        }
        values = list(row)
        for index in decimal_indexes:
            if values[index] is not None:
                values[index] = Decimal(values[index])
        return OptionChainAnalytics(*values)
