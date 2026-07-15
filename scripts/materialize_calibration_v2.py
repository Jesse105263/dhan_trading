import argparse
from datetime import date,datetime,timedelta
from decimal import Decimal
from uuid import UUID

from services.calibration_v2_models import CalibrationPeriod,CalibrationPolicyV2
from services.calibration_v2_service import CalibrationV2Service


def default_policy(policy_id):
    return CalibrationPolicyV2(policy_id,'calibration-v2.1','OPTION_PATH','LONG_CALL','SESSION','ALL','ALL','ALL',(
        CalibrationPeriod('TRAIN',date(2020,1,1),date(2023,12,31)),
        CalibrationPeriod('VALIDATION',date(2024,1,1),date(2024,12,31)),
        CalibrationPeriod('CALIBRATION',date(2025,1,1),date(2025,6,30)),
        CalibrationPeriod('TEST',date(2025,7,1),date(2026,12,31))))


class FixtureRepository:
    def __init__(self):self.saved=None
    def observations(self,policy,cutoff):
        base=datetime(2025,3,1)
        return [{'candidate_id':UUID(int=100+i),'outcome_id':UUID(int=200+i),'observed_at':base+timedelta(days=i),'terminal_at':base+timedelta(days=i+1),'raw_score':Decimal('.6'),'realized_return':Decimal(1 if i%2 else -1),'evidence_weight':Decimal(1)} for i in range(8)]
    def persist_calibration(self,prepared):self.saved=prepared


def main():
    parser=argparse.ArgumentParser(description='Materialize leakage-safe Calibration V2 evidence.')
    parser.add_argument('--policy-id',type=UUID);parser.add_argument('--fixture',action='store_true')
    args=parser.parse_args()
    if args.policy_id is None and not args.fixture:parser.error('--policy-id is required unless --fixture is used')
    policy_id=args.policy_id or UUID(int=29);service=CalibrationV2Service(FixtureRepository(),clock=lambda:datetime(2026,7,16)) if args.fixture else CalibrationV2Service()
    result=service.materialize(default_policy(policy_id),datetime(2026,7,16))
    print(f'Calibration V2 materialized | run={result.run_id} state={result.state} sample={result.sample_size} trusted=false')
    return 0


if __name__=='__main__':raise SystemExit(main())
