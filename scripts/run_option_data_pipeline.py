import argparse
from datetime import timedelta

from app.logging_config import configure_logging
from app.settings import OPTION_PIPELINE_SETTINGS, SCHEDULER_SETTINGS
from services.market_calendar import MarketCalendar
from services.option_data_pipeline import build_option_data_pipeline
from services.scheduler import PipelineScheduler
from services.scheduler_repository import SchedulerRepository


def build_scheduler() -> PipelineScheduler:
    settings = OPTION_PIPELINE_SETTINGS
    return PipelineScheduler(
        pipeline_factory=lambda: build_option_data_pipeline(
            symbols=settings.symbols,
            max_attempts=settings.max_attempts,
            retry_backoff_seconds=settings.retry_backoff_seconds,
            throttle_seconds=settings.throttle_seconds,
            minimum_days_to_expiry=settings.minimum_days_to_expiry,
            maximum_days_to_expiry=settings.maximum_days_to_expiry,
            nearby_strikes_each_side=settings.nearby_strikes_each_side,
            maximum_source_age=timedelta(seconds=settings.maximum_source_age_seconds),
            request_timeout_seconds=settings.request_timeout_seconds,
        ),
        calendar=MarketCalendar(
            timezone=SCHEDULER_SETTINGS.timezone,
            open_time=SCHEDULER_SETTINGS.market_open_time,
            close_time=SCHEDULER_SETTINGS.market_close_time,
            holidays=SCHEDULER_SETTINGS.market_holidays,
        ),
        repository=SchedulerRepository(),
        lock_name=settings.lock_name,
        lock_ttl_seconds=settings.lock_ttl_seconds,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run option data pipeline once.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    configure_logging()
    result = build_scheduler().run_once(force=args.force)
    print(f"Option pipeline status: {result.status}")
    print(f"Reason: {result.reason}")
    return 0 if result.status in {"COMPLETED", "SKIPPED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
