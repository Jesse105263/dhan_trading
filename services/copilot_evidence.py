from __future__ import annotations

from typing import Any

from services.copilot_models import COPILOT_RESOURCES, CopilotEvidence, CopilotRequest


RESOURCE_KEYWORDS = {
    "rankings": ("rank", "ranking", "opportunity", "score", "compare"),
    "selections": ("selection", "select", "contract", "strike", "spread", "premium"),
    "risk": ("risk", "approval", "approved", "rejection", "rejected", "exposure", "loss", "size"),
    "signals": ("signal", "confidence", "entry", "direction", "bullish", "bearish"),
    "backtests": ("backtest", "performance", "pnl", "profit", "win rate", "drawdown", "trade evidence"),
}

RUN_ID_FIELDS = {
    "rankings": "ranking_run_id",
    "selections": "selection_run_id",
    "risk": "risk_run_id",
    "signals": "signal_run_id",
    "backtests": "backtest_run_id",
}


class CopilotEvidenceService:
    def __init__(self, api_client) -> None:
        self.api_client = api_client

    def collect(self, request: CopilotRequest) -> tuple[CopilotEvidence, ...]:
        normalized = request.normalized()
        resources = self.resources_for_question(normalized.question)
        evidence: list[CopilotEvidence] = []
        for resource in resources:
            collection = self.api_client.list_runs(resource, normalized.runs_per_resource)
            runs = collection.get("data", [])
            if not isinstance(runs, list):
                raise ValueError(f"Unexpected {resource} collection from read API.")
            for run_summary in runs:
                if not isinstance(run_summary, dict):
                    continue
                run_id = str(run_summary.get(RUN_ID_FIELDS[resource], ""))
                if not run_id:
                    continue
                detail_payload = self.api_client.get_run(resource, run_id)
                detail = detail_payload.get("data", {})
                if not isinstance(detail, dict):
                    continue
                items = detail.get("items", [])
                matching_items = [
                    item for item in items
                    if isinstance(item, dict) and self._matches_symbol(item, normalized.symbol)
                ] if isinstance(items, list) else []
                if matching_items:
                    for item in matching_items:
                        evidence.append(self._item_evidence(resource, run_id, item))
                        if len(evidence) >= normalized.maximum_evidence_records:
                            return tuple(evidence)
                elif normalized.symbol is None:
                    summary = {key: value for key, value in detail.items() if key != "items"}
                    evidence.append(
                        CopilotEvidence(
                            citation=f"[{resource}:{run_id}]", resource=resource,
                            run_id=run_id, item_id=None, data=summary,
                        )
                    )
                    if len(evidence) >= normalized.maximum_evidence_records:
                        return tuple(evidence)
        return tuple(evidence)

    @staticmethod
    def resources_for_question(question: str) -> tuple[str, ...]:
        lowered = question.lower()
        selected = tuple(
            resource for resource in COPILOT_RESOURCES
            if any(keyword in lowered for keyword in RESOURCE_KEYWORDS[resource])
        )
        return selected or COPILOT_RESOURCES

    @staticmethod
    def _matches_symbol(item: dict[str, Any], symbol: str | None) -> bool:
        if symbol is None:
            return True
        value = item.get("underlying_symbol", item.get("symbol"))
        return isinstance(value, str) and value.upper() == symbol

    @staticmethod
    def _item_evidence(resource: str, run_id: str, item: dict[str, Any]) -> CopilotEvidence:
        item_id = next(
            (str(value) for key, value in item.items() if key.endswith("_id") and key != RUN_ID_FIELDS[resource]),
            None,
        )
        citation = f"[{resource}:{run_id}:{item_id}]" if item_id else f"[{resource}:{run_id}]"
        return CopilotEvidence(citation, resource, run_id, item_id, dict(item))
