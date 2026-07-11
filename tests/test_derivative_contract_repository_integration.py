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


RUN_INTEGRATION_TESTS = (
    os.getenv("RUN_DB_INTEGRATION_TESTS", "0") == "1"
)


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class DerivativeContractRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid4().hex[:8].upper()
        self.exchange = "NSE"
        self.segment = "NSE_FNO"
        self.underlying = f"ZZD{suffix}"
        self.expiry = date(2026, 7, 30)
        self.repository = DerivativeContractRepository()

        self.call_security_id = f"91{suffix}"
        self.put_security_id = f"92{suffix}"
        self.future_security_id = f"93{suffix}"

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

    def test_upsert_queries_and_deactivation(self) -> None:
        contracts = [
            self._option(self.call_security_id, "CE", "100"),
            self._option(self.put_security_id, "PE", "100"),
            DerivativeContract(
                exchange=self.exchange,
                segment=self.segment,
                security_id=self.future_security_id,
                trading_symbol=f"{self.underlying}-FUT",
                underlying_symbol=self.underlying,
                instrument_type="FUTSTK",
                expiry=self.expiry,
                lot_size=25,
                tick_size=Decimal("0.05"),
            ),
        ]

        inserted = self.repository.bulk_upsert(contracts)
        self.assertEqual(inserted, 3)

        stored = self.repository.get_by_identity(
            self.exchange,
            self.segment,
            self.call_security_id,
        )
        self.assertIsNotNone(stored)
        self.assertEqual(stored.option_type, "CE")
        self.assertEqual(stored.strike, Decimal("100.000000"))

        option_chain = self.repository.list_active_by_underlying(
            self.underlying,
            expiry=self.expiry,
            instrument_type="OPTSTK",
        )
        self.assertEqual(len(option_chain), 2)

        expiries = self.repository.list_active_expiries(
            self.underlying,
            instrument_type="OPTSTK",
        )
        self.assertEqual(expiries, [self.expiry])

        deactivated = self.repository.deactivate_missing(
            self.exchange,
            self.segment,
            [self.call_security_id, self.future_security_id],
        )
        self.assertEqual(deactivated, 1)

        active = self.repository.list_active_by_underlying(
            self.underlying
        )
        self.assertEqual(len(active), 2)
        self.assertEqual(self.repository.count(active_only=True) >= 2, True)

    def test_upsert_updates_existing_identity(self) -> None:
        original = self._option(self.call_security_id, "CE", "100")
        updated = DerivativeContract(
            exchange=original.exchange,
            segment=original.segment,
            security_id=original.security_id,
            trading_symbol=original.trading_symbol,
            underlying_symbol=original.underlying_symbol,
            instrument_type=original.instrument_type,
            expiry=original.expiry,
            strike=original.strike,
            option_type=original.option_type,
            lot_size=50,
            tick_size=Decimal("0.10"),
        )

        self.repository.bulk_upsert([original])
        self.repository.bulk_upsert([updated])

        stored = self.repository.get_by_identity(
            self.exchange,
            self.segment,
            self.call_security_id,
        )
        self.assertIsNotNone(stored)
        self.assertEqual(stored.lot_size, 50)
        self.assertEqual(stored.tick_size, Decimal("0.100000"))

    def _option(
        self,
        security_id: str,
        option_type: str,
        strike: str,
    ) -> DerivativeContract:
        return DerivativeContract(
            exchange=self.exchange,
            segment=self.segment,
            security_id=security_id,
            trading_symbol=(
                f"{self.underlying}-{strike}-{option_type}"
            ),
            underlying_symbol=self.underlying,
            instrument_type="OPTSTK",
            expiry=self.expiry,
            strike=Decimal(strike),
            option_type=option_type,
            lot_size=25,
            tick_size=Decimal("0.05"),
        )


if __name__ == "__main__":
    unittest.main()
