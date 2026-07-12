from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable
from uuid import uuid4

from services.option_analytics_history_models import (
    OptionAnalyticsChange,
    OptionAnalyticsComparisonRequest,
    OptionAnalyticsHistoryRequest,
    OptionAnalyticsPair,
)
from services.option_analytics_history_repository import OptionAnalyticsHistoryRepository
from services.option_analytics_models import OptionChainAnalytics


class OptionAnalyticsComparisonError(ValueError):
    pass


class OptionAnalyticsHistoryService:
    def __init__(
        self,
        repository: OptionAnalyticsHistoryRepository,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.repository = repository
        self.clock = clock

    def list_history(self, request: OptionAnalyticsHistoryRequest) -> list[OptionChainAnalytics]:
        normalized = request.normalized()
        return self.repository.list_history(
            normalized.underlying_symbol,
            normalized.expiry,
            normalized.limit,
        )

    def compare_and_persist(
        self,
        request: OptionAnalyticsComparisonRequest,
    ) -> OptionAnalyticsChange:
        pair = self.repository.get_consecutive_pair(request.current_analytics_id)
        change = self.compare(pair, self.clock())
        return self.repository.upsert_change(change)

    @staticmethod
    def compare(pair: OptionAnalyticsPair, calculated_at: datetime) -> OptionAnalyticsChange:
        previous, current = pair.previous, pair.current
        if previous.underlying_symbol.upper() != current.underlying_symbol.upper():
            raise OptionAnalyticsComparisonError("Snapshots have different underlyings.")
        if previous.expiry != current.expiry:
            raise OptionAnalyticsComparisonError("Snapshots have different expiries.")
        if previous.analytics_id == current.analytics_id:
            raise OptionAnalyticsComparisonError("Snapshots must be distinct.")
        if current.source_captured_at <= previous.source_captured_at:
            raise OptionAnalyticsComparisonError("Snapshots are unordered or simultaneous.")
        if calculated_at < current.source_captured_at:
            raise OptionAnalyticsComparisonError("calculated_at cannot precede current snapshot.")
        elapsed = int((current.source_captured_at - previous.source_captured_at).total_seconds())
        return OptionAnalyticsChange(
            change_id=uuid4(),
            previous_analytics_id=previous.analytics_id,
            current_analytics_id=current.analytics_id,
            previous_source_run_id=previous.source_run_id,
            current_source_run_id=current.source_run_id,
            underlying_symbol=current.underlying_symbol,
            expiry=current.expiry,
            previous_captured_at=previous.source_captured_at,
            current_captured_at=current.source_captured_at,
            calculated_at=calculated_at,
            elapsed_seconds=elapsed,
            spot_price_change=current.spot_price - previous.spot_price,
            atm_straddle_change=current.atm_straddle_cost - previous.atm_straddle_cost,
            total_call_oi_change=current.total_call_oi - previous.total_call_oi,
            total_put_oi_change=current.total_put_oi - previous.total_put_oi,
            total_pcr_change=OptionAnalyticsHistoryService._delta(current.total_pcr, previous.total_pcr),
            nearby_call_oi_change=current.nearby_call_oi - previous.nearby_call_oi,
            nearby_put_oi_change=current.nearby_put_oi - previous.nearby_put_oi,
            nearby_pcr_change=OptionAnalyticsHistoryService._delta(current.nearby_pcr, previous.nearby_pcr),
            atm_mean_iv_change=OptionAnalyticsHistoryService._delta(current.atm_mean_iv, previous.atm_mean_iv),
            nearby_mean_iv_change=OptionAnalyticsHistoryService._delta(current.nearby_mean_iv, previous.nearby_mean_iv),
            call_oi_wall_strike_change=OptionAnalyticsHistoryService._delta(current.call_oi_wall_strike, previous.call_oi_wall_strike),
            put_oi_wall_strike_change=OptionAnalyticsHistoryService._delta(current.put_oi_wall_strike, previous.put_oi_wall_strike),
            call_oi_wall_value_change=OptionAnalyticsHistoryService._int_delta(current.call_oi_wall_value, previous.call_oi_wall_value),
            put_oi_wall_value_change=OptionAnalyticsHistoryService._int_delta(current.put_oi_wall_value, previous.put_oi_wall_value),
            call_wall_changed=current.call_oi_wall_strike != previous.call_oi_wall_strike,
            put_wall_changed=current.put_oi_wall_strike != previous.put_oi_wall_strike,
            liquidity_coverage_change=current.liquidity_coverage - previous.liquidity_coverage,
            price_coverage_change=current.price_coverage - previous.price_coverage,
        )

    @staticmethod
    def _delta(current: Decimal | None, previous: Decimal | None) -> Decimal | None:
        if current is None or previous is None:
            return None
        return current - previous

    @staticmethod
    def _int_delta(current: int | None, previous: int | None) -> int | None:
        if current is None or previous is None:
            return None
        return current - previous
