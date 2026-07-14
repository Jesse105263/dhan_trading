from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Any, Callable, Iterable
from urllib.parse import parse_qs
from uuid import UUID

from services.read_api_repository import ReadApiRepository
from services.market_workspace_service import MarketWorkspaceService, WorkspaceQueryError, WorkspaceUnavailable


@dataclass(frozen=True)
class ApiResponse:
    status: HTTPStatus
    body: dict[str, Any]


class ReadOnlyApi:
    API_PREFIX = "/api/v1"
    DEFAULT_LIMIT = 20
    MAX_LIMIT = 100

    def __init__(self, repository: ReadApiRepository | None = None, workspace: MarketWorkspaceService | None = None) -> None:
        self.repository = repository or ReadApiRepository()
        self.workspace = workspace or MarketWorkspaceService()

    def handle(self, method: str, path: str, query_string: str = "") -> ApiResponse:
        if method.upper() != "GET":
            return self._error(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "Only GET is supported.")
        normalized = path.rstrip("/") or "/"
        if normalized == "/health":
            return ApiResponse(HTTPStatus.OK, self.repository.health())
        if normalized == "/api/v2":
            return ApiResponse(HTTPStatus.OK, {"name": "Dhan Trading Platform Read API", "version": "v2", "resources": ["overview", "opportunities"]})
        if normalized == "/api/v2/overview":
            try:
                return ApiResponse(HTTPStatus.OK, self.workspace.overview())
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted market data is unavailable.")
        if normalized == "/api/v2/opportunities":
            try:
                query = {key: values[0] for key, values in parse_qs(query_string, keep_blank_values=True).items()}
                return ApiResponse(HTTPStatus.OK, self.workspace.opportunities(query))
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted market data is unavailable.")
        opportunity_prefix = "/api/v2/opportunities/"
        if normalized.startswith(opportunity_prefix) and "/" not in normalized[len(opportunity_prefix):]:
            try:
                ranking_id = UUID(normalized[len(opportunity_prefix):])
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_ranking_id", "Ranking item ID must be a valid UUID.")
            try:
                row = self.workspace.opportunity(ranking_id)
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted market data is unavailable.")
            if row is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Opportunity was not found.")
            return ApiResponse(HTTPStatus.OK, {"data": row})
        if normalized == self.API_PREFIX:
            return ApiResponse(
                HTTPStatus.OK,
                {"name": "Dhan Trading Platform Read API", "version": "v1", "resources": list(self.repository.resources())},
            )
        prefix = self.API_PREFIX + "/"
        if not normalized.startswith(prefix):
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "Route not found.")
        parts = normalized[len(prefix):].split("/")
        resource = parts[0]
        if resource not in self.repository.resources():
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "Resource not found.")
        if len(parts) == 1:
            try:
                limit = self._parse_limit(query_string)
            except ValueError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_limit", str(exc))
            rows = self.repository.list_latest(resource, limit)
            return ApiResponse(HTTPStatus.OK, {"resource": resource, "count": len(rows), "data": rows})
        if len(parts) == 2:
            try:
                run_id = UUID(parts[1])
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_run_id", "Run ID must be a valid UUID.")
            row = self.repository.get_run(resource, run_id)
            if row is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", f"{resource} run was not found.")
            return ApiResponse(HTTPStatus.OK, {"resource": resource, "data": row})
        return self._error(HTTPStatus.NOT_FOUND, "not_found", "Route not found.")

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        response = self.handle(
            str(environ.get("REQUEST_METHOD", "GET")),
            str(environ.get("PATH_INFO", "/")),
            str(environ.get("QUERY_STRING", "")),
        )
        payload = json.dumps(response.body, default=self._json_default, separators=(",", ":")).encode("utf-8")
        start_response(
            f"{response.status.value} {response.status.phrase}",
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
        return [payload]

    @classmethod
    def _parse_limit(cls, query_string: str) -> int:
        values = parse_qs(query_string).get("limit", [str(cls.DEFAULT_LIMIT)])
        try:
            limit = int(values[0])
        except (TypeError, ValueError) as exc:
            raise ValueError("limit must be an integer.") from exc
        if not 1 <= limit <= cls.MAX_LIMIT:
            raise ValueError(f"limit must be between 1 and {cls.MAX_LIMIT}.")
        return limit

    @staticmethod
    def _json_default(value: Any) -> str:
        if isinstance(value, (UUID, date, datetime, Decimal)):
            return str(value)
        raise TypeError(f"Unsupported JSON value: {type(value).__name__}")

    @staticmethod
    def _error(status: HTTPStatus, code: str, message: str) -> ApiResponse:
        return ApiResponse(status, {"error": {"code": code, "message": message}})


application = ReadOnlyApi()
