from __future__ import annotations

import json
from typing import Callable, Protocol, TextIO
from urllib.request import Request, urlopen

from services.alert_models import AlertEvent


class AlertChannel(Protocol):
    @property
    def name(self) -> str: ...

    def deliver(self, alert: AlertEvent) -> None: ...


class ConsoleAlertChannel:
    name = "console"

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def deliver(self, alert: AlertEvent) -> None:
        self.stream.write(
            f"[{alert.severity}] {alert.title}\n{alert.message}\n"
            f"source={alert.source_type}:{alert.source_id} alert_id={alert.alert_id}\n"
        )
        self.stream.flush()


class WebhookAlertChannel:
    name = "webhook"

    def __init__(
        self,
        url: str,
        timeout_seconds: float = 5.0,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        if not url.strip():
            raise ValueError("Webhook URL must not be empty.")
        if timeout_seconds <= 0:
            raise ValueError("Webhook timeout must be greater than zero.")
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.opener = opener

    def deliver(self, alert: AlertEvent) -> None:
        body = json.dumps(
            {
                "alert_id": str(alert.alert_id),
                "source_type": alert.source_type,
                "source_id": alert.source_id,
                "source_run_id": alert.source_run_id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "payload": alert.payload,
                "occurred_at": alert.occurred_at.isoformat(),
            },
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with self.opener(request, timeout=self.timeout_seconds) as response:
            status = int(getattr(response, "status", 200))
            if not 200 <= status < 300:
                raise RuntimeError(f"Webhook returned HTTP {status}.")
