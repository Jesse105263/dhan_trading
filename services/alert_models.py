from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


SOURCE_TYPES = frozenset({"SIGNAL", "RISK_DECISION", "PIPELINE_HEALTH"})
SEVERITIES = frozenset({"INFO", "WARNING", "CRITICAL"})


@dataclass(frozen=True)
class AlertCandidate:
    source_type: str
    source_id: str
    source_run_id: str
    severity: str
    title: str
    message: str
    payload: dict[str, Any]
    occurred_at: datetime

    def normalized(self) -> "AlertCandidate":
        source_type = self.source_type.strip().upper()
        severity = self.severity.strip().upper()
        source_id = self.source_id.strip()
        source_run_id = self.source_run_id.strip()
        title = self.title.strip()
        message = self.message.strip()
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"Unsupported alert source type: {source_type}")
        if severity not in SEVERITIES:
            raise ValueError(f"Unsupported alert severity: {severity}")
        if not source_id or not source_run_id or not title or not message:
            raise ValueError("Alert identity, title and message must not be empty.")
        return AlertCandidate(
            source_type, source_id, source_run_id, severity, title, message,
            dict(self.payload), self.occurred_at,
        )


@dataclass(frozen=True)
class AlertEvent:
    alert_id: UUID
    source_type: str
    source_id: str
    source_run_id: str
    severity: str
    title: str
    message: str
    payload: dict[str, Any]
    occurred_at: datetime
    created_at: datetime


@dataclass(frozen=True)
class PersistedAlert:
    event: AlertEvent
    created: bool


@dataclass(frozen=True)
class AlertRunResult:
    candidates_found: int
    alerts_created: int
    duplicate_alerts: int
    deliveries_succeeded: int
    deliveries_failed: int
    deliveries_skipped: int
    alert_ids: tuple[UUID, ...]
