from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable
from uuid import uuid4

from services.market_replay_models import MarketReplayEvent, MarketReplayRequest, MarketReplayResult, ReplayLineage


class MarketReplayEligibilityError(ValueError):
    pass


class MarketReplayService:
    METHODOLOGY_VERSION = "persisted-lineage-replay-v1"

    def __init__(self, repository, clock: Callable[[], datetime] = datetime.now) -> None:
        self.repository = repository
        self.clock = clock

    def replay_and_persist(self, request: MarketReplayRequest) -> MarketReplayResult:
        rows = self.repository.load_lineage(request.signal_run_id)
        if not rows:
            raise MarketReplayEligibilityError("Signal run has no persisted signals.")
        replay_run_id = uuid4()
        events: list[MarketReplayEvent] = []
        sequence = 1
        for row in rows:
            self._validate(row, request)
            definitions = (
                ("OPTION_CHAIN_CAPTURED", row.source_captured_at, None, row.source_run_id,
                 {"status": row.source_status, "source_run_id": str(row.source_run_id)}),
                ("ANALYTICS_CALCULATED", row.analytics_calculated_at, None, row.analytics_id,
                 {"analytics_id": str(row.analytics_id), "change_id": str(row.change_id)}),
                ("RANKED", row.ranking_calculated_at, None, row.ranking_id,
                 {"ranking_id": str(row.ranking_id), "ranking_run_id": str(row.ranking_run_id)}),
                ("CONTRACT_SELECTED", row.selection_calculated_at, row.option_type, row.selection_id,
                 {"selection_id": str(row.selection_id), "selection_run_id": str(row.selection_run_id),
                  "security_id": row.security_id, "trading_symbol": row.trading_symbol}),
                ("RISK_APPROVED", row.risk_calculated_at, row.option_type, row.assessment_id,
                 {"assessment_id": str(row.assessment_id), "risk_run_id": str(row.risk_run_id),
                  "approved_lots": row.approved_lots, "approved_quantity": row.approved_quantity,
                  "maximum_loss": self._json_number(row.maximum_loss)}),
                ("SIGNAL_GENERATED", row.signal_calculated_at, row.option_type, row.signal_id,
                 {"signal_id": str(row.signal_id), "signal_run_id": str(row.signal_run_id),
                  "action": row.action, "direction": row.direction,
                  "strategy_context": row.strategy_context,
                  "entry_price": self._json_number(row.entry_price),
                  "confidence_score": self._json_number(row.confidence_score)}),
            )
            for event_type, event_time, option_type, entity_id, payload in definitions:
                events.append(MarketReplayEvent(
                    replay_event_id=uuid4(), replay_run_id=replay_run_id,
                    sequence_number=sequence, event_type=event_type,
                    event_time=event_time, underlying_symbol=row.underlying_symbol,
                    expiry=row.expiry, option_type=option_type, entity_id=entity_id,
                    payload=payload,
                ))
                sequence += 1
        result = MarketReplayResult(
            replay_run_id=replay_run_id, signal_run_id=request.signal_run_id,
            requested_as_of=request.as_of, replayed_at=self.clock(),
            methodology_version=self.METHODOLOGY_VERSION,
            signal_count=len(rows), events=tuple(events),
        )
        return self.repository.persist(result)

    @staticmethod
    def _validate(row: ReplayLineage, request: MarketReplayRequest) -> None:
        if row.signal_run_id != request.signal_run_id:
            raise MarketReplayEligibilityError("Signal lineage belongs to another signal run.")
        if row.source_status != "COMPLETED":
            raise MarketReplayEligibilityError("Source option-chain run is not completed.")
        if row.expiry < row.source_captured_at.date():
            raise MarketReplayEligibilityError("Source lineage contains an already-expired contract.")
        times = (
            row.source_captured_at, row.analytics_calculated_at,
            row.ranking_calculated_at, row.selection_calculated_at,
            row.risk_calculated_at, row.signal_calculated_at,
        )
        if any(later < earlier for earlier, later in zip(times, times[1:])):
            raise MarketReplayEligibilityError("Lineage timestamps are out of order.")
        if row.signal_calculated_at > request.as_of:
            raise MarketReplayEligibilityError("Signal run is newer than replay as-of time.")
        if row.approved_lots <= 0 or row.approved_quantity <= 0:
            raise MarketReplayEligibilityError("Replay lineage contains an unapproved position.")

    @staticmethod
    def _json_number(value) -> str:
        return format(Decimal(value), "f")
