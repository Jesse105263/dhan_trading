import unittest
from http import HTTPStatus
from app.read_api import ReadOnlyApi
from services.market_workspace_service import WorkspaceQueryError

IDENTIFIER="11111111-1111-4111-8111-111111111111"
class Events:
    def list(self,query):
        if query.get("limit")=="bad": raise WorkspaceQueryError("limit must be an integer.")
        return {"data":[],"count":0}
    def detail(self,event_id): return {"event_id":event_id} if str(event_id).startswith("1") else None
    def context(self,query): return {"events":[],"counts":{}} if query.get("symbol") else None
    def opportunity_context(self,opportunity_id): return {"events":[]} if str(opportunity_id).startswith("1") else None
class NewsEventApiTest(unittest.TestCase):
    def setUp(self): self.api=ReadOnlyApi(events=Events())
    def test_lists_details_context_and_opportunity_context(self):
        self.assertEqual(self.api.handle("GET","/api/v2/events").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET",f"/api/v2/events/{IDENTIFIER}").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET","/api/v2/events/context","symbol=ABC").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET",f"/api/v2/trade-opportunities/{IDENTIFIER}/events").status,HTTPStatus.OK)
    def test_structured_invalid_and_missing(self):
        self.assertEqual(self.api.handle("GET","/api/v2/events","limit=bad").status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET","/api/v2/events/nope").status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET","/api/v2/events/22222222-2222-4222-8222-222222222222").status,HTTPStatus.NOT_FOUND)
        self.assertEqual(self.api.handle("GET","/api/v2/events/context","vector_id=22222222-2222-4222-8222-222222222222").status,HTTPStatus.NOT_FOUND)
if __name__=="__main__": unittest.main()
