from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.option_risk_models import OptionRiskRequest
from services.option_risk_repository import OptionRiskRepository
from services.option_risk_service import OptionRiskService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("selection_run_id", type=UUID)
    parser.add_argument("--account-equity", type=Decimal, default=Decimal("1000000"))
    parser.add_argument("--available-capital", type=Decimal, default=Decimal("250000"))
    parser.add_argument("--existing-total-exposure", type=Decimal, default=Decimal("0"))
    parser.add_argument("--max-total-exposure-pct", type=Decimal, default=Decimal("0.25"))
    parser.add_argument("--max-underlying-exposure-pct", type=Decimal, default=Decimal("0.10"))
    parser.add_argument("--max-single-trade-loss-pct", type=Decimal, default=Decimal("0.02"))
    parser.add_argument("--max-lots", type=int, default=10)
    args = parser.parse_args()

    result = OptionRiskService(OptionRiskRepository()).assess_and_persist(
        OptionRiskRequest(
            selection_run_id=args.selection_run_id,
            as_of=datetime.now(),
            account_equity=args.account_equity,
            available_capital=args.available_capital,
            existing_total_exposure=args.existing_total_exposure,
            maximum_total_exposure_pct=args.max_total_exposure_pct,
            maximum_underlying_exposure_pct=args.max_underlying_exposure_pct,
            maximum_single_trade_loss_pct=args.max_single_trade_loss_pct,
            maximum_lots_per_contract=args.max_lots,
        )
    )

    print("Option risk assessment completed")
    print(f"Risk run ID: {result.risk_run_id}")
    print(f"Selection run ID: {result.selection_run_id}")
    print(f"Approved contracts: {len(result.approved)}")
    print(f"Rejected contracts: {len(result.rejected)}")
    print(f"Approved exposure: {result.approved_exposure}")
    for item in result.assessments:
        status = "APPROVED" if item.approved else f"REJECTED:{item.rejection_code}"
        print(
            f"{status} {item.underlying_symbol} {item.expiry} {item.option_type} "
            f"{item.trading_symbol} lots={item.approved_lots} quantity={item.approved_quantity} "
            f"exposure={item.approved_exposure} max_loss={item.maximum_loss}"
        )


if __name__ == "__main__":
    main()
