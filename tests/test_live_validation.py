import unittest
from datetime import datetime,timedelta
from decimal import Decimal
from uuid import UUID

from scripts.materialize_recommendation_validation import FixtureRepository
from services.live_validation_models import LiveValidationPolicy
from services.live_validation_service import LiveValidationService


class Repo(FixtureRepository):
    def __init__(self):super().__init__();self.source=self.recommendation_source(UUID(int=1));self.metric_saved=None;self.drift_saved=None;self.user=None;self.fills=[]
    def recommendation_source(self,evaluation_id):return dict(self.source) if hasattr(self,'source') else super().recommendation_source(evaluation_id)
    def persist_metrics(self,policy,run,segments):self.metric_saved=(policy,run,segments)
    def persist_drift(self,policy,evaluation,suspension):self.drift_saved=(policy,evaluation,suspension)
    def user_fill(self,recommendation_id,as_of):return self.user
    def persist_fill(self,fill):self.fills.append(fill);self.user=fill


class LiveValidationTest(unittest.TestCase):
    def setUp(self):self.now=datetime(2026,7,16,16);self.repo=Repo();self.policy=LiveValidationPolicy('test-live',minimum_metric_sample=3,minimum_shadow_sessions=60);self.service=LiveValidationService(self.repo,clock=lambda:self.now);self.snapshot=self.service.snapshot(UUID(int=1),self.policy)
    def test_snapshot_is_deterministic_complete_and_never_trusted(self):
        again=self.service.snapshot(UUID(int=1),self.policy);self.assertEqual(self.snapshot.recommendation_id,again.recommendation_id);row=self.repo.snapshots[self.snapshot.recommendation_id]
        self.assertEqual(row['instrument_revision_id'],UUID(int=8));self.assertEqual(row['option_type'],'CE');self.assertFalse(row['operationally_trusted']);self.assertEqual(len(row['lineage_checksum']),64);self.assertEqual(row['validation_state'],'ELIGIBLE')
    def test_rejected_and_abstained_snapshots_are_preserved(self):
        for state,expected in (('ILLIQUID','REJECTED'),('INSUFFICIENT_EVIDENCE','ABSTAINED')):
            repo=Repo();repo.source['evaluation_state']=state;repo.source['evaluation_id']=UUID(int=10 if expected=='REJECTED' else 11);service=LiveValidationService(repo,clock=lambda:self.now);result=service.snapshot(repo.source['evaluation_id'],self.policy);self.assertEqual(result.state,expected)
    def test_target_first_touch_fill_slippage_mfe_mae_and_net_return(self):
        result=self.service.materialize(self.snapshot.recommendation_id,self.now,self.policy);self.assertEqual(result.state,'FILLED');observations,fill,outcome,classification=self.repo.validations[-1]
        self.assertEqual(outcome['first_touch'],'TARGET');self.assertEqual(outcome['target_hit'],1);self.assertFalse(outcome['stop_hit']);self.assertGreater(outcome['mfe_pct'],0);self.assertLess(outcome['mae_pct'],0);self.assertLess(outcome['net_return_pct'],outcome['realized_return_pct']);self.assertIsNotNone(fill['fill_quality']);self.assertEqual(len(observations),2);self.assertEqual(classification['classification'],'UNCLASSIFIED')
    def test_stop_first_touch_and_market_failure(self):
        base=self.repo.snapshots[self.snapshot.recommendation_id]['recommendation_at'];self.repo.path=lambda s,a:[{'bar_revision_id':UUID(int=500),'manifest_id':UUID(int=501),'observed_at':base+timedelta(minutes=5),'available_at':base+timedelta(minutes=5),'open_price':Decimal(10),'high_price':Decimal('10.2'),'low_price':Decimal(9),'close_price':Decimal('9.2')}]
        self.service.materialize(self.snapshot.recommendation_id,self.now,self.policy);outcome=self.repo.validations[-1][2];self.assertEqual(outcome['first_touch'],'STOP');self.assertEqual(outcome['failure_classification'],'MARKET_FAILURE')
    def test_ambiguous_bar_and_missing_path_do_not_fabricate_result(self):
        base=self.repo.snapshots[self.snapshot.recommendation_id]['recommendation_at'];self.repo.path=lambda s,a:[{'bar_revision_id':UUID(int=600),'manifest_id':UUID(int=601),'observed_at':base+timedelta(minutes=5),'available_at':base+timedelta(minutes=5),'open_price':Decimal(10),'high_price':Decimal(12),'low_price':Decimal(9),'close_price':Decimal(10)}]
        self.service.materialize(self.snapshot.recommendation_id,self.now,self.policy);outcome=self.repo.validations[-1][2];self.assertEqual(outcome['state'],'INSUFFICIENT_PATH');self.assertIsNone(outcome['net_return_pct'])
        self.repo.path=lambda s,a:[];self.service.materialize(self.snapshot.recommendation_id,self.now,self.policy);self.assertEqual(self.repo.validations[-1][2]['state'],'INSUFFICIENT_PATH')
    def test_unfilled_and_unresolved_are_distinct(self):
        base=self.repo.snapshots[self.snapshot.recommendation_id]['recommendation_at'];bar={'bar_revision_id':UUID(int=700),'manifest_id':UUID(int=701),'observed_at':base+timedelta(minutes=5),'available_at':base+timedelta(minutes=5),'open_price':Decimal(20),'high_price':Decimal(21),'low_price':Decimal(19),'close_price':Decimal(20)};self.repo.path=lambda s,a:[bar]
        self.service.materialize(self.snapshot.recommendation_id,base+timedelta(minutes=10),self.policy);self.assertEqual(self.repo.validations[-1][2]['state'],'UNRESOLVED')
        self.service.materialize(self.snapshot.recommendation_id,self.now,self.policy);self.assertEqual(self.repo.validations[-1][2]['state'],'UNFILLED')
    def test_expired_recommendation_remains_unfilled_without_fabrication(self):
        snapshot=self.repo.snapshots[self.snapshot.recommendation_id];snapshot['expiry']=(self.now-timedelta(days=1)).date();base=snapshot['recommendation_at'];self.repo.path=lambda s,a:[{'bar_revision_id':UUID(int=710),'manifest_id':UUID(int=711),'observed_at':base+timedelta(minutes=5),'available_at':base+timedelta(minutes=5),'open_price':Decimal(20),'high_price':Decimal(21),'low_price':Decimal(19),'close_price':Decimal(20)}]
        self.service.materialize(self.snapshot.recommendation_id,self.now,self.policy);outcome=self.repo.validations[-1][2];self.assertEqual(outcome['state'],'EXPIRED');self.assertIsNone(outcome['net_return_pct'])
    def test_explicit_user_fill_is_immutable_input_not_execution(self):
        fill_id=self.service.record_user_fill(self.snapshot.recommendation_id,self.now-timedelta(hours=1),Decimal('10.05'),'USER_JOURNAL:1');self.assertEqual(fill_id,self.service.record_user_fill(self.snapshot.recommendation_id,self.now-timedelta(hours=1),Decimal('10.05'),'USER_JOURNAL:1'));self.assertEqual(self.repo.user['fill_type'],'USER_RECORDED')
        self.service.materialize(self.snapshot.recommendation_id,self.now,self.policy);self.assertEqual(self.repo.validations[-1][2]['fill_id'],fill_id);self.assertIsNone(self.repo.validations[-1][1])
    def records(self,count=3):
        row=self.repo.snapshots[self.snapshot.recommendation_id]
        return [{**row,'outcome_state':'FILLED','terminal_reason':'TARGET' if i%2 else 'STOP','mfe_pct':Decimal(5),'mae_pct':Decimal(-2),'net_return_pct':Decimal(2 if i%2 else -1),'failure_classification':'UNCLASSIFIED','fill_quality':Decimal('.99'),'slippage_pct':Decimal('.1')} for i in range(count)]
    def test_rolling_metrics_minimums_brier_calibration_and_segments(self):
        records=self.records();run,metrics=self.service.compute_metrics(records,self.policy,self.now,self.now-timedelta(days=30),self.now);self.assertIsNotNone(metrics['brier_score']);self.assertIsNotNone(metrics['calibration_error']);self.assertIsNotNone(metrics['interval_coverage']);self.assertTrue(any(x['segment_type']=='STRATEGY' for x in self.repo.metric_saved[2]));self.assertEqual(run,self.repo.metric_saved[1]['run_id'])
        self.assertIsNone(self.service._metrics(records[:2],self.policy)['win_rate'])
    def test_drift_states_and_suspension_require_60_sessions(self):
        insufficient=self.service.evaluate_drift({'calibration':'.5'},{'calibration':'0'},59,self.policy,self.now);self.assertEqual(insufficient.state,'INSUFFICIENT_EVIDENCE');self.assertIsNone(self.repo.drift_saved[2])
        suspended=self.service.evaluate_drift({'calibration':'.5','feature':'.4','population':'.35'},{'calibration':'0','feature':'0','population':'0'},60,self.policy,self.now);self.assertTrue(suspended.suspended);self.assertEqual(self.repo.drift_saved[2]['state'],'SUSPENDED');self.assertIn('feature',self.repo.drift_saved[1]['reasons']);self.assertFalse(self.repo.snapshots[self.snapshot.recommendation_id]['operationally_trusted'])
        healthy=self.service.evaluate_drift({'calibration':'.01'},{'calibration':'0'},60,self.policy,self.now);self.assertEqual(healthy.state,'HEALTHY')
    def test_no_execution_or_self_learning_surface(self):
        import inspect
        source=inspect.getsource(LiveValidationService);self.assertNotIn('dhan',source.lower());self.assertNotIn('order(',source.lower());self.assertNotIn('retrain',source.lower());self.assertNotIn('UPDATE ',source)


if __name__=='__main__':unittest.main()
