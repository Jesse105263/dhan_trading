from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from services.paper_trading_models import (
    PaperCloseRequest,
    PaperCloseResult,
    PaperFill,
    PaperMarkRequest,
    PaperOpenRequest,
    PaperOpenResult,
    PaperOrder,
    PaperPosition,
)


class PaperTradingStateError(ValueError):
    pass


class PaperTradingService:
    MONEY = Decimal("0.01")
    PRICE = Decimal("0.000001")
    BPS = Decimal("10000")

    def __init__(self, repository) -> None:
        self.repository = repository

    def open_position(self, request: PaperOpenRequest) -> PaperOpenResult:
        request = request.normalized()
        signal = self.repository.get_signal(request.signal_id)
        if signal is None:
            raise PaperTradingStateError("Persisted signal was not found.")
        if self.repository.get_position_for_signal(signal.signal_id) is not None:
            raise PaperTradingStateError("A paper position already exists for this signal.")
        if signal.quantity <= 0 or signal.signal_entry_price <= 0:
            raise PaperTradingStateError("Persisted signal has invalid quantity or entry price.")
        if signal.signal_calculated_at > request.as_of:
            raise PaperTradingStateError("Paper order as-of time precedes signal generation.")
        if signal.expiry < request.as_of.date():
            raise PaperTradingStateError("Persisted signal contract is expired.")

        order_id = uuid4()
        mark = self.repository.latest_mark(signal, request.as_of)
        if mark is None:
            order = PaperOrder(
                order_id, signal.signal_id, signal.source_run_id, "BUY", signal.quantity,
                "REJECTED", request.as_of, None, None, None, None, "NO_PERSISTED_MARK",
            )
            return self.repository.persist_open(PaperOpenResult(order, None, None), {})

        position_id = uuid4()
        fill_price = self._price(mark.last_price * (Decimal("1") + request.slippage_bps / self.BPS))
        entry_cost = self._money(fill_price * signal.quantity * request.transaction_cost_bps / self.BPS)
        order = PaperOrder(
            order_id, signal.signal_id, signal.source_run_id, "BUY", signal.quantity,
            "FILLED", request.as_of, mark.captured_at, mark.run_id,
            mark.last_price, fill_price, None,
        )
        fill = PaperFill(
            uuid4(), order_id, position_id, "BUY", signal.quantity, mark.run_id,
            mark.last_price, fill_price, mark.captured_at, entry_cost,
        )
        position = PaperPosition(
            position_id, signal, order_id, None, "OPEN", mark.run_id,
            mark.captured_at, fill_price, mark.run_id, mark.captured_at,
            mark.last_price, None, None, None, Decimal("0.00"), entry_cost,
            -entry_cost, request.as_of,
        )
        payload = self._payload(position) | {"event": "simulated fill; no broker order"}
        return self.repository.persist_open(PaperOpenResult(order, position, fill), payload)

    def mark_position(self, request: PaperMarkRequest) -> PaperPosition:
        position = self._open_position(request.position_id)
        if request.as_of <= position.latest_mark_time:
            raise PaperTradingStateError("Mark as-of time must be after the latest position mark.")
        mark = self.repository.latest_mark(position.signal, request.as_of, position.latest_mark_time)
        if mark is None:
            raise PaperTradingStateError("No newer persisted market mark is available.")
        gross = self._money((mark.last_price - position.entry_price) * position.signal.quantity)
        updated = replace(
            position, latest_mark_run_id=mark.run_id, latest_mark_time=mark.captured_at,
            latest_mark_price=mark.last_price, gross_pnl=gross,
            net_pnl=self._money(gross - position.transaction_costs), updated_at=request.as_of,
        )
        return self.repository.persist_mark(updated, self._payload(updated))

    def close_position(self, request: PaperCloseRequest) -> PaperCloseResult:
        request = request.normalized()
        position = self._open_position(request.position_id)
        if request.as_of <= position.entry_time:
            raise PaperTradingStateError("Close as-of time must be after paper entry.")
        mark = self.repository.latest_mark(position.signal, request.as_of, position.entry_time)
        if mark is None:
            raise PaperTradingStateError("No persisted exit mark is available.")
        order_id = uuid4()
        exit_price = self._price(mark.last_price * (Decimal("1") - request.slippage_bps / self.BPS))
        exit_cost = self._money(exit_price * position.signal.quantity * request.transaction_cost_bps / self.BPS)
        total_cost = self._money(position.transaction_costs + exit_cost)
        gross = self._money((exit_price - position.entry_price) * position.signal.quantity)
        net = self._money(gross - total_cost)
        order = PaperOrder(
            order_id, position.signal.signal_id, position.signal.source_run_id, "SELL",
            position.signal.quantity, "FILLED", request.as_of, mark.captured_at,
            mark.run_id, mark.last_price, exit_price, None,
        )
        fill = PaperFill(
            uuid4(), order_id, position.position_id, "SELL", position.signal.quantity,
            mark.run_id, mark.last_price, exit_price, mark.captured_at, exit_cost,
        )
        closed = replace(
            position, exit_order_id=order_id, status="CLOSED",
            latest_mark_run_id=mark.run_id, latest_mark_time=mark.captured_at,
            latest_mark_price=mark.last_price, exit_run_id=mark.run_id,
            exit_time=mark.captured_at, exit_price=exit_price, gross_pnl=gross,
            transaction_costs=total_cost, net_pnl=net, updated_at=request.as_of,
        )
        result = PaperCloseResult(order, closed, fill)
        return self.repository.persist_close(result, self._payload(closed) | {"event": "simulated close; no broker order"})

    def list_positions(self, status: str | None = None, limit: int = 20):
        normalized_status = status.strip().upper() if status else None
        if normalized_status not in {None, "OPEN", "CLOSED"}:
            raise ValueError("Paper position status must be OPEN or CLOSED.")
        if not 1 <= limit <= 100:
            raise ValueError("Paper position limit must be between 1 and 100.")
        return self.repository.list_positions(normalized_status, limit)

    def _open_position(self, position_id):
        position = self.repository.get_position(position_id)
        if position is None:
            raise PaperTradingStateError("Paper position was not found.")
        if position.status != "OPEN":
            raise PaperTradingStateError("Paper position is not open.")
        return position

    @staticmethod
    def _payload(position: PaperPosition) -> dict[str, str | int]:
        return {
            "signal_id": str(position.signal.signal_id),
            "source_run_id": str(position.signal.source_run_id),
            "status": position.status,
            "quantity": position.signal.quantity,
            "latest_mark_run_id": str(position.latest_mark_run_id),
            "latest_mark_price": str(position.latest_mark_price),
            "gross_pnl": str(position.gross_pnl),
            "transaction_costs": str(position.transaction_costs),
            "net_pnl": str(position.net_pnl),
        }

    @classmethod
    def _money(cls, value) -> Decimal:
        return Decimal(value).quantize(cls.MONEY, rounding=ROUND_HALF_UP)

    @classmethod
    def _price(cls, value) -> Decimal:
        return Decimal(value).quantize(cls.PRICE, rounding=ROUND_HALF_UP)
