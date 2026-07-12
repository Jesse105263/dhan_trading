from __future__ import annotations

import time
from datetime import timedelta
from typing import Any, Callable

from services.dhan_option_chain_client import DhanOptionChainClient
from services.error_sanitizer import classify_retryable, sanitize_error_message
from services.expiry_service import ExpiryService
from services.failure_repository import FailureRepository, PipelineFailure
from services.option_analytics_models import OptionAnalyticsRequest
from services.option_analytics_repository import OptionAnalyticsRepository
from services.option_analytics_service import OptionAnalyticsService
from services.option_chain_collector import OptionChainCollector
from services.option_chain_models import OptionChainCollectionRequest
from services.option_chain_repository import OptionChainRepository
from services.pipeline import Pipeline
from services.stage import Stage


class OptionCollectionStage(Stage):
    def __init__(self, symbols: tuple[str, ...], collector: OptionChainCollector,
                 failure_repository: FailureRepository, max_attempts: int = 3,
                 retry_backoff_seconds: float = 1.0,
                 throttle_seconds: float = 0.0,
                 minimum_days_to_expiry: int = 0,
                 maximum_days_to_expiry: int | None = None,
                 sleeper: Callable[[float], None] = time.sleep) -> None:
        super().__init__("Option Chain Collection")
        if not symbols:
            raise ValueError("At least one option underlying is required.")
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive.")
        self.symbols = tuple(dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip()))
        self.collector = collector
        self.failure_repository = failure_repository
        self.max_attempts = max_attempts
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self.throttle_seconds = max(0.0, throttle_seconds)
        self.minimum_days_to_expiry = minimum_days_to_expiry
        self.maximum_days_to_expiry = maximum_days_to_expiry
        self.sleeper = sleeper

    def run(self, context: dict[str, Any]) -> None:
        results = {}
        failures = {}
        quotes_written = 0
        for index, symbol in enumerate(self.symbols):
            context["current_symbol"] = symbol
            last_error: Exception | None = None
            for attempt in range(1, self.max_attempts + 1):
                try:
                    result = self.collector.collect(OptionChainCollectionRequest(
                        underlying_symbol=symbol,
                        minimum_days_to_expiry=self.minimum_days_to_expiry,
                        maximum_days_to_expiry=self.maximum_days_to_expiry,
                    ))
                    results[symbol] = result
                    quotes_written += result.quotes_inserted
                    last_error = None
                    break
                except Exception as error:
                    last_error = error
                    if attempt >= self.max_attempts or not classify_retryable(error):
                        break
                    self.sleeper(self.retry_backoff_seconds * attempt)
            if last_error is not None:
                message = sanitize_error_message(str(last_error))
                failures[symbol] = message
                self.failure_repository.insert(PipelineFailure(
                    run_id=str(context["run_id"]), stage_name=self.name,
                    symbol=symbol, error_type=type(last_error).__name__,
                    error_message=message, retryable=classify_retryable(last_error),
                    occurred_at=context["current_stage_started_at"],
                ))
            if index < len(self.symbols) - 1 and self.throttle_seconds:
                self.sleeper(self.throttle_seconds)
        context["option_collection_results"] = results
        context["option_collection_failures"] = failures
        context["current_symbol"] = None
        context["stage_metric_data"] = {
            "records_requested": len(self.symbols),
            "records_received": len(results),
            "records_written": quotes_written,
        }


class OptionAnalyticsStage(Stage):
    def __init__(self, service: OptionAnalyticsService,
                 failure_repository: FailureRepository,
                 nearby_strikes_each_side: int = 5,
                 maximum_source_age: timedelta = timedelta(hours=24)) -> None:
        super().__init__("Option Analytics")
        self.service = service
        self.failure_repository = failure_repository
        self.nearby_strikes_each_side = nearby_strikes_each_side
        self.maximum_source_age = maximum_source_age

    def run(self, context: dict[str, Any]) -> None:
        collections = context.get("option_collection_results", {})
        analytics = {}
        failures = {}
        for symbol, result in collections.items():
            context["current_symbol"] = symbol
            try:
                analytics[symbol] = self.service.calculate_and_persist(
                    OptionAnalyticsRequest(
                        source_run_id=result.run_id,
                        nearby_strikes_each_side=self.nearby_strikes_each_side,
                        maximum_source_age=self.maximum_source_age,
                    )
                )
            except Exception as error:
                message = sanitize_error_message(str(error))
                failures[symbol] = message
                self.failure_repository.insert(PipelineFailure(
                    run_id=str(context["run_id"]), stage_name=self.name,
                    symbol=symbol, error_type=type(error).__name__,
                    error_message=message, retryable=classify_retryable(error),
                    occurred_at=context["current_stage_started_at"],
                ))
        context["option_analytics_results"] = analytics
        context["option_analytics_failures"] = failures
        context["current_symbol"] = None
        context["stage_metric_data"] = {
            "records_requested": len(collections),
            "records_received": len(analytics),
            "records_written": len(analytics),
        }


def build_option_data_pipeline(symbols: tuple[str, ...], max_attempts: int = 3,
                               retry_backoff_seconds: float = 1.0,
                               throttle_seconds: float = 0.0,
                               minimum_days_to_expiry: int = 0,
                               maximum_days_to_expiry: int | None = None,
                               nearby_strikes_each_side: int = 5,
                               maximum_source_age: timedelta = timedelta(hours=24),
                               request_timeout_seconds: int = 20) -> Pipeline:
    failures = FailureRepository()
    collector = OptionChainCollector(
        repository=OptionChainRepository(),
        expiry_service=ExpiryService(),
        client=DhanOptionChainClient(timeout_seconds=request_timeout_seconds),
    )
    analytics = OptionAnalyticsService(OptionAnalyticsRepository())
    return Pipeline(stages=[
        OptionCollectionStage(symbols, collector, failures, max_attempts,
                              retry_backoff_seconds, throttle_seconds,
                              minimum_days_to_expiry, maximum_days_to_expiry),
        OptionAnalyticsStage(analytics, failures, nearby_strikes_each_side,
                             maximum_source_age),
    ])
