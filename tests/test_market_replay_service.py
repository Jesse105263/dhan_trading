from __future__ import annotations
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.market_replay_models import MarketReplayRequest, ReplayLineage
from services.market_replay_service import MarketReplayEligibilityError, MarketReplayService


class FakeRepository:
    def __init__(self, rows): self.rows, self.persisted = rows, None
    def load_lineage(self, signal_run_id): return [r for r in self.rows if r.signal_run_id == signal_run_id]
    def persist(self, result): self.persisted = result; return result


def lineage(**changes):
    t = datetime(2026, 7, 12, 9, 0)
    base = ReplayLineage(
        signal_id=uuid4(), signal_run_id=uuid4(), risk_run_id=uuid4(), assessment_id=uuid4(),
        selection_id=uuid4(), selection_run_id=uuid4(), ranking_id=uuid4(), ranking_run_id=uuid4(),
        analytics_id=uuid4(), change_id=uuid4(), source_run_id=uuid4(), underlying_symbol="RELIANCE",
        expiry=date(2026, 7, 28), option_type="CE", source_status="COMPLETED",
        source_captured_at=t, analytics_calculated_at=t+timedelta(seconds=1),
        ranking_calculated_at=t+timedelta(seconds=2), selection_calculated_at=t+timedelta(seconds=3),
        risk_calculated_at=t+timedelta(seconds=4), signal_calculated_at=t+timedelta(seconds=5),
        security_id="100", trading_symbol="REL-CE", action="BUY_TO_OPEN", direction="BULLISH",
        strategy_context="LONG_CALL", approved_lots=1, approved_quantity=500,
        entry_price=Decimal("28.1"), maximum_loss=Decimal("14050"), confidence_score=Decimal("0.65"),
    )
    return replace(base, **changes)


class MarketReplayServiceTest(unittest.TestCase):
    def test_replays_ordered_lineage_deterministically(self):
        row = lineage()
        repo = FakeRepository([row])
        result = MarketReplayService(repo, clock=lambda: datetime(2026,7,12,10)).replay_and_persist(
            MarketReplayRequest(row.signal_run_id, datetime(2026,7,12,11))
        )
        self.assertEqual(result.signal_count, 1)
        self.assertEqual([e.sequence_number for e in result.events], list(range(1,7)))
        self.assertEqual([e.event_type for e in result.events], [
            "OPTION_CHAIN_CAPTURED","ANALYTICS_CALCULATED","RANKED",
            "CONTRACT_SELECTED","RISK_APPROVED","SIGNAL_GENERATED"])
        self.assertIs(repo.persisted, result)

    def test_rejects_incomplete_source(self):
        row = lineage(source_status="FAILED")
        with self.assertRaises(MarketReplayEligibilityError):
            MarketReplayService(FakeRepository([row])).replay_and_persist(
                MarketReplayRequest(row.signal_run_id, datetime(2026,7,12,11)))

    def test_rejects_out_of_order_lineage(self):
        row = lineage(ranking_calculated_at=datetime(2026,7,12,8))
        with self.assertRaises(MarketReplayEligibilityError):
            MarketReplayService(FakeRepository([row])).replay_and_persist(
                MarketReplayRequest(row.signal_run_id, datetime(2026,7,12,11)))

    def test_rejects_future_signal_and_empty_run(self):
        row = lineage()
        with self.assertRaises(MarketReplayEligibilityError):
            MarketReplayService(FakeRepository([row])).replay_and_persist(
                MarketReplayRequest(row.signal_run_id, datetime(2026,7,12,8)))
        with self.assertRaises(MarketReplayEligibilityError):
            MarketReplayService(FakeRepository([])).replay_and_persist(
                MarketReplayRequest(uuid4(), datetime(2026,7,12,11)))

if __name__ == "__main__": unittest.main()
