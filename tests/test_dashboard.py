from __future__ import annotations

import io
import json
import unittest
from http import HTTPStatus
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app.dashboard import DashboardApiClient, DashboardApiError, DashboardApplication, RESOURCE_LABELS


class FakeDashboardClient:
    def __init__(self) -> None:
        self.error: DashboardApiError | None = None
        self.empty_resources: set[str] = set()

    def health(self):
        if self.error:
            raise self.error
        return {"status": "ok", "database_ready": True}

    def list_runs(self, resource: str, limit: int = 20):
        if self.error:
            raise self.error
        if resource in self.empty_resources:
            return {"resource": resource, "count": 0, "data": []}
        run_field = {
            "rankings": "ranking_run_id", "selections": "selection_run_id", "risk": "risk_run_id",
            "signals": "signal_run_id", "replays": "replay_run_id", "backtests": "backtest_run_id",
        }[resource]
        return {"resource": resource, "count": 1, "data": [{run_field: "00000000-0000-0000-0000-000000000001", "calculated_at": "2026-07-12T10:00:00"}]}

    def get_run(self, resource: str, run_id: str):
        if self.error:
            raise self.error
        item = {"underlying_symbol": "RELIANCE", "approved": True, "explanation": {"reason": "liquid"}}
        if resource == "replays":
            item = {"sequence_number": 1, "event_type": "SIGNAL_GENERATED", "payload": {"signal": "BUY"}}
        return {"resource": resource, "data": {"ranking_run_id": run_id, "items": [item]}}


class DashboardApplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeDashboardClient()
        self.app = DashboardApplication(self.client)

    def test_overview_shows_health_and_all_resources(self) -> None:
        response = self.app.handle("GET", "/")
        self.assertEqual(response.status, HTTPStatus.OK)
        self.assertIn("Read API and database are ready", response.body)
        for label in RESOURCE_LABELS.values():
            self.assertIn(label, response.body)

    def test_each_resource_list_links_to_detail(self) -> None:
        for resource in RESOURCE_LABELS:
            with self.subTest(resource=resource):
                response = self.app.handle("GET", f"/dashboard/{resource}/")
                self.assertEqual(response.status, HTTPStatus.OK)
                self.assertIn(f"/dashboard/{resource}/00000000-0000-0000-0000-000000000001", response.body)

    def test_empty_collection_is_a_stable_success_state(self) -> None:
        self.client.empty_resources.add("signals")
        response = self.app.handle("GET", "/dashboard/signals")
        self.assertEqual(response.status, HTTPStatus.OK)
        self.assertIn("No signals are available yet", response.body)

    def test_detail_renders_nested_evidence_and_replay_timeline(self) -> None:
        detail = self.app.handle("GET", "/dashboard/risk/run-id")
        self.assertEqual(detail.status, HTTPStatus.OK)
        self.assertIn("RELIANCE", detail.body)
        self.assertIn("liquid", detail.body)
        replay = self.app.handle("GET", "/dashboard/replays/run-id")
        self.assertIn("Replay timeline", replay.body)
        self.assertIn("SIGNAL_GENERATED", replay.body)

    def test_api_errors_and_not_found_are_visible(self) -> None:
        self.client.error = DashboardApiError("missing", HTTPStatus.NOT_FOUND)
        missing = self.app.handle("GET", "/dashboard/rankings/run-id")
        self.assertEqual(missing.status, HTTPStatus.NOT_FOUND)
        self.assertIn("missing", missing.body)
        unavailable = self.app.handle("GET", "/dashboard/rankings")
        self.assertEqual(unavailable.status, HTTPStatus.BAD_GATEWAY)
        self.assertIn("Unable to load data", unavailable.body)

    def test_unknown_routes_and_write_methods_are_rejected(self) -> None:
        self.assertEqual(self.app.handle("GET", "/dashboard/unknown").status, HTTPStatus.NOT_FOUND)
        self.assertEqual(self.app.handle("POST", "/").status, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_wsgi_response_has_private_security_headers(self) -> None:
        captured = {}
        body = b"".join(self.app({"REQUEST_METHOD": "GET", "PATH_INFO": "/"}, lambda status, headers: captured.update(status=status, headers=dict(headers))))
        self.assertIn(b"Dhan Monitor", body)
        self.assertEqual(captured["headers"]["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", captured["headers"]["Content-Security-Policy"])


class FakeUrlResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return self.payload


class DashboardApiClientTest(unittest.TestCase):
    @patch("app.dashboard.urlopen")
    def test_uses_get_only_api_routes(self, mocked_urlopen) -> None:
        mocked_urlopen.return_value = FakeUrlResponse({"count": 0, "data": []})
        client = DashboardApiClient("http://127.0.0.1:8080/")
        client.list_runs("signals", 5)
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "http://127.0.0.1:8080/api/v1/signals?limit=5")

    @patch("app.dashboard.urlopen", side_effect=URLError("offline"))
    def test_reports_unavailable_api(self, _mocked_urlopen) -> None:
        with self.assertRaisesRegex(DashboardApiError, "unavailable"):
            DashboardApiClient().health()

    @patch("app.dashboard.urlopen")
    def test_preserves_structured_api_error(self, mocked_urlopen) -> None:
        payload = json.dumps({"error": {"message": "run was not found"}}).encode("utf-8")
        mocked_urlopen.side_effect = HTTPError("url", 404, "Not Found", {}, io.BytesIO(payload))
        with self.assertRaises(DashboardApiError) as raised:
            DashboardApiClient().get_run("rankings", "missing")
        self.assertEqual(raised.exception.status, 404)
        self.assertEqual(str(raised.exception), "run was not found")

    def test_rejects_unknown_resources_before_network_access(self) -> None:
        with self.assertRaises(ValueError):
            DashboardApiClient().list_runs("orders")


if __name__ == "__main__":
    unittest.main()
