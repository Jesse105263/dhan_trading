from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.database import get_connection
from services.option_analytics_models import (
    CompletedOptionChainRun,
    OptionChainAnalytics,
)
from services.option_chain_models import OptionQuoteSnapshot


class CompletedOptionChainRunNotFoundError(LookupError):
    pass


class OptionAnalyticsRepository:
    def get_completed_run(self, run_id: UUID) -> CompletedOptionChainRun:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        run_id,
                        underlying_symbol,
                        expiry,
                        completed_at,
                        spot_price,
                        strikes_received,
                        quotes_received,
                        quotes_inserted
                    FROM option_chain_runs
                    WHERE run_id = %s
                      AND status = 'COMPLETED';
                    """,
                    (run_id,),
                )
                run = cursor.fetchone()
                if run is None:
                    raise CompletedOptionChainRunNotFoundError(
                        f"Completed option-chain run not found: {run_id}."
                    )
                cursor.execute(
                    """
                    SELECT
                        underlying_symbol,
                        expiry,
                        strike,
                        option_type,
                        captured_at,
                        security_id,
                        last_price,
                        implied_volatility,
                        open_interest,
                        volume,
                        bid_price,
                        ask_price
                    FROM option_chain_quotes
                    WHERE run_id = %s
                    ORDER BY strike, option_type;
                    """,
                    (run_id,),
                )
                quote_rows = cursor.fetchall()

        if run[3] is None or run[4] is None:
            raise CompletedOptionChainRunNotFoundError(
                f"Completed option-chain run has no completion or spot data: {run_id}."
            )
        quotes = tuple(
            OptionQuoteSnapshot(
                underlying_symbol=str(row[0]),
                expiry=row[1],
                strike=Decimal(row[2]),
                option_type=str(row[3]),
                captured_at=row[4],
                security_id=row[5],
                last_price=Decimal(row[6]) if row[6] is not None else None,
                implied_volatility=(
                    Decimal(row[7]) if row[7] is not None else None
                ),
                open_interest=int(row[8]) if row[8] is not None else None,
                volume=int(row[9]) if row[9] is not None else None,
                bid_price=Decimal(row[10]) if row[10] is not None else None,
                ask_price=Decimal(row[11]) if row[11] is not None else None,
            )
            for row in quote_rows
        )
        return CompletedOptionChainRun(
            run_id=run[0],
            underlying_symbol=str(run[1]),
            expiry=run[2],
            completed_at=run[3],
            spot_price=Decimal(run[4]),
            strikes_received=int(run[5]),
            quotes_received=int(run[6]),
            quotes_inserted=int(run[7]),
            quotes=quotes,
        )

    def upsert(self, analytics: OptionChainAnalytics) -> OptionChainAnalytics:
        values = (
            analytics.analytics_id,
            analytics.source_run_id,
            analytics.underlying_symbol,
            analytics.expiry,
            analytics.source_captured_at,
            analytics.calculated_at,
            analytics.spot_price,
            analytics.atm_strike,
            analytics.atm_distance,
            analytics.atm_distance_pct,
            analytics.atm_call_price,
            analytics.atm_put_price,
            analytics.atm_straddle_cost,
            analytics.total_call_oi,
            analytics.total_put_oi,
            analytics.total_pcr,
            analytics.nearby_call_oi,
            analytics.nearby_put_oi,
            analytics.nearby_pcr,
            analytics.atm_call_iv,
            analytics.atm_put_iv,
            analytics.atm_mean_iv,
            analytics.nearby_call_mean_iv,
            analytics.nearby_put_mean_iv,
            analytics.nearby_mean_iv,
            analytics.call_oi_wall_strike,
            analytics.call_oi_wall_value,
            analytics.put_oi_wall_strike,
            analytics.put_oi_wall_value,
            analytics.minimum_strike,
            analytics.maximum_strike,
            analytics.strike_count,
            analytics.nearby_strike_count,
            analytics.quote_count,
            analytics.priced_quote_count,
            analytics.liquid_quote_count,
            analytics.price_coverage,
            analytics.liquidity_coverage,
        )
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO option_chain_analytics
                    (
                        analytics_id, source_run_id, underlying_symbol, expiry,
                        source_captured_at, calculated_at, spot_price, atm_strike,
                        atm_distance, atm_distance_pct, atm_call_price,
                        atm_put_price, atm_straddle_cost, total_call_oi,
                        total_put_oi, total_pcr, nearby_call_oi, nearby_put_oi,
                        nearby_pcr, atm_call_iv, atm_put_iv, atm_mean_iv,
                        nearby_call_mean_iv, nearby_put_mean_iv, nearby_mean_iv,
                        call_oi_wall_strike, call_oi_wall_value,
                        put_oi_wall_strike, put_oi_wall_value, minimum_strike,
                        maximum_strike, strike_count, nearby_strike_count,
                        quote_count, priced_quote_count, liquid_quote_count,
                        price_coverage, liquidity_coverage
                    )
                    VALUES
                    (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (source_run_id) DO UPDATE SET
                        calculated_at = EXCLUDED.calculated_at,
                        spot_price = EXCLUDED.spot_price,
                        atm_strike = EXCLUDED.atm_strike,
                        atm_distance = EXCLUDED.atm_distance,
                        atm_distance_pct = EXCLUDED.atm_distance_pct,
                        atm_call_price = EXCLUDED.atm_call_price,
                        atm_put_price = EXCLUDED.atm_put_price,
                        atm_straddle_cost = EXCLUDED.atm_straddle_cost,
                        total_call_oi = EXCLUDED.total_call_oi,
                        total_put_oi = EXCLUDED.total_put_oi,
                        total_pcr = EXCLUDED.total_pcr,
                        nearby_call_oi = EXCLUDED.nearby_call_oi,
                        nearby_put_oi = EXCLUDED.nearby_put_oi,
                        nearby_pcr = EXCLUDED.nearby_pcr,
                        atm_call_iv = EXCLUDED.atm_call_iv,
                        atm_put_iv = EXCLUDED.atm_put_iv,
                        atm_mean_iv = EXCLUDED.atm_mean_iv,
                        nearby_call_mean_iv = EXCLUDED.nearby_call_mean_iv,
                        nearby_put_mean_iv = EXCLUDED.nearby_put_mean_iv,
                        nearby_mean_iv = EXCLUDED.nearby_mean_iv,
                        call_oi_wall_strike = EXCLUDED.call_oi_wall_strike,
                        call_oi_wall_value = EXCLUDED.call_oi_wall_value,
                        put_oi_wall_strike = EXCLUDED.put_oi_wall_strike,
                        put_oi_wall_value = EXCLUDED.put_oi_wall_value,
                        minimum_strike = EXCLUDED.minimum_strike,
                        maximum_strike = EXCLUDED.maximum_strike,
                        strike_count = EXCLUDED.strike_count,
                        nearby_strike_count = EXCLUDED.nearby_strike_count,
                        quote_count = EXCLUDED.quote_count,
                        priced_quote_count = EXCLUDED.priced_quote_count,
                        liquid_quote_count = EXCLUDED.liquid_quote_count,
                        price_coverage = EXCLUDED.price_coverage,
                        liquidity_coverage = EXCLUDED.liquidity_coverage
                    RETURNING analytics_id;
                    """,
                    values,
                )
                stored_id = cursor.fetchone()[0]
            connection.commit()
        if stored_id == analytics.analytics_id:
            return analytics
        return OptionChainAnalytics(
            **{**analytics.__dict__, "analytics_id": stored_id}
        )
