from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from statistics import mean
from typing import Callable, Iterable
from uuid import uuid4

from services.option_analytics_models import (
    CompletedOptionChainRun,
    OptionAnalyticsRequest,
    OptionChainAnalytics,
)
from services.option_analytics_repository import OptionAnalyticsRepository
from services.option_chain_models import OptionQuoteSnapshot


class OptionAnalyticsValidationError(ValueError):
    pass


class OptionAnalyticsService:
    def __init__(
        self,
        repository: OptionAnalyticsRepository,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.repository = repository
        self.clock = clock

    def calculate_and_persist(
        self,
        request: OptionAnalyticsRequest,
    ) -> OptionChainAnalytics:
        normalized = request.normalized()
        calculated_at = self.clock()
        source = self.repository.get_completed_run(normalized.source_run_id)
        analytics = self.calculate(
            source,
            calculated_at=calculated_at,
            nearby_strikes_each_side=normalized.nearby_strikes_each_side,
            maximum_source_age=normalized.maximum_source_age,
        )
        return self.repository.upsert(analytics)

    @staticmethod
    def calculate(
        source: CompletedOptionChainRun,
        calculated_at: datetime,
        nearby_strikes_each_side: int,
        maximum_source_age,
    ) -> OptionChainAnalytics:
        if calculated_at < source.completed_at:
            raise OptionAnalyticsValidationError(
                "calculated_at cannot precede source completion."
            )
        if calculated_at - source.completed_at > maximum_source_age:
            raise OptionAnalyticsValidationError(
                "Source option chain is stale."
            )
        if source.spot_price <= 0:
            raise OptionAnalyticsValidationError("Spot price must be positive.")
        quotes_by_strike = OptionAnalyticsService._validate_and_group(source)
        strikes = sorted(quotes_by_strike)
        atm_strike = min(strikes, key=lambda strike: (abs(strike - source.spot_price), strike))
        atm = quotes_by_strike[atm_strike]
        atm_call = atm["CE"]
        atm_put = atm["PE"]
        if atm_call.last_price is None or atm_put.last_price is None:
            raise OptionAnalyticsValidationError(
                "ATM call and put prices are required."
            )

        atm_index = strikes.index(atm_strike)
        start = max(0, atm_index - nearby_strikes_each_side)
        end = min(len(strikes), atm_index + nearby_strikes_each_side + 1)
        nearby_strikes = strikes[start:end]
        all_quotes = [quote for strike in strikes for quote in quotes_by_strike[strike].values()]
        nearby_quotes = [quote for strike in nearby_strikes for quote in quotes_by_strike[strike].values()]
        calls = [quote for quote in all_quotes if quote.option_type == "CE"]
        puts = [quote for quote in all_quotes if quote.option_type == "PE"]
        nearby_calls = [quote for quote in nearby_quotes if quote.option_type == "CE"]
        nearby_puts = [quote for quote in nearby_quotes if quote.option_type == "PE"]

        total_call_oi = sum(quote.open_interest or 0 for quote in calls)
        total_put_oi = sum(quote.open_interest or 0 for quote in puts)
        nearby_call_oi = sum(quote.open_interest or 0 for quote in nearby_calls)
        nearby_put_oi = sum(quote.open_interest or 0 for quote in nearby_puts)
        call_wall = OptionAnalyticsService._oi_wall(calls)
        put_wall = OptionAnalyticsService._oi_wall(puts)
        priced = sum(quote.last_price is not None for quote in all_quotes)
        liquid = sum(
            quote.bid_price is not None
            and quote.ask_price is not None
            and quote.ask_price >= quote.bid_price
            and quote.ask_price > 0
            for quote in all_quotes
        )
        quote_count = len(all_quotes)
        distance = abs(atm_strike - source.spot_price)
        return OptionChainAnalytics(
            analytics_id=uuid4(),
            source_run_id=source.run_id,
            underlying_symbol=source.underlying_symbol,
            expiry=source.expiry,
            source_captured_at=source.completed_at,
            calculated_at=calculated_at,
            spot_price=source.spot_price,
            atm_strike=atm_strike,
            atm_distance=distance,
            atm_distance_pct=distance / source.spot_price,
            atm_call_price=atm_call.last_price,
            atm_put_price=atm_put.last_price,
            atm_straddle_cost=atm_call.last_price + atm_put.last_price,
            total_call_oi=total_call_oi,
            total_put_oi=total_put_oi,
            total_pcr=OptionAnalyticsService._ratio(total_put_oi, total_call_oi),
            nearby_call_oi=nearby_call_oi,
            nearby_put_oi=nearby_put_oi,
            nearby_pcr=OptionAnalyticsService._ratio(nearby_put_oi, nearby_call_oi),
            atm_call_iv=atm_call.implied_volatility,
            atm_put_iv=atm_put.implied_volatility,
            atm_mean_iv=OptionAnalyticsService._decimal_mean(
                [atm_call.implied_volatility, atm_put.implied_volatility]
            ),
            nearby_call_mean_iv=OptionAnalyticsService._quote_iv_mean(nearby_calls),
            nearby_put_mean_iv=OptionAnalyticsService._quote_iv_mean(nearby_puts),
            nearby_mean_iv=OptionAnalyticsService._quote_iv_mean(nearby_quotes),
            call_oi_wall_strike=call_wall.strike if call_wall else None,
            call_oi_wall_value=call_wall.open_interest if call_wall else None,
            put_oi_wall_strike=put_wall.strike if put_wall else None,
            put_oi_wall_value=put_wall.open_interest if put_wall else None,
            minimum_strike=strikes[0],
            maximum_strike=strikes[-1],
            strike_count=len(strikes),
            nearby_strike_count=len(nearby_strikes),
            quote_count=quote_count,
            priced_quote_count=priced,
            liquid_quote_count=liquid,
            price_coverage=Decimal(priced) / Decimal(quote_count),
            liquidity_coverage=Decimal(liquid) / Decimal(quote_count),
        )

    @staticmethod
    def _validate_and_group(source: CompletedOptionChainRun):
        if not source.quotes:
            raise OptionAnalyticsValidationError("Source chain has no quotes.")
        grouped: dict[Decimal, dict[str, OptionQuoteSnapshot]] = {}
        for quote in source.quotes:
            if quote.underlying_symbol.upper() != source.underlying_symbol.upper():
                raise OptionAnalyticsValidationError("Quote underlying does not match source run.")
            if quote.expiry != source.expiry:
                raise OptionAnalyticsValidationError("Quote expiry does not match source run.")
            sides = grouped.setdefault(quote.strike, {})
            if quote.option_type in sides:
                raise OptionAnalyticsValidationError("Duplicate option side for strike.")
            sides[quote.option_type] = quote
        incomplete = [strike for strike, sides in grouped.items() if set(sides) != {"CE", "PE"}]
        if incomplete:
            raise OptionAnalyticsValidationError("Source chain is incomplete.")
        if source.strikes_received != len(grouped):
            raise OptionAnalyticsValidationError("Source strike count does not match stored quotes.")
        if source.quotes_inserted != len(source.quotes) or source.quotes_received != len(source.quotes):
            raise OptionAnalyticsValidationError("Source quote counts do not match stored quotes.")
        return grouped

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> Decimal | None:
        if denominator == 0:
            return None
        return Decimal(numerator) / Decimal(denominator)

    @staticmethod
    def _decimal_mean(values: Iterable[Decimal | None]) -> Decimal | None:
        present = [value for value in values if value is not None]
        return Decimal(str(mean(present))) if present else None

    @staticmethod
    def _quote_iv_mean(quotes: Iterable[OptionQuoteSnapshot]) -> Decimal | None:
        return OptionAnalyticsService._decimal_mean(quote.implied_volatility for quote in quotes)

    @staticmethod
    def _oi_wall(quotes: Iterable[OptionQuoteSnapshot]) -> OptionQuoteSnapshot | None:
        candidates = [quote for quote in quotes if quote.open_interest is not None]
        if not candidates:
            return None
        return min(candidates, key=lambda quote: (-quote.open_interest, quote.strike))
