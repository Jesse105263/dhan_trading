import unittest
from http import HTTPStatus
from uuid import UUID

from app.read_api import ReadOnlyApi
from services.market_workspace_service import WorkspaceQueryError


IDENTIFIER="11111111-1111-4111-8111-111111111111"


class Similarity:
    def models(self): return {"data":[{"model_version":"v1"}]}
    def analyze(self,identifier,query):
        if query.get("limit")=="bad": raise WorkspaceQueryError("limit must be an integer.")
        return None if str(identifier).startswith("2") else {"run_id":identifier,"matches":[]}
    def run(self,identifier,matches=False): return {"run_id":identifier,"matches":[]} if str(identifier).startswith("1") else None


class SimilarityApiTest(unittest.TestCase):
    def setUp(self): self.api=ReadOnlyApi(similarity=Similarity())
    def test_models_and_analysis(self):
        self.assertEqual(self.api.handle("GET","/api/v2/similarity/models").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET","/api/v2/similarity",f"vector_id={IDENTIFIER}&limit=10").status,HTTPStatus.OK)
    def test_validation_and_not_found(self):
        self.assertEqual(self.api.handle("GET","/api/v2/similarity","vector_id=nope").status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET","/api/v2/similarity",f"vector_id={IDENTIFIER}&limit=bad").status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET","/api/v2/similarity","vector_id=22222222-2222-4222-8222-222222222222").status,HTTPStatus.NOT_FOUND)
    def test_persisted_run_routes(self):
        self.assertEqual(self.api.handle("GET",f"/api/v2/similarity/runs/{IDENTIFIER}").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET",f"/api/v2/similarity/runs/{IDENTIFIER}/matches").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET","/api/v2/similarity/runs/nope").status,HTTPStatus.BAD_REQUEST)


if __name__=="__main__": unittest.main()
