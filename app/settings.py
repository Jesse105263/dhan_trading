import os
from dataclasses import dataclass

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


@dataclass(frozen=True)
class PipelineSettings:
    dhan_request_timeout_seconds: int
    dhan_max_instruments_per_request: int
    feature_lookback_runs: int
    log_level: str


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