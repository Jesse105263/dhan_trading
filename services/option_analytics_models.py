from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from services.option_chain_models import OptionQuoteSnapshot


@dataclass(frozen=True)
class OptionAnalyticsRequest:
    source_run_id: UUID
    nearby_strikes_each_side: int = 5
    maximum_source_age: timedelta = timedelta(hours=24)

    def normalized(self) -> OptionAnalyticsRequest:
        if self.nearby_strikes_each_side < 0:
            raise ValueError("nearby_strikes_each_side cannot be negative.")
        if self.maximum_source_age <= timedelta(0):
            raise ValueError("maximum_source_age must be positive.")
        return self


@dataclass(frozen=True)
class CompletedOptionChainRun:
    run_id: UUID
    underlying_symbol: str
    expiry: date
    completed_at: datetime
    spot_price: Decimal
    strikes_received: int
    quotes_received: int
    quotes_inserted: int
    quotes: tuple[OptionQuoteSnapshot, ...]


@dataclass(frozen=True)
class OptionChainAnalytics:
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    source_captured_at: datetime
    calculated_at: datetime
    spot_price: Decimal
    atm_strike: Decimal
    atm_distance: Decimal
    atm_distance_pct: Decimal
    atm_call_price: Decimal
    atm_put_price: Decimal
    atm_straddle_cost: Decimal
    total_call_oi: int
    total_put_oi: int
    total_pcr: Decimal | None
    nearby_call_oi: int
    nearby_put_oi: int
    nearby_pcr: Decimal | None
    atm_call_iv: Decimal | None
    atm_put_iv: Decimal | None
    atm_mean_iv: Decimal | None
    nearby_call_mean_iv: Decimal | None
    nearby_put_mean_iv: Decimal | None
    nearby_mean_iv: Decimal | None
    call_oi_wall_strike: Decimal | None
    call_oi_wall_value: int | None
    put_oi_wall_strike: Decimal | None
    put_oi_wall_value: int | None
    minimum_strike: Decimal
    maximum_strike: Decimal
    strike_count: int
    nearby_strike_count: int
    quote_count: int
    priced_quote_count: int
    liquid_quote_count: int
    price_coverage: Decimal
    liquidity_coverage: Decimal
