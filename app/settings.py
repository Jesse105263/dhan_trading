import os
from dataclasses import dataclass
from datetime import date, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


load_dotenv()


def _read_positive_integer(
    name: str,
    default: int,
) -> int:
    raw_value = os.getenv(name, str(default)).strip()

    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(
            f"{name} must be a valid integer."
        ) from error

    if value <= 0:
        raise RuntimeError(
            f"{name} must be greater than zero."
        )

    return value


def _read_log_level() -> str:
    value = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).strip().upper()

    allowed_levels = {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }

    if value not in allowed_levels:
        raise RuntimeError(
            "LOG_LEVEL must be one of: "
            + ", ".join(sorted(allowed_levels))
        )

    return value


def _read_time(
    name: str,
    default: str,
) -> time:
    raw_value = os.getenv(name, default).strip()

    try:
        return time.fromisoformat(raw_value)
    except ValueError as error:
        raise RuntimeError(
            f"{name} must use HH:MM or HH:MM:SS format."
        ) from error


def _read_timezone(
    name: str,
    default: str,
) -> ZoneInfo:
    value = os.getenv(name, default).strip()

    try:
        return ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
        raise RuntimeError(
            f"{name} is not a valid IANA timezone: {value}"
        ) from error


def _read_dates(
    name: str,
) -> frozenset[date]:
    raw_value = os.getenv(name, "").strip()

    if not raw_value:
        return frozenset()

    parsed_dates: set[date] = set()

    for raw_date in raw_value.split(","):
        value = raw_date.strip()

        if not value:
            continue

        try:
            parsed_dates.add(date.fromisoformat(value))
        except ValueError as error:
            raise RuntimeError(
                f"{name} contains an invalid ISO date: {value}"
            ) from error

    return frozenset(parsed_dates)


def _read_non_empty_string(
    name: str,
    default: str,
) -> str:
    value = os.getenv(name, default).strip()

    if not value:
        raise RuntimeError(
            f"{name} must not be empty."
        )

    return value


def _read_aliases(name: str) -> tuple[tuple[str, str], ...]:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return tuple()

    aliases: dict[str, str] = {}
    for item in raw_value.split(","):
        value = item.strip()
        if not value:
            continue
        if "=" not in value:
            raise RuntimeError(
                f"{name} entries must use SOURCE=TARGET format."
            )
        source, target = value.split("=", maxsplit=1)
        source = source.strip().upper()
        target = target.strip().upper()
        if not source or not target:
            raise RuntimeError(
                f"{name} entries must use SOURCE=TARGET format."
            )
        aliases[source] = target

    return tuple(sorted(aliases.items()))


@dataclass(frozen=True)
class DerivativeImportSettings:
    source_url: str
    request_timeout_seconds: int
    max_persisted_failures: int
    symbol_aliases: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class PipelineSettings:
    dhan_request_timeout_seconds: int
    dhan_max_instruments_per_request: int
    feature_lookback_runs: int
    log_level: str


@dataclass(frozen=True)
class SchedulerSettings:
    timezone: ZoneInfo
    market_open_time: time
    market_close_time: time
    market_holidays: frozenset[date]
    lock_name: str
    lock_ttl_seconds: int
    interval_seconds: int


PIPELINE_SETTINGS = PipelineSettings(
    dhan_request_timeout_seconds=(
        _read_positive_integer(
            "DHAN_REQUEST_TIMEOUT_SECONDS",
            30,
        )
    ),
    dhan_max_instruments_per_request=(
        _read_positive_integer(
            "DHAN_MAX_INSTRUMENTS_PER_REQUEST",
            1000,
        )
    ),
    feature_lookback_runs=(
        _read_positive_integer(
            "FEATURE_LOOKBACK_RUNS",
            20,
        )
    ),
    log_level=_read_log_level(),
)


SCHEDULER_SETTINGS = SchedulerSettings(
    timezone=_read_timezone(
        "MARKET_TIMEZONE",
        "Asia/Kolkata",
    ),
    market_open_time=_read_time(
        "MARKET_OPEN_TIME",
        "09:15",
    ),
    market_close_time=_read_time(
        "MARKET_CLOSE_TIME",
        "15:30",
    ),
    market_holidays=_read_dates(
        "MARKET_HOLIDAYS"
    ),
    lock_name=_read_non_empty_string(
        "SCHEDULER_LOCK_NAME",
        "production-market-pipeline",
    ),
    lock_ttl_seconds=_read_positive_integer(
        "SCHEDULER_LOCK_TTL_SECONDS",
        1800,
    ),
    interval_seconds=_read_positive_integer(
        "SCHEDULER_INTERVAL_SECONDS",
        300,
    ),
)


DERIVATIVE_IMPORT_SETTINGS = DerivativeImportSettings(
    source_url=_read_non_empty_string(
        "DHAN_SECURITY_MASTER_URL",
        "https://images.dhan.co/api-data/api-scrip-master-detailed.csv",
    ),
    request_timeout_seconds=_read_positive_integer(
        "DHAN_SECURITY_MASTER_TIMEOUT_SECONDS",
        120,
    ),
    max_persisted_failures=_read_positive_integer(
        "DERIVATIVE_IMPORT_MAX_FAILURES",
        1000,
    ),
    symbol_aliases=_read_aliases(
        "DERIVATIVE_SYMBOL_ALIASES"
    ),
)


if (
    SCHEDULER_SETTINGS.market_close_time
    <= SCHEDULER_SETTINGS.market_open_time
):
    raise RuntimeError(
        "MARKET_CLOSE_TIME must be later than "
        "MARKET_OPEN_TIME."
    )
