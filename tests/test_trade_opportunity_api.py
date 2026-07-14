import unittest
from http import HTTPStatus

from app.read_api import ReadOnlyApi
from services.market_workspace_service import WorkspaceQueryError

IDENTIFIER="11111111-1111-4111-8111-111111111111"


class Opportunities:
    def list(self,query):
        if query.get("limit")=="bad": raise WorkspaceQueryError("limit must be an integer.")
        return {"data":[],"count":0}
    def detail(self,identifier): return {"opportunity_id":identifier} if str(identifier).startswith("1") else None


class TradeOpportunityApiTest(unittest.TestCase):
    def setUp(self): self.api=ReadOnlyApi(trade_opportunities=Opportunities())
    def test_list_detail_errors_and_not_found(self):
        self.assertEqual(self.api.handle("GET","/api/v2/trade-opportunities").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET","/api/v2/trade-opportunities","limit=bad").status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET",f"/api/v2/trade-opportunities/{IDENTIFIER}").status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("GET","/api/v2/trade-opportunities/nope").status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("GET","/api/v2/trade-opportunities/22222222-2222-4222-8222-222222222222").status,HTTPStatus.NOT_FOUND)


if __name__=="__main__": unittest.main()
