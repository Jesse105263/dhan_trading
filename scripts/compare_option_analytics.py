from __future__ import annotations

import argparse
from uuid import UUID

from services.option_analytics_history_models import OptionAnalyticsComparisonRequest
from services.option_analytics_history_repository import OptionAnalyticsHistoryRepository
from services.option_analytics_history_service import OptionAnalyticsHistoryService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare a completed option analytics snapshot with its predecessor."
    )
    parser.add_argument("analytics_id", type=UUID)
    args = parser.parse_args()
    result = OptionAnalyticsHistoryService(
        OptionAnalyticsHistoryRepository()
    ).compare_and_persist(OptionAnalyticsComparisonRequest(args.analytics_id))
    print("Option analytics change detection completed")
    print(f"Change ID: {result.change_id}")
    print(f"Previous analytics ID: {result.previous_analytics_id}")
    print(f"Current analytics ID: {result.current_analytics_id}")
    print(f"Underlying: {result.underlying_symbol}")
    print(f"Expiry: {result.expiry}")
    print(f"Elapsed seconds: {result.elapsed_seconds}")
    print(f"Spot change: {result.spot_price_change}")
    print(f"ATM straddle change: {result.atm_straddle_change}")
    print(f"Total call OI change: {result.total_call_oi_change}")
    print(f"Total put OI change: {result.total_put_oi_change}")
    print(f"Total PCR change: {result.total_pcr_change}")
    print(f"ATM mean IV change: {result.atm_mean_iv_change}")
    print(f"Liquidity coverage change: {result.liquidity_coverage_change}")


if __name__ == "__main__":
    main()
