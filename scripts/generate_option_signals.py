from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.option_signal_models import OptionSignalRequest
from services.option_signal_repository import OptionSignalRepository
from services.option_signal_service import OptionSignalService


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic option signals.")
    parser.add_argument("risk_run_id", type=UUID)
    parser.add_argument("--minimum-confidence", type=Decimal, default=Decimal("0"))
    args = parser.parse_args()
    result = OptionSignalService(OptionSignalRepository()).generate_and_persist(
        OptionSignalRequest(
            risk_run_id=args.risk_run_id,
            as_of=datetime.now(),
            minimum_confidence=args.minimum_confidence,
        )
    )
    print("Option signal generation completed")
    print(f"Signal run ID: {result.signal_run_id}")
    print(f"Risk run ID: {result.risk_run_id}")
    print(f"Signals generated: {len(result.signals)}")
    for signal in result.signals:
        print(
            f"{signal.action} {signal.underlying_symbol} {signal.expiry} "
            f"{signal.option_type} {signal.trading_symbol} direction={signal.direction} "
            f"context={signal.strategy_context} lots={signal.approved_lots} "
            f"quantity={signal.approved_quantity} entry={signal.entry_price} "
            f"max_loss={signal.maximum_loss} confidence={signal.confidence_score}"
        )


if __name__ == "__main__":
    main()
