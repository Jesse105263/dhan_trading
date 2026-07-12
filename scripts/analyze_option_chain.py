from __future__ import annotations

import argparse
from datetime import timedelta
from uuid import UUID

from services.option_analytics_models import OptionAnalyticsRequest
from services.option_analytics_repository import OptionAnalyticsRepository
from services.option_analytics_service import OptionAnalyticsService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate and persist analytics for a completed option-chain run."
    )
    parser.add_argument("run_id", type=UUID)
    parser.add_argument("--nearby-strikes", type=int, default=5)
    parser.add_argument("--maximum-age-hours", type=float, default=24.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    service = OptionAnalyticsService(OptionAnalyticsRepository())
    analytics = service.calculate_and_persist(
        OptionAnalyticsRequest(
            source_run_id=args.run_id,
            nearby_strikes_each_side=args.nearby_strikes,
            maximum_source_age=timedelta(hours=args.maximum_age_hours),
        )
    )
    print("Option-chain analytics completed")
    print(f"Analytics ID: {analytics.analytics_id}")
    print(f"Source run ID: {analytics.source_run_id}")
    print(f"Underlying: {analytics.underlying_symbol}")
    print(f"Expiry: {analytics.expiry}")
    print(f"ATM strike: {analytics.atm_strike}")
    print(f"ATM straddle: {analytics.atm_straddle_cost}")
    print(f"Total PCR: {analytics.total_pcr}")
    print(f"Nearby PCR: {analytics.nearby_pcr}")
    print(f"Call OI wall: {analytics.call_oi_wall_strike}")
    print(f"Put OI wall: {analytics.put_oi_wall_strike}")
    print(f"Liquidity coverage: {analytics.liquidity_coverage}")


if __name__ == "__main__":
    main()
