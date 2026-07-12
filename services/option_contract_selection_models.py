from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class OptionContractSelectionRequest:
    ranking_run_id: UUID
    as_of: datetime
    top_underlyings: int = 10
    maximum_source_age: timedelta = timedelta(hours=24)
    maximum_distance_pct: Decimal = Decimal("0.05")
    maximum_spread_pct: Decimal = Decimal("0.20")
    minimum_open_interest: int = 1
    minimum_volume: int = 0
    maximum_premium_per_lot: Decimal | None = None

    def normalized(self) -> OptionContractSelectionRequest:
        if self.top_underlyings <= 0:
            raise ValueError("top_underlyings must be positive.")
        if self.maximum_source_age <= timedelta(0):
            raise ValueError("maximum_source_age must be positive.")
        if self.maximum_distance_pct < 0:
            raise ValueError("maximum_distance_pct cannot be negative.")
        if self.maximum_spread_pct < 0:
            raise ValueError("maximum_spread_pct cannot be negative.")
        if self.minimum_open_interest < 0 or self.minimum_volume < 0:
            raise ValueError("minimum liquidity values cannot be negative.")
        if (
            self.maximum_premium_per_lot is not None
            and self.maximum_premium_per_lot <= 0
        ):
            raise ValueError("maximum_premium_per_lot must be positive.")
        return self


@dataclass(frozen=True)
class RankedUnderlying:
    ranking_id: UUID
    ranking_run_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    source_captured_at: datetime
    rank_position: int
    ranking_score: Decimal
    spot_price: Decimal


@dataclass(frozen=True)
class ContractCandidate:
    ranking_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    strike: Decimal
    spot_price: Decimal
    last_price: Decimal | None
    bid_price: Decimal | None
    ask_price: Decimal | None
    open_interest: int
    volume: int
    lot_size: int


@dataclass(frozen=True)
class OptionContractSelection:
    selection_id: UUID
    selection_run_id: UUID
    ranking_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    strike: Decimal
    spot_price: Decimal
    last_price: Decimal
    bid_price: Decimal | None
    ask_price: Decimal | None
    open_interest: int
    volume: int
    lot_size: int
    distance_pct: Decimal
    spread_pct: Decimal | None
    premium_per_lot: Decimal
    contract_score: Decimal
    explanation: dict[str, str]


@dataclass(frozen=True)
class OptionContractSelectionResult:
    selection_run_id: UUID
    ranking_run_id: UUID
    as_of: datetime
    calculated_at: datetime
    methodology_version: str
    requested_underlying_count: int
    selections: tuple[OptionContractSelection, ...]
