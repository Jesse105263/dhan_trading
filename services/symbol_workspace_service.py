from __future__ import annotations

from datetime import date, datetime
from typing import Any

import psycopg

from services.market_workspace_service import MarketWorkspaceService, WorkspaceQueryError, WorkspaceUnavailable
from services.symbol_workspace_repository import SymbolWorkspaceRepository


class SymbolWorkspaceService:
    EVENTS = ("collection", "analytics", "ranking", "selection", "risk", "signal")

    def __init__(self, repository: SymbolWorkspaceRepository | None = None, clock=None) -> None:
        self.repository = repository or SymbolWorkspaceRepository()
        self.market = MarketWorkspaceService(clock=clock)

    def search(self, query: str, limit: int) -> dict[str, Any]:
        normalized = query.strip().upper()
        if len(normalized) > 30:
            raise WorkspaceQueryError("query must contain at most 30 characters.")
        if not 1 <= limit <= 25:
            raise WorkspaceQueryError("limit must be between 1 and 25.")
        try:
            rows = self.repository.search(normalized, limit)
            return {"data": rows, "count": len(rows)}
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Persisted symbol data is unavailable.") from exc

    def intelligence(self, symbol: str, expiry: str | None) -> dict[str, Any] | None:
        normalized = symbol.strip().upper()
        if not normalized or len(normalized) > 30:
            raise WorkspaceQueryError("symbol must contain 1 to 30 characters.")
        if expiry:
            try:
                date.fromisoformat(expiry)
            except ValueError as exc:
                raise WorkspaceQueryError("expiry must be an ISO date.") from exc
        try:
            data = self.repository.intelligence(normalized, expiry)
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Persisted symbol data is unavailable.") from exc
        if data is None:
            return None
        latest = data["analytics"][0]
        rankings = data["rankings"]
        current_rank = rankings[0] if rankings else None
        previous_rank = rankings[1] if len(rankings) > 1 else None
        timeline = self._timeline(data)
        return {
            **data,
            "freshness": self.market.freshness(latest["source_captured_at"]),
            "last_update": latest["source_captured_at"],
            "current_ranking": current_rank,
            "previous_rank": previous_rank["rank_position"] if previous_rank else None,
            "rank_movement": (previous_rank["rank_position"] - current_rank["rank_position"]) if current_rank and previous_rank else None,
            "timeline": timeline,
            "unsupported": ["iv_percentile", "greeks", "risk_score"],
        }

    def _timeline(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        events = []
        mappings = (
            ("collection", data["collections"], "requested_at", "run_id"),
            ("analytics", data["analytics"], "calculated_at", "analytics_id"),
            ("ranking", data["rankings"], "calculated_at", "ranking_id"),
            ("selection", data["selections"], "calculated_at", "selection_id"),
            ("risk", data["risk"], "calculated_at", "assessment_id"),
            ("signal", data["signals"], "calculated_at", "signal_id"),
        )
        for event_type, rows, timestamp, identifier in mappings:
            events.extend({"type": event_type, "timestamp": row[timestamp], "id": row[identifier]} for row in rows)
        return sorted(events, key=lambda event: (event["timestamp"], event["type"], str(event["id"])), reverse=True)
