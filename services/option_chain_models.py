from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class OptionChainCollectionRequest:
    underlying_symbol: str
    expiry: date | None = None
    minimum_days_to_expiry: int = 0
    maximum_days_to_expiry: int | None = None

    def normalized(self) -> OptionChainCollectionRequest:
        symbol = self.underlying_symbol.strip().upper()
        if not symbol:
            raise ValueError("underlying_symbol is required.")
        if self.minimum_days_to_expiry < 0:
            raise ValueError(
                "minimum_days_to_expiry cannot be negative."
            )
        if (
            self.maximum_days_to_expiry is not None
            and self.maximum_days_to_expiry
            < self.minimum_days_to_expiry
        ):
            raise ValueError(
                "maximum_days_to_expiry cannot be less than "
                "minimum_days_to_expiry."
            )
        return OptionChainCollectionRequest(
            underlying_symbol=symbol,
            expiry=self.expiry,
            minimum_days_to_expiry=self.minimum_days_to_expiry,
            maximum_days_to_expiry=self.maximum_days_to_expiry,
        )


@dataclass(frozen=True)
class UnderlyingIdentity:
    symbol: str
    security_id: str
    segment: str


@dataclass(frozen=True)
class OptionQuoteSnapshot:
    underlying_symbol: str
    expiry: date
    strike: Decimal
    option_type: str
    captured_at: datetime
    security_id: str | None = None
    last_price: Decimal | None = None
    implied_volatility: Decimal | None = None
    open_interest: int | None = None
    volume: int | None = None
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None


@dataclass(frozen=True)
class NormalizedOptionChain:
    spot_price: Decimal | None
    quotes: tuple[OptionQuoteSnapshot, ...]

    @property
    def strike_count(self) -> int:
        return len({quote.strike for quote in self.quotes})


@dataclass(frozen=True)
class OptionChainCollectionResult:
    run_id: UUID
    underlying_symbol: str
    underlying_security_id: str
    expiry: date
    spot_price: Decimal | None
    strikes_received: int
    quotes_received: int
    quotes_inserted: int
