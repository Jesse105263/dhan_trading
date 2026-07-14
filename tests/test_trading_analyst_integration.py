import os
import unittest

from app.read_api import application
from services.database import get_connection


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS") == "1", "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class TradingAnalystIntegrationTest(unittest.TestCase):
    def test_packet_preserves_persisted_opportunity_and_evidence_lineage(self):
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT opportunity_id FROM trade_opportunities ORDER BY observed_at DESC LIMIT 1")
            row = cursor.fetchone()
        if row is None: self.skipTest("No persisted trade opportunity is available.")
        packet = application.analyst.evidence_service.assemble(row[0])
        self.assertEqual(packet["opportunity_id"], row[0])
        self.assertEqual(packet["lineage"]["opportunity_id"], row[0])
        self.assertTrue(any(item["type"] == "trade_opportunity" for item in packet["citations"]))


if __name__ == "__main__": unittest.main()
