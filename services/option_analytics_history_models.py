from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from services.option_analytics_models import OptionChainAnalytics


@dataclass(frozen=True)
class OptionAnalyticsHistoryRequest:
    underlying_symbol: str
    expiry: date
    limit: int = 100

    def normalized(self) -> OptionAnalyticsHistoryRequest:
        symbol = self.underlying_symbol.strip().upper()
        if not symbol:
            raise ValueError("underlying_symbol is required.")
        if self.limit < 2 or self.limit > 1000:
            raise ValueError("limit must be between 2 and 1000.")
        return OptionAnalyticsHistoryRequest(symbol, self.expiry, self.limit)


@dataclass(frozen=True)
class OptionAnalyticsComparisonRequest:
    current_analytics_id: UUID


@dataclass(frozen=True)
class OptionAnalyticsPair:
    previous: OptionChainAnalytics
    current: OptionChainAnalytics


@dataclass(frozen=True)
class OptionAnalyticsChange:
    change_id: UUID
    previous_analytics_id: UUID
    current_analytics_id: UUID
    previous_source_run_id: UUID
    current_source_run_id: UUID
    underlying_symbol: str
    expiry: date
    previous_captured_at: datetime
    current_captured_at: datetime
    calculated_at: datetime
    elapsed_seconds: int
    spot_price_change: Decimal
    atm_straddle_change: Decimal
    total_call_oi_change: int
    total_put_oi_change: int
    total_pcr_change: Decimal | None
    nearby_call_oi_change: int
    nearby_put_oi_change: int
    nearby_pcr_change: Decimal | None
    atm_mean_iv_change: Decimal | None
    nearby_mean_iv_change: Decimal | None
    call_oi_wall_strike_change: Decimal | None
    put_oi_wall_strike_change: Decimal | None
    call_oi_wall_value_change: int | None
    put_oi_wall_value_change: int | None
    call_wall_changed: bool
    put_wall_changed: bool
    liquidity_coverage_change: Decimal
    price_coverage_change: Decimal
