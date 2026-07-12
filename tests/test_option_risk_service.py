from __future__ import annotations

import unittest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from services.option_risk_models import OptionRiskRequest, SelectedOptionContract
from services.option_risk_service import OptionRiskEligibilityError, OptionRiskService


class FakeRepository:
    def __init__(self, selections):
        self.selections = selections
        self.persisted = None

    def list_selected_contracts(self, selection_run_id):
        return self.selections

    def persist(self, result):
        self.persisted = result
        return result


def contract(symbol="RELIANCE", side="CE", premium="10000", score="0.9", lot_size=250):
    selection_run_id = uuid4()
    return SelectedOptionContract(
        selection_id=uuid4(),
        selection_run_id=selection_run_id,
        ranking_id=uuid4(),
        analytics_id=uuid4(),
        source_run_id=uuid4(),
        underlying_symbol=symbol,
        expiry=date(2026, 7, 28),
        option_type=side,
        security_id=uuid4().hex[:10],
        trading_symbol=f"{symbol}-{side}",
        premium_per_lot=Decimal(premium),
        lot_size=lot_size,
        contract_score=Decimal(score),
    )


class OptionRiskServiceTest(unittest.TestCase):
    def test_sizes_deterministically_under_all_limits(self):
        first = contract(premium="10000")
        second = contract(side="PE", premium="12000", score="0.8")
        second = SelectedOptionContract(**{**second.__dict__, "selection_run_id": first.selection_run_id})
        repo = FakeRepository([first, second])
        result = OptionRiskService(repo, clock=lambda: datetime(2026, 7, 12, 10)).assess_and_persist(
            OptionRiskRequest(
                selection_run_id=first.selection_run_id,
                as_of=datetime(2026, 7, 12, 9),
                account_equity=Decimal("1000000"),
                available_capital=Decimal("50000"),
                maximum_total_exposure_pct=Decimal("0.10"),
                maximum_underlying_exposure_pct=Decimal("0.05"),
                maximum_single_trade_loss_pct=Decimal("0.02"),
            )
        )
        self.assertEqual([item.approved_lots for item in result.assessments], [2, 1])
        self.assertEqual(result.approved_exposure, Decimal("32000.00"))
        self.assertEqual(result.approved[0].maximum_loss, result.approved[0].approved_exposure)

    def test_rejects_when_single_lot_exceeds_trade_loss_limit(self):
        item = contract(premium="25000")
        result = OptionRiskService(FakeRepository([item])).assess_and_persist(
            OptionRiskRequest(
                selection_run_id=item.selection_run_id,
                as_of=datetime.now(),
                account_equity=Decimal("1000000"),
                available_capital=Decimal("100000"),
                maximum_single_trade_loss_pct=Decimal("0.02"),
            )
        )
        self.assertFalse(result.assessments[0].approved)
        self.assertEqual(result.assessments[0].rejection_code, "SINGLE_TRADE_LOSS_LIMIT")

    def test_existing_underlying_exposure_blocks_concentration(self):
        item = contract(premium="10000")
        result = OptionRiskService(FakeRepository([item])).assess_and_persist(
            OptionRiskRequest(
                selection_run_id=item.selection_run_id,
                as_of=datetime.now(),
                account_equity=Decimal("1000000"),
                available_capital=Decimal("100000"),
                existing_underlying_exposure={"reliance": Decimal("95000")},
                maximum_underlying_exposure_pct=Decimal("0.10"),
            )
        )
        self.assertEqual(result.assessments[0].rejection_code, "UNDERLYING_CONCENTRATION_LIMIT")

    def test_request_validation(self):
        with self.assertRaises(ValueError):
            OptionRiskRequest(uuid4(), datetime.now(), Decimal("0"), Decimal("1")).normalized()
        with self.assertRaises(ValueError):
            OptionRiskRequest(uuid4(), datetime.now(), Decimal("1"), Decimal("1"), maximum_total_exposure_pct=Decimal("2")).normalized()

    def test_rejects_empty_selection_run(self):
        with self.assertRaises(OptionRiskEligibilityError):
            OptionRiskService(FakeRepository([])).assess_and_persist(
                OptionRiskRequest(uuid4(), datetime.now(), Decimal("100000"), Decimal("10000"))
            )


if __name__ == "__main__":
    unittest.main()
