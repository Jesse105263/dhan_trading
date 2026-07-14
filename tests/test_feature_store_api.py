import unittest
from http import HTTPStatus
from uuid import UUID

from app.read_api import ReadOnlyApi


ID=UUID("11111111-1111-4111-8111-111111111111")
class Features:
    SCHEMA_VERSION="test-v1"
    @staticmethod
    def definitions(): return [{"name":"spot_price"}]
    def list(self, query): return {"data":[],"count":0,"limit":int(query.get("limit",50))}
    def detail(self, vector_id): return {"vector_id":vector_id} if vector_id==ID else None

class FeatureStoreApiTest(unittest.TestCase):
    def setUp(self): self.api=ReadOnlyApi(features=Features())
    def test_definitions_list_and_detail(self):
        self.assertEqual(self.api.handle("GET","/api/v2/features/definitions").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET","/api/v2/features","symbol=REL").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET",f"/api/v2/features/{ID}").status,HTTPStatus.OK)
    def test_invalid_and_missing_detail(self):
        self.assertEqual(self.api.handle("GET","/api/v2/features/nope").status,HTTPStatus.BAD_REQUEST)
        missing=self.api.handle("GET","/api/v2/features/22222222-2222-4222-8222-222222222222")
        self.assertEqual(missing.status,HTTPStatus.NOT_FOUND)
