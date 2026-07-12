from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from services.copilot_models import COPILOT_RESOURCES


class CopilotApiError(RuntimeError):
    pass


class CopilotApiClient:
    """GET-only HTTP client for Copilot evidence retrieval."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        timeout_seconds: float = 5.0,
        opener=urlopen,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("API timeout must be greater than zero.")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.opener = opener

    def list_runs(self, resource: str, limit: int) -> dict[str, Any]:
        self._validate_resource(resource)
        return self._get(f"/api/v1/{resource}?limit={limit}")

    def get_run(self, resource: str, run_id: str) -> dict[str, Any]:
        self._validate_resource(resource)
        return self._get(f"/api/v1/{resource}/{quote(run_id, safe='')}")

    def _get(self, path: str) -> dict[str, Any]:
        request = Request(self.base_url + path, method="GET", headers={"Accept": "application/json"})
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            try:
                message = self._error_message(exc)
            finally:
                exc.close()
            raise CopilotApiError(message) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise CopilotApiError("The read API is unavailable.") from exc
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise CopilotApiError("The read API returned invalid JSON.") from exc
        if not isinstance(value, dict):
            raise CopilotApiError("The read API returned an unexpected response.")
        return value

    @staticmethod
    def _validate_resource(resource: str) -> None:
        if resource not in COPILOT_RESOURCES:
            raise ValueError(f"Unsupported Copilot resource: {resource}")

    @staticmethod
    def _error_message(error: HTTPError) -> str:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            return str(payload["error"]["message"])
        except (KeyError, TypeError, ValueError, UnicodeDecodeError):
            return f"The read API returned HTTP {error.code}."
