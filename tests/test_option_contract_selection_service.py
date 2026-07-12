import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.option_contract_selection_models import (
    ContractCandidate,
    OptionContractSelectionRequest,
    RankedUnderlying,
)
from services.option_contract_selection_service import (
    OptionContractSelectionEligibilityError,
    OptionContractSelectionService,
)


class FakeRepo:
    def __init__(self, ranked, candidates):
        self.ranked = ranked
        self.candidates = candidates
        self.saved = None

    def list_ranked_underlyings(self, ranking_run_id, limit):
        return self.ranked[:limit]

    def list_contract_candidates(self, ranked):
        return self.candidates

    def persist(self, result):
        self.saved = result
        return result


class TestSelection(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 12, 14, 0)
        self.run = uuid4()
        self.analytics = uuid4()
        self.source = uuid4()
        self.ranking = uuid4()
        self.ranked = [
            RankedUnderlying(
                self.ranking,
                self.run,
                self.analytics,
                self.source,
                "AAA",
                date(2026, 7, 28),
                self.now - timedelta(minutes=5),
                1,
                Decimal("0.8"),
                Decimal("100"),
            )
        ]

    def candidate(
        self,
        side,
        strike,
        oi=100,
        volume=10,
        bid="4.9",
        ask="5.1",
        price="5",
        sid="1",
        lot_size=50,
        spot="100",
    ):
        return ContractCandidate(
            self.ranking,
            self.analytics,
            self.source,
            "AAA",
            date(2026, 7, 28),
            side,
            sid,
            f"AAA-{side}-{strike}",
            Decimal(strike),
            Decimal(spot),
            Decimal(price) if price is not None else None,
            Decimal(bid) if bid is not None else None,
            Decimal(ask) if ask is not None else None,
            oi,
            volume,
            lot_size,
        )

    def test_selects_one_contract_per_side_deterministically(self):
        repo = FakeRepo(
            self.ranked,
            [
                self.candidate("CE", "100", sid="2"),
                self.candidate("CE", "101", oi=1000),
                self.candidate("PE", "100", sid="3"),
            ],
        )
        result = OptionContractSelectionService(
            repo,
            clock=lambda: self.now,
        ).select_and_persist(
            OptionContractSelectionRequest(self.run, self.now)
        )

        self.assertEqual(len(result.selections), 2)
        self.assertEqual(
            {selection.option_type for selection in result.selections},
            {"CE", "PE"},
        )
        self.assertEqual(
            {selection.strike for selection in result.selections},
            {Decimal("100")},
        )
        self.assertIs(repo.saved, result)

    def test_filters_wide_spread_and_low_oi(self):
        repo = FakeRepo(
            self.ranked,
            [
                self.candidate("CE", "100", oi=0),
                self.candidate("PE", "100", bid="1", ask="9"),
            ],
        )

        with self.assertRaises(OptionContractSelectionEligibilityError):
            OptionContractSelectionService(
                repo,
                clock=lambda: self.now,
            ).select_and_persist(
                OptionContractSelectionRequest(self.run, self.now)
            )

    def test_rejects_missing_last_price_without_crashing(self):
        repo = FakeRepo(
            self.ranked,
            [
                self.candidate("CE", "100", price=None),
                self.candidate("PE", "100", price=None),
            ],
        )

        with self.assertRaises(OptionContractSelectionEligibilityError):
            OptionContractSelectionService(
                repo,
                clock=lambda: self.now,
            ).select_and_persist(
                OptionContractSelectionRequest(self.run, self.now)
            )

    def test_skips_missing_price_and_selects_valid_candidate(self):
        repo = FakeRepo(
            self.ranked,
            [
                self.candidate("CE", "100", price=None, sid="missing"),
                self.candidate("CE", "101", price="5", sid="valid-ce"),
                self.candidate("PE", "100", price="5", sid="valid-pe"),
            ],
        )

        result = OptionContractSelectionService(
            repo,
            clock=lambda: self.now,
        ).select_and_persist(
            OptionContractSelectionRequest(self.run, self.now)
        )

        self.assertEqual(len(result.selections), 2)
        self.assertEqual(
            {selection.security_id for selection in result.selections},
            {"valid-ce", "valid-pe"},
        )

    def test_rejects_invalid_required_market_fields(self):
        repo = FakeRepo(
            self.ranked,
            [
                self.candidate("CE", "100", lot_size=0),
                self.candidate("PE", "100", spot="0"),
            ],
        )

        with self.assertRaises(OptionContractSelectionEligibilityError):
            OptionContractSelectionService(
                repo,
                clock=lambda: self.now,
            ).select_and_persist(
                OptionContractSelectionRequest(self.run, self.now)
            )

    def test_premium_constraint(self):
        repo = FakeRepo(
            self.ranked,
            [
                self.candidate("CE", "100", price="10"),
                self.candidate("PE", "100", price="10"),
            ],
        )

        with self.assertRaises(OptionContractSelectionEligibilityError):
            OptionContractSelectionService(
                repo,
                clock=lambda: self.now,
            ).select_and_persist(
                OptionContractSelectionRequest(
                    self.run,
                    self.now,
                    maximum_premium_per_lot=Decimal("100"),
                )
            )

    def test_request_validation(self):
        with self.assertRaises(ValueError):
            OptionContractSelectionRequest(
                self.run,
                self.now,
                top_underlyings=0,
            ).normalized()

        with self.assertRaises(ValueError):
            OptionContractSelectionRequest(
                self.run,
                self.now,
                maximum_spread_pct=Decimal("-1"),
            ).normalized()


if __name__ == "__main__":
    unittest.main()
