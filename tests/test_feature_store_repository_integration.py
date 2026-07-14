import os, unittest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from services.database import get_connection
from services.feature_store_repository import FeatureStoreRepository
from services.feature_store_service import FeatureStoreService

@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class FeatureStoreRepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.symbol=f"ZZF{uuid4().hex[:8].upper()}"; self.run_id=uuid4(); self.analytics_id=uuid4()
        captured=datetime(2026,7,14,12)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO option_chain_runs
                (run_id,underlying_symbol,underlying_security_id,underlying_segment,expiry,status,requested_at,completed_at,spot_price,strikes_received,quotes_received,quotes_inserted)
                VALUES (%s,%s,%s,'TEST',%s,'COMPLETED',%s,%s,100,3,6,6)""",
                (self.run_id,self.symbol,uuid4().hex[:12],date(2026,7,30),captured,captured))
                cursor.execute("""INSERT INTO option_chain_analytics VALUES
                (%s,%s,%s,%s,%s,%s,100,100,0,0,5,5,10,100,150,1.5,60,90,1.5,20,22,21,20,22,21,110,100,90,150,90,110,3,3,6,6,6,1,1,CURRENT_TIMESTAMP)""",
                (self.analytics_id,self.run_id,self.symbol,date(2026,7,30),captured,captured))
            connection.commit()
    def tearDown(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM option_chain_analytics WHERE analytics_id=%s",(self.analytics_id,))
                cursor.execute("DELETE FROM option_chain_runs WHERE run_id=%s",(self.run_id,))
            connection.commit()
    def test_idempotent_materialization_and_exact_lineage(self):
        repository=FeatureStoreRepository(); service=FeatureStoreService(repository)
        service.materialize(10000); service.materialize(10000)
        rows=repository.list_vectors(self.symbol,None,10)
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]["analytics_id"],self.analytics_id)
        self.assertEqual(Decimal(rows[0]["features"]["time_to_expiry_days"]),Decimal("16"))
        self.assertEqual(len(rows[0]["features"]),len(service.definitions()))
