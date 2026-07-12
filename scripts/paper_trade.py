from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.paper_trading_models import PaperCloseRequest, PaperMarkRequest, PaperOpenRequest
from services.paper_trading_repository import PaperTradingRepository
from services.paper_trading_service import PaperTradingService, PaperTradingStateError


def _as_of(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("as-of must use ISO date-time format") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Operate isolated paper option positions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    open_parser = subparsers.add_parser("open", help="Open a paper position from a persisted signal.")
    open_parser.add_argument("signal_id", type=UUID)
    open_parser.add_argument("--as-of", type=_as_of, default=datetime.now())
    open_parser.add_argument("--slippage-bps", type=Decimal, default=Decimal("10"))
    open_parser.add_argument("--transaction-cost-bps", type=Decimal, default=Decimal("5"))

    mark_parser = subparsers.add_parser("mark", help="Mark an open paper position to persisted data.")
    mark_parser.add_argument("position_id", type=UUID)
    mark_parser.add_argument("--as-of", type=_as_of, default=datetime.now())

    close_parser = subparsers.add_parser("close", help="Close an open paper position with a persisted mark.")
    close_parser.add_argument("position_id", type=UUID)
    close_parser.add_argument("--as-of", type=_as_of, default=datetime.now())
    close_parser.add_argument("--slippage-bps", type=Decimal, default=Decimal("10"))
    close_parser.add_argument("--transaction-cost-bps", type=Decimal, default=Decimal("5"))

    status_parser = subparsers.add_parser("status", help="List simulated positions and P&L.")
    status_parser.add_argument("--status", choices=("OPEN", "CLOSED"))
    status_parser.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    service = PaperTradingService(PaperTradingRepository())
    try:
        _run(args, service)
    except PaperTradingStateError as exc:
        parser.exit(2, f"Paper trading error: {exc}\n")


def _run(args, service) -> None:
    if args.command == "open":
        result = service.open_position(PaperOpenRequest(
            args.signal_id, args.as_of, args.slippage_bps, args.transaction_cost_bps,
        ))
        print(f"Paper order: {result.order.order_id} status={result.order.status}")
        if result.position is None:
            print(f"Rejection: {result.order.rejection_code}")
            return
        print(f"Paper position: {result.position.position_id} status={result.position.status}")
        print(f"Entry: {result.position.entry_price} quantity={result.position.signal.quantity}")
        print(f"Signal lineage: {result.position.signal.signal_id}")
    elif args.command == "mark":
        position = service.mark_position(PaperMarkRequest(args.position_id, args.as_of))
        print(f"Paper position: {position.position_id} status={position.status}")
        print(f"Mark: {position.latest_mark_price} net_pnl={position.net_pnl}")
        print(f"Mark run: {position.latest_mark_run_id}")
    elif args.command == "close":
        result = service.close_position(PaperCloseRequest(
            args.position_id, args.as_of, args.slippage_bps, args.transaction_cost_bps,
        ))
        print(f"Paper order: {result.order.order_id} status={result.order.status}")
        print(f"Paper position: {result.position.position_id} status={result.position.status}")
        print(f"Exit: {result.position.exit_price} net_pnl={result.position.net_pnl}")
        print(f"Signal lineage: {result.position.signal.signal_id}")
    else:
        positions = service.list_positions(args.status, args.limit)
        print(f"Paper positions: {len(positions)}")
        for position in positions:
            print(
                f"{position.position_id} {position.status} "
                f"{position.signal.underlying_symbol} {position.signal.option_type} "
                f"quantity={position.signal.quantity} entry={position.entry_price} "
                f"mark={position.latest_mark_price} net_pnl={position.net_pnl} "
                f"signal={position.signal.signal_id}"
            )


if __name__ == "__main__":
    main()
