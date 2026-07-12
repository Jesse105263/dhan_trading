from __future__ import annotations

import os
import unittest

from app.read_api import ReadOnlyApi
from services.copilot_evidence import CopilotEvidenceService
from services.copilot_models import CopilotRequest
from services.copilot_service import CopilotService
from services.read_api_repository import ReadApiRepository


class ReadApiAdapter:
    """Exercises Copilot retrieval through the existing API response contract."""

    def __init__(self) -> None:
        self.api = ReadOnlyApi(ReadApiRepository())

    def list_runs(self, resource, limit):
        response = self.api.handle("GET", f"/api/v1/{resource}", f"limit={limit}")
        if response.status.value != 200:
            raise RuntimeError(response.body)
        return response.body

    def get_run(self, resource, run_id):
        response = self.api.handle("GET", f"/api/v1/{resource}/{run_id}")
        if response.status.value != 200:
            raise RuntimeError(response.body)
        return response.body


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class CopilotIntegrationTest(unittest.TestCase):
    def test_grounded_local_answer_from_persisted_ranking_api(self) -> None:
        result = CopilotService(CopilotEvidenceService(ReadApiAdapter())).ask(
            CopilotRequest("Explain the latest ranking", runs_per_resource=1)
        )
        if not result.evidence:
            self.skipTest("No persisted ranking run is available.")
        self.assertFalse(result.insufficient_evidence)
        self.assertEqual({item.resource for item in result.evidence}, {"rankings"})
        self.assertIn("Verified platform sources", result.answer)
        for item in result.evidence:
            self.assertIn(item.run_id, result.answer)

    def test_missing_symbol_is_non_destructive_and_explicit(self) -> None:
        result = CopilotService(CopilotEvidenceService(ReadApiAdapter())).ask(
            CopilotRequest("Explain the latest risk", symbol="COPILOT_NO_SUCH_SYMBOL", runs_per_resource=1)
        )
        self.assertTrue(result.insufficient_evidence)
        self.assertEqual(result.evidence, ())
        self.assertIn("Insufficient persisted evidence", result.answer)


if __name__ == "__main__":
    unittest.main()
