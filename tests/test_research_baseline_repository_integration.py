import os
import unittest

from services.research_baseline import RESEARCH_CONTRACT, ResearchBaselineService


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class ResearchBaselineRepositoryIntegrationTest(unittest.TestCase):
    def test_report_is_select_only_deterministic_and_lineage_bounded(self):
        service = ResearchBaselineService()
        first = service.report()
        second = service.report()
        self.assertEqual(first, second)
        self.assertEqual(first["contract_checksum"], RESEARCH_CONTRACT.checksum())
        self.assertEqual(
            [period["name"] for period in first["periods"]],
            [period.name for period in RESEARCH_CONTRACT.periods],
        )
        for period in first["periods"]:
            self.assertEqual(
                [baseline["name"] for baseline in period["baselines"]],
                list(RESEARCH_CONTRACT.baseline_names),
            )


if __name__ == "__main__":
    unittest.main()
