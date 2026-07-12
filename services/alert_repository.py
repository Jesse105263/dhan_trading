from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from services.alert_models import AlertCandidate, AlertEvent, PersistedAlert
from services.database import get_connection


class AlertRepository:
    """Database-only boundary for persisted alert sources and audit records."""

    def list_candidates(self, source_types: tuple[str, ...], limit: int) -> list[AlertCandidate]:
        if not source_types:
            return []
        candidates: list[AlertCandidate] = []
        if "SIGNAL" in source_types:
            candidates.extend(self._signal_candidates(limit))
        if "RISK_DECISION" in source_types:
            candidates.extend(self._risk_candidates(limit))
        if "PIPELINE_HEALTH" in source_types:
            candidates.extend(self._pipeline_candidates(limit))
        return sorted(
            candidates,
            key=lambda item: (item.occurred_at, item.source_type, item.source_id),
            reverse=True,
        )[:limit]

    def ensure_alert(self, candidate: AlertCandidate, created_at: datetime) -> PersistedAlert:
        normalized = candidate.normalized()
        alert_id = uuid4()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO alert_events (
                        alert_id, source_type, source_id, source_run_id, severity,
                        title, message, payload, occurred_at, created_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (source_type, source_id) DO NOTHING
                    RETURNING alert_id, source_type, source_id, source_run_id, severity,
                              title, message, payload, occurred_at, created_at
                    """,
                    (
                        alert_id, normalized.source_type, normalized.source_id,
                        normalized.source_run_id, normalized.severity, normalized.title,
                        normalized.message, Jsonb(normalized.payload), normalized.occurred_at,
                        created_at,
                    ),
                )
                row = cursor.fetchone()
                created = row is not None
                if row is None:
                    cursor.execute(
                        """
                        SELECT alert_id, source_type, source_id, source_run_id, severity,
                               title, message, payload, occurred_at, created_at
                        FROM alert_events WHERE source_type = %s AND source_id = %s
                        """,
                        (normalized.source_type, normalized.source_id),
                    )
                    row = cursor.fetchone()
            connection.commit()
        if row is None:
            raise RuntimeError("Alert event could not be persisted or loaded.")
        return PersistedAlert(self._event(row), created)

    def was_delivered(self, alert_id: UUID, channel_name: str) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM alert_delivery_attempts WHERE alert_id = %s AND channel_name = %s AND status = 'DELIVERED'",
                    (alert_id, channel_name),
                )
                return cursor.fetchone() is not None

    def start_delivery(self, alert_id: UUID, channel_name: str, started_at: datetime) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(attempt_number), 0) + 1
                    FROM alert_delivery_attempts
                    WHERE alert_id = %s AND channel_name = %s
                    """,
                    (alert_id, channel_name),
                )
                attempt_number = int(cursor.fetchone()[0])
                cursor.execute(
                    """
                    INSERT INTO alert_delivery_attempts (
                        alert_id, channel_name, attempt_number, status, started_at
                    ) VALUES (%s,%s,%s,'PENDING',%s) RETURNING attempt_id
                    """,
                    (alert_id, channel_name, attempt_number, started_at),
                )
                attempt_id = int(cursor.fetchone()[0])
            connection.commit()
        return attempt_id

    def finish_delivery(
        self,
        attempt_id: int,
        delivered: bool,
        completed_at: datetime,
        error_message: str | None = None,
    ) -> None:
        status = "DELIVERED" if delivered else "FAILED"
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE alert_delivery_attempts
                    SET status = %s, completed_at = %s, error_message = %s
                    WHERE attempt_id = %s AND status = 'PENDING'
                    """,
                    (status, completed_at, error_message, attempt_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("Pending alert delivery attempt was not found.")
            connection.commit()

    @staticmethod
    def _signal_candidates(limit: int) -> list[AlertCandidate]:
        query = """
            SELECT s.signal_id, s.signal_run_id, s.underlying_symbol, s.expiry,
                   s.option_type, s.trading_symbol, s.action, s.direction,
                   s.strategy_context, s.approved_lots, s.approved_quantity,
                   s.entry_price, s.maximum_loss, s.confidence_score, s.rationale,
                   s.created_at
            FROM option_signals s
            ORDER BY s.created_at DESC, s.signal_id DESC LIMIT %s
        """
        rows = AlertRepository._fetch_all(query, (limit,))
        return [AlertCandidate(
            "SIGNAL", str(row[0]), str(row[1]), "INFO",
            f"Signal: {row[6]} {row[2]} {row[4]}",
            f"{row[7]} {row[5]} at {row[11]} with confidence {row[13]} and maximum loss {row[12]}.",
            {
                "underlying_symbol": row[2], "expiry": str(row[3]), "option_type": row[4],
                "trading_symbol": row[5], "action": row[6], "direction": row[7],
                "strategy_context": row[8], "approved_lots": row[9],
                "approved_quantity": row[10], "entry_price": str(row[11]),
                "maximum_loss": str(row[12]), "confidence_score": str(row[13]),
                "rationale": row[14],
            }, row[15],
        ) for row in rows]

    @staticmethod
    def _risk_candidates(limit: int) -> list[AlertCandidate]:
        query = """
            SELECT r.assessment_id, r.risk_run_id, r.underlying_symbol, r.expiry,
                   r.option_type, r.trading_symbol, r.approved, r.approved_lots,
                   r.approved_quantity, r.approved_exposure, r.maximum_loss,
                   r.rejection_code, r.explanation, r.created_at
            FROM option_risk_assessments r
            ORDER BY r.created_at DESC, r.assessment_id DESC LIMIT %s
        """
        rows = AlertRepository._fetch_all(query, (limit,))
        output = []
        for row in rows:
            decision = "APPROVED" if row[6] else "REJECTED"
            reason = "approved for sizing" if row[6] else f"rejected: {row[11]}"
            output.append(AlertCandidate(
                "RISK_DECISION", str(row[0]), str(row[1]), "INFO" if row[6] else "WARNING",
                f"Risk {decision}: {row[2]} {row[4]}",
                f"{row[5]} was {reason}. Exposure {row[9]}; maximum loss {row[10]}.",
                {
                    "underlying_symbol": row[2], "expiry": str(row[3]), "option_type": row[4],
                    "trading_symbol": row[5], "approved": row[6], "approved_lots": row[7],
                    "approved_quantity": row[8], "approved_exposure": str(row[9]),
                    "maximum_loss": str(row[10]), "rejection_code": row[11],
                    "explanation": row[12],
                }, row[13],
            ))
        return output

    @staticmethod
    def _pipeline_candidates(limit: int) -> list[AlertCandidate]:
        query = """
            SELECT p.run_id, p.status, p.started_at, p.completed_at,
                   COUNT(f.id) AS failure_count,
                   COALESCE(array_agg(DISTINCT f.stage_name) FILTER (WHERE f.stage_name IS NOT NULL), ARRAY[]::varchar[]) AS failed_stages
            FROM pipeline_runs p
            LEFT JOIN pipeline_failures f ON f.run_id = p.run_id
            WHERE p.status = 'FAILED' OR f.id IS NOT NULL
            GROUP BY p.run_id, p.status, p.started_at, p.completed_at
            ORDER BY p.started_at DESC, p.run_id DESC LIMIT %s
        """
        rows = AlertRepository._fetch_all(query, (limit,))
        return [AlertCandidate(
            "PIPELINE_HEALTH", str(row[0]), str(row[0]), "CRITICAL" if row[1] == "FAILED" else "WARNING",
            f"Pipeline {row[1]}: {row[0]}",
            f"Pipeline run {row[0]} has {row[4]} persisted failure record(s).",
            {
                "status": row[1], "started_at": row[2].isoformat(),
                "completed_at": row[3].isoformat() if row[3] else None,
                "failure_count": row[4], "failed_stages": list(row[5]),
            }, row[3] or row[2],
        ) for row in rows]

    @staticmethod
    def _fetch_all(query: str, parameters: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                return cursor.fetchall()

    @staticmethod
    def _event(row: tuple[Any, ...]) -> AlertEvent:
        return AlertEvent(
            alert_id=UUID(str(row[0])), source_type=str(row[1]), source_id=str(row[2]),
            source_run_id=str(row[3]), severity=str(row[4]), title=str(row[5]),
            message=str(row[6]), payload=dict(row[7]), occurred_at=row[8], created_at=row[9],
        )
