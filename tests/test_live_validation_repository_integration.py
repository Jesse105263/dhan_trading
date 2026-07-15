import os,unittest
from datetime import datetime,timedelta
from uuid import UUID

from services.database import get_connection
from services.live_validation_models import LiveValidationPolicy
from services.live_validation_repository import LiveValidationRepository
from services.live_validation_service import LiveValidationService
from tests.test_calibration_v2_repository_integration import CalibrationV2RepositoryIntegrationTest


@unittest.skipUnless(os.getenv('RUN_DB_INTEGRATION_TESTS')=='1','Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.')
class LiveValidationRepositoryIntegrationTest(unittest.TestCase):
    TABLES=('validation_policy_suspensions_v2','validation_drift_evaluations_v2','validation_metrics_v2','validation_metric_runs_v2','recommendation_failure_classifications_v2','recommendation_outcomes_v2','recommendation_fills_v2','recommendation_validation_observations_v2','recommendation_snapshots_v2','live_validation_policies')
    def setUp(self):
        self.fixture=CalibrationV2RepositoryIntegrationTest('test_persists_idempotent_fail_closed_calibration_and_evaluation');self.fixture.setUp();self.fixture.test_persists_idempotent_fail_closed_calibration_and_evaluation()
    def tearDown(self):
        with get_connection() as c:
            with c.cursor() as q:
                for table in self.TABLES:q.execute(f'ALTER TABLE {table} DISABLE TRIGGER ALL')
                for table in self.TABLES:q.execute(f'DELETE FROM {table}')
                for table in reversed(self.TABLES):q.execute(f'ALTER TABLE {table} ENABLE TRIGGER ALL')
            c.commit()
        self.fixture.tearDown()
    def test_snapshot_outcome_metrics_drift_idempotency_and_immutability(self):
        repository=LiveValidationRepository();service=LiveValidationService(repository,clock=lambda:datetime(2026,7,16,16));policy=LiveValidationPolicy('v38-integration',minimum_metric_sample=2)
        with get_connection() as c:
            with c.cursor() as q:q.execute('SELECT evaluation_id FROM recommendation_evaluations_v2 WHERE policy_id=%s',(UUID(int=29),));evaluation_id=q.fetchone()[0]
        a=service.snapshot(evaluation_id,policy);b=service.snapshot(evaluation_id,policy);self.assertEqual(a.recommendation_id,b.recommendation_id);self.assertEqual(a.state,'ABSTAINED')
        outcome=service.materialize(a.recommendation_id,datetime(2026,7,16,16),policy);self.assertEqual(outcome.state,'ABSTAINED')
        records=repository.metric_records(datetime(2026,7,1),datetime(2026,7,31));run,_=service.compute_metrics(records,policy,datetime(2026,7,16),datetime(2026,7,1),datetime(2026,7,31));drift=service.evaluate_drift({}, {},0,policy,datetime(2026,7,16));self.assertEqual(drift.state,'INSUFFICIENT_EVIDENCE')
        with get_connection() as c:
            with c.cursor() as q:q.execute('SELECT operationally_trusted,lineage_checksum FROM recommendation_snapshots_v2 WHERE recommendation_id=%s',(a.recommendation_id,));trusted,lineage=q.fetchone();self.assertFalse(trusted);self.assertEqual(len(lineage),64);q.execute('SELECT COUNT(*) FROM validation_metric_runs_v2 WHERE run_id=%s',(run,));self.assertEqual(q.fetchone()[0],1)
        with self.assertRaises(Exception):
            with get_connection() as c:
                with c.cursor() as q:q.execute('UPDATE recommendation_snapshots_v2 SET validation_state=%s WHERE recommendation_id=%s',('REJECTED',a.recommendation_id))


if __name__=='__main__':unittest.main()
