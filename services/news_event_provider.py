from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class EventProvider(Protocol):
    def records(self, limit: int) -> list[dict[str, Any]]: ...


class LocalJsonEventProvider:
    """Bounded local JSON adapter. It performs no network access."""

    def __init__(self,path:Path): self.path=path

    def records(self,limit:int)->list[dict[str,Any]]:
        data=json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data,list): raise ValueError("Event fixture must contain a JSON array.")
        if len(data)>limit: raise ValueError(f"Event fixture exceeds the {limit} record limit.")
        return data
