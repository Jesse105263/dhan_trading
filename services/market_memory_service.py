from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

import psycopg

from services.market_memory_repository import MarketMemoryRepository
from services.market_workspace_service import MarketWorkspaceService, WorkspaceQueryError, WorkspaceUnavailable


class MarketMemoryService:
    """Canonical projections over persisted observations; never calculates market analytics."""

    FEATURES = (
        "spot_price", "atm_strike", "atm_distance", "atm_distance_pct",
        "atm_call_price", "atm_put_price", "atm_straddle_cost", "total_call_oi",
        "total_put_oi", "total_pcr", "nearby_call_oi", "nearby_put_oi", "nearby_pcr",
        "atm_call_iv", "atm_put_iv", "atm_mean_iv", "nearby_call_mean_iv",
        "nearby_put_mean_iv", "nearby_mean_iv", "call_oi_wall_strike",
        "call_oi_wall_value", "put_oi_wall_strike", "put_oi_wall_value",
        "price_coverage", "liquidity_coverage", "rank_position", "total_score",
        "liquidity_score", "activity_score", "volatility_score", "directional_score",
    )
    MAX_LIMIT = 200

    def __init__(self, repository: MarketMemoryRepository | None = None, clock=None) -> None:
        self.repository = repository or MarketMemoryRepository()
        self.market = MarketWorkspaceService(clock=clock)

    def list(self, query: dict[str, str], before: str | None = None) -> dict[str, Any]:
        symbol = self._symbol(query.get("symbol"))
        expiry = self._date(query.get("expiry"), "expiry")
        start = self._timestamp(query.get("from"), "from")
        end = self._timestamp(query.get("to"), "to")
        boundary = self._timestamp(before, "before")
        limit = self._limit(query.get("limit"))
        if start and end and start > end:
            raise WorkspaceQueryError("from must not be later than to.")
        try:
            rows = self.repository.snapshots(symbol, expiry, start, end, limit, boundary)
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Persisted market memory is unavailable.") from exc
        data = [self._snapshot(row) for row in rows]
        return {"data": data, "count": len(data), "limit": limit, "features": list(self.FEATURES)}

    def latest(self, query: dict[str, str], previous: bool = False) -> dict[str, Any] | None:
        result = self.list({**query, "limit": "2" if previous else "1"})["data"]
        index = 1 if previous else 0
        return result[index] if len(result) > index else None

    def detail(self, snapshot_id: UUID) -> dict[str, Any] | None:
        try:
            row = self.repository.snapshot(snapshot_id)
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Persisted market memory is unavailable.") from exc
        return self._snapshot(row) if row else None

    def compare(self, previous_id: UUID, current_id: UUID) -> dict[str, Any] | None:
        previous, current = self.detail(previous_id), self.detail(current_id)
        if previous is None or current is None:
            return None
        if previous["captured_at"] > current["captured_at"]:
            previous, current = current, previous
        changes = [
            {"feature": name, "previous": previous[name], "current": current[name]}
            for name in ("symbol", "expiry")
            if previous[name] != current[name]
        ] + [
            {"feature": name, "previous": previous["features"][name], "current": current["features"][name]}
            for name in self.FEATURES
            if previous["features"][name] != current["features"][name]
        ]
        return {
            "symbol": current["symbol"], "expiry": current["expiry"],
            "previous_snapshot_id": previous["snapshot_id"],
            "current_snapshot_id": current["snapshot_id"],
            "previous_captured_at": previous["captured_at"],
            "current_captured_at": current["captured_at"], "changes": changes,
        }

    def feature_history(self, feature: str, query: dict[str, str]) -> dict[str, Any]:
        if feature not in self.FEATURES:
            raise WorkspaceQueryError(f"feature must be one of: {', '.join(self.FEATURES)}.")
        result = self.list(query)
        return {
            "feature": feature,
            "symbol": self._symbol(query.get("symbol")),
            "data": [
                {"snapshot_id": row["snapshot_id"], "captured_at": row["captured_at"],
                 "expiry": row["expiry"], "value": row["features"][feature], "freshness": row["freshness"]}
                for row in reversed(result["data"])
            ],
            "count": result["count"], "limit": result["limit"],
        }

    def _snapshot(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "snapshot_id": row["analytics_id"], "snapshot_type": "option_analytics",
            "symbol": row["underlying_symbol"], "expiry": row["expiry"],
            "captured_at": row["source_captured_at"], "calculated_at": row["calculated_at"],
            "freshness": self.market.freshness(row["source_captured_at"]),
            "features": {name: row.get(name) for name in self.FEATURES},
            "lineage": {key: row.get(key) for key in (
                "source_run_id", "analytics_id", "change_id", "previous_analytics_id",
                "ranking_id", "ranking_run_id")},
        }

    @staticmethod
    def _symbol(value: str | None) -> str:
        symbol = (value or "").strip().upper()
        if not symbol or len(symbol) > 30:
            raise WorkspaceQueryError("symbol must contain 1 to 30 characters.")
        return symbol

    @staticmethod
    def _date(value: str | None, name: str) -> str | None:
        if value is None or value == "": return None
        try: date.fromisoformat(value)
        except ValueError as exc: raise WorkspaceQueryError(f"{name} must be an ISO date.") from exc
        return value

    @staticmethod
    def _timestamp(value: str | None, name: str) -> str | None:
        if value is None or value == "": return None
        try: datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc: raise WorkspaceQueryError(f"{name} must be an ISO timestamp.") from exc
        return value

    @classmethod
    def _limit(cls, value: str | None) -> int:
        try: limit = int(value or "50")
        except ValueError as exc: raise WorkspaceQueryError("limit must be an integer.") from exc
        if not 1 <= limit <= cls.MAX_LIMIT:
            raise WorkspaceQueryError(f"limit must be between 1 and {cls.MAX_LIMIT}.")
        return limit
