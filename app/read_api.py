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
from services.symbol_workspace_service import SymbolWorkspaceService
from services.market_memory_service import MarketMemoryService
from services.feature_store_service import FeatureStoreService
from services.historical_outcome_service import HistoricalOutcomeService
from services.similarity_service import SimilarityService
from services.trade_opportunity_service import TradeOpportunityService
from services.news_event_service import NewsEventService
from services.trading_analyst import AnalystRequest, TradingAnalystEvidenceService, TradingAnalystService


@dataclass(frozen=True)
class ApiResponse:
    status: HTTPStatus
    body: dict[str, Any]


class ReadOnlyApi:
    API_PREFIX = "/api/v1"
    DEFAULT_LIMIT = 20
    MAX_LIMIT = 100

    def __init__(self, repository: ReadApiRepository | None = None, workspace: MarketWorkspaceService | None = None, symbols: SymbolWorkspaceService | None = None, memory: MarketMemoryService | None = None, features: FeatureStoreService | None = None, outcomes: HistoricalOutcomeService | None = None, similarity: SimilarityService | None = None, trade_opportunities: TradeOpportunityService | None = None, events: NewsEventService | None = None, analyst: TradingAnalystService | None = None) -> None:
        self.repository = repository or ReadApiRepository()
        self.workspace = workspace or MarketWorkspaceService()
        self.symbols = symbols or SymbolWorkspaceService()
        self.memory = memory or MarketMemoryService()
        self.features = features or FeatureStoreService()
        self.outcomes = outcomes or HistoricalOutcomeService()
        self.similarity = similarity or SimilarityService()
        self.trade_opportunities = trade_opportunities or TradeOpportunityService()
        self.events = events or NewsEventService()
        self.analyst = analyst or TradingAnalystService(TradingAnalystEvidenceService(
            self.trade_opportunities, self.features, self.memory, self.similarity, self.events
        ))

    def handle(self, method: str, path: str, query_string: str = "", body: dict[str, Any] | None = None) -> ApiResponse:
        normalized = path.rstrip("/") or "/"
        if method.upper() == "POST" and normalized.startswith("/api/v2/analyst/"):
            return self._handle_analyst(normalized, body)
        if method.upper() != "GET":
            return self._error(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "Only GET is supported except bounded analyst research commands.")
        if normalized == "/health":
            return ApiResponse(HTTPStatus.OK, self.repository.health())
        if normalized == "/api/v2":
            return ApiResponse(HTTPStatus.OK, {"name": "Dhan Trading Platform Read API", "version": "v2", "resources": ["overview", "opportunities", "symbols", "memory", "features", "outcomes", "similarity", "trade-opportunities", "events", "analyst"]})
        if normalized in ("/api/v2/events","/api/v2/events/context"):
            query={key:values[0] for key,values in parse_qs(query_string,keep_blank_values=True).items()}
            try:
                data=self.events.context(query) if normalized.endswith("/context") else self.events.list(query)
            except WorkspaceQueryError as exc: return self._error(HTTPStatus.BAD_REQUEST,"invalid_query",str(exc))
            except WorkspaceUnavailable: return self._error(HTTPStatus.SERVICE_UNAVAILABLE,"database_unavailable","Event intelligence is unavailable.")
            if data is None: return self._error(HTTPStatus.NOT_FOUND,"not_found","Event context source was not found.")
            return ApiResponse(HTTPStatus.OK,{"data":data} if normalized.endswith("/context") else data)
        event_prefix="/api/v2/events/"
        if normalized.startswith(event_prefix) and "/" not in normalized[len(event_prefix):]:
            try: event_id=UUID(normalized[len(event_prefix):])
            except ValueError: return self._error(HTTPStatus.BAD_REQUEST,"invalid_event_id","Event ID must be a valid UUID.")
            try: data=self.events.detail(event_id)
            except WorkspaceUnavailable: return self._error(HTTPStatus.SERVICE_UNAVAILABLE,"database_unavailable","Event intelligence is unavailable.")
            if data is None: return self._error(HTTPStatus.NOT_FOUND,"not_found","Event was not found.")
            return ApiResponse(HTTPStatus.OK,{"data":data})
        trade_event_suffix="/events"
        if normalized.startswith("/api/v2/trade-opportunities/") and normalized.endswith(trade_event_suffix):
            identifier=normalized[len("/api/v2/trade-opportunities/"):-len(trade_event_suffix)]
            try: opportunity_id=UUID(identifier)
            except ValueError: return self._error(HTTPStatus.BAD_REQUEST,"invalid_opportunity_id","Opportunity ID must be a valid UUID.")
            try: data=self.events.opportunity_context(opportunity_id)
            except WorkspaceUnavailable: return self._error(HTTPStatus.SERVICE_UNAVAILABLE,"database_unavailable","Event intelligence is unavailable.")
            if data is None: return self._error(HTTPStatus.NOT_FOUND,"not_found","Trade opportunity was not found.")
            return ApiResponse(HTTPStatus.OK,{"data":data})
        if normalized == "/api/v2/trade-opportunities":
            query={key:values[0] for key,values in parse_qs(query_string,keep_blank_values=True).items()}
            try: return ApiResponse(HTTPStatus.OK,self.trade_opportunities.list(query))
            except WorkspaceQueryError as exc: return self._error(HTTPStatus.BAD_REQUEST,"invalid_query",str(exc))
            except WorkspaceUnavailable: return self._error(HTTPStatus.SERVICE_UNAVAILABLE,"database_unavailable","Trade opportunities are unavailable.")
        trade_prefix="/api/v2/trade-opportunities/"
        if normalized.startswith(trade_prefix) and "/" not in normalized[len(trade_prefix):]:
            try: opportunity_id=UUID(normalized[len(trade_prefix):])
            except ValueError: return self._error(HTTPStatus.BAD_REQUEST,"invalid_opportunity_id","Opportunity ID must be a valid UUID.")
            try: data=self.trade_opportunities.detail(opportunity_id)
            except WorkspaceUnavailable: return self._error(HTTPStatus.SERVICE_UNAVAILABLE,"database_unavailable","Trade opportunities are unavailable.")
            if data is None: return self._error(HTTPStatus.NOT_FOUND,"not_found","Trade opportunity was not found.")
            return ApiResponse(HTTPStatus.OK,{"data":data})
        if normalized == "/api/v2/similarity/models":
            return ApiResponse(HTTPStatus.OK, self.similarity.models())
        if normalized == "/api/v2/similarity":
            query = {key: values[0] for key, values in parse_qs(query_string, keep_blank_values=True).items()}
            try:
                vector_id = UUID(query.pop("vector_id", ""))
                data = self.similarity.analyze(vector_id, query)
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_vector_id", "vector_id must be a valid UUID.")
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Similarity evidence is unavailable.")
            if data is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Feature vector was not found.")
            return ApiResponse(HTTPStatus.OK, {"data": data})
        run_prefix = "/api/v2/similarity/runs/"
        if normalized.startswith(run_prefix):
            remainder=normalized[len(run_prefix):]; include_matches=remainder.endswith("/matches")
            identifier=remainder[:-8] if include_matches else remainder
            if "/" in identifier: return self._error(HTTPStatus.NOT_FOUND,"not_found","Route not found.")
            try: run_id=UUID(identifier)
            except ValueError: return self._error(HTTPStatus.BAD_REQUEST,"invalid_run_id","Run ID must be a valid UUID.")
            try: data=self.similarity.run(run_id,matches=include_matches)
            except WorkspaceUnavailable: return self._error(HTTPStatus.SERVICE_UNAVAILABLE,"database_unavailable","Similarity evidence is unavailable.")
            if data is None: return self._error(HTTPStatus.NOT_FOUND,"not_found","Similarity run was not found.")
            return ApiResponse(HTTPStatus.OK,{"data":data})
        if normalized in ("/api/v2/outcomes", "/api/v2/outcomes/history", "/api/v2/outcomes/statistics"):
            try:
                query = {key: values[0] for key, values in parse_qs(query_string, keep_blank_values=True).items()}
                if normalized.endswith("/statistics"):
                    return ApiResponse(HTTPStatus.OK, self.outcomes.statistics(query))
                return ApiResponse(HTTPStatus.OK, self.outcomes.list(query, ascending=normalized.endswith("/history")))
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Historical outcomes are unavailable.")
        outcome_prefix = "/api/v2/outcomes/"
        if normalized.startswith(outcome_prefix) and "/" not in normalized[len(outcome_prefix):]:
            try:
                outcome_id = UUID(normalized[len(outcome_prefix):])
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_outcome_id", "Outcome ID must be a valid UUID.")
            try:
                data = self.outcomes.detail(outcome_id)
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Historical outcomes are unavailable.")
            if data is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Historical outcome was not found.")
            return ApiResponse(HTTPStatus.OK, {"data": data})
        if normalized == "/api/v2/features/definitions":
            return ApiResponse(HTTPStatus.OK, {"data": self.features.definitions(), "schema_version": self.features.SCHEMA_VERSION})
        if normalized == "/api/v2/features":
            try:
                query = {key: values[0] for key, values in parse_qs(query_string, keep_blank_values=True).items()}
                return ApiResponse(HTTPStatus.OK, self.features.list(query))
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted features are unavailable.")
        feature_prefix = "/api/v2/features/"
        if normalized.startswith(feature_prefix) and "/" not in normalized[len(feature_prefix):]:
            try:
                vector_id = UUID(normalized[len(feature_prefix):])
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_vector_id", "Feature vector ID must be a valid UUID.")
            try:
                data = self.features.detail(vector_id)
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted features are unavailable.")
            if data is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Feature vector was not found.")
            return ApiResponse(HTTPStatus.OK, {"data": data})
        if normalized in ("/api/v2/memory", "/api/v2/memory/latest", "/api/v2/memory/previous"):
            try:
                query = {key: values[0] for key, values in parse_qs(query_string, keep_blank_values=True).items()}
                if normalized == "/api/v2/memory":
                    return ApiResponse(HTTPStatus.OK, self.memory.list(query))
                data = self.memory.latest(query, previous=normalized.endswith("/previous"))
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted market memory is unavailable.")
            if data is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Market-memory snapshot was not found.")
            return ApiResponse(HTTPStatus.OK, {"data": data})
        if normalized == "/api/v2/memory/compare":
            query = parse_qs(query_string, keep_blank_values=True)
            try:
                previous_id = UUID(query.get("previous", [""])[0])
                current_id = UUID(query.get("current", [""])[0])
                data = self.memory.compare(previous_id, current_id)
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_snapshot_id", "previous and current must be valid UUIDs.")
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted market memory is unavailable.")
            if data is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "One or both snapshots were not found.")
            return ApiResponse(HTTPStatus.OK, {"data": data})
        feature_prefix = "/api/v2/memory/features/"
        if normalized.startswith(feature_prefix) and "/" not in normalized[len(feature_prefix):]:
            try:
                query = {key: values[0] for key, values in parse_qs(query_string, keep_blank_values=True).items()}
                return ApiResponse(HTTPStatus.OK, self.memory.feature_history(normalized[len(feature_prefix):], query))
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted market memory is unavailable.")
        snapshot_prefix = "/api/v2/memory/snapshots/"
        if normalized.startswith(snapshot_prefix) and "/" not in normalized[len(snapshot_prefix):]:
            try:
                snapshot_id = UUID(normalized[len(snapshot_prefix):])
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_snapshot_id", "Snapshot ID must be a valid UUID.")
            try:
                data = self.memory.detail(snapshot_id)
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted market memory is unavailable.")
            if data is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Market-memory snapshot was not found.")
            return ApiResponse(HTTPStatus.OK, {"data": data})
        if normalized == "/api/v2/symbols":
            try:
                query = {key: values[0] for key, values in parse_qs(query_string, keep_blank_values=True).items()}
                limit = int(query.get("limit", "10"))
                return ApiResponse(HTTPStatus.OK, self.symbols.search(query.get("query", ""), limit))
            except ValueError:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", "limit must be an integer.")
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted symbol data is unavailable.")
        symbol_prefix = "/api/v2/symbols/"
        if normalized.startswith(symbol_prefix) and "/" not in normalized[len(symbol_prefix):]:
            try:
                query = parse_qs(query_string, keep_blank_values=True)
                data = self.symbols.intelligence(normalized[len(symbol_prefix):], query.get("expiry", [None])[0])
            except WorkspaceQueryError as exc:
                return self._error(HTTPStatus.BAD_REQUEST, "invalid_query", str(exc))
            except WorkspaceUnavailable:
                return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "database_unavailable", "Persisted symbol data is unavailable.")
            if data is None:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Symbol intelligence was not found.")
            return ApiResponse(HTTPStatus.OK, {"data": data})
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
        body = None
        if str(environ.get("REQUEST_METHOD", "GET")).upper() == "POST":
            try:
                length = int(environ.get("CONTENT_LENGTH") or 0)
                if length > 32768:
                    response = self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "request_too_large", "Request body must not exceed 32768 bytes.")
                else:
                    raw = environ["wsgi.input"].read(length) if length else b"{}"
                    body = json.loads(raw.decode("utf-8"))
                    if not isinstance(body, dict): raise ValueError
                    response = self.handle(str(environ.get("REQUEST_METHOD")), str(environ.get("PATH_INFO", "/")), str(environ.get("QUERY_STRING", "")), body)
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
                response = self._error(HTTPStatus.BAD_REQUEST, "invalid_json", "Request body must be a JSON object.")
        else:
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

    def _handle_analyst(self, path: str, body: dict[str, Any] | None) -> ApiResponse:
        payload = body or {}
        try:
            question = str(payload.get("question", ""))
            if path == "/api/v2/analyst/questions":
                identifiers = payload.get("opportunity_ids", [])
            elif path == "/api/v2/analyst/compare":
                identifiers = payload.get("opportunity_ids", [])
                if not isinstance(identifiers, list) or len(identifiers) < 2:
                    raise ValueError("compare requires at least two opportunity_ids.")
            elif path.startswith("/api/v2/analyst/opportunities/") and path.endswith("/explain"):
                value = path[len("/api/v2/analyst/opportunities/"):-len("/explain")]
                if "/" in value: return self._error(HTTPStatus.NOT_FOUND, "not_found", "Route not found.")
                identifiers = [value]
            else:
                return self._error(HTTPStatus.NOT_FOUND, "not_found", "Route not found.")
            if not isinstance(identifiers, list): raise ValueError("opportunity_ids must be an array.")
            request = AnalystRequest(question, tuple(UUID(str(value)) for value in identifiers)).normalized()
            return ApiResponse(HTTPStatus.OK, {"data": self.analyst.ask(request)})
        except LookupError as exc:
            return self._error(HTTPStatus.NOT_FOUND, "not_found", f"Trade opportunity {exc} was not found.")
        except (ValueError, TypeError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_request", str(exc))
        except WorkspaceUnavailable:
            return self._error(HTTPStatus.SERVICE_UNAVAILABLE, "evidence_unavailable", "Verified analyst evidence is unavailable.")

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
