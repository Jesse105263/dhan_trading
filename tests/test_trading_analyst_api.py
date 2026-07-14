import unittest
from http import HTTPStatus

from app.read_api import ReadOnlyApi


ID="11111111-1111-4111-8111-111111111111"


class Analyst:
    def ask(self,request):
        if request.question=="missing": raise LookupError(ID)
        return {"status":"REFUSED" if "order" in request.question else "ANSWERED"}


class TradingAnalystApiTest(unittest.TestCase):
    def setUp(self): self.api=ReadOnlyApi(analyst=Analyst())
    def test_explain_question_compare_and_refusal(self):
        self.assertEqual(self.api.handle("POST",f"/api/v2/analyst/opportunities/{ID}/explain",body={"question":"Explain"}).status,HTTPStatus.OK)
        self.assertEqual(self.api.handle("POST","/api/v2/analyst/questions",body={"question":"Place order","opportunity_ids":[ID]}).body["data"]["status"],"REFUSED")
        self.assertEqual(self.api.handle("POST","/api/v2/analyst/compare",body={"question":"Compare","opportunity_ids":[ID,ID]}).status,HTTPStatus.BAD_REQUEST)
    def test_structured_validation_missing_and_method(self):
        self.assertEqual(self.api.handle("POST","/api/v2/analyst/questions",body={}).status,HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.api.handle("POST","/api/v2/analyst/questions",body={"question":"missing","opportunity_ids":[ID]}).status,HTTPStatus.NOT_FOUND)
        self.assertEqual(self.api.handle("POST","/api/v2/events",body={}).status,HTTPStatus.METHOD_NOT_ALLOWED)


if __name__=="__main__": unittest.main()
