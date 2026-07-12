from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PaperOpenRequest:
    signal_id: UUID
    as_of: datetime
    slippage_bps: Decimal = Decimal("10")
    transaction_cost_bps: Decimal = Decimal("5")

    def normalized(self) -> "PaperOpenRequest":
        if self.slippage_bps < 0 or self.transaction_cost_bps < 0:
            raise ValueError("Paper slippage and transaction cost cannot be negative.")
        return self


@dataclass(frozen=True)
class PaperMarkRequest:
    position_id: UUID
    as_of: datetime


@dataclass(frozen=True)
class PaperCloseRequest:
    position_id: UUID
    as_of: datetime
    slippage_bps: Decimal = Decimal("10")
    transaction_cost_bps: Decimal = Decimal("5")

    def normalized(self) -> "PaperCloseRequest":
        if self.slippage_bps < 0 or self.transaction_cost_bps < 0:
            raise ValueError("Paper slippage and transaction cost cannot be negative.")
        return self


@dataclass(frozen=True)
class PaperSignal:
    signal_id: UUID
    signal_run_id: UUID
    risk_run_id: UUID
    assessment_id: UUID
    selection_id: UUID
    ranking_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    quantity: int
    signal_entry_price: Decimal
    source_captured_at: datetime
    signal_calculated_at: datetime


@dataclass(frozen=True)
class PaperMarketMark:
    run_id: UUID
    captured_at: datetime
    last_price: Decimal


@dataclass(frozen=True)
class PaperOrder:
    order_id: UUID
    signal_id: UUID
    source_run_id: UUID
    side: str
    quantity: int
    status: str
    requested_at: datetime
    filled_at: datetime | None
    reference_run_id: UUID | None
    reference_price: Decimal | None
    fill_price: Decimal | None
    rejection_code: str | None


@dataclass(frozen=True)
class PaperFill:
    fill_id: UUID
    order_id: UUID
    position_id: UUID
    side: str
    quantity: int
    reference_run_id: UUID
    reference_price: Decimal
    fill_price: Decimal
    filled_at: datetime
    transaction_cost: Decimal


@dataclass(frozen=True)
class PaperPosition:
    position_id: UUID
    signal: PaperSignal
    entry_order_id: UUID
    exit_order_id: UUID | None
    status: str
    entry_run_id: UUID
    entry_time: datetime
    entry_price: Decimal
    latest_mark_run_id: UUID
    latest_mark_time: datetime
    latest_mark_price: Decimal
    exit_run_id: UUID | None
    exit_time: datetime | None
    exit_price: Decimal | None
    gross_pnl: Decimal
    transaction_costs: Decimal
    net_pnl: Decimal
    updated_at: datetime


@dataclass(frozen=True)
class PaperOpenResult:
    order: PaperOrder
    position: PaperPosition | None
    fill: PaperFill | None


@dataclass(frozen=True)
class PaperCloseResult:
    order: PaperOrder
    position: PaperPosition
    fill: PaperFill
