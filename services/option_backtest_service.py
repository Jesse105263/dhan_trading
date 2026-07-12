from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable
from uuid import uuid4

from services.option_backtest_models import (
    BacktestMarketMark,
    BacktestSignal,
    OptionBacktestRequest,
    OptionBacktestResult,
    OptionBacktestTrade,
)


class OptionBacktestEligibilityError(ValueError):
    pass


class OptionBacktestService:
    METHODOLOGY_VERSION = "persisted-option-marks-v1"
    MONEY = Decimal("0.01")
    PRICE = Decimal("0.000001")
    RATE = Decimal("0.00000001")
    BPS = Decimal("10000")

    def __init__(self, repository, clock: Callable[[], datetime] = datetime.now) -> None:
        self.repository = repository
        self.clock = clock

    def run_and_persist(self, request: OptionBacktestRequest) -> OptionBacktestResult:
        request = request.normalized()
        signals = self.repository.list_signals(request.signal_run_id)
        if not signals:
            raise OptionBacktestEligibilityError("Signal run has no persisted signals.")

        run_id = uuid4()
        trades: list[OptionBacktestTrade] = []
        for signal in signals:
            self._validate_signal(signal, request)
            marks = self.repository.list_future_marks(signal, request.as_of)
            trades.append(self._simulate(run_id, signal, marks, request))

        completed = [trade for trade in trades if trade.exit_reason != "NO_FUTURE_MARK"]
        skipped_count = len(trades) - len(completed)
        gross_pnl = self._money(sum((trade.gross_pnl for trade in completed), Decimal("0")))
        costs = self._money(sum((trade.transaction_costs for trade in completed), Decimal("0")))
        net_pnl = self._money(sum((trade.net_pnl for trade in completed), Decimal("0")))
        exposure = sum(
            (trade.entry_execution_price * trade.quantity for trade in completed),
            Decimal("0"),
        )
        return_on_exposure = self._rate(net_pnl / exposure) if exposure > 0 else None
        wins = [trade for trade in completed if trade.net_pnl > 0]
        losses = [trade for trade in completed if trade.net_pnl < 0]
        win_rate = self._rate(Decimal(len(wins)) / Decimal(len(completed))) if completed else None
        gross_profit = sum((trade.net_pnl for trade in wins), Decimal("0"))
        gross_loss = abs(sum((trade.net_pnl for trade in losses), Decimal("0")))
        profit_factor = self._rate(gross_profit / gross_loss) if gross_loss > 0 else None
        maximum_drawdown = self._maximum_drawdown(completed)

        result = OptionBacktestResult(
            backtest_run_id=run_id,
            signal_run_id=request.signal_run_id,
            requested_as_of=request.as_of,
            calculated_at=self.clock(),
            methodology_version=self.METHODOLOGY_VERSION,
            parameters={
                "target_return": str(request.target_return),
                "stop_loss_return": str(request.stop_loss_return),
                "entry_slippage_bps": str(request.entry_slippage_bps),
                "exit_slippage_bps": str(request.exit_slippage_bps),
                "transaction_cost_bps": str(request.transaction_cost_bps),
            },
            signal_count=len(signals),
            completed_trade_count=len(completed),
            skipped_trade_count=skipped_count,
            gross_pnl=gross_pnl,
            transaction_costs=costs,
            net_pnl=net_pnl,
            return_on_exposure=return_on_exposure,
            win_rate=win_rate,
            profit_factor=profit_factor,
            maximum_drawdown=maximum_drawdown,
            trades=tuple(trades),
        )
        return self.repository.persist(result)

    def _simulate(
        self,
        run_id,
        signal: BacktestSignal,
        marks: list[BacktestMarketMark],
        request: OptionBacktestRequest,
    ) -> OptionBacktestTrade:
        entry_execution = self._price(
            signal.entry_price * (Decimal("1") + request.entry_slippage_bps / self.BPS)
        )
        if not marks:
            return OptionBacktestTrade(
                uuid4(), run_id, signal.signal_id, signal.source_run_id, None,
                signal.underlying_symbol, signal.expiry, signal.option_type,
                signal.security_id, signal.trading_symbol, signal.approved_quantity,
                signal.source_captured_at, None, signal.entry_price, entry_execution,
                None, None, "NO_FUTURE_MARK", Decimal("0.00"), Decimal("0.00"),
                Decimal("0.00"), None,
            )

        target = entry_execution * (Decimal("1") + request.target_return)
        stop = entry_execution * (Decimal("1") - request.stop_loss_return)
        chosen = marks[-1]
        reason = "LAST_AVAILABLE"
        for mark in marks:
            if mark.last_price >= target:
                chosen = mark
                reason = "TARGET"
                break
            if mark.last_price <= stop:
                chosen = mark
                reason = "STOP_LOSS"
                break

        exit_execution = self._price(
            chosen.last_price * (Decimal("1") - request.exit_slippage_bps / self.BPS)
        )
        gross = self._money((exit_execution - entry_execution) * signal.approved_quantity)
        entry_notional = entry_execution * signal.approved_quantity
        exit_notional = exit_execution * signal.approved_quantity
        costs = self._money(
            (entry_notional + exit_notional) * request.transaction_cost_bps / self.BPS
        )
        net = self._money(gross - costs)
        rate = self._rate(net / entry_notional) if entry_notional > 0 else None
        return OptionBacktestTrade(
            uuid4(), run_id, signal.signal_id, signal.source_run_id, chosen.run_id,
            signal.underlying_symbol, signal.expiry, signal.option_type,
            signal.security_id, signal.trading_symbol, signal.approved_quantity,
            signal.source_captured_at, chosen.captured_at,
            signal.entry_price, entry_execution, chosen.last_price, exit_execution,
            reason, gross, costs, net, rate,
        )

    @staticmethod
    def _validate_signal(signal: BacktestSignal, request: OptionBacktestRequest) -> None:
        if signal.signal_run_id != request.signal_run_id:
            raise OptionBacktestEligibilityError("Signal belongs to another signal run.")
        if signal.approved_quantity <= 0 or signal.entry_price <= 0:
            raise OptionBacktestEligibilityError("Signal has invalid entry data.")
        if signal.source_captured_at > request.as_of:
            raise OptionBacktestEligibilityError("Signal source is newer than backtest as-of time.")
        if signal.expiry < signal.source_captured_at.date():
            raise OptionBacktestEligibilityError("Signal contract was expired at entry.")

    def _maximum_drawdown(self, trades: list[OptionBacktestTrade]) -> Decimal:
        equity = Decimal("0")
        peak = Decimal("0")
        maximum = Decimal("0")
        for trade in sorted(trades, key=lambda item: (item.exit_time, str(item.signal_id))):
            equity += trade.net_pnl
            peak = max(peak, equity)
            maximum = max(maximum, peak - equity)
        return self._money(maximum)

    @classmethod
    def _money(cls, value: Decimal) -> Decimal:
        return Decimal(value).quantize(cls.MONEY, rounding=ROUND_HALF_UP)

    @classmethod
    def _price(cls, value: Decimal) -> Decimal:
        return Decimal(value).quantize(cls.PRICE, rounding=ROUND_HALF_UP)

    @classmethod
    def _rate(cls, value: Decimal) -> Decimal:
        return Decimal(value).quantize(cls.RATE, rounding=ROUND_HALF_UP)
