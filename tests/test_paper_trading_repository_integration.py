from __future__ import annotations

import os
import unittest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from services.database import get_connection
from services.option_signal_models import OptionSignalRequest
from services.option_signal_repository import OptionSignalRepository
from services.option_signal_service import OptionSignalService
from services.paper_trading_models import PaperCloseRequest, PaperOpenRequest
from services.paper_trading_repository import PaperTradingRepository
from services.paper_trading_service import PaperTradingService


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION_TESTS") == "1",
    "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.",
)
class PaperTradingRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT risk_run_id FROM option_risk_assessment_runs
                    WHERE approved_contract_count > 0 ORDER BY calculated_at DESC LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row is None:
                    self.skipTest("No production risk run with approved contracts is available.")
                self.risk_run_id = UUID(str(row[0]))
                cursor.execute("DELETE FROM option_signal_runs WHERE risk_run_id=%s", (self.risk_run_id,))
            connection.commit()
        signal_result = OptionSignalService(OptionSignalRepository()).generate_and_persist(
            OptionSignalRequest(self.risk_run_id, datetime.now())
        )
        self.signal_run_id = signal_result.signal_run_id
        self.signal_id = signal_result.signals[0].signal_id
        repository = PaperTradingRepository()
        self.signal = repository.get_signal(self.signal_id)
        self.assertIsNotNone(self.signal)
        self.entry_run_id = uuid4()
        self.exit_run_id = uuid4()
        self.entry_time = self.signal.signal_calculated_at + timedelta(minutes=1)
        self.exit_time = self.entry_time + timedelta(minutes=1)
        self._insert_mark(self.entry_run_id, self.entry_time, "100")
        self._insert_mark(self.exit_run_id, self.exit_time, "120")

    def tearDown(self) -> None:
        if not hasattr(self, "signal_run_id"):
            return
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM paper_position_events WHERE position_id IN (SELECT position_id FROM paper_positions WHERE signal_id=%s)",
                    (self.signal_id,),
                )
                cursor.execute(
                    "DELETE FROM paper_trade_fills WHERE position_id IN (SELECT position_id FROM paper_positions WHERE signal_id=%s)",
                    (self.signal_id,),
                )
                cursor.execute("DELETE FROM paper_positions WHERE signal_id=%s", (self.signal_id,))
                cursor.execute("DELETE FROM paper_trade_orders WHERE signal_id=%s", (self.signal_id,))
                cursor.execute("DELETE FROM option_chain_runs WHERE run_id IN (%s,%s)", (self.entry_run_id, self.exit_run_id))
                cursor.execute("DELETE FROM option_signal_runs WHERE signal_run_id=%s", (self.signal_run_id,))
            connection.commit()

    def _insert_mark(self, run_id, captured_at, price) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO option_chain_runs (
                        run_id, underlying_symbol, underlying_security_id,
                        underlying_segment, expiry, status, requested_at, completed_at,
                        spot_price, strikes_received, quotes_received, quotes_inserted
                    ) VALUES (%s,%s,'PAPER-UNDERLYING','PAPER_TEST',%s,'COMPLETED',%s,%s,1000,1,1,1)
                    """,
                    (run_id, self.signal.underlying_symbol, self.signal.expiry, captured_at, captured_at),
                )
                cursor.execute(
                    """
                    INSERT INTO option_chain_quotes (
                        run_id, underlying_symbol, expiry, strike, option_type,
                        security_id, last_price, captured_at
                    ) VALUES (%s,%s,%s,1000,%s,%s,%s,%s)
                    """,
                    (
                        run_id, self.signal.underlying_symbol, self.signal.expiry,
                        self.signal.option_type, self.signal.security_id, price, captured_at,
                    ),
                )
            connection.commit()

    def test_open_close_and_audit_full_signal_lineage(self) -> None:
        repository = PaperTradingRepository()
        service = PaperTradingService(repository)
        opened = service.open_position(PaperOpenRequest(self.signal_id, self.entry_time))
        self.assertEqual(opened.position.status, "OPEN")
        closed = service.close_position(PaperCloseRequest(opened.position.position_id, self.exit_time))
        self.assertEqual(closed.position.status, "CLOSED")
        self.assertEqual(closed.position.signal.risk_run_id, self.risk_run_id)
        self.assertGreater(closed.position.net_pnl, 0)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT side, status FROM paper_trade_orders WHERE signal_id=%s ORDER BY filled_at",
                    (self.signal_id,),
                )
                self.assertEqual(cursor.fetchall(), [("BUY", "FILLED"), ("SELL", "FILLED")])
                cursor.execute(
                    "SELECT event_type, sequence_number FROM paper_position_events WHERE position_id=%s ORDER BY sequence_number",
                    (opened.position.position_id,),
                )
                self.assertEqual(cursor.fetchall(), [("OPENED", 1), ("CLOSED", 2)])


if __name__ == "__main__":
    unittest.main()
