from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.paper_trading_models import (
    PaperCloseRequest,
    PaperMarkRequest,
    PaperMarketMark,
    PaperOpenRequest,
    PaperPosition,
    PaperSignal,
)
from services.paper_trading_service import PaperTradingService, PaperTradingStateError


class FakeRepository:
    def __init__(self, signal, marks=None) -> None:
        self.signal = signal
        self.marks = list(marks or [])
        self.position = None
        self.open_results = []
        self.marked = []
        self.closed = []

    def get_signal(self, signal_id):
        return self.signal if self.signal and self.signal.signal_id == signal_id else None

    def get_position_for_signal(self, signal_id):
        return self.position if self.position and self.position.signal.signal_id == signal_id else None

    def get_position(self, position_id):
        return self.position if self.position and self.position.position_id == position_id else None

    def latest_mark(self, signal, as_of, after=None):
        eligible = [mark for mark in self.marks if mark.captured_at <= as_of and (after is None or mark.captured_at > after)]
        return max(eligible, key=lambda mark: mark.captured_at) if eligible else None

    def persist_open(self, result, event_payload):
        self.open_results.append((result, event_payload))
        self.position = result.position
        return result

    def persist_mark(self, position, event_payload):
        self.position = position
        self.marked.append((position, event_payload))
        return position

    def persist_close(self, result, event_payload):
        self.position = result.position
        self.closed.append((result, event_payload))
        return result

    def list_positions(self, status, limit):
        values = [self.position] if self.position and (status is None or self.position.status == status) else []
        return values[:limit]


class PaperTradingServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 12, 10)
        self.signal = PaperSignal(
            uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4(),
            "RELIANCE", date(2026, 7, 30), "CE", "SEC-1", "REL-CE", 10,
            Decimal("100"), self.now - timedelta(minutes=10), self.now - timedelta(minutes=5),
        )

    def mark(self, minutes, price):
        return PaperMarketMark(uuid4(), self.now + timedelta(minutes=minutes), Decimal(price))

    def open(self, repository, as_of=None, **kwargs):
        return PaperTradingService(repository).open_position(
            PaperOpenRequest(self.signal.signal_id, as_of or self.now + timedelta(minutes=1), **kwargs)
        )

    def test_opens_filled_position_with_full_lineage_and_costs(self) -> None:
        repository = FakeRepository(self.signal, [self.mark(1, "100")])
        result = self.open(repository, slippage_bps=Decimal("10"), transaction_cost_bps=Decimal("5"))
        self.assertEqual(result.order.status, "FILLED")
        self.assertEqual(result.order.side, "BUY")
        self.assertEqual(result.position.status, "OPEN")
        self.assertEqual(result.position.entry_price, Decimal("100.100000"))
        self.assertEqual(result.position.transaction_costs, Decimal("0.50"))
        self.assertEqual(result.position.net_pnl, Decimal("-0.50"))
        self.assertEqual(result.position.signal.risk_run_id, self.signal.risk_run_id)
        self.assertIn("no broker order", repository.open_results[0][1]["event"])

    def test_missing_mark_persists_rejection_without_position(self) -> None:
        repository = FakeRepository(self.signal)
        result = self.open(repository)
        self.assertEqual(result.order.status, "REJECTED")
        self.assertEqual(result.order.rejection_code, "NO_PERSISTED_MARK")
        self.assertIsNone(result.position)
        self.assertIsNone(result.fill)

    def test_marks_open_position_and_calculates_unrealized_pnl(self) -> None:
        first = self.mark(1, "100")
        second = self.mark(2, "110")
        repository = FakeRepository(self.signal, [first, second])
        result = self.open(repository, as_of=first.captured_at, slippage_bps=Decimal("0"), transaction_cost_bps=Decimal("0"))
        position = PaperTradingService(repository).mark_position(PaperMarkRequest(result.position.position_id, second.captured_at))
        self.assertEqual(position.latest_mark_run_id, second.run_id)
        self.assertEqual(position.gross_pnl, Decimal("100.00"))
        self.assertEqual(position.net_pnl, Decimal("100.00"))
        self.assertEqual(len(repository.marked), 1)

    def test_closes_position_with_exit_fill_realized_pnl_and_costs(self) -> None:
        first = self.mark(1, "100")
        second = self.mark(2, "120")
        repository = FakeRepository(self.signal, [first, second])
        opened = self.open(repository, as_of=first.captured_at, slippage_bps=Decimal("0"), transaction_cost_bps=Decimal("5"))
        result = PaperTradingService(repository).close_position(
            PaperCloseRequest(opened.position.position_id, second.captured_at, Decimal("0"), Decimal("5"))
        )
        self.assertEqual(result.order.side, "SELL")
        self.assertEqual(result.position.status, "CLOSED")
        self.assertEqual(result.position.exit_price, Decimal("120.000000"))
        self.assertEqual(result.position.gross_pnl, Decimal("200.00"))
        self.assertEqual(result.position.transaction_costs, Decimal("1.10"))
        self.assertEqual(result.position.net_pnl, Decimal("198.90"))
        self.assertIn("no broker order", repository.closed[0][1]["event"])

    def test_invalid_transitions_and_missing_new_prices_do_not_persist(self) -> None:
        first = self.mark(1, "100")
        repository = FakeRepository(self.signal, [first])
        opened = self.open(repository, as_of=first.captured_at)
        service = PaperTradingService(repository)
        with self.assertRaisesRegex(PaperTradingStateError, "No newer"):
            service.mark_position(PaperMarkRequest(opened.position.position_id, first.captured_at + timedelta(minutes=1)))
        with self.assertRaisesRegex(PaperTradingStateError, "No persisted exit"):
            service.close_position(PaperCloseRequest(opened.position.position_id, first.captured_at + timedelta(minutes=1)))
        repository.position = replace(opened.position, status="CLOSED")
        with self.assertRaisesRegex(PaperTradingStateError, "not open"):
            service.close_position(PaperCloseRequest(opened.position.position_id, first.captured_at + timedelta(minutes=2)))
        self.assertEqual(repository.marked, [])
        self.assertEqual(repository.closed, [])

    def test_rejects_duplicate_expired_future_and_invalid_requests(self) -> None:
        first = self.mark(1, "100")
        repository = FakeRepository(self.signal, [first])
        opened = self.open(repository, as_of=first.captured_at)
        with self.assertRaisesRegex(PaperTradingStateError, "already exists"):
            self.open(repository, as_of=first.captured_at)
        repository.position = None
        with self.assertRaisesRegex(PaperTradingStateError, "precedes"):
            self.open(repository, as_of=self.signal.signal_calculated_at - timedelta(seconds=1))
        repository.signal = replace(self.signal, expiry=date(2026, 7, 11))
        with self.assertRaisesRegex(PaperTradingStateError, "expired"):
            self.open(repository, as_of=self.now)
        with self.assertRaises(ValueError):
            PaperOpenRequest(self.signal.signal_id, self.now, Decimal("-1")).normalized()
        with self.assertRaises(ValueError):
            PaperCloseRequest(opened.position.position_id, self.now, transaction_cost_bps=Decimal("-1")).normalized()

    def test_lists_positions_with_status_and_limit_validation(self) -> None:
        repository = FakeRepository(self.signal, [self.mark(1, "100")])
        opened = self.open(repository)
        service = PaperTradingService(repository)
        self.assertEqual(service.list_positions("open", 1), [opened.position])
        self.assertEqual(service.list_positions("CLOSED", 1), [])
        with self.assertRaises(ValueError):
            service.list_positions("INVALID", 1)
        with self.assertRaises(ValueError):
            service.list_positions(None, 101)


if __name__ == "__main__":
    unittest.main()
