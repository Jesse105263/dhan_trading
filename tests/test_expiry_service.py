import unittest
from datetime import date

from services.expiry_repository import ExpiryAvailability
from services.expiry_service import (
    ExpiryNotFoundError,
    ExpiryService,
)


class FakeExpiryRepository:
    def __init__(
        self,
        expiries: list[date],
        available: bool = True,
    ) -> None:
        self.expiries = expiries
        self.available = available

    def list_available(
        self,
        underlying_symbol: str,
        instrument_type: str = "OPTSTK",
        on_or_after: date | None = None,
    ) -> list[ExpiryAvailability]:
        return [
            ExpiryAvailability(
                underlying_symbol=underlying_symbol.strip().upper(),
                instrument_type=instrument_type.strip().upper(),
                expiry=expiry,
                contract_count=100,
            )
            for expiry in self.expiries
            if on_or_after is None or expiry >= on_or_after
        ]

    def is_available(
        self,
        underlying_symbol: str,
        expiry: date,
        instrument_type: str = "OPTSTK",
    ) -> bool:
        return self.available and expiry in self.expiries

    def count_underlyings(
        self,
        instrument_type: str = "OPTSTK",
        on_or_after: date | None = None,
    ) -> int:
        return 1 if self.expiries else 0


class ExpiryServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.expiries = [
            date(2026, 7, 16),
            date(2026, 7, 23),
            date(2026, 7, 30),
            date(2026, 8, 27),
            date(2026, 9, 24),
        ]
        self.service = ExpiryService(
            FakeExpiryRepository(self.expiries)
        )

    def test_selects_nearest_eligible_expiry(self) -> None:
        selected = self.service.select_nearest(
            "reliance",
            as_of_date=date(2026, 7, 12),
        )
        self.assertEqual(selected, date(2026, 7, 16))

    def test_respects_minimum_and_maximum_days(self) -> None:
        selected = self.service.select_nearest(
            "RELIANCE",
            as_of_date=date(2026, 7, 12),
            minimum_days_to_expiry=10,
            maximum_days_to_expiry=20,
        )
        self.assertEqual(selected, date(2026, 7, 23))

    def test_rejects_when_no_expiry_is_in_window(self) -> None:
        with self.assertRaises(ExpiryNotFoundError):
            self.service.select_nearest(
                "RELIANCE",
                as_of_date=date(2026, 7, 12),
                maximum_days_to_expiry=2,
            )

    def test_selects_next_expiry(self) -> None:
        selected = self.service.select_next(
            "RELIANCE",
            after_expiry=date(2026, 7, 23),
        )
        self.assertEqual(selected, date(2026, 7, 30))

    def test_identifies_last_available_expiry_per_month(self) -> None:
        monthly = self.service.list_monthly_expiries(
            "RELIANCE",
            as_of_date=date(2026, 7, 12),
        )
        self.assertEqual(
            monthly,
            [
                date(2026, 7, 30),
                date(2026, 8, 27),
                date(2026, 9, 24),
            ],
        )

    def test_validates_active_expiry(self) -> None:
        validated = self.service.validate(
            "RELIANCE",
            date(2026, 7, 30),
            as_of_date=date(2026, 7, 12),
        )
        self.assertEqual(validated, date(2026, 7, 30))

    def test_rejects_inactive_expiry(self) -> None:
        with self.assertRaises(ExpiryNotFoundError):
            self.service.validate(
                "RELIANCE",
                date(2026, 7, 17),
                as_of_date=date(2026, 7, 12),
            )

    def test_rejects_expired_date(self) -> None:
        with self.assertRaisesRegex(ValueError, "as_of_date"):
            self.service.validate(
                "RELIANCE",
                date(2026, 7, 10),
                as_of_date=date(2026, 7, 12),
            )

    def test_lists_eligible_dates_in_centralized_order(self) -> None:
        eligible = ExpiryService.eligible_expiries_from(
            [
                date(2026, 7, 30),
                date(2026, 7, 16),
                date(2026, 7, 23),
            ],
            as_of_date=date(2026, 7, 12),
            minimum_days_to_expiry=5,
        )
        self.assertEqual(
            eligible,
            [date(2026, 7, 23), date(2026, 7, 30)],
        )

    def test_static_selection_normalizes_unsorted_duplicates(self) -> None:
        selected = ExpiryService.select_nearest_from(
            [
                date(2026, 7, 30),
                date(2026, 7, 16),
                date(2026, 7, 16),
            ],
            as_of_date=date(2026, 7, 12),
        )
        self.assertEqual(selected, date(2026, 7, 16))

    def test_rejects_invalid_day_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "maximum"):
            self.service.select_nearest(
                "RELIANCE",
                as_of_date=date(2026, 7, 12),
                minimum_days_to_expiry=10,
                maximum_days_to_expiry=5,
            )


if __name__ == "__main__":
    unittest.main()
