import unittest
from http import HTTPStatus
from uuid import UUID
from app.read_api import ReadOnlyApi
ID=UUID("11111111-1111-4111-8111-111111111111")
class Outcomes:
    def list(self,query,ascending=False):return {"data":[],"ascending":ascending}
    def statistics(self,query):return {"data":{"outcome_count":0}}
    def detail(self,outcome_id):return {"outcome_id":outcome_id} if outcome_id==ID else None
class HistoricalOutcomeApiTest(unittest.TestCase):
    def setUp(self):self.api=ReadOnlyApi(outcomes=Outcomes())
    def test_list_history_statistics_and_detail(self):
        self.assertEqual(self.api.handle("GET","/api/v2/outcomes").status,HTTPStatus.OK)
        self.assertTrue(self.api.handle("GET","/api/v2/outcomes/history").body["ascending"])
        self.assertEqual(self.api.handle("GET","/api/v2/outcomes/statistics").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET",f"/api/v2/outcomes/{ID}").status,HTTPStatus.OK)
    def test_invalid_and_missing(self):
        self.assertEqual(self.api.handle("GET","/api/v2/outcomes/nope").status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET","/api/v2/outcomes/22222222-2222-4222-8222-222222222222").status,HTTPStatus.NOT_FOUND)
