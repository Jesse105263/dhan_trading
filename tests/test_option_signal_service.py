from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from services.option_signal_models import ApprovedRiskCandidate, OptionSignalRequest
from services.option_signal_service import OptionSignalEligibilityError, OptionSignalService


class FakeRepository:
    def __init__(self, candidates):
        self.candidates = candidates
        self.persisted = None

    def list_approved_candidates(self, risk_run_id):
        return [item for item in self.candidates if item.risk_run_id == risk_run_id]

    def persist(self, result):
        self.persisted = result
        return result


def candidate(option_type="CE", **changes):
    base = ApprovedRiskCandidate(
        assessment_id=uuid4(), risk_run_id=uuid4(), selection_id=uuid4(),
        ranking_id=uuid4(), analytics_id=uuid4(), source_run_id=uuid4(),
        underlying_symbol="RELIANCE", expiry=date(2026, 7, 28),
        option_type=option_type, security_id="100", trading_symbol="REL-CE",
        approved_lots=1, approved_quantity=500,
        premium_per_lot=Decimal("14050"), approved_exposure=Decimal("14050"),
        maximum_loss=Decimal("14050"), lot_size=500,
        contract_score=Decimal("0.90"), ranking_score=Decimal("0.80"),
        liquidity_score=Decimal("0.70"), activity_score=Decimal("0.60"),
        volatility_score=Decimal("0.50"), directional_score=Decimal("0.40"),
    )
    return replace(base, **changes)


class OptionSignalServiceTest(unittest.TestCase):
    def test_generates_explainable_signal_with_lineage(self):
        item = candidate()
        repo = FakeRepository([item])
        result = OptionSignalService(repo, clock=lambda: datetime(2026, 7, 12, 10)).generate_and_persist(
            OptionSignalRequest(item.risk_run_id, datetime(2026, 7, 12, 9))
        )
        self.assertEqual(len(result.signals), 1)
        signal = result.signals[0]
        self.assertEqual(signal.direction, "BULLISH")
        self.assertEqual(signal.action, "BUY_TO_OPEN")
        self.assertEqual(signal.entry_price, Decimal("28.100000"))
        self.assertEqual(signal.assessment_id, item.assessment_id)
        self.assertEqual(signal.confidence_score, Decimal("0.78000000"))
        self.assertIs(repo.persisted, result)

    def test_call_and_put_pair_is_straddle_context(self):
        call = candidate("CE")
        put = candidate("PE", risk_run_id=call.risk_run_id, assessment_id=uuid4(), security_id="101")
        result = OptionSignalService(FakeRepository([call, put])).generate_and_persist(
            OptionSignalRequest(call.risk_run_id, datetime(2026, 7, 12))
        )
        self.assertEqual({s.strategy_context for s in result.signals}, {"LONG_STRADDLE_LEG"})
        self.assertEqual({s.direction for s in result.signals}, {"BULLISH", "BEARISH"})

    def test_minimum_confidence_filters_candidates(self):
        item = candidate()
        with self.assertRaises(OptionSignalEligibilityError):
            OptionSignalService(FakeRepository([item])).generate_and_persist(
                OptionSignalRequest(item.risk_run_id, datetime(2026, 7, 12), Decimal("0.90"))
            )

    def test_rejects_expired_candidate(self):
        item = candidate(expiry=date(2026, 7, 11))
        with self.assertRaises(OptionSignalEligibilityError):
            OptionSignalService(FakeRepository([item])).generate_and_persist(
                OptionSignalRequest(item.risk_run_id, datetime(2026, 7, 12))
            )

    def test_request_validation_and_empty_run(self):
        with self.assertRaises(ValueError):
            OptionSignalRequest(uuid4(), datetime.now(), Decimal("1.1")).normalized()
        with self.assertRaises(OptionSignalEligibilityError):
            OptionSignalService(FakeRepository([])).generate_and_persist(
                OptionSignalRequest(uuid4(), datetime(2026, 7, 12))
            )


if __name__ == "__main__":
    unittest.main()
