import os,unittest
from datetime import date,datetime
from uuid import UUID

from services.calibration_v2_models import CalibrationPeriod,CalibrationPolicyV2
from services.calibration_v2_repository import CalibrationV2Repository
from services.calibration_v2_service import CalibrationV2Service
from services.database import get_connection
from tests.test_opportunity_v2_repository_integration import OpportunityV2RepositoryIntegrationTest


@unittest.skipUnless(os.getenv('RUN_DB_INTEGRATION_TESTS')=='1','Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.')
class CalibrationV2RepositoryIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.fixture=OpportunityV2RepositoryIntegrationTest('test_idempotent_abstention_persistence_and_exact_lineage');self.fixture.setUp();self.fixture.test_idempotent_abstention_persistence_and_exact_lineage()
    def tearDown(self):
        with get_connection() as c:
            with c.cursor() as q:
                for table in ('recommendation_evaluations_v2','calibration_dataset_lineage_v2','calibration_reliability_bins_v2','calibration_runs_v2','calibration_policies_v2'):q.execute(f'ALTER TABLE {table} DISABLE TRIGGER ALL')
                q.execute("DELETE FROM recommendation_evaluations_v2 WHERE policy_id=%s",(UUID(int=29),));q.execute("DELETE FROM calibration_dataset_lineage_v2 WHERE run_id IN (SELECT run_id FROM calibration_runs_v2 WHERE policy_id=%s)",(UUID(int=29),));q.execute("DELETE FROM calibration_reliability_bins_v2 WHERE run_id IN (SELECT run_id FROM calibration_runs_v2 WHERE policy_id=%s)",(UUID(int=29),));q.execute("DELETE FROM calibration_runs_v2 WHERE policy_id=%s",(UUID(int=29),));q.execute("DELETE FROM calibration_policies_v2 WHERE policy_id=%s",(UUID(int=29),))
                for table in ('recommendation_evaluations_v2','calibration_dataset_lineage_v2','calibration_reliability_bins_v2','calibration_runs_v2','calibration_policies_v2'):q.execute(f'ALTER TABLE {table} ENABLE TRIGGER ALL')
            c.commit()
        self.fixture.tearDown()
    def test_persists_idempotent_fail_closed_calibration_and_evaluation(self):
        periods=(CalibrationPeriod('TRAIN',date(2020,1,1),date(2023,12,31)),CalibrationPeriod('VALIDATION',date(2024,1,1),date(2024,12,31)),CalibrationPeriod('CALIBRATION',date(2025,1,1),date(2026,6,30)),CalibrationPeriod('TEST',date(2026,7,1),date(2026,12,31)))
        policy=CalibrationPolicyV2(UUID(int=29),'v37-integration','V35_TEST','LONG_CALL','SESSION','ALL','ALL','ALL',periods,purge_days=0,embargo_days=0,minimum_sample_size=1)
        repository=CalibrationV2Repository();service=CalibrationV2Service(repository,clock=lambda:datetime(2026,7,16));a=service.materialize(policy,datetime(2026,7,16));b=service.materialize(policy,datetime(2026,7,16));self.assertEqual(a.run_id,b.run_id);self.assertEqual(a.state,'INSUFFICIENT_EVIDENCE')
        with get_connection() as c:
            with c.cursor() as q:q.execute("SELECT candidate_id FROM opportunity_candidates_v2 WHERE strategy_code='V35_TEST'");candidate_id=q.fetchone()[0]
        evaluation=service.evaluate(candidate_id,a.run_id,policy);self.assertFalse(evaluation.eligible);self.assertEqual(evaluation.state,'UNCALIBRATED')
        with get_connection() as c:
            with c.cursor() as q:q.execute('SELECT COUNT(*),COUNT(DISTINCT lineage_checksum) FROM recommendation_evaluations_v2 WHERE evaluation_id=%s',(evaluation.evaluation_id,));self.assertEqual(q.fetchone(),(1,1))
        with self.assertRaises(Exception):
            with get_connection() as c:
                with c.cursor() as q:q.execute('UPDATE recommendation_evaluations_v2 SET state=%s WHERE evaluation_id=%s',('INELIGIBLE',evaluation.evaluation_id))


if __name__=='__main__':unittest.main()
