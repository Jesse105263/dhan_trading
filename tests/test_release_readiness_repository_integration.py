from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import psycopg

from services.config import POSTGRES_SETTINGS
from services.release_readiness_repository import ReleaseReadinessRepository


RUN_INTEGRATION_TESTS = os.getenv("RUN_DB_INTEGRATION_TESTS") == "1"
RELEASE_TEST_DATABASE = os.getenv("RELEASE_TEST_POSTGRES_DB", "").strip()


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS and bool(RELEASE_TEST_DATABASE),
    "Set RUN_DB_INTEGRATION_TESTS=1 and RELEASE_TEST_POSTGRES_DB to an isolated database.",
)
class ReleaseReadinessRepositoryIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not RELEASE_TEST_DATABASE.startswith("dhan_release_test_"):
            raise unittest.SkipTest(
                "RELEASE_TEST_POSTGRES_DB must use the dhan_release_test_ prefix."
            )
        if RELEASE_TEST_DATABASE != POSTGRES_SETTINGS.dbname:
            raise unittest.SkipTest(
                "POSTGRES_DB must point to RELEASE_TEST_POSTGRES_DB for the isolated suite."
            )

    @staticmethod
    def _isolated_connection():
        return psycopg.connect(
            host=POSTGRES_SETTINGS.host,
            port=POSTGRES_SETTINGS.port,
            dbname=RELEASE_TEST_DATABASE,
            user=POSTGRES_SETTINGS.user,
            password=POSTGRES_SETTINGS.password,
        )

    def setUp(self) -> None:
        patcher = patch(
            "services.release_readiness_repository.get_connection",
            side_effect=self._isolated_connection,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repository = ReleaseReadinessRepository()

    def test_reads_isolated_database_identity_and_migrations(self) -> None:
        database_name, database_user, _ = self.repository.database_identity()
        migrations = self.repository.applied_migrations()

        self.assertEqual(database_name, RELEASE_TEST_DATABASE)
        self.assertTrue(database_user)
        self.assertEqual([item.version for item in migrations], [
            f"{number:03d}" for number in range(1, 23)
        ])

    def test_all_audit_queries_are_readable_on_isolated_schema(self) -> None:
        metrics = self.repository.audit_metrics()

        self.assertEqual(set(metrics), {
            "option_chain_lineage",
            "decision_lineage",
            "evaluation_lineage",
            "alert_lineage",
            "paper_lineage",
            "operational_state",
            "feature_store_lineage",
            "historical_outcome_lineage",
            "similarity_lineage_and_leakage",
            "trade_opportunity_lineage",
            "news_event_lineage_and_leakage",
            "analyst_evidence_grounding",
            "execution_schema_boundary",
        })
        self.assertTrue(all(metric.violation_count == 0 for metric in metrics.values()))


if __name__ == "__main__":
    unittest.main()
