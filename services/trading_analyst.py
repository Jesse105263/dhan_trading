from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from services.copilot_models import CopilotEvidence
from services.error_sanitizer import sanitize_error_message


REFUSAL_PHRASES = (
    "place an order", "execute a trade", "submit to dhan", "auto-trade",
    "autotrade", "bypass risk", "paper to live", "guarantee profit",
)


class AnalystProvider(Protocol):
    @property
    def name(self) -> str: ...

    def answer(self, question: str, evidence: tuple[CopilotEvidence, ...]) -> str: ...


@dataclass(frozen=True)
class AnalystRequest:
    question: str
    opportunity_ids: tuple[UUID, ...]

    def normalized(self) -> "AnalystRequest":
        question = " ".join(self.question.split())
        if not question:
            raise ValueError("question must not be empty.")
        if len(question) > 2000:
            raise ValueError("question must not exceed 2000 characters.")
        if not 1 <= len(self.opportunity_ids) <= 5:
            raise ValueError("opportunity_ids must contain between 1 and 5 identifiers.")
        if len(set(self.opportunity_ids)) != len(self.opportunity_ids):
            raise ValueError("opportunity_ids must not contain duplicates.")
        return AnalystRequest(question, self.opportunity_ids)


class TradingAnalystEvidenceService:
    SCHEMA_VERSION = "trading-analyst-evidence-v1"

    def __init__(self, opportunities, features, memory, similarity, events) -> None:
        self.opportunities = opportunities
        self.features = features
        self.memory = memory
        self.similarity = similarity
        self.events = events

    def assemble(self, opportunity_id: UUID) -> dict[str, Any] | None:
        opportunity = self.opportunities.detail(opportunity_id)
        if opportunity is None:
            return None
        vector = self.features.detail(UUID(str(opportunity["query_vector_id"])))
        snapshot = self.memory.detail(UUID(str(opportunity["query_analytics_id"])))
        similarity = self.similarity.run(UUID(str(opportunity["similarity_run_id"])), matches=True)
        event_context = self.events.opportunity_context(opportunity_id)
        evidence = opportunity.get("evidence", [])
        similarity_matches = (similarity or {}).get("matches", [])
        historical_outcomes = [row.get("outcome") for row in similarity_matches if row.get("outcome")]
        citations = self._citations(opportunity, evidence, similarity_matches, event_context)
        eligible = opportunity["state"] == "ELIGIBLE"
        packet = {
            "schema_version": self.SCHEMA_VERSION,
            "opportunity_id": opportunity_id,
            "evidence_state": opportunity["state"],
            "opportunity": {
                key: opportunity.get(key) for key in (
                    "underlying_symbol", "expiry", "observed_at", "direction",
                    "opportunity_score", "evidence_quality", "match_count", "classified_count",
                    "entry_zone_low", "entry_zone_high", "stop_zone", "target_zones",
                    "historical_win_rate", "expected_value", "risk_reward",
                    "reasons_for", "reasons_against",
                )
            },
            "underlying_reference_levels": {
                "entry_zone_low": opportunity.get("entry_zone_low") if eligible else None,
                "entry_zone_high": opportunity.get("entry_zone_high") if eligible else None,
                "stop_zone": opportunity.get("stop_zone") if eligible else None,
                "target_zones": opportunity.get("target_zones", []) if eligible else [],
                "instrument_basis": "underlying_reference",
            },
            "feature_vector": vector,
            "market_memory": snapshot,
            "similarity": similarity,
            "historical_outcomes": historical_outcomes,
            "event_context": event_context,
            "limitations": self._limitations(opportunity, vector, similarity, event_context),
            "lineage": {
                "opportunity_id": opportunity_id,
                "similarity_run_id": opportunity.get("similarity_run_id"),
                "query_vector_id": opportunity.get("query_vector_id"),
                "query_analytics_id": opportunity.get("query_analytics_id"),
                "query_ranking_id": opportunity.get("query_ranking_id"),
                "matched_evidence": [
                    {key: row.get(key) for key in (
                        "similarity_match_id", "matched_vector_id", "matched_outcome_id"
                    )} for row in evidence
                ],
            },
            "citations": citations,
        }
        return packet

    @staticmethod
    def _citations(opportunity, evidence, similarity_matches, event_context):
        rows = [
            {"id": str(opportunity["opportunity_id"]), "type": "trade_opportunity",
             "citation": f"[opportunity:{opportunity['opportunity_id']}]"},
            {"id": str(opportunity["query_vector_id"]), "type": "feature_vector",
             "citation": f"[feature:{opportunity['query_vector_id']}]"},
            {"id": str(opportunity["query_analytics_id"]), "type": "market_memory",
             "citation": f"[memory:{opportunity['query_analytics_id']}]"},
            {"id": str(opportunity["similarity_run_id"]), "type": "similarity_run",
             "citation": f"[similarity:{opportunity['similarity_run_id']}]"},
        ]
        for item in evidence:
            rows.extend((
                {"id": str(item["matched_vector_id"]), "type": "feature_vector",
                 "citation": f"[feature:{item['matched_vector_id']}]"},
                {"id": str(item["matched_outcome_id"]), "type": "historical_outcome",
                 "citation": f"[outcome:{item['matched_outcome_id']}]"},
            ))
        existing = {(row["type"], row["id"]) for row in rows}
        for item in similarity_matches:
            outcome_id = item.get("matched_outcome_id") or item.get("outcome_id")
            if outcome_id is not None and ("historical_outcome", str(outcome_id)) not in existing:
                rows.append({"id": str(outcome_id), "type": "historical_outcome",
                             "citation": f"[outcome:{outcome_id}]"})
        for context in (event_context or {}).get("events", []):
            rows.append({"id": str(context["event_id"]), "type": "market_event",
                         "citation": f"[event:{context['event_id']}]"})
        return rows

    @staticmethod
    def _limitations(opportunity, vector, similarity, events):
        result = [
            "The analyst explains persisted deterministic evidence; it does not create or modify opportunities.",
            "Entry, stop, and targets are underlying reference levels, not option-premium prices or execution instructions.",
            "Historical behavior does not guarantee future results.",
        ]
        if opportunity["state"] != "ELIGIBLE":
            result.append("INSUFFICIENT_EVIDENCE: recommendation fields are unavailable.")
        if vector is None: result.append("The query Feature Store vector is unavailable.")
        if similarity is None: result.append("The persisted similarity run is unavailable.")
        if not (events or {}).get("events"): result.append("No linked news or event context is available.")
        return result


class TradingAnalystService:
    def __init__(self, evidence_service: TradingAnalystEvidenceService, provider: AnalystProvider | None = None) -> None:
        self.evidence_service = evidence_service
        self.provider = provider

    def ask(self, request: AnalystRequest) -> dict[str, Any]:
        normalized = request.normalized()
        if any(phrase in normalized.question.lower() for phrase in REFUSAL_PHRASES):
            return {"status": "REFUSED", "provider": "safety-boundary", "answer": self._refusal(),
                    "evidence": [], "citations": [], "model_error": None}
        packets = []
        for identifier in normalized.opportunity_ids:
            packet = self.evidence_service.assemble(identifier)
            if packet is None:
                raise LookupError(str(identifier))
            packets.append(packet)
        answer = self._local_answer(packets, compare=len(packets) > 1)
        provider_name, model_error = "local", None
        if self.provider is not None:
            provider_name = self.provider.name
            try:
                answer = self.provider.answer(normalized.question, self._provider_evidence(packets))
            except Exception as exc:
                model_error = sanitize_error_message(str(exc))
                provider_name += "+local-fallback"
        citations = [citation for packet in packets for citation in packet["citations"]]
        return {"status": "ANSWERED", "provider": provider_name, "answer": answer,
                "evidence": packets, "citations": citations, "model_error": model_error}

    @staticmethod
    def _provider_evidence(packets):
        return tuple(CopilotEvidence(
            f"[opportunity:{packet['opportunity_id']}]", "trade_opportunity",
            str(packet["opportunity_id"]), None, packet,
        ) for packet in packets)

    @staticmethod
    def _refusal():
        return "I cannot execute trades, submit orders, bypass controls, convert paper records to live orders, or guarantee profit. I can explain persisted evidence."

    @staticmethod
    def _local_answer(packets, compare=False):
        sections = []
        for packet in packets:
            item = packet["opportunity"]
            event_context = packet.get("event_context") or {}
            reasons_for = [*item.get("reasons_for", []), *event_context.get("reasons_for", [])]
            reasons_against = [*item.get("reasons_against", []), *event_context.get("reasons_against", [])]
            citation = f"[opportunity:{packet['opportunity_id']}]"
            if packet["evidence_state"] != "ELIGIBLE":
                sections.append(f"Facts\nINSUFFICIENT_EVIDENCE {citation}\n\nLimitations\n" + "\n".join(f"- {x}" for x in packet["limitations"]))
                continue
            levels = packet["underlying_reference_levels"]
            sections.append(
                "Facts\n"
                f"- {item['underlying_symbol']} expires {item['expiry']}; underlying reference entry "
                f"{levels['entry_zone_low']}–{levels['entry_zone_high']}, stop {levels['stop_zone']}, "
                f"targets {json.dumps(levels['target_zones'], default=str)}. {citation}\n"
                f"- Historical win rate {item['historical_win_rate']}; expected value {item['expected_value']}; "
                f"risk/reward {item['risk_reward']}; evidence quality {item['evidence_quality']}; "
                f"classified sample {item['classified_count']}. {citation}\n\n"
                "Historical evidence\n"
                f"- {item['match_count']} similarity matches and {item['classified_count']} classified outcomes support the persisted assessment. {citation}\n\n"
                "Interpretation\n- This is an explanation of the deterministic opportunity, not a new recommendation or execution instruction.\n\n"
                "Reasons for\n" + ("\n".join(f"- {x}" for x in reasons_for) or "- None persisted.") +
                "\n\nReasons against\n" + ("\n".join(f"- {x}" for x in reasons_against) or "- None persisted.") +
                "\n\nLimitations\n" + "\n".join(f"- {x}" for x in packet["limitations"])
            )
        prefix = "Comparison of persisted opportunities\n\n" if compare else ""
        return prefix + "\n\n---\n\n".join(sections)
