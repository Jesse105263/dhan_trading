from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from uuid import UUID, uuid5

from services.v3_scale_models import BackfillSpec, BatchResult, DEPENDENCIES, STAGES, ScalePolicy

NAMESPACE = UUID("9db2a683-62e4-4f62-9aca-594877df0310")


def stable_id(kind: str, value: object) -> UUID:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return uuid5(NAMESPACE, f"{kind}:{payload}")


def checksum(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


class V3ScaleService:
    def __init__(self, repository=None, policy: ScalePolicy = ScalePolicy(), clock=datetime.utcnow):
        self.repository, self.policy, self.clock = repository, policy, clock

    def affected_stages(self, changed: set[str]) -> tuple[str, ...]:
        affected = set(changed)
        while True:
            new = {stage for stage, deps in DEPENDENCIES.items() if affected.intersection(deps)}
            if new <= affected: break
            affected |= new
        return tuple(stage for stage in STAGES if stage in affected)

    def job(self, spec: BackfillSpec) -> dict:
        body = {"dataset_type": spec.dataset_type, "provider_code": spec.provider_code,
                "scope": sorted(spec.scope), "partition_start": spec.partition_start,
                "partition_end": spec.partition_end, "resolution": spec.resolution,
                "policy_version": self.policy.version}
        return {"job_id": stable_id("backfill", body), **body, "priority": spec.priority,
                "dependency_job_id": spec.dependency_job_id, "status": "PENDING",
                "checkpoint": None, "attempt_count": 0, "max_attempts": self.policy.max_attempts,
                "created_at": self.clock(), "updated_at": self.clock()}

    def schedule(self, spec: BackfillSpec) -> UUID:
        row = self.job(spec)
        if self.repository: self.repository.schedule(row)
        return row["job_id"]

    def execute_fixture(self, job: dict, records: list[dict], fail_after: int | None = None) -> BatchResult:
        ordered = sorted(records, key=lambda row: (str(row.get("partition_key", "")), str(row.get("record_id", ""))))
        start = int(job.get("checkpoint") or 0)
        batch = ordered[start:start + self.policy.batch_size]
        if fail_after is not None: batch = batch[:fail_after]
        processed = len(batch); next_offset = start + processed
        complete = next_offset >= len(ordered) and fail_after is None
        digest = checksum([row.get("record_id") for row in batch])
        return BatchResult(processed, None if complete else str(next_offset), complete, digest)

    def retry_state(self, attempt_count: int) -> tuple[str, datetime | None]:
        if attempt_count >= self.policy.max_attempts: return "FAILED", None
        return "RETRYING", self.clock() + timedelta(seconds=min(300, 2 ** attempt_count))

    @staticmethod
    def bulk_batches(rows: list[dict], size: int) -> tuple[tuple[dict, ...], ...]:
        if size < 1: raise ValueError("Batch size must be positive.")
        ordered = sorted(rows, key=lambda row: str(row.get("record_id", row)))
        return tuple(tuple(ordered[i:i + size]) for i in range(0, len(ordered), size))

    @staticmethod
    def retention_policies(now: datetime) -> tuple[dict, ...]:
        policies = (
            ("RAW_PAYLOAD", 2555), ("CANONICAL", None), ("DERIVED_EVIDENCE", None),
            ("RESEARCH_ARTIFACT", None), ("RECOMMENDATION_VALIDATION", None),
            ("AUDIT_HISTORY", None), ("BACKUP", 90),
        )
        return tuple({"policy_id": stable_id("retention", (kind, days, "v3.10")), "record_class": kind,
                      "policy_version": "v3.10", "minimum_days": days, "archive_eligible": False,
                      "destructive_action_enabled": False, "owner_approval_required": True,
                      "created_at": now} for kind, days in policies)
