from __future__ import annotations

import json

from services.copilot_models import CopilotAnswer, CopilotEvidence, CopilotRequest
from services.error_sanitizer import sanitize_error_message


EXECUTION_PHRASES = (
    "place an order", "place order", "execute order", "execute trade",
    "buy for me", "sell for me", "submit order", "send order",
)


class CopilotService:
    def __init__(self, evidence_service, provider=None) -> None:
        self.evidence_service = evidence_service
        self.provider = provider

    def ask(self, request: CopilotRequest) -> CopilotAnswer:
        normalized = request.normalized()
        if any(phrase in normalized.question.lower() for phrase in EXECUTION_PHRASES):
            return CopilotAnswer(
                normalized.question,
                "I cannot place or submit orders. I can explain persisted rankings, selections, risk decisions, signals, and backtest evidence.",
                (), "safety-boundary", True,
            )
        evidence = self.evidence_service.collect(normalized)
        if not evidence:
            scope = f" for {normalized.symbol}" if normalized.symbol else ""
            return CopilotAnswer(
                normalized.question,
                f"Insufficient persisted evidence{scope} to answer this question.",
                (), self.provider.name if self.provider else "local", True,
            )

        model_error = None
        if self.provider is None:
            answer = self._local_answer(evidence)
            provider_name = "local"
        else:
            provider_name = self.provider.name
            try:
                answer = self.provider.answer(normalized.question, evidence)
            except Exception as exc:
                model_error = sanitize_error_message(str(exc))
                answer = "The configured model was unavailable. " + self._local_answer(evidence)
                provider_name += "+local-fallback"
        sources = " ".join(item.citation for item in evidence)
        return CopilotAnswer(
            normalized.question,
            f"{answer.rstrip()}\n\nVerified platform sources: {sources}",
            evidence, provider_name, False, model_error,
        )

    @staticmethod
    def _local_answer(evidence: tuple[CopilotEvidence, ...]) -> str:
        lines = ["Persisted evidence summary:"]
        for item in evidence:
            data = item.data
            subject = data.get("underlying_symbol", data.get("trading_symbol", "run summary"))
            facts = CopilotService._important_facts(item.resource, data)
            lines.append(f"- {item.resource.title()} — {subject}: {facts} {item.citation}")
        return "\n".join(lines)

    @staticmethod
    def _important_facts(resource: str, data: dict) -> str:
        fields = {
            "rankings": ("rank_position", "total_score", "expiry"),
            "selections": ("option_type", "strike", "contract_score", "premium_per_lot"),
            "risk": ("approved", "rejection_code", "approved_lots", "approved_exposure", "maximum_loss"),
            "signals": ("action", "direction", "confidence_score", "entry_price", "maximum_loss"),
            "backtests": ("status", "total_net_pnl", "win_rate", "maximum_drawdown", "exit_reason"),
        }[resource]
        values = [f"{field}={json.dumps(data[field], default=str)}" for field in fields if field in data]
        return ", ".join(values) if values else "lineage metadata is available"
