import os
import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from services.database import get_connection
from services.failure_repository import FailureRepository
from services.metrics_repository import MetricsRepository
from services.option_chain_models import OptionChainCollectionResult
from services.option_data_pipeline import OptionAnalyticsStage, OptionCollectionStage
from services.pipeline import Pipeline


RUN_DB_TESTS = os.getenv("RUN_DB_INTEGRATION_TESTS") == "1"


class FakeCollector:
    def collect(self, request):
        if request.underlying_symbol == "BROKEN":
            raise ValueError("invalid configured underlying")
        return OptionChainCollectionResult(
            run_id=uuid4(),
            underlying_symbol=request.underlying_symbol,
            underlying_security_id="1",
            expiry=date(2026, 7, 28),
            spot_price=Decimal("100"),
            strikes_received=2,
            quotes_received=4,
            quotes_inserted=4,
        )


class FakeAnalytics:
    def calculate_and_persist(self, request):
        return request.source_run_id


@unittest.skipUnless(
    RUN_DB_TESTS,
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class OptionDataPipelineIntegrationTest(unittest.TestCase):
    def test_partial_success_persists_metrics_and_failure(self):
        failure_repository = FailureRepository()
        pipeline = Pipeline(
            stages=[
                OptionCollectionStage(
                    ("GOOD", "BROKEN"),
                    FakeCollector(),
                    failure_repository,
                    max_attempts=1,
                ),
                OptionAnalyticsStage(
                    FakeAnalytics(),
                    failure_repository,
                ),
            ]
        )
        pipeline.start()
        run_id = pipeline.context["run_id"]
        self.assertEqual(pipeline.context["pipeline_status"], "COMPLETED")
        self.assertEqual(set(pipeline.context["option_analytics_results"]), {"GOOD"})
        self.assertEqual(FailureRepository().count_for_run(run_id), 1)
        self.assertEqual(MetricsRepository().count_for_run(run_id), 2)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM pipeline_runs WHERE run_id = %s;",
                    (run_id,),
                )
                row = cursor.fetchone()
        self.assertEqual(row[0], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
