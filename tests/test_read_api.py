from __future__ import annotations

import unittest
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from uuid import UUID, uuid4

from app.read_api import ReadOnlyApi


class FakeRepository:
    def __init__(self) -> None:
        self.run_id = uuid4()

    def resources(self) -> tuple[str, ...]:
        return ("rankings", "signals")

    def health(self):
        return {"status": "ok", "database_ready": True}

    def list_latest(self, resource: str, limit: int):
        return [{"ranking_run_id": self.run_id, "score": Decimal("0.5"), "calculated_at": datetime(2026, 7, 12)}][:limit]

    def get_run(self, resource: str, run_id: UUID):
        if run_id != self.run_id:
            return None
        return {"ranking_run_id": run_id, "items": []}


class ReadOnlyApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeRepository()
        self.workspace = FakeWorkspace()
        self.api = ReadOnlyApi(self.repository, self.workspace)

    def test_health_and_index(self) -> None:
        self.assertEqual(self.api.handle("GET", "/health").status, HTTPStatus.OK)
        response = self.api.handle("GET", "/api/v1")
        self.assertEqual(response.status, HTTPStatus.OK)
        self.assertEqual(response.body["resources"], ["rankings", "signals"])

    def test_lists_latest_with_valid_limit(self) -> None:
        response = self.api.handle("GET", "/api/v1/rankings", "limit=1")
        self.assertEqual(response.status, HTTPStatus.OK)
        self.assertEqual(response.body["count"], 1)

    def test_rejects_invalid_limit(self) -> None:
        for query in ("limit=0", "limit=101", "limit=bad"):
            with self.subTest(query=query):
                self.assertEqual(self.api.handle("GET", "/api/v1/rankings", query).status, HTTPStatus.BAD_REQUEST)

    def test_gets_detail_and_returns_not_found(self) -> None:
        found = self.api.handle("GET", f"/api/v1/rankings/{self.repository.run_id}")
        self.assertEqual(found.status, HTTPStatus.OK)
        missing = self.api.handle("GET", f"/api/v1/rankings/{uuid4()}")
        self.assertEqual(missing.status, HTTPStatus.NOT_FOUND)

    def test_rejects_invalid_uuid_unknown_routes_and_writes(self) -> None:
        self.assertEqual(self.api.handle("GET", "/api/v1/rankings/not-a-uuid").status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET", "/api/v1/unknown").status, HTTPStatus.NOT_FOUND)
        self.assertEqual(self.api.handle("POST", "/api/v1/rankings").status, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_v2_read_routes_errors_and_not_found(self) -> None:
        self.assertEqual(self.api.handle("GET", "/api/v2").body["version"], "v2")
        self.assertEqual(self.api.handle("GET", "/api/v2/overview").status, HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET", "/api/v2/opportunities", "limit=2").body["page"]["limit"], 2)
        self.assertEqual(self.api.handle("GET", "/api/v2/opportunities", "limit=bad").status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET", f"/api/v2/opportunities/{self.workspace.item_id}").status, HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET", f"/api/v2/opportunities/{uuid4()}").status, HTTPStatus.NOT_FOUND)


class FakeWorkspace:
    def __init__(self) -> None:
        self.item_id = uuid4()

    def overview(self):
        return {"platform": {"status": "ok", "database_ready": True}}

    def opportunities(self, query):
        if query.get("limit") == "bad":
            from services.market_workspace_service import WorkspaceQueryError
            raise WorkspaceQueryError("limit must be an integer.")
        return {"data": [], "page": {"limit": int(query.get("limit", 25)), "offset": 0, "count": 0, "total": 0}}

    def opportunity(self, ranking_id):
        return {"ranking_id": ranking_id} if ranking_id == self.item_id else None
