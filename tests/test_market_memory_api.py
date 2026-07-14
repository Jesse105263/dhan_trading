import unittest
from http import HTTPStatus
from uuid import UUID

from app.read_api import ReadOnlyApi
from services.market_workspace_service import WorkspaceQueryError


IDENTIFIER = UUID("11111111-1111-4111-8111-111111111111")


class Memory:
    def list(self, query): return {"data": [], "count": 0, "limit": int(query.get("limit", 50)), "features": []}
    def latest(self, query, previous=False): return None if previous else {"snapshot_id": IDENTIFIER}
    def detail(self, identifier): return {"snapshot_id": identifier} if identifier == IDENTIFIER else None
    def compare(self, previous, current): return {"changes": []} if previous == current == IDENTIFIER else None
    def feature_history(self, feature, query):
        if feature == "bad": raise WorkspaceQueryError("unsupported")
        return {"feature": feature, "data": []}


class MarketMemoryApiTest(unittest.TestCase):
    def setUp(self): self.api = ReadOnlyApi(memory=Memory())

    def test_timeline_latest_previous_detail_and_feature_routes(self):
        self.assertEqual(self.api.handle("GET", "/api/v2/memory", "symbol=REL").status, HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET", "/api/v2/memory/latest", "symbol=REL").status, HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET", "/api/v2/memory/previous", "symbol=REL").status, HTTPStatus.NOT_FOUND)
        self.assertEqual(self.api.handle("GET", f"/api/v2/memory/snapshots/{IDENTIFIER}").status, HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET", "/api/v2/memory/features/spot_price", "symbol=REL").status, HTTPStatus.OK)

    def test_structured_invalid_and_not_found_responses(self):
        response = self.api.handle("GET", "/api/v2/memory/compare", "previous=nope&current=nope")
        self.assertEqual(response.status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.body["error"]["code"], "invalid_snapshot_id")
        missing = self.api.handle("GET", "/api/v2/memory/snapshots/22222222-2222-4222-8222-222222222222")
        self.assertEqual(missing.status, HTTPStatus.NOT_FOUND)
        self.assertEqual(self.api.handle("GET", "/api/v2/memory/features/bad", "symbol=REL").status, HTTPStatus.BAD_REQUEST)
