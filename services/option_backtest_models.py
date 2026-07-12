from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class OptionBacktestRequest:
    signal_run_id: UUID
    as_of: datetime
    target_return: Decimal = Decimal("0.25")
    stop_loss_return: Decimal = Decimal("0.20")
    entry_slippage_bps: Decimal = Decimal("10")
    exit_slippage_bps: Decimal = Decimal("10")
    transaction_cost_bps: Decimal = Decimal("5")

    def normalized(self) -> "OptionBacktestRequest":
        if self.target_return <= 0:
            raise ValueError("target_return must be positive.")
        if not Decimal("0") < self.stop_loss_return < Decimal("1"):
            raise ValueError("stop_loss_return must be between zero and one.")
        for name, value in (
            ("entry_slippage_bps", self.entry_slippage_bps),
            ("exit_slippage_bps", self.exit_slippage_bps),
            ("transaction_cost_bps", self.transaction_cost_bps),
        ):
            if value < 0:
                raise ValueError(f"{name} cannot be negative.")
        return self


@dataclass(frozen=True)
class BacktestSignal:
    signal_id: UUID
    signal_run_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    approved_quantity: int
    entry_price: Decimal
    source_captured_at: datetime
    signal_calculated_at: datetime


@dataclass(frozen=True)
class BacktestMarketMark:
    run_id: UUID
    captured_at: datetime
    last_price: Decimal


@dataclass(frozen=True)
class OptionBacktestTrade:
    backtest_trade_id: UUID
    backtest_run_id: UUID
    signal_id: UUID
    source_run_id: UUID
    exit_run_id: UUID | None
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    quantity: int
    entry_time: datetime
    exit_time: datetime | None
    entry_reference_price: Decimal
    entry_execution_price: Decimal
    exit_reference_price: Decimal | None
    exit_execution_price: Decimal | None
    exit_reason: str
    gross_pnl: Decimal
    transaction_costs: Decimal
    net_pnl: Decimal
    return_rate: Decimal | None


@dataclass(frozen=True)
class OptionBacktestResult:
    backtest_run_id: UUID
    signal_run_id: UUID
    requested_as_of: datetime
    calculated_at: datetime
    methodology_version: str
    parameters: dict[str, Any]
    signal_count: int
    completed_trade_count: int
    skipped_trade_count: int
    gross_pnl: Decimal
    transaction_costs: Decimal
    net_pnl: Decimal
    return_on_exposure: Decimal | None
    win_rate: Decimal | None
    profit_factor: Decimal | None
    maximum_drawdown: Decimal
    trades: tuple[OptionBacktestTrade, ...]
