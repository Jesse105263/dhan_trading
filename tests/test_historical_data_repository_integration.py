import os
import unittest
from datetime import datetime

from services.database import get_connection
from services.historical_data_models import HistoricalDataSource
from services.historical_data_provider import LocalJsonHistoricalDataAdapter
from services.historical_data_repository import HistoricalDataRepository
from services.historical_data_service import HistoricalDataService
from tests.test_historical_data_foundation import envelope, fixture, policy


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class HistoricalDataRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.source = HistoricalDataSource(
            "V31_TEST", "LOCAL", "FOUNDATION", "LOCAL_FIXTURE", "integration-test"
        )
        self.service = HistoricalDataService(
            HistoricalDataRepository(), clock=lambda: datetime(2026, 7, 15, 11)
        )
        self.adapter = LocalJsonHistoricalDataAdapter()

    def tearDown(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT source_id FROM historical_data_sources WHERE provider_code='V31_TEST'"
                )
                row = cursor.fetchone()
                if row:
                    source_id = row[0]
                    cursor.execute(
                        "DELETE FROM corporate_action_revisions WHERE manifest_id IN "
                        "(SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",
                        (source_id,),
                    )
                    cursor.execute(
                        "DELETE FROM historical_bar_revisions WHERE manifest_id IN "
                        "(SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",
                        (source_id,),
                    )
                    cursor.execute(
                        "DELETE FROM source_instrument_mappings WHERE source_id=%s",
                        (source_id,),
                    )
                    cursor.execute(
                        "DELETE FROM canonical_instrument_revisions WHERE manifest_id IN "
                        "(SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",
                        (source_id,),
                    )
                    cursor.execute(
                        "DELETE FROM canonical_instruments WHERE identity_key LIKE 'NSE|%%|TESTCO%%'"
                    )
                    cursor.execute(
                        "DELETE FROM historical_raw_manifests WHERE source_id=%s",
                        (source_id,),
                    )
                    cursor.execute(
                        "DELETE FROM historical_raw_payloads WHERE source_id=%s",
                        (source_id,),
                    )
                    cursor.execute(
                        "DELETE FROM historical_retention_policies WHERE source_id=%s",
                        (source_id,),
                    )
                    cursor.execute(
                        "DELETE FROM historical_data_sources WHERE source_id=%s",
                        (source_id,),
                    )
            connection.commit()

    def test_atomic_idempotent_import_and_revision_lineage(self):
        first = self.service.import_payload(
            self.source, policy(), envelope(fixture(), "integration-1"), self.adapter
        )
        duplicate = self.service.import_payload(
            self.source, policy(), envelope(fixture(), "integration-1"), self.adapter
        )
        revised = self.service.import_payload(
            self.source,
            policy(),
            envelope(fixture(close_price="102"), "integration-2"),
            self.adapter,
        )
        self.assertFalse(first.raw_duplicate)
        self.assertTrue(duplicate.raw_duplicate)
        self.assertEqual(duplicate.bar_revisions_inserted, 0)
        self.assertEqual(revised.bar_revisions_inserted, 1)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT bar_revision_id,revision_number,is_current,
                              supersedes_revision_id,close_price
                       FROM historical_bar_revisions
                       WHERE instrument_id=%s ORDER BY revision_number""",
                    (fixture()["instruments"][1]["instrument_id"],),
                )
                rows = cursor.fetchall()
                self.assertEqual(len(rows), 2)
                self.assertEqual([row[1] for row in rows], [1, 2])
                self.assertFalse(rows[0][2])
                self.assertTrue(rows[1][2])
                self.assertEqual(rows[1][3], rows[0][0])
                cursor.execute(
                    "SELECT payload_checksum,octet_length(payload_bytes),byte_count "
                    "FROM historical_raw_payloads WHERE payload_id=%s",
                    (first.payload_id,),
                )
                raw = cursor.fetchone()
                self.assertEqual(raw[0], first.payload_checksum)
                self.assertEqual(raw[1], raw[2])

    def test_raw_payload_update_is_rejected(self):
        result = self.service.import_payload(
            self.source, policy(), envelope(fixture(), "immutable"), self.adapter
        )
        with self.assertRaises(Exception):
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE historical_raw_payloads SET content_type='text/plain' "
                        "WHERE payload_id=%s",
                        (result.payload_id,),
                    )


if __name__ == "__main__":
    unittest.main()
