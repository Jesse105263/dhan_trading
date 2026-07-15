from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID


DATASET_TYPES = {
    "INSTRUMENT_MASTER", "UNDERLYING_BARS", "INDEX_BARS", "FUTURES_BARS",
    "OPTION_CONTRACT_BARS", "OPTION_CHAIN_SNAPSHOTS", "QUOTE_DEPTH_SNAPSHOTS",
    "CORPORATE_ACTIONS", "EVENTS_ANNOUNCEMENTS",
}
SESSIONS = {"PRE_OPEN", "REGULAR", "CLOSE", "POST_CLOSE", "NON_TRADING"}
WORK_STATUSES = {"PENDING", "RUNNING", "RETRYING", "COMPLETED", "PARTIAL", "FAILED", "UNAVAILABLE"}


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: int = 30
    multiplier: int = 2
    maximum_delay_seconds: int = 900

    def delay(self, attempt: int) -> int:
        return min(self.maximum_delay_seconds, self.initial_delay_seconds * self.multiplier ** max(0, attempt - 1))


@dataclass(frozen=True)
class CollectionWork:
    work_id: UUID
    provider_code: str
    dataset_type: str
    scope: tuple[str, ...]
    requested_start: datetime | None
    requested_end: datetime | None
    resolution: str | None
    session: str
    priority: int
    retry_policy: RetryPolicy
    source_lineage: dict[str, Any]
    created_at: datetime
    status: str = "PENDING"
    attempt_count: int = 0
    next_retry_at: datetime | None = None
    terminal_failure_state: str | None = None
    schedule_id: UUID | None = None
    repair_job_id: UUID | None = None


@dataclass(frozen=True)
class ProviderBatch:
    payload: bytes
    content_type: str
    provider_schema_version: str
    captured_at: datetime
    received_at: datetime
    succeeded_scope: tuple[str, ...]
    failed_scope: tuple[str, ...] = ()
    quota_remaining: int | None = None
    quota_resets_at: datetime | None = None


@dataclass(frozen=True)
class CoverageExpectation:
    provider_code: str
    dataset_type: str
    instrument_id: UUID
    session_date: date
    resolution: str
    expected_intervals: tuple[datetime, ...]
    expected_expiries: tuple[date, ...] = ()
    expected_contract_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class CoverageSnapshot:
    expected_sessions: tuple[date, ...] = ()
    observed_sessions: tuple[date, ...] = ()
    expected_intervals: tuple[str, ...] = ()
    observed_intervals: tuple[str, ...] = ()
    expected_symbols: tuple[str, ...] = ()
    observed_symbols: tuple[str, ...] = ()
    expected_expiries: tuple[date, ...] = ()
    observed_expiries: tuple[date, ...] = ()
    expected_contracts: tuple[str, ...] = ()
    observed_contracts: tuple[str, ...] = ()
    expected_revision: str | None = None
    observed_revision: str | None = None


@dataclass(frozen=True)
class CollectionRunSummary:
    claimed: int
    completed: int
    partial: int
    retrying: int
    failed: int
    unavailable: int


@dataclass(frozen=True)
class CollectionHealth:
    metrics: dict[str, int | float | None]
    measured_at: datetime
