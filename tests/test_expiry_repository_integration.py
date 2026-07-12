import os
import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from services.database import get_connection
from services.derivative_contract_repository import (
    DerivativeContract,
    DerivativeContractRepository,
)
from services.expiry_repository import ExpiryRepository
from services.expiry_service import ExpiryService


RUN_INTEGRATION_TESTS = (
    os.getenv("RUN_DB_INTEGRATION_TESTS", "0") == "1"
)


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class ExpiryRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid4().hex[:8].upper()
        self.underlying = f"ZZE{suffix}"
        self.contract_repository = DerivativeContractRepository()
        self.expiry_repository = ExpiryRepository()
        self.service = ExpiryService(self.expiry_repository)
        self.first_expiry = date(2026, 7, 30)
        self.second_expiry = date(2026, 8, 27)

        contracts = [
            self._option("1", self.first_expiry, "CE", "100"),
            self._option("2", self.first_expiry, "PE", "100"),
            self._option("3", self.second_expiry, "CE", "110"),
            self._option("4", self.second_expiry, "PE", "110"),
        ]
        self.contract_repository.bulk_upsert(contracts)

    def tearDown(self) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM derivative_contracts
                    WHERE underlying_symbol = %s;
                    """,
                    (self.underlying,),
                )
            connection.commit()

    def test_lists_counts_selects_and_validates_expiries(self) -> None:
        availability = self.expiry_repository.list_available(
            self.underlying,
            instrument_type="OPTSTK",
            on_or_after=date(2026, 7, 1),
        )

        self.assertEqual(
            [item.expiry for item in availability],
            [self.first_expiry, self.second_expiry],
        )
        self.assertEqual(
            [item.contract_count for item in availability],
            [2, 2],
        )
        self.assertTrue(
            self.expiry_repository.is_available(
                self.underlying,
                self.first_expiry,
            )
        )
        self.assertEqual(
            self.service.select_nearest(
                self.underlying,
                as_of_date=date(2026, 7, 1),
            ),
            self.first_expiry,
        )
        self.assertEqual(
            self.service.select_next(
                self.underlying,
                after_expiry=self.first_expiry,
            ),
            self.second_expiry,
        )

    def _option(
        self,
        identity_suffix: str,
        expiry: date,
        option_type: str,
        strike: str,
    ) -> DerivativeContract:
        return DerivativeContract(
            exchange="NSE",
            segment="NSE_FNO",
            security_id=(
                f"97{self.underlying[-8:]}{identity_suffix}"
            ),
            trading_symbol=(
                f"{self.underlying}-{expiry.isoformat()}-"
                f"{strike}-{option_type}"
            ),
            underlying_symbol=self.underlying,
            instrument_type="OPTSTK",
            expiry=expiry,
            strike=Decimal(strike),
            option_type=option_type,
            lot_size=25,
            tick_size=Decimal("0.05"),
        )


if __name__ == "__main__":
    unittest.main()
