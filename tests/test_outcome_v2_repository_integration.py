import json
import os
import unittest
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.database import get_connection
from services.historical_data_models import HistoricalDataSource, RawPayloadEnvelope
from services.historical_data_provider import LocalJsonHistoricalDataAdapter
from services.historical_data_repository import HistoricalDataRepository
from services.historical_data_service import HistoricalDataService
from services.outcome_v2_models import OutcomeHorizon, OutcomePolicy
from services.outcome_v2_repository import OutcomeV2Repository
from services.outcome_v2_service import OutcomeV2Service
from tests.test_historical_data_foundation import policy


INSTRUMENT=UUID("a1111111-1111-4111-8111-111111111111")


def payload(first_close="100", available="2026-07-15T09:30:00"):
    bars=[]
    for index,(opened,closed,price,high,low) in enumerate((("09:15:00","09:30:00",first_close,"101","99"),("09:30:00","09:45:00","105","106","100"),("09:45:00","10:00:00","110","112","104"))):
        bars.append({"instrument_id":str(INSTRUMENT),"interval_code":"15M","bar_open_at":f"2026-07-15T{opened}","bar_close_at":f"2026-07-15T{closed}",
            "session_date":"2026-07-15","adjustment_state":"RAW","open_price":price,"high_price":high,"low_price":low,"close_price":price,
            "event_at":f"2026-07-15T{closed}","available_at":available if index==0 else f"2026-07-15T{closed}"})
    return {"instruments":[{"instrument_id":str(INSTRUMENT),"identity_key":"V33|NSE|EQUITY|TEST",
        "instrument_class":"EQUITY","exchange":"NSE","segment":"NSE_EQ","trading_symbol":"V33TEST",
        "valid_from":"2026-01-01T00:00:00","available_at":"2026-01-01T00:00:00"}],"mappings":[],"bars":bars,"corporate_actions":[]}


@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class OutcomeV2RepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.source=HistoricalDataSource("V33_TEST","LOCAL","OUTCOME_V2","LOCAL_FIXTURE","integration")
        self.foundation=HistoricalDataService(HistoricalDataRepository(),clock=lambda:datetime(2026,7,16))
        self._import(payload(),"base")

    def _import(self,data,batch):
        raw=json.dumps(data,sort_keys=True,separators=(",",":")).encode()
        envelope=RawPayloadEnvelope(batch,"fixture-v1","application/json",raw,datetime(2026,7,15,10),datetime(2026,7,15,10))
        return self.foundation.import_payload(self.source,policy(),envelope,LocalJsonHistoricalDataAdapter())

    def tearDown(self):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE historical_outcome_path_v2 DISABLE TRIGGER outcome_v2_path_immutable")
                cursor.execute("ALTER TABLE historical_outcomes_v2 DISABLE TRIGGER outcome_v2_immutable")
                cursor.execute("DELETE FROM historical_outcome_path_v2 WHERE outcome_id IN (SELECT outcome_id FROM historical_outcomes_v2 WHERE instrument_id=%s)",(INSTRUMENT,))
                cursor.execute("DELETE FROM historical_outcomes_v2 WHERE instrument_id=%s",(INSTRUMENT,))
                cursor.execute("ALTER TABLE historical_outcomes_v2 ENABLE TRIGGER outcome_v2_immutable")
                cursor.execute("ALTER TABLE historical_outcome_path_v2 ENABLE TRIGGER outcome_v2_path_immutable")
                cursor.execute("DELETE FROM outcome_materialization_runs_v2 WHERE model_version LIKE 'v33-test-%%'")
                cursor.execute("DELETE FROM outcome_model_versions_v2 WHERE model_version LIKE 'v33-test-%%'")
                cursor.execute("SELECT source_id FROM historical_data_sources WHERE provider_code='V33_TEST'"); row=cursor.fetchone()
                if row:
                    sid=row[0]; cursor.execute("DELETE FROM historical_bar_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,))
                    cursor.execute("DELETE FROM canonical_instrument_revisions WHERE manifest_id IN (SELECT manifest_id FROM historical_raw_manifests WHERE source_id=%s)",(sid,))
                    cursor.execute("DELETE FROM canonical_instruments WHERE instrument_id=%s",(INSTRUMENT,)); cursor.execute("DELETE FROM historical_raw_manifests WHERE source_id=%s",(sid,))
                    cursor.execute("DELETE FROM historical_raw_payloads WHERE source_id=%s",(sid,)); cursor.execute("DELETE FROM historical_retention_policies WHERE source_id=%s",(sid,))
                    cursor.execute("DELETE FROM historical_data_sources WHERE source_id=%s",(sid,))
            connection.commit()

    def test_materialization_is_idempotent_and_preserves_exact_path_lineage(self):
        repository=OutcomeV2Repository(); service=OutcomeV2Service(repository,clock=lambda:datetime(2026,7,16))
        policy_v2=OutcomePolicy("v33-test-path-v2",(OutcomeHorizon("30M",duration_seconds=1800),),total_cost_bps=Decimal("10"))
        first=service.materialize(policy_v2,as_of=datetime(2026,7,15,11),limit=1); second=service.materialize(policy_v2,as_of=datetime(2026,7,15,11),limit=1)
        self.assertEqual(first.run_id,second.run_id); self.assertEqual(first.complete_count,1)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT outcome_state,gross_return_pct,net_return_pct,path_observation_count,lineage_checksum FROM historical_outcomes_v2 WHERE model_version=%s",(policy_v2.model_version,)); row=cursor.fetchone()
                self.assertEqual(row[:4],("COMPLETE",Decimal("10.0"),Decimal("9.9"),2)); self.assertEqual(len(row[4]),64)
                cursor.execute("SELECT COUNT(*),COUNT(DISTINCT bar_revision_id),COUNT(DISTINCT manifest_id) FROM historical_outcome_path_v2"); counts=cursor.fetchone()
                self.assertGreaterEqual(counts[0],2); self.assertEqual(counts[0],counts[1])
        stats=repository.statistics(policy_v2.model_version,"30M"); self.assertEqual(stats["expectancy"],Decimal("9.9"))

    def test_as_of_query_uses_revision_available_then_not_current_now(self):
        revised=payload(first_close="101",available="2026-07-16T09:30:00"); revised["bars"]=revised["bars"][:1]
        self._import(revised,"late-revision")
        repository=OutcomeV2Repository(); old=repository.anchors(datetime(2026,7,15,11),10); current=repository.anchors(datetime(2026,7,17),10)
        old_anchor=[item for item in old if item.instrument_id==INSTRUMENT and item.bar_close_at==datetime(2026,7,15,9,30)][0]
        current_anchor=[item for item in current if item.instrument_id==INSTRUMENT and item.bar_close_at==datetime(2026,7,15,9,30)][0]
        self.assertEqual(old_anchor.close_price,Decimal("100")); self.assertEqual(current_anchor.close_price,Decimal("101"))


if __name__=="__main__": unittest.main()
