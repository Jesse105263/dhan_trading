import os
import unittest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from services.database import get_connection
from services.option_chain_models import OptionQuoteSnapshot, UnderlyingIdentity
from services.option_chain_repository import OptionChainRepository


RUN_INTEGRATION_TESTS = os.getenv("RUN_DB_INTEGRATION_TESTS", "0") == "1"


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class OptionChainRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        suffix = uuid4().hex[:8].upper()
        self.symbol = f"ZZOC{suffix}"
        self.security_id = f"88{suffix}"
        self.run_id = uuid4()
        self.expiry = date(2026, 8, 25)
        self.now = datetime(2026, 7, 12, 10, 30)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO instruments
                    (symbol, exchange, security_id, instrument_type)
                    VALUES (%s, 'NSE_EQ', %s, 'EQUITY');
                    """,
                    (self.symbol, self.security_id),
                )
            connection.commit()

    def tearDown(self) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM option_chain_runs WHERE run_id = %s;",
                    (self.run_id,),
                )
                cursor.execute(
                    "DELETE FROM instruments WHERE symbol = %s;",
                    (self.symbol,),
                )
            connection.commit()

    def test_resolves_and_persists_chain_transactionally(self):
        repository = OptionChainRepository()
        identity = repository.resolve_underlying(self.symbol.lower())
        self.assertEqual(identity.security_id, self.security_id)
        repository.start_run(self.run_id, identity, self.expiry, self.now)

        quotes = [
            OptionQuoteSnapshot(
                underlying_symbol=self.symbol,
                expiry=self.expiry,
                strike=Decimal("100"),
                option_type="CE",
                security_id="1",
                last_price=Decimal("5.5"),
                open_interest=100,
                volume=10,
                captured_at=self.now,
            ),
            OptionQuoteSnapshot(
                underlying_symbol=self.symbol,
                expiry=self.expiry,
                strike=Decimal("100"),
                option_type="PE",
                security_id="2",
                last_price=Decimal("4.5"),
                open_interest=120,
                volume=12,
                captured_at=self.now,
            ),
        ]
        inserted = repository.complete_run_with_quotes(
            self.run_id,
            self.now,
            Decimal("100.25"),
            quotes,
        )
        self.assertEqual(inserted, 2)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT status, strikes_received, quotes_inserted
                    FROM option_chain_runs WHERE run_id = %s;
                    """,
                    (self.run_id,),
                )
                run = cursor.fetchone()
                cursor.execute(
                    "SELECT COUNT(*) FROM option_chain_quotes WHERE run_id = %s;",
                    (self.run_id,),
                )
                quote_count = cursor.fetchone()[0]
        self.assertEqual(run, ("COMPLETED", 1, 2))
        self.assertEqual(quote_count, 2)


if __name__ == "__main__":
    unittest.main()
