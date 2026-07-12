import os
import unittest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from services.database import get_connection
from services.option_analytics_models import OptionAnalyticsRequest
from services.option_analytics_repository import OptionAnalyticsRepository
from services.option_analytics_service import OptionAnalyticsService
from services.option_chain_models import OptionQuoteSnapshot, UnderlyingIdentity
from services.option_chain_repository import OptionChainRepository


RUN_INTEGRATION_TESTS = os.getenv("RUN_DB_INTEGRATION_TESTS", "0") == "1"


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class OptionAnalyticsRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        suffix = uuid4().hex[:8].upper()
        self.symbol = f"ZZAN{suffix}"
        self.security_id = f"77{suffix}"
        self.run_id = uuid4()
        self.expiry = date(2026, 8, 25)
        self.now = datetime.now().replace(microsecond=0)
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
        chain_repository = OptionChainRepository()
        chain_repository.start_run(
            self.run_id,
            UnderlyingIdentity(self.symbol, self.security_id, "NSE_EQ"),
            self.expiry,
            self.now,
        )
        chain_repository.complete_run_with_quotes(
            self.run_id,
            self.now,
            Decimal("100"),
            self._quotes(),
        )

    def tearDown(self):
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

    def test_reads_calculates_and_upserts_with_lineage(self):
        repository = OptionAnalyticsRepository()
        service = OptionAnalyticsService(repository, clock=lambda: self.now)
        result = service.calculate_and_persist(
            OptionAnalyticsRequest(self.run_id, nearby_strikes_each_side=1)
        )
        second = service.calculate_and_persist(
            OptionAnalyticsRequest(self.run_id, nearby_strikes_each_side=1)
        )
        self.assertEqual(result.analytics_id, second.analytics_id)
        self.assertEqual(result.source_run_id, self.run_id)
        self.assertEqual(result.atm_strike, Decimal("100"))
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*), MIN(source_run_id::text), MAX(quote_count)
                    FROM option_chain_analytics
                    WHERE source_run_id = %s;
                    """,
                    (self.run_id,),
                )
                row = cursor.fetchone()
        self.assertEqual(row, (1, str(self.run_id), 4))

    def _quotes(self):
        return [
            OptionQuoteSnapshot(
                underlying_symbol=self.symbol,
                expiry=self.expiry,
                strike=Decimal(strike),
                option_type=side,
                captured_at=self.now,
                last_price=Decimal(price),
                implied_volatility=Decimal(iv),
                open_interest=oi,
                bid_price=Decimal(price) - Decimal("0.1"),
                ask_price=Decimal(price) + Decimal("0.1"),
            )
            for strike, side, price, iv, oi in [
                ("90", "CE", "12", "20", 100),
                ("90", "PE", "2", "22", 200),
                ("100", "CE", "6", "21", 150),
                ("100", "PE", "5", "23", 180),
            ]
        ]


if __name__ == "__main__":
    unittest.main()
