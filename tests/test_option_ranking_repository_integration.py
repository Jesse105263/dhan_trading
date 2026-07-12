import os
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.database import get_connection
from services.option_analytics_history_models import OptionAnalyticsComparisonRequest
from services.option_analytics_history_repository import OptionAnalyticsHistoryRepository
from services.option_analytics_history_service import OptionAnalyticsHistoryService
from services.option_analytics_models import OptionChainAnalytics
from services.option_ranking_models import OptionRankingRequest
from services.option_ranking_repository import OptionRankingRepository
from services.option_ranking_service import OptionRankingService

RUN_INTEGRATION_TESTS = os.getenv("RUN_DB_INTEGRATION_TESTS", "0") == "1"


@unittest.skipUnless(RUN_INTEGRATION_TESTS, "Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class OptionRankingRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.symbol = f"ZZR{uuid4().hex[:8].upper()}"
        self.expiry = date(2026, 8, 25)
        first = self._insert_snapshot(datetime.now().replace(microsecond=0) - timedelta(minutes=5), 100)
        second = self._insert_snapshot(datetime.now().replace(microsecond=0), 140)
        OptionAnalyticsHistoryService(OptionAnalyticsHistoryRepository(), clock=datetime.now).compare_and_persist(
            OptionAnalyticsComparisonRequest(second.analytics_id)
        )

    def tearDown(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM option_ranking_runs WHERE ranking_run_id IN (SELECT ranking_run_id FROM option_rankings WHERE underlying_symbol=%s);", (self.symbol,))
                cursor.execute("DELETE FROM option_analytics_changes WHERE underlying_symbol=%s;", (self.symbol,))
                cursor.execute("DELETE FROM option_chain_analytics WHERE underlying_symbol=%s;", (self.symbol,))
                cursor.execute("DELETE FROM option_chain_runs WHERE underlying_symbol=%s;", (self.symbol,))
            connection.commit()

    def test_latest_candidates_and_persistence(self):
        now = datetime.now().replace(microsecond=0)
        repository = OptionRankingRepository()
        candidates = [c for c in repository.list_latest_candidates(now) if c.underlying_symbol == self.symbol]
        self.assertEqual(len(candidates), 1)
        result = OptionRankingService(repository, clock=lambda: now).rank_and_persist(OptionRankingRequest(now))
        self.assertTrue(any(r.underlying_symbol == self.symbol for r in result.rankings))
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM option_rankings WHERE ranking_run_id=%s;", (result.ranking_run_id,))
                self.assertEqual(cursor.fetchone()[0], len(result.rankings))

    def _insert_snapshot(self, captured_at, call_oi):
        run_id = uuid4()
        analytics = OptionChainAnalytics(
            analytics_id=uuid4(), source_run_id=run_id, underlying_symbol=self.symbol,
            expiry=self.expiry, source_captured_at=captured_at, calculated_at=captured_at,
            spot_price=Decimal("100"), atm_strike=Decimal("100"), atm_distance=Decimal("0"),
            atm_distance_pct=Decimal("0"), atm_call_price=Decimal("5"), atm_put_price=Decimal("5"),
            atm_straddle_cost=Decimal("10"), total_call_oi=call_oi, total_put_oi=150,
            total_pcr=Decimal("1.5"), nearby_call_oi=60, nearby_put_oi=90,
            nearby_pcr=Decimal("1.5"), atm_call_iv=Decimal("20"), atm_put_iv=Decimal("22"),
            atm_mean_iv=Decimal("21"), nearby_call_mean_iv=Decimal("20"),
            nearby_put_mean_iv=Decimal("22"), nearby_mean_iv=Decimal("21"),
            call_oi_wall_strike=Decimal("110"), call_oi_wall_value=call_oi,
            put_oi_wall_strike=Decimal("90"), put_oi_wall_value=150,
            minimum_strike=Decimal("90"), maximum_strike=Decimal("110"), strike_count=3,
            nearby_strike_count=3, quote_count=6, priced_quote_count=6, liquid_quote_count=6,
            price_coverage=Decimal("1"), liquidity_coverage=Decimal("1"),
        )
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO option_chain_runs
                    (run_id, underlying_symbol, underlying_security_id, underlying_segment,
                     expiry, status, requested_at, completed_at, spot_price,
                     strikes_received, quotes_received, quotes_inserted)
                    VALUES (%s,%s,%s,'TEST',%s,'COMPLETED',%s,%s,100,3,6,6);
                """, (run_id, self.symbol, uuid4().hex[:12], self.expiry, captured_at, captured_at))
                fields = analytics.__dict__
                cursor.execute(f"INSERT INTO option_chain_analytics ({', '.join(fields)}) VALUES ({', '.join(['%s']*len(fields))});", tuple(fields.values()))
            connection.commit()
        return analytics


if __name__ == "__main__":
    unittest.main()
