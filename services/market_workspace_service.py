from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import psycopg

from services.market_workspace_repository import MarketWorkspaceRepository


class WorkspaceQueryError(ValueError):
    pass


class WorkspaceUnavailable(RuntimeError):
    pass


class MarketWorkspaceService:
    CURRENT = timedelta(minutes=15)
    AGING = timedelta(minutes=60)
    SORTS = ("rank", "score", "captured_at", "symbol")

    def __init__(self, repository: MarketWorkspaceRepository | None = None, clock=None) -> None:
        self.repository = repository or MarketWorkspaceRepository()
        self.clock = clock or datetime.now

    def freshness(self, timestamp: datetime | None) -> str:
        if timestamp is None:
            return "unavailable"
        age = max(self.clock() - timestamp, timedelta())
        if age <= self.CURRENT:
            return "current"
        if age <= self.AGING:
            return "aging"
        return "stale"

    def overview(self) -> dict[str, Any]:
        try:
            data = self.repository.overview()
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Persisted market data is unavailable.") from exc
        option_run = data["latest_option_run"]
        ranking_run = data["latest_ranking_run"]
        source_time = option_run["completed_at"] if option_run else None
        return {
            "platform": {"status": "ok" if data["database_ready"] else "unavailable", "database_ready": bool(data["database_ready"])},
            "freshness": {"state": self.freshness(source_time), "source_timestamp": source_time},
            "latest_option_run": option_run,
            "latest_ranking_run": ranking_run,
            "counts": data["counts"],
            "recent_failures": data["failures"],
        }

    def opportunities(self, query: dict[str, str]) -> dict[str, Any]:
        limit = self._integer(query, "limit", 25, 1, 100)
        offset = self._integer(query, "offset", 0, 0, 10000)
        sort = query.get("sort", "rank")
        if sort not in self.SORTS:
            raise WorkspaceQueryError(f"sort must be one of: {', '.join(self.SORTS)}.")
        direction = query.get("direction", "asc" if sort in ("rank", "symbol") else "desc").lower()
        if direction not in ("asc", "desc"):
            raise WorkspaceQueryError("direction must be asc or desc.")
        minimum_score = self._score(query.get("minimum_score"))
        filters = {name: self._boolean(query.get(name)) for name in ("selection", "risk_approved", "signal")}
        freshness_filter = query.get("freshness")
        if freshness_filter and freshness_filter not in ("current", "aging", "stale"):
            raise WorkspaceQueryError("freshness must be current, aging, or stale.")
        now = self.clock()
        try:
            rows, total = self.repository.list_opportunities(
                symbol=query.get("symbol") or None, expiry=query.get("expiry") or None,
                minimum_score=minimum_score, freshness=freshness_filter,
                current_cutoff=now - self.CURRENT, aging_cutoff=now - self.AGING,
                sort=sort, direction=direction,
                limit=limit, offset=offset, **filters,
            )
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Persisted market data is unavailable.") from exc
        projected = [dict(row, freshness=self.freshness(row["source_captured_at"])) for row in rows]
        return {"data": projected, "page": {"limit": limit, "offset": offset, "count": len(projected), "total": total}, "sort": {"field": sort, "direction": direction}}

    def opportunity(self, ranking_id: UUID) -> dict[str, Any] | None:
        try:
            row = self.repository.get_opportunity(ranking_id)
        except psycopg.Error as exc:
            raise WorkspaceUnavailable("Persisted market data is unavailable.") from exc
        return None if row is None else dict(row, freshness=self.freshness(row["source_captured_at"]))

    @staticmethod
    def _integer(query: dict[str, str], name: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(query.get(name, str(default)))
        except ValueError as exc:
            raise WorkspaceQueryError(f"{name} must be an integer.") from exc
        if not minimum <= value <= maximum:
            raise WorkspaceQueryError(f"{name} must be between {minimum} and {maximum}.")
        return value

    @staticmethod
    def _boolean(value: str | None) -> bool | None:
        if value in (None, ""):
            return None
        if value.lower() not in ("true", "false"):
            raise WorkspaceQueryError("availability filters must be true or false.")
        return value.lower() == "true"

    @staticmethod
    def _score(value: str | None) -> Decimal | None:
        if value in (None, ""):
            return None
        try:
            score = Decimal(value)
        except InvalidOperation as exc:
            raise WorkspaceQueryError("minimum_score must be a number between 0 and 1.") from exc
        if not Decimal("0") <= score <= Decimal("1"):
            raise WorkspaceQueryError("minimum_score must be a number between 0 and 1.")
        return score
