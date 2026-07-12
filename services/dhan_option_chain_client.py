from __future__ import annotations

from typing import Any

import requests

from services.config import DHAN_SETTINGS


class DhanOptionChainClient:
    endpoint = "https://api.dhan.co/v2/optionchain"

    def __init__(
        self,
        timeout_seconds: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def fetch(
        self,
        underlying_security_id: str,
        underlying_segment: str,
        expiry: str,
    ) -> dict[str, Any]:
        response = self.session.post(
            self.endpoint,
            headers={
                "access-token": DHAN_SETTINGS.access_token,
                "client-id": DHAN_SETTINGS.client_id,
                "Content-Type": "application/json",
            },
            json={
                "UnderlyingScrip": int(underlying_security_id),
                "UnderlyingSeg": underlying_segment,
                "Expiry": expiry,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(
                "Dhan option-chain response must be a JSON object."
            )
        if str(payload.get("status", "success")).lower() == "failure":
            raise RuntimeError(
                str(payload.get("remarks") or "Dhan request failed.")
            )
        return payload
