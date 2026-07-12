import unittest
from datetime import date, datetime
from decimal import Decimal

from services.option_chain_collector import (
    OptionChainCollector,
    OptionChainValidationError,
)
from services.option_chain_models import OptionChainCollectionRequest
from services.option_chain_repository import UnderlyingIdentity


class FakeRepository:
    def __init__(self) -> None:
        self.started = []
        self.completed = []
        self.failed = []

    def resolve_underlying(self, symbol):
        return UnderlyingIdentity(symbol.strip().upper(), "1333", "NSE_EQ")

    def start_run(self, run_id, identity, expiry, requested_at):
        self.started.append((run_id, identity, expiry, requested_at))

    def complete_run_with_quotes(self, run_id, completed_at, spot_price, quotes):
        quote_list = list(quotes)
        self.completed.append((run_id, completed_at, spot_price, quote_list))
        return len(quote_list)

    def fail_run(self, run_id, completed_at, error_message):
        self.failed.append((run_id, completed_at, error_message))


class FakeExpiryService:
    def __init__(self, expiry=date(2026, 7, 28)) -> None:
        self.expiry = expiry
        self.selected = []
        self.validated = []

    def select_nearest(self, symbol, **kwargs):
        self.selected.append((symbol, kwargs))
        return self.expiry

    def validate(self, symbol, expiry, **kwargs):
        self.validated.append((symbol, expiry, kwargs))
        return expiry


class FakeClient:
    def __init__(self, payload=None, error=None) -> None:
        self.payload = payload
        self.error = error
        self.calls = []

    def fetch(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.payload


class OptionChainCollectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 12, 10, 30)
        self.repository = FakeRepository()
        self.expiry_service = FakeExpiryService()
        self.client = FakeClient(self._payload())
        self.collector = OptionChainCollector(
            repository=self.repository,
            expiry_service=self.expiry_service,
            client=self.client,
            clock=lambda: self.now,
        )

    def test_collects_and_persists_complete_chain(self):
        result = self.collector.collect(
            OptionChainCollectionRequest(" reliance "),
            as_of_date=date(2026, 7, 12),
        )
        self.assertEqual(result.underlying_symbol, "RELIANCE")
        self.assertEqual(result.expiry, date(2026, 7, 28))
        self.assertEqual(result.strikes_received, 2)
        self.assertEqual(result.quotes_received, 4)
        self.assertEqual(result.quotes_inserted, 4)
        self.assertEqual(result.spot_price, Decimal("1500.25"))
        self.assertEqual(len(self.repository.started), 1)
        self.assertEqual(len(self.repository.completed), 1)
        self.assertEqual(self.repository.failed, [])
        self.assertEqual(
            self.client.calls[0]["expiry"],
            "2026-07-28",
        )

    def test_explicit_expiry_is_validated(self):
        expiry = date(2026, 8, 25)
        self.collector.collect(
            OptionChainCollectionRequest("RELIANCE", expiry=expiry),
            as_of_date=date(2026, 7, 12),
        )
        self.assertEqual(len(self.expiry_service.validated), 1)
        self.assertEqual(self.expiry_service.validated[0][1], expiry)
        self.assertEqual(self.expiry_service.selected, [])

    def test_rejects_missing_option_side(self):
        payload = self._payload()
        del payload["data"]["oc"]["1500.0"]["pe"]
        with self.assertRaises(OptionChainValidationError):
            OptionChainCollector.normalize_response(
                payload,
                "RELIANCE",
                date(2026, 7, 28),
                self.now,
            )

    def test_rejects_empty_chain(self):
        with self.assertRaises(OptionChainValidationError):
            OptionChainCollector.normalize_response(
                {"data": {"oc": {}}},
                "RELIANCE",
                date(2026, 7, 28),
                self.now,
            )

    def test_marks_started_run_failed_and_sanitizes_error(self):
        self.client = FakeClient(
            error=RuntimeError("access-token=top-secret")
        )
        collector = OptionChainCollector(
            self.repository,
            self.expiry_service,
            self.client,
            clock=lambda: self.now,
        )
        with self.assertRaises(RuntimeError):
            collector.collect(
                OptionChainCollectionRequest("RELIANCE"),
                as_of_date=date(2026, 7, 12),
            )
        self.assertEqual(len(self.repository.failed), 1)
        self.assertNotIn("top-secret", self.repository.failed[0][2])
        self.assertIn("[REDACTED]", self.repository.failed[0][2])

    def test_request_rejects_invalid_window(self):
        with self.assertRaises(ValueError):
            OptionChainCollectionRequest(
                "RELIANCE",
                minimum_days_to_expiry=10,
                maximum_days_to_expiry=5,
            ).normalized()

    @staticmethod
    def _payload():
        return {
            "status": "success",
            "data": {
                "last_price": 1500.25,
                "oc": {
                    "1500.0": {
                        "ce": {
                            "security_id": "1",
                            "last_price": 45.5,
                            "implied_volatility": 20.2,
                            "oi": 1000,
                            "volume": 100,
                            "top_bid_price": 45.4,
                            "top_ask_price": 45.6,
                        },
                        "pe": {
                            "security_id": "2",
                            "last_price": 42.5,
                            "implied_volatility": 21.2,
                            "oi": 1200,
                            "volume": 110,
                        },
                    },
                    "1520.0": {
                        "ce": {"security_id": "3", "ltp": 35, "oi": 800},
                        "pe": {"security_id": "4", "ltp": 51, "oi": 900},
                    },
                },
            },
        }


if __name__ == "__main__":
    unittest.main()
