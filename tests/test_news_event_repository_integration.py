import os,unittest
from datetime import datetime
from pathlib import Path
from services.database import get_connection
from services.news_event_provider import LocalJsonEventProvider
from services.news_event_repository import NewsEventRepository
from services.news_event_service import NewsEventService

@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class NewsEventRepositoryIntegrationTest(unittest.TestCase):
    def test_idempotent_import_exact_lineage_links_and_no_source_mutation(self):
        repository=NewsEventRepository();service=NewsEventService(repository,clock=lambda:datetime(2026,7,15))
        before=repository._fetch("SELECT COUNT(*) count FROM feature_store_vectors",())[0]["count"]
        provider=LocalJsonEventProvider(Path("fixtures/news_events.json"));service.import_records(provider);service.import_records(provider)
        events=repository.events();self.assertEqual(len([e for e in events if e["source"]=="local-verification"]),2)
        service.link_historical();service.link_opportunities()
        self.assertEqual(repository._fetch("SELECT COUNT(*) count FROM feature_store_vectors",())[0]["count"],before)
        detail=repository.get(events[0]["event_id"]);self.assertEqual(detail["raw_source_checksum"],events[0]["raw_source_checksum"])
        with get_connection() as connection:
            with connection.cursor() as cursor: cursor.execute("DELETE FROM market_events WHERE source='local-verification'")
            connection.commit()
