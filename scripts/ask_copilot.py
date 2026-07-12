from __future__ import annotations

import argparse
import os

from services.copilot_api_client import CopilotApiClient
from services.copilot_evidence import CopilotEvidenceService
from services.copilot_models import CopilotRequest
from services.copilot_provider import OpenAIResponsesProvider
from services.copilot_service import CopilotService


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the private read-only Dhan research Copilot.")
    parser.add_argument("question")
    parser.add_argument("--symbol")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--api-timeout", type=float, default=5.0)
    parser.add_argument("--runs-per-resource", type=int, default=2)
    parser.add_argument("--maximum-evidence-records", type=int, default=20)
    parser.add_argument("--provider", choices=("local", "openai"), default="local")
    parser.add_argument("--model", default=os.getenv("OPENAI_COPILOT_MODEL", "gpt-5.6"))
    parser.add_argument("--model-timeout", type=float, default=30.0)
    args = parser.parse_args()

    provider = None
    if args.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            parser.error("OPENAI_API_KEY is required when --provider openai is used")
        provider = OpenAIResponsesProvider(api_key, args.model, args.model_timeout)
    service = CopilotService(
        CopilotEvidenceService(CopilotApiClient(args.api_base_url, args.api_timeout)),
        provider,
    )
    result = service.ask(
        CopilotRequest(
            question=args.question,
            symbol=args.symbol,
            runs_per_resource=args.runs_per_resource,
            maximum_evidence_records=args.maximum_evidence_records,
        )
    )
    print(result.answer)
    print(f"\nProvider: {result.provider}")
    print(f"Evidence records: {len(result.evidence)}")
    if result.model_error:
        print(f"Model error: {result.model_error}")


if __name__ == "__main__":
    main()
