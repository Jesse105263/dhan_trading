from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


OUTCOME_STATES = {"COMPLETE", "UNKNOWN", "INSUFFICIENT", "AMBIGUOUS"}
TERMINAL_REASONS = {"TARGET", "STOP", "TIMEOUT", "EXPIRY", "MISSING_DATA", "CORPORATE_ACTION", "AMBIGUOUS_BARRIER"}


@dataclass(frozen=True)
class OutcomeHorizon:
    code: str
    duration_seconds: int | None = None
    trading_sessions: int | None = None
    through_expiry: bool = False

    def __post_init__(self) -> None:
        modes = sum((self.duration_seconds is not None, self.trading_sessions is not None, self.through_expiry))
        if not self.code or modes != 1:
            raise ValueError("A horizon requires exactly one duration, session count, or expiry mode.")
        if self.duration_seconds is not None and self.duration_seconds <= 0:
            raise ValueError("Horizon duration must be positive.")
        if self.trading_sessions is not None and self.trading_sessions <= 0:
            raise ValueError("Horizon session count must be positive.")


@dataclass(frozen=True)
class OutcomePolicy:
    model_version: str
    horizons: tuple[OutcomeHorizon, ...]
    target_return_pct: Decimal | None = None
    stop_return_pct: Decimal | None = None
    total_cost_bps: Decimal = Decimal("0")
    minimum_path_observations: int = 1

    def __post_init__(self) -> None:
        if not self.model_version or not self.horizons:
            raise ValueError("Outcome policy requires a version and horizons.")
        if len({item.code for item in self.horizons}) != len(self.horizons):
            raise ValueError("Outcome horizon codes must be unique.")
        if self.total_cost_bps < 0 or self.minimum_path_observations < 1:
            raise ValueError("Outcome costs and minimum observations must be non-negative/positive.")
        if (self.target_return_pct is None) != (self.stop_return_pct is None):
            raise ValueError("Target and stop barriers must be configured together.")
        if self.target_return_pct is not None and (self.target_return_pct <= 0 or self.stop_return_pct >= 0):
            raise ValueError("Target must be positive and stop must be negative.")


@dataclass(frozen=True)
class OutcomeAnchor:
    bar_revision_id: UUID
    instrument_id: UUID
    instrument_class: str
    underlying_instrument_id: UUID | None
    interval_code: str
    session_date: object
    bar_close_at: datetime
    available_at: datetime
    expiry: object | None
    close_price: Decimal
    manifest_id: UUID


@dataclass(frozen=True)
class OutcomePathBar:
    bar_revision_id: UUID
    manifest_id: UUID
    session_date: object
    bar_open_at: datetime
    bar_close_at: datetime
    available_at: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal


@dataclass(frozen=True)
class OutcomeMaterializationResult:
    run_id: UUID
    anchor_count: int
    outcome_count: int
    complete_count: int
    unknown_count: int
    insufficient_count: int
    ambiguous_count: int
