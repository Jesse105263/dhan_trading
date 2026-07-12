from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class MarketReplayRequest:
    signal_run_id: UUID
    as_of: datetime


@dataclass(frozen=True)
class ReplayLineage:
    signal_id: UUID
    signal_run_id: UUID
    risk_run_id: UUID
    assessment_id: UUID
    selection_id: UUID
    selection_run_id: UUID
    ranking_id: UUID
    ranking_run_id: UUID
    analytics_id: UUID
    change_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    source_status: str
    source_captured_at: datetime
    analytics_calculated_at: datetime
    ranking_calculated_at: datetime
    selection_calculated_at: datetime
    risk_calculated_at: datetime
    signal_calculated_at: datetime
    security_id: str
    trading_symbol: str
    action: str
    direction: str
    strategy_context: str
    approved_lots: int
    approved_quantity: int
    entry_price: object
    maximum_loss: object
    confidence_score: object


@dataclass(frozen=True)
class MarketReplayEvent:
    replay_event_id: UUID
    replay_run_id: UUID
    sequence_number: int
    event_type: str
    event_time: datetime
    underlying_symbol: str
    expiry: date
    option_type: str | None
    entity_id: UUID
    payload: dict[str, Any]


@dataclass(frozen=True)
class MarketReplayResult:
    replay_run_id: UUID
    signal_run_id: UUID
    requested_as_of: datetime
    replayed_at: datetime
    methodology_version: str
    signal_count: int
    events: tuple[MarketReplayEvent, ...]
