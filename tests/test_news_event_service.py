import unittest
from datetime import date,datetime
from pathlib import Path
from uuid import UUID

from services.market_workspace_service import WorkspaceQueryError
from services.news_event_provider import LocalJsonEventProvider
from services.news_event_service import NewsEventService

VECTOR=UUID("11111111-1111-4111-8111-111111111111"); RUN=UUID("22222222-2222-4222-8222-222222222222"); OPPORTUNITY=UUID("33333333-3333-4333-8333-333333333333")

class Repository:
    def __init__(self): self.stored=[];self.vector_links=[];self.similarity_links=[];self.opportunity_links=[]
    def upsert(self,event):
        self.stored=[row for row in self.stored if row["event_id"]!=event["event_id"]]+[event]
    def events(self): return self.stored
    def vectors(self): return [{"vector_id":VECTOR,"underlying_symbol":"ABC","expiry":date(2026,7,30),"observed_at":datetime(2026,7,15,12),"outcome_id":None,"terminal_observed_at":datetime(2026,7,20,12)}]
    def similarity_runs(self): return [{"run_id":RUN,"query_vector_id":VECTOR}]
    def opportunities(self): return [{"opportunity_id":OPPORTUNITY,"query_vector_id":VECTOR,"underlying_symbol":"ABC","expiry":date(2026,7,30),"observed_at":datetime(2026,7,15,12)}]
    def replace_vector_links(self,links): self.vector_links=links
    def replace_similarity_links(self,links): self.similarity_links=links
    def replace_opportunity_links(self,links): self.opportunity_links=links
    def list(self,filters,limit): return self.stored[:limit]
    def get(self,event_id): return next((e for e in self.stored if e["event_id"]==event_id),None)
    def vector_exists(self,vector_id): return vector_id==VECTOR
    def vector_context(self,vector_id): return self.vector_links
    def opportunity_exists(self,opportunity_id): return opportunity_id==OPPORTUNITY
    def opportunity_context(self,opportunity_id):
        result=[]
        for link in self.opportunity_links:
            event=next(e for e in self.stored if e["event_id"]==link["event_id"])
            result.append({**link,"seconds_from_observation":link["seconds"],"event":event})
        return result

class Provider:
    def __init__(self,records): self.data=records
    def records(self,limit): return self.data

def record(identifier,event_at,published_at="2026-07-10T10:00:00",symbols=None,market=False,scheduled=True):
    return {"source":"fixture","source_event_id":identifier,"event_type":"COMPANY_NEWS","title":identifier,
      "summary":"context api_key=secret","published_at":published_at,"event_at":event_at,"is_scheduled":scheduled,
      "market_wide":market,"affected_symbols":symbols if symbols is not None else ["ABC"],"affected_sectors":["ENERGY"],
      "source_reference":"fixture:test","metadata":{"access_token":"secret","safe":"yes"}}

class NewsEventServiceTest(unittest.TestCase):
    def setUp(self): self.repository=Repository();self.service=NewsEventService(self.repository,clock=lambda:datetime(2026,7,15))
    def test_deterministic_id_deduplication_sanitization_and_lineage(self):
        source=record("one","2026-07-14T10:00:00")
        self.service.import_records(Provider([source])); first=self.repository.stored[0]
        self.service.import_records(Provider([source])); second=self.repository.stored[0]
        self.assertEqual(first["event_id"],second["event_id"]);self.assertEqual(len(self.repository.stored),1)
        self.assertIn("[REDACTED]",second["summary"]);self.assertNotIn("access_token",second["metadata"])
        self.assertEqual(len(second["raw_source_checksum"]),64);self.assertEqual(second["symbols"],["ABC"])
    def test_relevance_and_future_leakage(self):
        records=[record("before","2026-07-14T10:00:00"),record("during","2026-07-18T10:00:00",published_at="2026-07-17T10:00:00"),
          record("unknown-future","2026-07-16T10:00:00",published_at="2026-07-16T09:00:00"),record("unrelated","2026-07-14T10:00:00",symbols=["XYZ"]),
          record("market","2026-07-14T11:00:00",symbols=[],market=True)]
        self.service.import_records(Provider(records));result=self.service.link_historical()
        before=[x for x in self.repository.vector_links if x["context_type"]=="BEFORE_OBSERVATION"]
        during=[x for x in self.repository.vector_links if x["context_type"]=="DURING_HOLDING"]
        self.assertEqual(len(before),2);self.assertTrue(all(x["predictive_eligible"] for x in before))
        self.assertEqual(len(during),2);self.assertTrue(all(not x["predictive_eligible"] for x in during))
        self.assertEqual(result["similarity_link_count"],2)
    def test_opportunity_context_is_context_only(self):
        self.service.import_records(Provider([record("upcoming","2026-07-18T10:00:00")]))
        self.service.link_opportunities();context=self.service.opportunity_context(OPPORTUNITY)
        self.assertEqual(context["upcoming_event_count"],1);self.assertEqual(context["reasons_for"],[])
        self.assertIn("does not alter opportunity",context["limitations"][0])
    def test_filter_validation_and_local_adapter(self):
        rows=LocalJsonEventProvider(Path("fixtures/news_events.json")).records(10);self.assertEqual(len(rows),2)
        invalid=record("invalid","2026-07-14T10:00:00");invalid["is_scheduled"]="false"
        with self.assertRaises(ValueError): self.service.import_records(Provider([invalid]))
        for query in ({"event_type":"bad"},{"scheduled":"yes"},{"limit":"0"},{"from":"bad"}):
            with self.assertRaises(WorkspaceQueryError): self.service.list(query)

if __name__=="__main__": unittest.main()
