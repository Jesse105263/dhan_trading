import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.option_ranking_models import OptionRankingCandidate, OptionRankingRequest
from services.option_ranking_service import OptionRankingEligibilityError, OptionRankingService


class FakeRepository:
    def __init__(self, candidates):
        self.candidates = candidates
        self.saved = None

    def list_latest_candidates(self, as_of):
        return self.candidates

    def persist(self, result):
        self.saved = result
        return result


class OptionRankingServiceTest(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime(2026, 7, 12, 14, 0)

    def candidate(self, symbol, liquidity, activity, iv_change, pcr, pcr_change):
        return OptionRankingCandidate(
            analytics_id=uuid4(), change_id=uuid4(), underlying_symbol=symbol,
            expiry=date(2026, 7, 28), source_captured_at=self.as_of - timedelta(minutes=5),
            liquidity_coverage=Decimal(liquidity), price_coverage=Decimal("1"),
            total_call_oi_change=activity, total_put_oi_change=activity,
            atm_straddle_change=Decimal("1"), atm_mean_iv_change=Decimal(iv_change),
            total_pcr=Decimal(pcr), total_pcr_change=Decimal(pcr_change),
            spot_price=Decimal("100"), call_oi_wall_strike=Decimal("110"),
            put_oi_wall_strike=Decimal("90"),
        )

    def test_ranks_deterministically_and_persists(self):
        candidates = [
            self.candidate("AAA", "0.9", 100, "3", "1.6", "0.2"),
            self.candidate("BBB", "0.4", 10, "0.5", "1.0", "0"),
        ]
        repository = FakeRepository(candidates)
        service = OptionRankingService(repository, clock=lambda: self.as_of)
        result = service.rank_and_persist(OptionRankingRequest(self.as_of))
        self.assertEqual([r.underlying_symbol for r in result.rankings], ["AAA", "BBB"])
        self.assertEqual(result.rankings[0].rank_position, 1)
        self.assertGreater(result.rankings[0].total_score, result.rankings[1].total_score)
        self.assertEqual(result.rankings[0].explanation["methodology"], "ranking-v1")
        self.assertIs(repository.saved, result)

    def test_ties_are_broken_by_symbol(self):
        rows = [self.candidate("BBB", "0.5", 10, "1", "1", "0"),
                self.candidate("AAA", "0.5", 10, "1", "1", "0")]
        result = OptionRankingService.rank(rows, self.as_of, self.as_of)
        self.assertEqual([r.underlying_symbol for r in result.rankings], ["AAA", "BBB"])

    def test_rejects_no_eligible_candidates(self):
        stale = self.candidate("AAA", "0.9", 100, "3", "1.6", "0.2")
        stale = OptionRankingCandidate(**{**stale.__dict__, "source_captured_at": self.as_of - timedelta(days=2)})
        service = OptionRankingService(FakeRepository([stale]), clock=lambda: self.as_of)
        with self.assertRaises(OptionRankingEligibilityError):
            service.rank_and_persist(OptionRankingRequest(self.as_of))

    def test_request_validation(self):
        with self.assertRaises(ValueError):
            OptionRankingRequest(self.as_of, maximum_age=timedelta(0)).normalized()
        with self.assertRaises(ValueError):
            OptionRankingRequest(self.as_of, minimum_liquidity_coverage=Decimal("1.1")).normalized()


if __name__ == "__main__":
    unittest.main()
