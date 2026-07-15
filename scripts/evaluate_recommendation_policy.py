import argparse
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from scripts.materialize_calibration_v2 import FixtureRepository,default_policy
from services.calibration_v2_service import CalibrationV2Service


class EvaluationFixtureRepository(FixtureRepository):
    def __init__(self):super().__init__();self.evaluations=[]
    def calibration(self,run_id):
        if not self.saved:return None
        run=dict(self.saved['run']);run['bins']=self.saved['bins'];return run
    def candidate(self,candidate_id):
        return {'candidate_id':candidate_id,'state':'PROVISIONAL','historical_win_rate':Decimal('.8'),'effective_sample_size':Decimal(8),'evidence_quality':Decimal('.95'),'concentration_metrics':{'symbol':Decimal('.25'),'expiry':Decimal('.25'),'regime':Decimal('.5'),'episode':Decimal('.125')},'fill_metrics':{}}
    def release_ready(self):return True
    def persist_evaluation(self,e):self.evaluations.append(e)


def main():
    parser=argparse.ArgumentParser(description='Evaluate a provisional candidate without creating a recommendation.')
    parser.add_argument('--candidate-id',type=UUID);parser.add_argument('--calibration-run-id',type=UUID);parser.add_argument('--policy-id',type=UUID);parser.add_argument('--fixture',action='store_true')
    args=parser.parse_args()
    if not args.fixture and (args.candidate_id is None or args.calibration_run_id is None):parser.error('--candidate-id and --calibration-run-id are required unless --fixture is used')
    policy=default_policy(args.policy_id or UUID(int=29))
    if args.fixture:
        repository=EvaluationFixtureRepository();service=CalibrationV2Service(repository,clock=lambda:datetime(2026,7,16));calibration=service.materialize(policy,datetime(2026,7,16));candidate_id=UUID(int=30);run_id=calibration.run_id
    else:service=CalibrationV2Service();candidate_id=args.candidate_id;run_id=args.calibration_run_id
    result=service.evaluate(candidate_id,run_id,policy)
    print(f'Recommendation policy evaluated | evaluation={result.evaluation_id} state={result.state} eligible={str(result.eligible).lower()} trusted=false recommendation=false')
    return 0


if __name__=='__main__':raise SystemExit(main())
