import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.option_analytics_history_models import (
    OptionAnalyticsComparisonRequest,
    OptionAnalyticsHistoryRequest,
    OptionAnalyticsPair,
)
from services.option_analytics_history_service import (
    OptionAnalyticsComparisonError,
    OptionAnalyticsHistoryService,
)
from services.option_analytics_models import OptionChainAnalytics


class FakeRepository:
    def __init__(self, pair):
        self.pair = pair
        self.saved = []

    def get_consecutive_pair(self, current_analytics_id):
        return self.pair

    def upsert_change(self, change):
        self.saved.append(change)
        return change

    def list_history(self, symbol, expiry, limit):
        return [self.pair.previous, self.pair.current][:limit]


class OptionAnalyticsHistoryServiceTest(unittest.TestCase):
    def setUp(self):
        self.previous = self._analytics(datetime(2026, 7, 12, 10, 0))
        self.current = self._analytics(
            datetime(2026, 7, 12, 10, 5),
            spot_price="102",
            atm_straddle_cost="12",
            total_call_oi=120,
            total_put_oi=180,
            total_pcr="1.5",
            nearby_call_oi=70,
            nearby_put_oi=105,
            nearby_pcr="1.5",
            atm_mean_iv="24",
            nearby_mean_iv="25",
            call_wall_strike="110",
            call_wall_value=80,
            put_wall_strike="90",
            put_wall_value=100,
            liquidity_coverage="0.8",
            price_coverage="1",
        )
        self.repository = FakeRepository(OptionAnalyticsPair(self.previous, self.current))
        self.service = OptionAnalyticsHistoryService(
            self.repository,
            clock=lambda: datetime(2026, 7, 12, 10, 6),
        )

    def test_calculates_and_persists_deterministic_changes(self):
        result = self.service.compare_and_persist(
            OptionAnalyticsComparisonRequest(self.current.analytics_id)
        )
        self.assertEqual(result.elapsed_seconds, 300)
        self.assertEqual(result.spot_price_change, Decimal("2"))
        self.assertEqual(result.atm_straddle_change, Decimal("2"))
        self.assertEqual(result.total_call_oi_change, 20)
        self.assertEqual(result.total_put_oi_change, 30)
        self.assertEqual(result.total_pcr_change, Decimal("0"))
        self.assertEqual(result.atm_mean_iv_change, Decimal("2"))
        self.assertEqual(result.call_oi_wall_strike_change, Decimal("10"))
        self.assertTrue(result.call_wall_changed)
        self.assertFalse(result.put_wall_changed)
        self.assertEqual(result.liquidity_coverage_change, Decimal("0.2"))
        self.assertEqual(len(self.repository.saved), 1)

    def test_rejects_different_expiry(self):
        current = OptionChainAnalytics(**{**self.current.__dict__, "expiry": date(2026, 8, 25)})
        with self.assertRaisesRegex(OptionAnalyticsComparisonError, "expiries"):
            OptionAnalyticsHistoryService.compare(
                OptionAnalyticsPair(self.previous, current),
                datetime(2026, 7, 12, 10, 6),
            )

    def test_rejects_unordered_snapshots(self):
        current = OptionChainAnalytics(
            **{**self.current.__dict__, "source_captured_at": self.previous.source_captured_at}
        )
        with self.assertRaisesRegex(OptionAnalyticsComparisonError, "unordered"):
            OptionAnalyticsHistoryService.compare(
                OptionAnalyticsPair(self.previous, current),
                datetime(2026, 7, 12, 10, 6),
            )

    def test_null_metrics_produce_null_changes(self):
        previous = OptionChainAnalytics(**{**self.previous.__dict__, "total_pcr": None})
        result = OptionAnalyticsHistoryService.compare(
            OptionAnalyticsPair(previous, self.current),
            datetime(2026, 7, 12, 10, 6),
        )
        self.assertIsNone(result.total_pcr_change)

    def test_history_request_normalization(self):
        request = OptionAnalyticsHistoryRequest(" reliance ", date(2026, 7, 28), 10).normalized()
        self.assertEqual(request.underlying_symbol, "RELIANCE")
        with self.assertRaises(ValueError):
            OptionAnalyticsHistoryRequest("", date(2026, 7, 28)).normalized()
        with self.assertRaises(ValueError):
            OptionAnalyticsHistoryRequest("X", date(2026, 7, 28), 1).normalized()

    def _analytics(
        self,
        captured_at,
        spot_price="100",
        atm_straddle_cost="10",
        total_call_oi=100,
        total_put_oi=150,
        total_pcr="1.5",
        nearby_call_oi=60,
        nearby_put_oi=90,
        nearby_pcr="1.5",
        atm_mean_iv="22",
        nearby_mean_iv="23",
        call_wall_strike="100",
        call_wall_value=70,
        put_wall_strike="90",
        put_wall_value=90,
        liquidity_coverage="0.6",
        price_coverage="0.9",
    ):
        return OptionChainAnalytics(
            analytics_id=uuid4(), source_run_id=uuid4(), underlying_symbol="TEST",
            expiry=date(2026, 7, 28), source_captured_at=captured_at,
            calculated_at=captured_at, spot_price=Decimal(spot_price),
            atm_strike=Decimal("100"), atm_distance=Decimal("0"),
            atm_distance_pct=Decimal("0"), atm_call_price=Decimal("5"),
            atm_put_price=Decimal("5"), atm_straddle_cost=Decimal(atm_straddle_cost),
            total_call_oi=total_call_oi, total_put_oi=total_put_oi,
            total_pcr=Decimal(total_pcr) if total_pcr is not None else None,
            nearby_call_oi=nearby_call_oi, nearby_put_oi=nearby_put_oi,
            nearby_pcr=Decimal(nearby_pcr) if nearby_pcr is not None else None,
            atm_call_iv=Decimal("21"), atm_put_iv=Decimal("23"),
            atm_mean_iv=Decimal(atm_mean_iv) if atm_mean_iv is not None else None,
            nearby_call_mean_iv=Decimal("22"), nearby_put_mean_iv=Decimal("24"),
            nearby_mean_iv=Decimal(nearby_mean_iv) if nearby_mean_iv is not None else None,
            call_oi_wall_strike=Decimal(call_wall_strike) if call_wall_strike else None,
            call_oi_wall_value=call_wall_value,
            put_oi_wall_strike=Decimal(put_wall_strike) if put_wall_strike else None,
            put_oi_wall_value=put_wall_value,
            minimum_strike=Decimal("90"), maximum_strike=Decimal("110"),
            strike_count=3, nearby_strike_count=3, quote_count=6,
            priced_quote_count=6, liquid_quote_count=4,
            price_coverage=Decimal(price_coverage),
            liquidity_coverage=Decimal(liquidity_coverage),
        )


if __name__ == "__main__":
    unittest.main()
