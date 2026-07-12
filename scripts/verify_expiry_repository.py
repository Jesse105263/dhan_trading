from datetime import date

from services.expiry_repository import ExpiryRepository
from services.expiry_service import ExpiryNotFoundError, ExpiryService


def main() -> None:
    repository = ExpiryRepository()
    service = ExpiryService(repository)
    today = date.today()
    underlying_count = repository.count_underlyings(
        instrument_type="OPTSTK",
        on_or_after=today,
    )

    print("Expiry repository production verification")
    print(f"As of: {today.isoformat()}")
    print(f"Active option underlyings: {underlying_count}")

    if underlying_count == 0:
        raise RuntimeError(
            "No active option underlyings were found."
        )

    for symbol in ("NIFTY", "BANKNIFTY", "RELIANCE", "MCX"):
        availability = service.list_available(
            symbol,
            instrument_type="OPTSTK",
            as_of_date=today,
        )
        if not availability:
            print(f"{symbol}: no active option expiries")
            continue

        try:
            nearest = service.select_nearest(
                symbol,
                instrument_type="OPTSTK",
                as_of_date=today,
            )
        except ExpiryNotFoundError:
            print(f"{symbol}: no eligible option expiry")
            continue

        print(
            f"{symbol}: expiries={len(availability)} "
            f"nearest={nearest.isoformat()} "
            f"contracts={availability[0].contract_count}"
        )


if __name__ == "__main__":
    main()
