from __future__ import annotations

import argparse
import json
import os
from uuid import UUID

from app.read_api import application
from services.copilot_provider import OpenAIResponsesProvider
from services.trading_analyst import AnalystRequest, TradingAnalystService


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the grounded local AI Trading Analyst.")
    parser.add_argument("--opportunity-id", action="append", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--provider", choices=("local", "openai"), default="local")
    parser.add_argument("--model", default=os.getenv("OPENAI_COPILOT_MODEL", "gpt-5.6"))
    args = parser.parse_args()
    provider = None
    if args.provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if not key: parser.error("OPENAI_API_KEY is required when --provider openai is used")
        provider = OpenAIResponsesProvider(key, args.model)
    service = TradingAnalystService(application.analyst.evidence_service, provider)
    request = AnalystRequest(args.question, tuple(UUID(value) for value in args.opportunity_id))
    print(json.dumps(service.ask(request), default=str, indent=2))


if __name__ == "__main__":
    main()
