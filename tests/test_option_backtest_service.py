from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.option_backtest_models import BacktestMarketMark, BacktestSignal, OptionBacktestRequest
from services.option_backtest_service import OptionBacktestEligibilityError, OptionBacktestService


class FakeRepository:
    def __init__(self, signals, marks):
        self.signals = signals
        self.marks = marks
        self.saved = None

    def list_signals(self, signal_run_id):
        return self.signals

    def list_future_marks(self, signal, as_of):
        return self.marks.get(signal.signal_id, [])

    def persist(self, result):
        self.saved = result
        return result


class OptionBacktestServiceTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 12, 12, 0, 0)
        self.signal_run_id = uuid4()

    def signal(self, option_type="CE", entry=Decimal("100"), quantity=10):
        return BacktestSignal(
            uuid4(), self.signal_run_id, uuid4(), "TEST", date(2026, 7, 30),
            option_type, f"SEC-{option_type}", f"TEST-{option_type}", quantity,
            entry, self.now - timedelta(minutes=10), self.now - timedelta(minutes=5),
        )

    def request(self, **kwargs):
        values = dict(signal_run_id=self.signal_run_id, as_of=self.now)
        values.update(kwargs)
        return OptionBacktestRequest(**values)

    def test_target_exit_and_costs(self):
        signal = self.signal()
        marks = [BacktestMarketMark(uuid4(), self.now - timedelta(minutes=1), Decimal("130"))]
        result = OptionBacktestService(FakeRepository([signal], {signal.signal_id: marks})).run_and_persist(self.request())
        trade = result.trades[0]
        self.assertEqual(trade.exit_reason, "TARGET")
        self.assertGreater(trade.net_pnl, 0)
        self.assertEqual(result.completed_trade_count, 1)
        self.assertEqual(result.win_rate, Decimal("1.00000000"))

    def test_stop_loss_exit(self):
        signal = self.signal()
        marks = [BacktestMarketMark(uuid4(), self.now - timedelta(minutes=1), Decimal("70"))]
        result = OptionBacktestService(FakeRepository([signal], {signal.signal_id: marks})).run_and_persist(self.request())
        self.assertEqual(result.trades[0].exit_reason, "STOP_LOSS")
        self.assertLess(result.net_pnl, 0)

    def test_last_available_exit(self):
        signal = self.signal()
        marks = [BacktestMarketMark(uuid4(), self.now - timedelta(minutes=1), Decimal("105"))]
        result = OptionBacktestService(FakeRepository([signal], {signal.signal_id: marks})).run_and_persist(self.request())
        self.assertEqual(result.trades[0].exit_reason, "LAST_AVAILABLE")

    def test_missing_future_mark_is_skipped(self):
        signal = self.signal()
        result = OptionBacktestService(FakeRepository([signal], {})).run_and_persist(self.request())
        self.assertEqual(result.skipped_trade_count, 1)
        self.assertEqual(result.trades[0].exit_reason, "NO_FUTURE_MARK")
        self.assertIsNone(result.win_rate)

    def test_maximum_drawdown_uses_ordered_net_pnl(self):
        first = self.signal("CE")
        second = self.signal("PE")
        marks = {
            first.signal_id: [BacktestMarketMark(uuid4(), self.now - timedelta(minutes=2), Decimal("130"))],
            second.signal_id: [BacktestMarketMark(uuid4(), self.now - timedelta(minutes=1), Decimal("70"))],
        }
        result = OptionBacktestService(FakeRepository([first, second], marks)).run_and_persist(self.request())
        self.assertGreater(result.maximum_drawdown, 0)

    def test_request_and_signal_validation(self):
        with self.assertRaises(ValueError):
            self.request(target_return=Decimal("0")).normalized()
        bad = self.signal(quantity=0)
        with self.assertRaises(OptionBacktestEligibilityError):
            OptionBacktestService(FakeRepository([bad], {})).run_and_persist(self.request())
        with self.assertRaises(OptionBacktestEligibilityError):
            OptionBacktestService(FakeRepository([], {})).run_and_persist(self.request())


if __name__ == "__main__":
    unittest.main()
