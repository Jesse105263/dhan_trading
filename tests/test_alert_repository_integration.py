from __future__ import annotations

import os
import unittest
from datetime import datetime
from uuid import uuid4

from services.alert_models import AlertCandidate
from services.alert_repository import AlertRepository
from services.database import get_connection


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class AlertRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.run_id = str(uuid4())
        self.source_id = str(uuid4())
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pipeline_runs (run_id, status, started_at, completed_at)
                    VALUES (%s, 'FAILED', %s, %s)
                    """,
                    (self.run_id, datetime(2026, 7, 12, 10), datetime(2026, 7, 12, 10, 1)),
                )
                cursor.execute(
                    """
                    INSERT INTO pipeline_failures (
                        run_id, stage_name, error_type, error_message, retryable, occurred_at
                    ) VALUES (%s, 'Alert Integration Stage', 'RuntimeError', 'synthetic failure', FALSE, %s)
                    """,
                    (self.run_id, datetime(2026, 7, 12, 10, 1)),
                )
            connection.commit()

    def tearDown(self) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM alert_events WHERE source_id IN (%s, %s)", (self.run_id, self.source_id))
                cursor.execute("DELETE FROM pipeline_failures WHERE run_id = %s", (self.run_id,))
                cursor.execute("DELETE FROM pipeline_runs WHERE run_id = %s", (self.run_id,))
            connection.commit()

    def test_pipeline_source_deduplication_and_delivery_audit(self) -> None:
        repository = AlertRepository()
        candidates = repository.list_candidates(("PIPELINE_HEALTH",), 1000)
        item = next(candidate for candidate in candidates if candidate.source_id == self.run_id)
        self.assertEqual(item.severity, "CRITICAL")
        self.assertEqual(item.payload["failure_count"], 1)

        first = repository.ensure_alert(item, datetime(2026, 7, 12, 10, 2))
        second = repository.ensure_alert(item, datetime(2026, 7, 12, 10, 3))
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.event.alert_id, second.event.alert_id)

        failed_attempt = repository.start_delivery(first.event.alert_id, "console", datetime(2026, 7, 12, 10, 4))
        repository.finish_delivery(failed_attempt, False, datetime(2026, 7, 12, 10, 5), "unavailable")
        self.assertFalse(repository.was_delivered(first.event.alert_id, "console"))
        successful_attempt = repository.start_delivery(first.event.alert_id, "console", datetime(2026, 7, 12, 10, 6))
        repository.finish_delivery(successful_attempt, True, datetime(2026, 7, 12, 10, 7))
        self.assertTrue(repository.was_delivered(first.event.alert_id, "console"))

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT status, attempt_number FROM alert_delivery_attempts WHERE alert_id = %s ORDER BY attempt_number",
                    (first.event.alert_id,),
                )
                self.assertEqual(cursor.fetchall(), [("FAILED", 1), ("DELIVERED", 2)])

    def test_signal_and_risk_candidate_queries_are_safe_when_empty(self) -> None:
        repository = AlertRepository()
        for source_type in ("SIGNAL", "RISK_DECISION"):
            with self.subTest(source_type=source_type):
                candidates = repository.list_candidates((source_type,), 1)
                self.assertLessEqual(len(candidates), 1)

    def test_persists_standalone_auditable_source_identity(self) -> None:
        item = AlertCandidate(
            "SIGNAL", self.source_id, "signal-run", "INFO", "Synthetic signal",
            "Persisted test signal.", {"signal_id": self.source_id}, datetime(2026, 7, 12, 11),
        )
        persisted = AlertRepository().ensure_alert(item, datetime(2026, 7, 12, 11, 1))
        self.assertTrue(persisted.created)
        self.assertEqual(persisted.event.payload["signal_id"], self.source_id)


if __name__ == "__main__":
    unittest.main()
