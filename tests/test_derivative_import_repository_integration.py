import os
import unittest
from datetime import datetime
from uuid import uuid4

from services.database import get_connection
from services.derivative_import_repository import (
    DerivativeImportFailure,
    DerivativeImportRepository,
)


RUN_INTEGRATION_TESTS = (
    os.getenv("RUN_DB_INTEGRATION_TESTS", "0") == "1"
)


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class DerivativeImportRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.run_id = uuid4()
        self.repository = DerivativeImportRepository()

    def tearDown(self) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM derivative_import_runs WHERE run_id = %s;",
                    (self.run_id,),
                )
            connection.commit()

    def test_run_lifecycle_and_failure_persistence(self) -> None:
        started_at = datetime.now()
        self.repository.start_run(
            run_id=self.run_id,
            started_at=started_at,
            source_url="https://example.test/master.csv",
            source_file_name="master.csv",
            source_timestamp=None,
        )

        inserted = self.repository.insert_failures(
            [
                DerivativeImportFailure(
                    run_id=self.run_id,
                    row_number=10,
                    security_id="123",
                    trading_symbol="ABC-TEST",
                    error_type="ValueError",
                    error_message="Invalid row",
                    occurred_at=datetime.now(),
                )
            ]
        )
        self.assertEqual(inserted, 1)

        self.repository.complete_run(
            run_id=self.run_id,
            completed_at=datetime.now(),
            rows_read=100,
            rows_eligible=20,
            contracts_upserted=19,
            contracts_deactivated=1,
            rows_rejected=1,
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT status, rows_read, contracts_upserted, rows_rejected
                    FROM derivative_import_runs
                    WHERE run_id = %s;
                    """,
                    (self.run_id,),
                )
                run = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM derivative_import_failures
                    WHERE run_id = %s;
                    """,
                    (self.run_id,),
                )
                failure_count = cursor.fetchone()

        self.assertEqual(run, ("COMPLETED", 100, 19, 1))
        self.assertEqual(failure_count[0], 1)


if __name__ == "__main__":
    unittest.main()
