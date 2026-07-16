from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


STAGES = (
    "CANONICAL", "FEATURE", "OUTCOME", "SIMILARITY", "OPPORTUNITY",
    "CALIBRATION", "VALIDATION", "GOVERNANCE",
)
DEPENDENCIES = {
    "CANONICAL": (), "FEATURE": ("CANONICAL",), "OUTCOME": ("CANONICAL",),
    "SIMILARITY": ("FEATURE", "OUTCOME"), "OPPORTUNITY": ("SIMILARITY",),
    "CALIBRATION": ("OPPORTUNITY", "OUTCOME"),
    "VALIDATION": ("CALIBRATION", "CANONICAL"),
    "GOVERNANCE": ("VALIDATION",),
}
JOB_STATES = {"PENDING", "RUNNING", "PAUSED", "RETRYING", "COMPLETED", "FAILED", "BLOCKED"}


@dataclass(frozen=True)
class ScalePolicy:
    version: str = "v3.10-default"
    batch_size: int = 500
    max_attempts: int = 3
    lease_seconds: int = 300
    concurrency: int = 2

    def __post_init__(self) -> None:
        if not self.version or min(self.batch_size, self.max_attempts, self.lease_seconds, self.concurrency) < 1:
            raise ValueError("Scale policy values must be positive.")


@dataclass(frozen=True)
class BackfillSpec:
    dataset_type: str
    provider_code: str
    scope: tuple[str, ...]
    partition_start: datetime
    partition_end: datetime
    resolution: str
    priority: int = 100
    dependency_job_id: str | None = None

    def __post_init__(self) -> None:
        if self.dataset_type not in STAGES or not self.provider_code or not self.scope:
            raise ValueError("Invalid backfill scope.")
        if self.partition_end < self.partition_start:
            raise ValueError("Backfill partition end precedes start.")


@dataclass(frozen=True)
class BatchResult:
    processed: int
    checkpoint: str | None
    complete: bool
    checksum: str
