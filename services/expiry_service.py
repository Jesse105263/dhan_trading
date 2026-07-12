from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

from services.expiry_repository import (
    ExpiryAvailability,
    ExpiryRepository,
)
from services.repository_contracts import ExpiryRepositoryContract


class ExpiryNotFoundError(LookupError):
    pass


class ExpiryService:
    def __init__(
        self,
        repository: ExpiryRepositoryContract | None = None,
    ) -> None:
        self.repository = repository or ExpiryRepository()

    def list_available(
        self,
        underlying_symbol: str,
        instrument_type: str = "OPTSTK",
        as_of_date: date | None = None,
    ) -> list[ExpiryAvailability]:
        return self.repository.list_available(
            underlying_symbol=underlying_symbol,
            instrument_type=instrument_type,
            on_or_after=as_of_date,
        )

    def select_nearest(
        self,
        underlying_symbol: str,
        instrument_type: str = "OPTSTK",
        as_of_date: date | None = None,
        minimum_days_to_expiry: int = 0,
        maximum_days_to_expiry: int | None = None,
    ) -> date:
        reference_date = as_of_date or date.today()
        self._validate_day_window(
            minimum_days_to_expiry,
            maximum_days_to_expiry,
        )
        eligible_from = reference_date + timedelta(
            days=minimum_days_to_expiry
        )
        expiries = self._expiry_dates(
            self.repository.list_available(
                underlying_symbol=underlying_symbol,
                instrument_type=instrument_type,
                on_or_after=eligible_from,
            )
        )

        if maximum_days_to_expiry is not None:
            eligible_until = reference_date + timedelta(
                days=maximum_days_to_expiry
            )
            expiries = [
                expiry
                for expiry in expiries
                if expiry <= eligible_until
            ]

        if not expiries:
            raise ExpiryNotFoundError(
                "No eligible active expiry found for "
                f"{underlying_symbol.strip().upper()}."
            )

        return expiries[0]

    def select_next(
        self,
        underlying_symbol: str,
        after_expiry: date,
        instrument_type: str = "OPTSTK",
    ) -> date:
        expiries = self._expiry_dates(
            self.repository.list_available(
                underlying_symbol=underlying_symbol,
                instrument_type=instrument_type,
                on_or_after=after_expiry + timedelta(days=1),
            )
        )

        if not expiries:
            raise ExpiryNotFoundError(
                "No active expiry exists after "
                f"{after_expiry.isoformat()} for "
                f"{underlying_symbol.strip().upper()}."
            )

        return expiries[0]

    def list_monthly_expiries(
        self,
        underlying_symbol: str,
        instrument_type: str = "OPTSTK",
        as_of_date: date | None = None,
    ) -> list[date]:
        expiries = self._expiry_dates(
            self.repository.list_available(
                underlying_symbol=underlying_symbol,
                instrument_type=instrument_type,
                on_or_after=as_of_date,
            )
        )
        return self.monthly_expiries_from(expiries)

    def select_nearest_monthly(
        self,
        underlying_symbol: str,
        instrument_type: str = "OPTSTK",
        as_of_date: date | None = None,
    ) -> date:
        monthly_expiries = self.list_monthly_expiries(
            underlying_symbol=underlying_symbol,
            instrument_type=instrument_type,
            as_of_date=as_of_date or date.today(),
        )

        if not monthly_expiries:
            raise ExpiryNotFoundError(
                "No active monthly expiry found for "
                f"{underlying_symbol.strip().upper()}."
            )

        return monthly_expiries[0]

    def validate(
        self,
        underlying_symbol: str,
        expiry: date,
        instrument_type: str = "OPTSTK",
        as_of_date: date | None = None,
    ) -> date:
        reference_date = as_of_date or date.today()

        if expiry < reference_date:
            raise ValueError(
                "expiry cannot be earlier than as_of_date."
            )

        if not self.repository.is_available(
            underlying_symbol=underlying_symbol,
            expiry=expiry,
            instrument_type=instrument_type,
        ):
            raise ExpiryNotFoundError(
                f"Expiry {expiry.isoformat()} is not active for "
                f"{underlying_symbol.strip().upper()}."
            )

        return expiry

    @staticmethod
    def eligible_expiries_from(
        expiries: Iterable[date],
        as_of_date: date,
        minimum_days_to_expiry: int = 0,
        maximum_days_to_expiry: int | None = None,
    ) -> list[date]:
        ExpiryService._validate_day_window(
            minimum_days_to_expiry,
            maximum_days_to_expiry,
        )
        eligible_from = as_of_date + timedelta(
            days=minimum_days_to_expiry
        )
        eligible_until = (
            as_of_date + timedelta(days=maximum_days_to_expiry)
            if maximum_days_to_expiry is not None
            else None
        )
        return [
            expiry
            for expiry in sorted(set(expiries))
            if expiry >= eligible_from
            and (
                eligible_until is None
                or expiry <= eligible_until
            )
        ]

    @staticmethod
    def select_nearest_from(
        expiries: Iterable[date],
        as_of_date: date,
        minimum_days_to_expiry: int = 0,
        maximum_days_to_expiry: int | None = None,
    ) -> date:
        eligible = ExpiryService.eligible_expiries_from(
            expiries=expiries,
            as_of_date=as_of_date,
            minimum_days_to_expiry=minimum_days_to_expiry,
            maximum_days_to_expiry=maximum_days_to_expiry,
        )

        if not eligible:
            raise ExpiryNotFoundError(
                "No eligible expiry found in the supplied dates."
            )

        return eligible[0]

    @staticmethod
    def monthly_expiries_from(
        expiries: Iterable[date],
    ) -> list[date]:
        monthly: dict[tuple[int, int], date] = {}
        for expiry in sorted(set(expiries)):
            monthly[(expiry.year, expiry.month)] = expiry
        return list(monthly.values())

    @staticmethod
    def _expiry_dates(
        availability: Iterable[ExpiryAvailability],
    ) -> list[date]:
        return sorted(
            {
                item.expiry
                for item in availability
            }
        )

    @staticmethod
    def _validate_day_window(
        minimum_days_to_expiry: int,
        maximum_days_to_expiry: int | None,
    ) -> None:
        if minimum_days_to_expiry < 0:
            raise ValueError(
                "minimum_days_to_expiry cannot be negative."
            )
        if (
            maximum_days_to_expiry is not None
            and maximum_days_to_expiry
            < minimum_days_to_expiry
        ):
            raise ValueError(
                "maximum_days_to_expiry cannot be less than "
                "minimum_days_to_expiry."
            )
