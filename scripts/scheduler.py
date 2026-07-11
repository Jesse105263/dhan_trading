import argparse
import time
from datetime import datetime

from app.logging_config import configure_logging
from app.settings import SCHEDULER_SETTINGS
from services.market_calendar import MarketCalendar
from services.production_pipeline import (
    build_production_pipeline,
)
from services.scheduler import PipelineScheduler
from services.scheduler_repository import (
    SchedulerRepository,
)


def build_scheduler() -> PipelineScheduler:
    calendar = MarketCalendar(
        timezone=SCHEDULER_SETTINGS.timezone,
        open_time=(
            SCHEDULER_SETTINGS.market_open_time
        ),
        close_time=(
            SCHEDULER_SETTINGS.market_close_time
        ),
        holidays=(
            SCHEDULER_SETTINGS.market_holidays
        ),
    )

    return PipelineScheduler(
        pipeline_factory=build_production_pipeline,
        calendar=calendar,
        repository=SchedulerRepository(),
        lock_name=SCHEDULER_SETTINGS.lock_name,
        lock_ttl_seconds=(
            SCHEDULER_SETTINGS.lock_ttl_seconds
        ),
    )


def _run_once(
    scheduler: PipelineScheduler,
    force: bool,
) -> int:
    result = scheduler.run_once(
        force=force
    )

    print(f"Scheduler status: {result.status}")
    print(f"Reason: {result.reason}")

    return 0


def _show_status(
    scheduler: PipelineScheduler,
) -> int:
    status = scheduler.status()

    print(
        "Checked at: "
        f"{status.market.checked_at.isoformat()}"
    )
    print(
        "Market allowed: "
        f"{status.market.allowed}"
    )
    print(
        "Market reason: "
        f"{status.market.reason}"
    )

    if status.lock is None:
        print("Lock status: FREE")
        return 0

    lock_state = (
        "STALE"
        if status.lock_is_stale
        else "ACTIVE"
    )

    print(f"Lock status: {lock_state}")
    print(f"Lock name: {status.lock.lock_name}")
    print(
        "Lock acquired at: "
        f"{status.lock.acquired_at.isoformat()}"
    )
    print(
        "Lock heartbeat at: "
        f"{status.lock.heartbeat_at.isoformat()}"
    )
    print(
        "Lock expires at: "
        f"{status.lock.expires_at.isoformat()}"
    )

    return 0


def _run_loop(
    scheduler: PipelineScheduler,
    interval_seconds: int,
) -> int:
    print(
        "Scheduler loop started | interval_seconds="
        f"{interval_seconds}"
    )

    try:
        while True:
            started_at = datetime.now()

            try:
                result = scheduler.run_once()
                print(
                    f"{started_at.isoformat()} | "
                    f"{result.status} | {result.reason}"
                )
            except Exception as error:
                print(
                    f"{started_at.isoformat()} | "
                    f"FAILED | {type(error).__name__}: "
                    f"{error}"
                )

            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Scheduler loop stopped.")

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run and inspect the Dhan production "
            "pipeline scheduler."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run one controlled scheduler cycle.",
    )
    run_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Ignore market-day and market-hours "
            "validation. The run lock is still enforced."
        ),
    )

    subparsers.add_parser(
        "status",
        help="Show market-session and run-lock status.",
    )

    loop_parser = subparsers.add_parser(
        "loop",
        help="Run recurring controlled scheduler cycles.",
    )
    loop_parser.add_argument(
        "--interval-seconds",
        type=int,
        default=(
            SCHEDULER_SETTINGS.interval_seconds
        ),
        help="Seconds between scheduler cycles.",
    )

    return parser


def main() -> int:
    configure_logging()
    parser = _build_parser()
    arguments = parser.parse_args()
    scheduler = build_scheduler()

    if arguments.command == "run":
        return _run_once(
            scheduler=scheduler,
            force=arguments.force,
        )

    if arguments.command == "status":
        return _show_status(scheduler)

    if arguments.command == "loop":
        if arguments.interval_seconds <= 0:
            parser.error(
                "--interval-seconds must be greater than zero."
            )

        return _run_loop(
            scheduler=scheduler,
            interval_seconds=(
                arguments.interval_seconds
            ),
        )

    parser.error("Unknown scheduler command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
