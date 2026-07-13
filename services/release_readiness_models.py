from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReleaseCheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True)
class MigrationManifestEntry:
    version: str
    filename: str
    checksum: str


@dataclass(frozen=True)
class AppliedMigration:
    version: str
    filename: str
    checksum: str


@dataclass(frozen=True)
class AuditMetric:
    name: str
    audited_count: int
    violation_count: int

    def __post_init__(self) -> None:
        if self.audited_count < 0 or self.violation_count < 0:
            raise ValueError("Audit counts must not be negative.")


@dataclass(frozen=True)
class ReleaseCheckResult:
    name: str
    status: ReleaseCheckStatus
    summary: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReleaseReadinessReport:
    database_name: str | None
    checks: tuple[ReleaseCheckResult, ...]

    @property
    def ready(self) -> bool:
        return all(
            check.status is not ReleaseCheckStatus.FAIL
            for check in self.checks
        )

    def count(self, status: ReleaseCheckStatus) -> int:
        return sum(check.status is status for check in self.checks)
