from __future__ import annotations

from dataclasses import dataclass
from typing import Any


COPILOT_RESOURCES = ("rankings", "selections", "risk", "signals", "backtests")


@dataclass(frozen=True)
class CopilotRequest:
    question: str
    symbol: str | None = None
    runs_per_resource: int = 2
    maximum_evidence_records: int = 20

    def normalized(self) -> "CopilotRequest":
        question = " ".join(self.question.split())
        symbol = self.symbol.strip().upper() if self.symbol else None
        if not question:
            raise ValueError("Copilot question must not be empty.")
        if len(question) > 2000:
            raise ValueError("Copilot question must not exceed 2000 characters.")
        if symbol is not None and (not symbol or len(symbol) > 30):
            raise ValueError("Copilot symbol must contain between 1 and 30 characters.")
        if not 1 <= self.runs_per_resource <= 5:
            raise ValueError("runs_per_resource must be between 1 and 5.")
        if not 1 <= self.maximum_evidence_records <= 100:
            raise ValueError("maximum_evidence_records must be between 1 and 100.")
        return CopilotRequest(
            question=question,
            symbol=symbol,
            runs_per_resource=self.runs_per_resource,
            maximum_evidence_records=self.maximum_evidence_records,
        )


@dataclass(frozen=True)
class CopilotEvidence:
    citation: str
    resource: str
    run_id: str
    item_id: str | None
    data: dict[str, Any]


@dataclass(frozen=True)
class CopilotAnswer:
    question: str
    answer: str
    evidence: tuple[CopilotEvidence, ...]
    provider: str
    insufficient_evidence: bool
    model_error: str | None = None
