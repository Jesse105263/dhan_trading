from __future__ import annotations

import io
import json
import unittest
from datetime import datetime
from unittest.mock import Mock
from urllib.error import URLError

from services.copilot_api_client import CopilotApiClient, CopilotApiError
from services.copilot_evidence import CopilotEvidenceService
from services.copilot_models import CopilotEvidence, CopilotRequest
from services.copilot_provider import OpenAIResponsesProvider
from services.copilot_service import CopilotService


RUN_ID = "00000000-0000-0000-0000-000000000001"
ITEM_ID = "00000000-0000-0000-0000-000000000002"


class FakeHttpResponse:
    status = 200

    def __init__(self, payload) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return self.payload


class CopilotApiClientTest(unittest.TestCase):
    def test_uses_only_versioned_get_routes(self) -> None:
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeHttpResponse({"data": []})

        client = CopilotApiClient("http://127.0.0.1:8080/", 4, opener)
        client.list_runs("rankings", 2)
        client.get_run("rankings", RUN_ID)
        self.assertEqual([call[0].get_method() for call in calls], ["GET", "GET"])
        self.assertEqual(calls[0][0].full_url, "http://127.0.0.1:8080/api/v1/rankings?limit=2")
        self.assertTrue(calls[1][0].full_url.endswith(f"/api/v1/rankings/{RUN_ID}"))

    def test_rejects_unknown_resource_and_reports_unavailable_api(self) -> None:
        with self.assertRaises(ValueError):
            CopilotApiClient().list_runs("orders", 1)
        with self.assertRaisesRegex(CopilotApiError, "unavailable"):
            CopilotApiClient(opener=Mock(side_effect=URLError("offline"))).list_runs("risk", 1)


class FakeEvidenceApi:
    def __init__(self, empty=False) -> None:
        self.empty = empty
        self.calls = []

    def list_runs(self, resource, limit):
        self.calls.append(("list", resource, limit))
        if self.empty:
            return {"data": []}
        return {"data": [{f"{resource[:-1] if resource.endswith('s') else resource}_run_id": RUN_ID}]}

    def get_run(self, resource, run_id):
        self.calls.append(("detail", resource, run_id))
        run_field = {
            "rankings": "ranking_run_id", "selections": "selection_run_id",
            "risk": "risk_run_id", "signals": "signal_run_id", "backtests": "backtest_run_id",
        }[resource]
        item = {
            "ranking_id": ITEM_ID,
            "underlying_symbol": "RELIANCE",
            "rank_position": 1,
            "total_score": "0.85",
            "expiry": "2026-07-30",
        }
        return {"data": {run_field: run_id, "items": [item]}}


class CopilotEvidenceServiceTest(unittest.TestCase):
    def test_selects_resources_from_question_and_preserves_lineage(self) -> None:
        api = FakeEvidenceApi()
        evidence = CopilotEvidenceService(api).collect(
            CopilotRequest("Explain the latest ranking", symbol="reliance")
        )
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].resource, "rankings")
        self.assertEqual(evidence[0].run_id, RUN_ID)
        self.assertEqual(evidence[0].item_id, ITEM_ID)
        self.assertIn(RUN_ID, evidence[0].citation)
        self.assertEqual(api.calls[0], ("list", "rankings", 2))

    def test_symbol_filter_and_empty_collections_produce_no_evidence(self) -> None:
        evidence = CopilotEvidenceService(FakeEvidenceApi()).collect(
            CopilotRequest("Explain risk", symbol="TCS")
        )
        self.assertEqual(evidence, ())
        self.assertEqual(
            CopilotEvidenceService(FakeEvidenceApi(empty=True)).collect(CopilotRequest("Explain signals")),
            (),
        )

    def test_general_question_uses_all_supported_resources(self) -> None:
        api = FakeEvidenceApi(empty=True)
        CopilotEvidenceService(api).collect(CopilotRequest("What does the platform show?"))
        listed = [call[1] for call in api.calls if call[0] == "list"]
        self.assertEqual(listed, ["rankings", "selections", "risk", "signals", "backtests"])

    def test_request_validation(self) -> None:
        for request in (
            CopilotRequest(""), CopilotRequest("x", runs_per_resource=0),
            CopilotRequest("x", maximum_evidence_records=101), CopilotRequest("x", symbol="X" * 31),
        ):
            with self.subTest(request=request), self.assertRaises(ValueError):
                request.normalized()


class StaticEvidenceService:
    def __init__(self, evidence) -> None:
        self.evidence = evidence
        self.calls = 0

    def collect(self, request):
        self.calls += 1
        return self.evidence


class FakeProvider:
    name = "fake-model"

    def __init__(self, error=None) -> None:
        self.error = error

    def answer(self, question, evidence):
        if self.error:
            raise self.error
        return f"Model-grounded answer {evidence[0].citation}"


def evidence_record():
    return CopilotEvidence(
        f"[rankings:{RUN_ID}:{ITEM_ID}]", "rankings", RUN_ID, ITEM_ID,
        {"underlying_symbol": "RELIANCE", "rank_position": 1, "total_score": "0.85"},
    )


class CopilotServiceTest(unittest.TestCase):
    def test_local_answer_contains_facts_and_verified_sources(self) -> None:
        result = CopilotService(StaticEvidenceService((evidence_record(),))).ask(
            CopilotRequest("Explain the ranking")
        )
        self.assertEqual(result.provider, "local")
        self.assertIn("rank_position=1", result.answer)
        self.assertIn("Verified platform sources", result.answer)
        self.assertIn(RUN_ID, result.answer)
        self.assertFalse(result.insufficient_evidence)

    def test_model_answer_uses_evidence_and_sources_are_appended(self) -> None:
        result = CopilotService(StaticEvidenceService((evidence_record(),)), FakeProvider()).ask(
            CopilotRequest("Explain the ranking")
        )
        self.assertEqual(result.provider, "fake-model")
        self.assertIn("Model-grounded answer", result.answer)
        self.assertTrue(result.answer.endswith(evidence_record().citation))

    def test_model_failure_falls_back_and_sanitizes_error(self) -> None:
        result = CopilotService(
            StaticEvidenceService((evidence_record(),)),
            FakeProvider(RuntimeError("api_key=secret-key unavailable")),
        ).ask(CopilotRequest("Explain the ranking"))
        self.assertEqual(result.provider, "fake-model+local-fallback")
        self.assertIn("configured model was unavailable", result.answer)
        self.assertNotIn("secret-key", result.model_error)

    def test_missing_evidence_is_explicit(self) -> None:
        result = CopilotService(StaticEvidenceService(())).ask(
            CopilotRequest("Explain risk", symbol="TCS")
        )
        self.assertTrue(result.insufficient_evidence)
        self.assertIn("Insufficient persisted evidence for TCS", result.answer)

    def test_execution_request_is_refused_before_retrieval(self) -> None:
        evidence_service = StaticEvidenceService((evidence_record(),))
        result = CopilotService(evidence_service).ask(CopilotRequest("Place an order for RELIANCE"))
        self.assertEqual(result.provider, "safety-boundary")
        self.assertIn("cannot place", result.answer)
        self.assertEqual(evidence_service.calls, 0)


class OpenAIResponsesProviderTest(unittest.TestCase):
    def test_posts_grounded_responses_request_and_parses_text(self) -> None:
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeHttpResponse({
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "Grounded."}]}]
            })

        provider = OpenAIResponsesProvider("test-key", "test-model", 9, opener)
        answer = provider.answer("Explain ranking", (evidence_record(),))
        request, timeout = calls[0]
        payload = json.loads(request.data)
        self.assertEqual(answer, "Grounded.")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(payload["model"], "test-model")
        self.assertIn(evidence_record().citation, payload["input"])
        self.assertEqual(timeout, 9)

    def test_rejects_invalid_configuration_and_empty_output(self) -> None:
        for args in (("", "model", 1), ("key", "", 1), ("key", "model", 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                OpenAIResponsesProvider(*args)
        provider = OpenAIResponsesProvider("key", "model", opener=lambda *args, **kwargs: FakeHttpResponse({}))
        with self.assertRaisesRegex(RuntimeError, "no text"):
            provider.answer("question", (evidence_record(),))


if __name__ == "__main__":
    unittest.main()
