import unittest
from datetime import date,datetime,timedelta
from decimal import Decimal
from uuid import UUID

from services.calibration_v2_models import CalibrationPeriod,CalibrationPolicyV2
from services.calibration_v2_service import CalibrationV2Service


class Repo:
    def __init__(self,rows=None):self.rows=rows or [];self.saved=None;self.evaluations=[];self.ready=True;self.candidate_row={'candidate_id':UUID(int=30),'state':'PROVISIONAL','historical_win_rate':Decimal('.6'),'effective_sample_size':Decimal(50),'evidence_quality':Decimal('.95'),'concentration_metrics':{'symbol':Decimal('.25'),'expiry':Decimal('.25'),'regime':Decimal('.25'),'episode':Decimal('.25')},'fill_metrics':{}}
    def observations(self,p,c):return self.rows
    def persist_calibration(self,p):self.saved=p
    def calibration(self,run_id):
        if not self.saved:return None
        return {**self.saved['run'],'bins':self.saved['bins']}
    def candidate(self,candidate_id):
        return dict(self.candidate_row)
    def release_ready(self):return self.ready
    def persist_evaluation(self,e):self.evaluations.append(e)


def policy(**changes):
    values=dict(policy_id=UUID(int=1),policy_version='test-v1',strategy='OPTION_PATH',direction='LONG_CALL',holding_horizon='SESSION',liquidity_regime='ALL',volatility_regime='ALL',market_regime='ALL',periods=(CalibrationPeriod('TRAIN',date(2020,1,1),date(2023,12,31)),CalibrationPeriod('VALIDATION',date(2024,1,1),date(2024,12,31)),CalibrationPeriod('CALIBRATION',date(2025,1,1),date(2025,6,30)),CalibrationPeriod('TEST',date(2025,7,1),date(2025,12,31))),purge_days=0,embargo_days=0,minimum_sample_size=30,minimum_effective_sample_size=Decimal(30),uncertainty_threshold=Decimal('.30'))
    values.update(changes);return CalibrationPolicyV2(**values)


def rows(count=50):
    base=datetime(2025,2,1)
    return [{'candidate_id':UUID(int=100+i),'outcome_id':UUID(int=1000+i),'observed_at':base+timedelta(days=i),'terminal_at':base+timedelta(days=i,hours=1),'raw_score':Decimal('.6'),'realized_return':Decimal(2 if i%5<3 else -1),'evidence_weight':Decimal(1)} for i in range(count)]


class CalibrationV2Test(unittest.TestCase):
    def setUp(self):self.repo=Repo(rows());self.service=CalibrationV2Service(self.repo,clock=lambda:datetime(2026,7,16));self.policy=policy()
    def materialize(self):return self.service.materialize(self.policy,datetime(2026,7,16))
    def test_deterministic_empirical_calibration_metrics_and_lineage(self):
        a=self.materialize();b=self.materialize();self.assertEqual(a.run_id,b.run_id);self.assertEqual(a.state,'CALIBRATED')
        run=self.repo.saved['run'];self.assertEqual(run['brier_score'],Decimal('.24'));self.assertEqual(run['expected_calibration_error'],0);self.assertIsNotNone(run['log_loss']);self.assertEqual(len(run['lineage_checksum']),64)
    def test_monotonic_and_empirical_bins_are_dependency_free(self):
        empirical=self.service._bins(rows(),policy(method='EMPIRICAL_BINNING'));monotonic=self.service._bins(rows(),policy(method='MONOTONIC_BINNING'))
        self.assertEqual(empirical[3]['observed_win_rate'],Decimal('.6'));self.assertEqual(monotonic[3]['calibrated_probability'],Decimal('.6'))
    def test_periods_purge_embargo_and_future_terminal_are_excluded(self):
        self.repo.rows=[{'candidate_id':UUID(int=i),'outcome_id':UUID(int=10+i),'observed_at':datetime(2025,1,2),'terminal_at':datetime(2025,7,1) if i==1 else datetime(2025,1,3),'raw_score':Decimal('.5'),'realized_return':Decimal(1),'evidence_weight':Decimal(1)} for i in (1,2)]
        self.service.materialize(policy(purge_days=45,embargo_days=7),datetime(2026,7,16));reasons={x['exclusion_reason'] for x in self.repo.saved['lineage']};self.assertIn('OUTCOME_AFTER_PERIOD',reasons);self.assertIn('PURGE_OR_EMBARGO',reasons)
    def test_train_validation_and_test_never_fit_calibrator(self):
        self.repo.rows=rows(2)+[{**rows(1)[0],'candidate_id':UUID(int=900),'outcome_id':UUID(int=901),'observed_at':datetime(2024,6,1),'terminal_at':datetime(2024,6,2)},{**rows(1)[0],'candidate_id':UUID(int=902),'outcome_id':UUID(int=903),'observed_at':datetime(2025,8,1),'terminal_at':datetime(2025,8,2)}]
        result=self.materialize();self.assertEqual(result.sample_size,2);lineage=self.repo.saved['lineage'];self.assertEqual(next(x for x in lineage if x['period_name']=='VALIDATION')['exclusion_reason'],'NON_CALIBRATION_PARTITION')
    def test_insufficient_sample_has_no_fabricated_metrics_or_bins(self):
        self.repo.rows=rows(2);result=self.materialize();self.assertEqual(result.state,'INSUFFICIENT_EVIDENCE');self.assertEqual(self.repo.saved['bins'],[]);self.assertIsNone(self.repo.saved['run']['brier_score'])
    def test_wilson_and_bootstrap_are_bounded_and_deterministic(self):
        low,high=self.service._wilson(Decimal('.6'),50);self.assertLess(low,Decimal('.6'));self.assertGreater(high,Decimal('.6'))
        values=[Decimal(-1),Decimal(2),Decimal(2)];self.assertEqual(self.service._bootstrap(values,100,37),self.service._bootstrap(values,100,37))
    def test_all_gates_can_make_candidate_eligible_without_trust_flag(self):
        calibration=self.materialize();result=self.service.evaluate(UUID(int=30),calibration.run_id,self.policy);self.assertTrue(result.eligible);self.assertEqual(result.state,'ELIGIBLE');self.assertNotIn('trusted',self.repo.evaluations[-1])
    def test_specific_abstention_states_fail_closed(self):
        calibration=self.materialize();cases=(('concentration_metrics',{'symbol':Decimal('.9')},'CONCENTRATED_EVIDENCE'),('state','OUT_OF_DISTRIBUTION','OUT_OF_DISTRIBUTION'),('state','ILLIQUID','ILLIQUID'),('evidence_quality',Decimal('.1'),'DATA_QUALITY_FAILURE'))
        for key,value,state in cases:
            candidate=Repo().candidate(UUID(int=30));candidate[key]=value;self.repo.candidate=lambda unused,candidate=candidate:candidate
            self.assertEqual(self.service.evaluate(UUID(int=30),calibration.run_id,self.policy).state,state)
    def test_drift_release_and_negative_ev_suspend_eligibility(self):
        calibration=self.materialize();candidate=self.repo.candidate(UUID(int=30));candidate['fill_metrics']={'drift':'.2'};self.repo.candidate=lambda unused:candidate
        self.assertEqual(self.service.evaluate(UUID(int=30),calibration.run_id,self.policy).state,'DRIFT_SUSPENDED')
        self.repo.candidate=lambda unused:{**candidate,'fill_metrics':{}};self.repo.ready=False;self.assertEqual(self.service.evaluate(UUID(int=30),calibration.run_id,self.policy).state,'INELIGIBLE')
        self.repo.ready=True;self.repo.saved['run']['expected_value_low']=Decimal('-1');self.assertEqual(self.service.evaluate(UUID(int=30),calibration.run_id,self.policy).state,'NEGATIVE_CONSERVATIVE_EV')
    def test_uncalibrated_candidate_never_becomes_recommendation(self):
        self.repo.rows=rows(2);calibration=self.materialize();result=self.service.evaluate(UUID(int=30),calibration.run_id,self.policy);self.assertFalse(result.eligible);self.assertEqual(result.state,'UNCALIBRATED')


if __name__=='__main__':unittest.main()
