import argparse
from datetime import date,datetime,timedelta
from decimal import Decimal
from uuid import UUID

from services.live_validation_models import LiveValidationPolicy
from services.live_validation_service import LiveValidationService


class FixtureRepository:
    def __init__(self):self.snapshots={};self.validations=[];self.policies=[]
    def recommendation_source(self,evaluation_id):
        return {'evaluation_id':evaluation_id,'candidate_id':UUID(int=2),'calibration_run_id':UUID(int=3),'run_id':UUID(int=4),'similarity_run_id':UUID(int=5),'query_vector_id':UUID(int=6),'instrument_id':UUID(int=7),'instrument_revision_id':UUID(int=8),'expiry':date(2026,7,30),'strike':Decimal(100),'option_type':'CE','strategy_code':'OPTION_PATH','direction':'LONG_CALL','holding_horizon':'SESSION','entry_zone_low':Decimal(10),'entry_zone_high':Decimal('10.1'),'stop_price':Decimal(9),'target_prices':[Decimal(11),Decimal(12)],'calibrated_win_probability':Decimal('.6'),'conservative_expected_value':Decimal('.2'),'win_probability_low':Decimal('.45'),'win_probability_high':Decimal('.72'),'uncertainty_tier':'HIGH','effective_sample_size':Decimal(8),'reasons_for':['fixture'],'reasons_against':[],'evaluation_state':'ELIGIBLE','evaluation_reasons':[],'dataset_checksum':'a'*64,'feature_version':'fixture-feature-v2','outcome_model_version':'fixture-outcome-v2','similarity_model_version':'fixture-similarity-v2','opportunity_policy_version':'fixture-opportunity-v2','calibration_policy_version':'fixture-calibration-v2','feature_contributions':{'regime':'FIXTURE'},'feature_lineage_checksum':'b'*64,'similarity_lineage_checksum':'c'*64,'contract_lineage_checksum':'d'*64,'lineage_checksum':'e'*64,'evaluated_at':datetime(2026,7,16,9,15)}
    def persist_snapshot(self,policy,row):self.snapshots[row['recommendation_id']]=row;self.policies.append(policy)
    def snapshot(self,recommendation_id):return self.snapshots.get(recommendation_id)
    def path(self,snapshot,as_of):
        base=snapshot['recommendation_at']
        return [{'bar_revision_id':UUID(int=100+i),'manifest_id':UUID(int=200+i),'bar_open_at':base+timedelta(minutes=5*i),'observed_at':base+timedelta(minutes=5*(i+1)),'available_at':base+timedelta(minutes=5*(i+1)),'open_price':Decimal('10.1'),'high_price':Decimal('10.5') if i==0 else Decimal('11.2'),'low_price':Decimal('10.0'),'close_price':Decimal('10.3') if i==0 else Decimal('11.1')} for i in range(2)]
    def user_fill(self,recommendation_id,as_of):return None
    def persist_validation(self,observations,fill,outcome,classification):self.validations.append((observations,fill,outcome,classification))


def main():
    parser=argparse.ArgumentParser(description='Materialize shadow-only recommendation validation.')
    parser.add_argument('--recommendation-id',type=UUID);parser.add_argument('--fixture',action='store_true');args=parser.parse_args()
    if not args.fixture and args.recommendation_id is None:parser.error('--recommendation-id is required unless --fixture is used')
    policy=LiveValidationPolicy('live-validation-v1');clock=lambda:datetime(2026,7,16,16)
    if args.fixture:
        repository=FixtureRepository();service=LiveValidationService(repository,clock);snap=service.snapshot(UUID(int=1),policy);result=service.materialize(snap.recommendation_id,datetime(2026,7,16,16),policy)
    else:
        service=LiveValidationService();recommendation_id=args.recommendation_id
        if service.repository.snapshot(recommendation_id) is None:recommendation_id=service.snapshot(recommendation_id,policy).recommendation_id
        result=service.materialize(recommendation_id,datetime.now(),policy)
    print(f'Live validation materialized | recommendation={result.recommendation_id} outcome={result.outcome_id} state={result.state} shadow=true trusted=false execution=false')
    return 0


if __name__=='__main__':raise SystemExit(main())
