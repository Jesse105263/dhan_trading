from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class OptionRankingRequest:
    as_of: datetime
    maximum_age: timedelta = timedelta(hours=24)
    minimum_liquidity_coverage: Decimal = Decimal("0.10")

    def normalized(self) -> "OptionRankingRequest":
        if self.maximum_age <= timedelta(0):
            raise ValueError("maximum_age must be positive.")
        if not Decimal("0") <= self.minimum_liquidity_coverage <= Decimal("1"):
            raise ValueError("minimum_liquidity_coverage must be between 0 and 1.")
        return self


@dataclass(frozen=True)
class OptionRankingCandidate:
    analytics_id: UUID
    change_id: UUID
    underlying_symbol: str
    expiry: date
    source_captured_at: datetime
    liquidity_coverage: Decimal
    price_coverage: Decimal
    total_call_oi_change: int
    total_put_oi_change: int
    atm_straddle_change: Decimal
    atm_mean_iv_change: Decimal | None
    total_pcr: Decimal | None
    total_pcr_change: Decimal | None
    spot_price: Decimal
    call_oi_wall_strike: Decimal | None
    put_oi_wall_strike: Decimal | None


@dataclass(frozen=True)
class OptionRanking:
    ranking_id: UUID
    ranking_run_id: UUID
    analytics_id: UUID
    change_id: UUID
    underlying_symbol: str
    expiry: date
    source_captured_at: datetime
    rank_position: int
    total_score: Decimal
    liquidity_score: Decimal
    activity_score: Decimal
    volatility_score: Decimal
    directional_score: Decimal
    explanation: dict[str, str]


@dataclass(frozen=True)
class OptionRankingResult:
    ranking_run_id: UUID
    as_of: datetime
    calculated_at: datetime
    methodology_version: str
    rankings: tuple[OptionRanking, ...]
