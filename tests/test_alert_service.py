from __future__ import annotations

import io
import json
import unittest
from datetime import datetime
from uuid import uuid4

from services.alert_channels import ConsoleAlertChannel, WebhookAlertChannel
from services.alert_models import AlertCandidate, AlertEvent, PersistedAlert
from services.alert_service import AlertService


NOW = datetime(2026, 7, 12, 10, 0, 0)


def candidate(source_type: str = "SIGNAL") -> AlertCandidate:
    return AlertCandidate(
        source_type=source_type,
        source_id="source-1",
        source_run_id="run-1",
        severity="INFO",
        title="Persisted event",
        message="Generated from persisted output.",
        payload={"lineage": "source-1"},
        occurred_at=NOW,
    )


class FakeRepository:
    def __init__(self, candidates=None, created=True) -> None:
        self.candidates = list(candidates or [])
        self.created = created
        self.delivered: set[tuple[object, str]] = set()
        self.attempts = []
        self.finished = []

    def list_candidates(self, source_types, limit):
        return [item for item in self.candidates if item.source_type in source_types][:limit]

    def ensure_alert(self, item, created_at):
        normalized = item.normalized()
        event = AlertEvent(
            uuid4(), normalized.source_type, normalized.source_id,
            normalized.source_run_id, normalized.severity, normalized.title,
            normalized.message, normalized.payload, normalized.occurred_at, created_at,
        )
        return PersistedAlert(event, self.created)

    def was_delivered(self, alert_id, channel_name):
        return (alert_id, channel_name) in self.delivered

    def start_delivery(self, alert_id, channel_name, started_at):
        self.attempts.append((alert_id, channel_name, started_at))
        return len(self.attempts)

    def finish_delivery(self, attempt_id, delivered, completed_at, error_message=None):
        self.finished.append((attempt_id, delivered, error_message))


class RecordingChannel:
    name = "recording"

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.alerts = []

    def deliver(self, alert):
        self.alerts.append(alert)
        if self.error:
            raise self.error


class AlertServiceTest(unittest.TestCase):
    def test_generates_persists_and_delivers_all_source_types(self) -> None:
        items = [candidate("SIGNAL"), candidate("RISK_DECISION"), candidate("PIPELINE_HEALTH")]
        repository = FakeRepository(items)
        channel = RecordingChannel()
        result = AlertService(repository, clock=lambda: NOW).generate_and_deliver(
            ("signal", "risk_decision", "pipeline_health"), (channel,)
        )
        self.assertEqual(result.candidates_found, 3)
        self.assertEqual(result.alerts_created, 3)
        self.assertEqual(result.deliveries_succeeded, 3)
        self.assertEqual(len(channel.alerts), 3)
        self.assertTrue(all(delivered for _, delivered, _ in repository.finished))

    def test_duplicate_event_is_reused_and_successful_channel_is_skipped(self) -> None:
        repository = FakeRepository([candidate()], created=False)
        original_ensure = repository.ensure_alert

        def ensure_and_mark(*args):
            persisted = original_ensure(*args)
            repository.delivered.add((persisted.event.alert_id, "recording"))
            return persisted

        repository.ensure_alert = ensure_and_mark
        channel = RecordingChannel()
        result = AlertService(repository, clock=lambda: NOW).generate_and_deliver(("SIGNAL",), (channel,))
        self.assertEqual(result.duplicate_alerts, 1)
        self.assertEqual(result.deliveries_skipped, 1)
        self.assertEqual(channel.alerts, [])
        self.assertEqual(repository.attempts, [])

    def test_delivery_failure_is_sanitized_audited_and_non_destructive(self) -> None:
        repository = FakeRepository([candidate()])
        channel = RecordingChannel(RuntimeError("password=secret-value unavailable"))
        result = AlertService(repository, clock=lambda: NOW).generate_and_deliver(("SIGNAL",), (channel,))
        self.assertEqual(result.alerts_created, 1)
        self.assertEqual(result.deliveries_failed, 1)
        self.assertNotIn("secret-value", repository.finished[0][2])
        self.assertIn("[REDACTED]", repository.finished[0][2])

    def test_validates_sources_limit_and_unique_channels(self) -> None:
        service = AlertService(FakeRepository())
        with self.assertRaises(ValueError):
            service.generate_and_deliver((), ())
        with self.assertRaises(ValueError):
            service.generate_and_deliver(("orders",), ())
        with self.assertRaises(ValueError):
            service.generate_and_deliver(("signal",), (), 0)
        with self.assertRaises(ValueError):
            service.generate_and_deliver(("signal",), (RecordingChannel(), RecordingChannel()))

    def test_candidate_normalizes_and_rejects_invalid_values(self) -> None:
        normalized = candidate().normalized()
        self.assertEqual(normalized.source_type, "SIGNAL")
        for changes in (
            {"source_type": "ORDER"}, {"severity": "UNKNOWN"}, {"source_id": ""},
        ):
            values = candidate().__dict__ | changes
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                AlertCandidate(**values).normalized()


class FakeResponse:
    status = 204

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class AlertChannelTest(unittest.TestCase):
    def setUp(self) -> None:
        item = candidate().normalized()
        self.alert = AlertEvent(
            uuid4(), item.source_type, item.source_id, item.source_run_id,
            item.severity, item.title, item.message, item.payload, item.occurred_at, NOW,
        )

    def test_console_channel_writes_auditable_identity(self) -> None:
        stream = io.StringIO()
        ConsoleAlertChannel(stream).deliver(self.alert)
        output = stream.getvalue()
        self.assertIn("Persisted event", output)
        self.assertIn(str(self.alert.alert_id), output)
        self.assertIn("SIGNAL:source-1", output)

    def test_webhook_channel_posts_structured_alert(self) -> None:
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse()

        WebhookAlertChannel("http://127.0.0.1:9999/alerts", 3, opener).deliver(self.alert)
        request, timeout = calls[0]
        payload = json.loads(request.data)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(timeout, 3)
        self.assertEqual(payload["alert_id"], str(self.alert.alert_id))
        self.assertEqual(payload["source_type"], "SIGNAL")

    def test_webhook_configuration_is_validated(self) -> None:
        with self.assertRaises(ValueError):
            WebhookAlertChannel("")
        with self.assertRaises(ValueError):
            WebhookAlertChannel("http://localhost", 0)


if __name__ == "__main__":
    unittest.main()
