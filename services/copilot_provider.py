from __future__ import annotations

import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from services.copilot_models import CopilotEvidence


class CopilotProvider(Protocol):
    @property
    def name(self) -> str: ...

    def answer(self, question: str, evidence: tuple[CopilotEvidence, ...]) -> str: ...


class OpenAIResponsesProvider:
    name = "openai"
    ENDPOINT = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        opener=urlopen,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OpenAI API key must not be empty.")
        if not model.strip():
            raise ValueError("OpenAI model must not be empty.")
        if timeout_seconds <= 0:
            raise ValueError("OpenAI timeout must be greater than zero.")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.opener = opener

    def answer(self, question: str, evidence: tuple[CopilotEvidence, ...]) -> str:
        evidence_payload = [
            {"citation": item.citation, "resource": item.resource, "data": item.data}
            for item in evidence
        ]
        body = json.dumps(
            {
                "model": self.model,
                "instructions": (
                    "You are the private Dhan research Copilot. Answer only from the supplied "
                    "persisted evidence. Cite factual claims with the exact supplied citation tokens. "
                    "Never claim to place orders, never invent missing values, and explicitly say when "
                    "the evidence is insufficient. Do not provide guaranteed-return claims."
                ),
                "input": f"Question: {question}\nPersisted evidence:\n{json.dumps(evidence_payload, default=str)}",
            },
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.ENDPOINT,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                message = self._error_message(exc)
            finally:
                exc.close()
            raise RuntimeError(message) from exc
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("OpenAI response generation failed.") from exc
        text = self._output_text(payload)
        if not text:
            raise RuntimeError("OpenAI returned no text output.")
        return text

    @staticmethod
    def _output_text(payload: object) -> str:
        if not isinstance(payload, dict):
            return ""
        direct = payload.get("output_text")
        if isinstance(direct, str):
            return direct.strip()
        parts = []
        for output in payload.get("output", []):
            if not isinstance(output, dict) or output.get("type") != "message":
                continue
            for content in output.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    parts.append(str(content.get("text", "")))
        return "\n".join(parts).strip()

    @staticmethod
    def _error_message(error: HTTPError) -> str:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            return f"OpenAI request failed: {payload['error']['message']}"
        except (KeyError, TypeError, ValueError, UnicodeDecodeError):
            return f"OpenAI request failed with HTTP {error.code}."
