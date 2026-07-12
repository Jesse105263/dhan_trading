import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.option_analytics_models import (
    CompletedOptionChainRun,
    OptionAnalyticsRequest,
)
from services.option_analytics_service import (
    OptionAnalyticsService,
    OptionAnalyticsValidationError,
)
from services.option_chain_models import OptionQuoteSnapshot


class FakeRepository:
    def __init__(self, source):
        self.source = source
        self.saved = []

    def get_completed_run(self, run_id):
        return self.source

    def upsert(self, analytics):
        self.saved.append(analytics)
        return analytics


class OptionAnalyticsServiceTest(unittest.TestCase):
    def setUp(self):
        self.run_id = uuid4()
        self.completed_at = datetime(2026, 7, 12, 10, 30)
        self.source = self._source()
        self.repository = FakeRepository(self.source)
        self.service = OptionAnalyticsService(
            self.repository,
            clock=lambda: datetime(2026, 7, 12, 10, 35),
        )

    def test_calculates_and_persists_deterministic_features(self):
        result = self.service.calculate_and_persist(
            OptionAnalyticsRequest(
                source_run_id=self.run_id,
                nearby_strikes_each_side=1,
            )
        )
        self.assertEqual(result.atm_strike, Decimal("100"))
        self.assertEqual(result.atm_straddle_cost, Decimal("10"))
        self.assertEqual(result.total_call_oi, 450)
        self.assertEqual(result.total_put_oi, 540)
        self.assertEqual(result.total_pcr, Decimal("1.2"))
        self.assertEqual(result.nearby_pcr, Decimal("1.2"))
        self.assertEqual(result.atm_mean_iv, Decimal("21"))
        self.assertEqual(result.call_oi_wall_strike, Decimal("110"))
        self.assertEqual(result.put_oi_wall_strike, Decimal("90"))
        self.assertEqual(result.price_coverage, Decimal("1"))
        self.assertEqual(
            result.liquidity_coverage,
            Decimal(4) / Decimal(6),
        )
        self.assertEqual(len(self.repository.saved), 1)

    def test_atm_tie_selects_lower_strike(self):
        source = self._source(spot=Decimal("105"))
        result = OptionAnalyticsService.calculate(
            source,
            calculated_at=datetime(2026, 7, 12, 10, 35),
            nearby_strikes_each_side=0,
            maximum_source_age=timedelta(hours=1),
        )
        self.assertEqual(result.atm_strike, Decimal("100"))
        self.assertEqual(result.nearby_strike_count, 1)

    def test_rejects_stale_source(self):
        with self.assertRaisesRegex(
            OptionAnalyticsValidationError,
            "stale",
        ):
            OptionAnalyticsService.calculate(
                self.source,
                calculated_at=datetime(2026, 7, 13, 10, 31),
                nearby_strikes_each_side=1,
                maximum_source_age=timedelta(hours=24),
            )

    def test_rejects_incomplete_source(self):
        source = self._source()
        source = CompletedOptionChainRun(
            **{
                **source.__dict__,
                "quotes": source.quotes[:-1],
                "quotes_received": 5,
                "quotes_inserted": 5,
            }
        )
        with self.assertRaisesRegex(
            OptionAnalyticsValidationError,
            "incomplete",
        ):
            OptionAnalyticsService.calculate(
                source,
                calculated_at=datetime(2026, 7, 12, 10, 35),
                nearby_strikes_each_side=1,
                maximum_source_age=timedelta(hours=1),
            )

    def test_rejects_mismatched_source_counts(self):
        source = CompletedOptionChainRun(
            **{**self.source.__dict__, "quotes_inserted": 5}
        )
        with self.assertRaisesRegex(
            OptionAnalyticsValidationError,
            "counts",
        ):
            OptionAnalyticsService.calculate(
                source,
                calculated_at=datetime(2026, 7, 12, 10, 35),
                nearby_strikes_each_side=1,
                maximum_source_age=timedelta(hours=1),
            )

    def test_zero_call_oi_returns_null_pcr(self):
        quotes = tuple(
            OptionQuoteSnapshot(
                **{
                    **quote.__dict__,
                    "open_interest": (
                        0 if quote.option_type == "CE" else quote.open_interest
                    ),
                }
            )
            for quote in self.source.quotes
        )
        source = CompletedOptionChainRun(
            **{**self.source.__dict__, "quotes": quotes}
        )
        result = OptionAnalyticsService.calculate(
            source,
            calculated_at=datetime(2026, 7, 12, 10, 35),
            nearby_strikes_each_side=1,
            maximum_source_age=timedelta(hours=1),
        )
        self.assertIsNone(result.total_pcr)
        self.assertIsNone(result.nearby_pcr)

    def test_request_validation(self):
        with self.assertRaises(ValueError):
            OptionAnalyticsRequest(
                source_run_id=self.run_id,
                nearby_strikes_each_side=-1,
            ).normalized()
        with self.assertRaises(ValueError):
            OptionAnalyticsRequest(
                source_run_id=self.run_id,
                maximum_source_age=timedelta(0),
            ).normalized()

    def _source(self, spot=Decimal("102")):
        rows = [
            ("90", "CE", "12", "20", 100, "11", "13"),
            ("90", "PE", "2", "22", 220, "1", "3"),
            ("100", "CE", "6", "20", 150, "5", "7"),
            ("100", "PE", "4", "22", 180, "3", "5"),
            ("110", "CE", "2", "24", 200, None, None),
            ("110", "PE", "12", "26", 140, None, None),
        ]
        quotes = tuple(
            OptionQuoteSnapshot(
                underlying_symbol="TEST",
                expiry=date(2026, 7, 28),
                strike=Decimal(strike),
                option_type=option_type,
                captured_at=self.completed_at,
                last_price=Decimal(price),
                implied_volatility=Decimal(iv),
                open_interest=oi,
                bid_price=Decimal(bid) if bid else None,
                ask_price=Decimal(ask) if ask else None,
            )
            for strike, option_type, price, iv, oi, bid, ask in rows
        )
        return CompletedOptionChainRun(
            run_id=self.run_id,
            underlying_symbol="TEST",
            expiry=date(2026, 7, 28),
            completed_at=self.completed_at,
            spot_price=spot,
            strikes_received=3,
            quotes_received=6,
            quotes_inserted=6,
            quotes=quotes,
        )


if __name__ == "__main__":
    unittest.main()
