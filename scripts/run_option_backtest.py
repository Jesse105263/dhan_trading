from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.option_backtest_models import OptionBacktestRequest
from services.option_backtest_repository import OptionBacktestRepository
from services.option_backtest_service import OptionBacktestService


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest a persisted option signal run.")
    parser.add_argument("signal_run_id", type=UUID)
    parser.add_argument("--target-return", type=Decimal, default=Decimal("0.25"))
    parser.add_argument("--stop-loss-return", type=Decimal, default=Decimal("0.20"))
    parser.add_argument("--entry-slippage-bps", type=Decimal, default=Decimal("10"))
    parser.add_argument("--exit-slippage-bps", type=Decimal, default=Decimal("10"))
    parser.add_argument("--transaction-cost-bps", type=Decimal, default=Decimal("5"))
    args = parser.parse_args()

    result = OptionBacktestService(OptionBacktestRepository()).run_and_persist(
        OptionBacktestRequest(
            signal_run_id=args.signal_run_id,
            as_of=datetime.now(),
            target_return=args.target_return,
            stop_loss_return=args.stop_loss_return,
            entry_slippage_bps=args.entry_slippage_bps,
            exit_slippage_bps=args.exit_slippage_bps,
            transaction_cost_bps=args.transaction_cost_bps,
        )
    )
    print("Option backtest completed")
    print(f"Backtest run ID: {result.backtest_run_id}")
    print(f"Signal run ID: {result.signal_run_id}")
    print(f"Signals: {result.signal_count}")
    print(f"Completed trades: {result.completed_trade_count}")
    print(f"Skipped trades: {result.skipped_trade_count}")
    print(f"Gross P&L: {result.gross_pnl}")
    print(f"Transaction costs: {result.transaction_costs}")
    print(f"Net P&L: {result.net_pnl}")
    print(f"Return on exposure: {result.return_on_exposure}")
    print(f"Win rate: {result.win_rate}")
    print(f"Profit factor: {result.profit_factor}")
    print(f"Maximum drawdown: {result.maximum_drawdown}")
    for trade in result.trades:
        print(
            f"{trade.exit_reason} {trade.underlying_symbol} {trade.expiry} "
            f"{trade.option_type} {trade.trading_symbol} quantity={trade.quantity} "
            f"entry={trade.entry_execution_price} exit={trade.exit_execution_price} "
            f"net_pnl={trade.net_pnl} return={trade.return_rate}"
        )


if __name__ == "__main__":
    main()
