from dataclasses import asdict
from datetime import timedelta
from decimal import Decimal
import hashlib,json,math,random
from uuid import UUID,uuid5
from services.calibration_v2_models import CalibrationResultV2,RecommendationResultV2
from services.calibration_v2_repository import CalibrationV2Repository

class CalibrationV2Service:
 NAMESPACE=UUID('bbef8df6-d83c-481c-bf32-c9ae24ae9b78')
 def __init__(self,repository=None,clock=None):
  from datetime import datetime
  self.repository=repository or CalibrationV2Repository();self.clock=clock or datetime.now
 def materialize(self,policy,cutoff):
  raw=self.repository.observations(policy,cutoff);periods={p.name:p for p in policy.periods};lineage=[];fit=[];test=[]
  for r in raw:
   period=next((p for p in policy.periods if p.start<=r['observed_at'].date()<=p.end),None);reason=None
   if period is None:reason='OUTSIDE_PERIOD'
   elif r['terminal_at'].date()>period.end:reason='OUTCOME_AFTER_PERIOD'
   elif r['observed_at'].date()<period.start+timedelta(days=policy.embargo_days) or r['observed_at'].date()>period.end-timedelta(days=policy.purge_days):reason='PURGE_OR_EMBARGO'
   elif r['raw_score'] is None or r['realized_return'] is None:reason='UNRESOLVED_OR_UNSUPPORTED'
   if reason is None and period.name not in {'CALIBRATION','TEST'}:reason='NON_CALIBRATION_PARTITION'
   included=reason is None and period.name in {'CALIBRATION','TEST'}
   lineage.append({'candidate_id':r['candidate_id'],'outcome_id':r['outcome_id'],'period_name':period.name if period else 'NONE','included':included,'exclusion_reason':reason,'observed_at':r['observed_at'],'terminal_at':r['terminal_at']})
   if included:(fit if period.name=='CALIBRATION' else test).append(r)
  dataset_checksum=self._hash([(str(x['candidate_id']),str(x['outcome_id']),x['period_name'],x['included']) for x in lineage]);doc=json.loads(json.dumps(asdict(policy),default=str));policy_checksum=self._hash(doc);run_id=uuid5(self.NAMESPACE,f"{policy.policy_id}:{cutoff.isoformat()}:{dataset_checksum}")
  ess=self._ess(fit);state='CALIBRATED' if len(fit)>=policy.minimum_sample_size and ess>=policy.minimum_effective_sample_size else 'INSUFFICIENT_EVIDENCE';bins=self._bins(fit,policy) if state=='CALIBRATED' else []
  calibrated=[(self._predict(Decimal(r['raw_score']),bins),Decimal(1 if Decimal(r['realized_return'])>0 else 0),Decimal(r['realized_return'])) for r in fit] if bins else []
  test_values=[(self._predict(Decimal(r['raw_score']),bins),Decimal(1 if Decimal(r['realized_return'])>0 else 0),Decimal(r['realized_return'])) for r in test] if bins else []
  metrics=self._metrics(calibrated,bins,fit,policy,test_values);now=self.clock();run={'run_id':run_id,'policy_id':policy.policy_id,'cutoff_at':cutoff,'dataset_checksum':dataset_checksum,'state':state,'calibration_sample_size':len(fit),'effective_sample_size':ess,**metrics,'lineage_checksum':self._hash(lineage),'started_at':now,'completed_at':self.clock()}
  self.repository.persist_calibration({'policy_id':policy.policy_id,'policy_version':policy.policy_version,'policy_checksum':policy_checksum,'strategy':policy.strategy,'direction':policy.direction,'holding_horizon':policy.holding_horizon,'policy':doc,'started_at':now,'run':run,'bins':[{'run_id':run_id,**b} for b in bins],'lineage':[{'run_id':run_id,**x} for x in lineage]})
  return CalibrationResultV2(run_id,state,len(fit))
 def evaluate(self,candidate_id,calibration_run_id,policy):
  c=self.repository.candidate(candidate_id);cal=self.repository.calibration(calibration_run_id);evaluation_id=uuid5(self.NAMESPACE,f"evaluation:{candidate_id}:{calibration_run_id}:{policy.policy_id}");state='UNCALIBRATED';prob=low=high=conservative=None;gates={}
  if c is None:raise ValueError('Opportunity candidate was not found.')
  if cal and cal['state']=='CALIBRATED' and c['historical_win_rate'] is not None:
   prob=self._predict(Decimal(c['historical_win_rate']),cal['bins']);low,high=self._wilson(prob,int(cal['calibration_sample_size']));conservative=cal['expected_value_low'];width=high-low if low is not None else None
   fill=c.get('fill_metrics') or {}; concentration=c.get('concentration_metrics') or {}
   gates={'sample':cal['calibration_sample_size']>=policy.minimum_sample_size,'ess':Decimal(cal['effective_sample_size'])>=policy.minimum_effective_sample_size,'calibration':cal['expected_calibration_error'] is not None and Decimal(cal['expected_calibration_error'])<=policy.calibration_error_threshold,'uncertainty':width is not None and width<=policy.uncertainty_threshold,'ev':conservative is not None and Decimal(conservative)>policy.conservative_ev_threshold,'concentration':bool(concentration) and max(Decimal(x) for x in concentration.values())<=policy.concentration_threshold,'ood':c['state']!='OUT_OF_DISTRIBUTION' and Decimal(str(fill.get('ood_score',0)))<=policy.out_of_distribution_threshold,'quality':Decimal(c['evidence_quality'])>=policy.minimum_data_quality and not bool(fill.get('data_quality_issue',False)),'drift':Decimal(str(fill.get('drift',0)))<=policy.maximum_drift,'liquidity':c['state']!='ILLIQUID' and not bool(fill.get('liquidity_rejected',False)),'release':self.repository.release_ready(),'provisional':c['state']=='PROVISIONAL'}
   failed=next((k for k,v in gates.items() if not v),None);state='ELIGIBLE' if failed is None else {'sample':'INSUFFICIENT_EVIDENCE','ess':'INSUFFICIENT_EVIDENCE','calibration':'UNCALIBRATED','uncertainty':'UNCERTAIN','ev':'NEGATIVE_CONSERVATIVE_EV','concentration':'CONCENTRATED_EVIDENCE','ood':'OUT_OF_DISTRIBUTION','quality':'DATA_QUALITY_FAILURE','drift':'DRIFT_SUSPENDED','liquidity':'ILLIQUID','release':'INELIGIBLE','provisional':'INELIGIBLE'}[failed]
  eligible=state=='ELIGIBLE';e={'evaluation_id':evaluation_id,'policy_id':policy.policy_id,'calibration_run_id':calibration_run_id if cal else None,'candidate_id':candidate_id,'state':state,'eligible':eligible,'calibrated_win_probability':prob if cal else None,'win_probability_low':low,'win_probability_high':high,'conservative_expected_value':conservative,'uncertainty_tier':('LOW' if eligible else 'HIGH') if low is not None else None,'effective_sample_size':Decimal(cal['effective_sample_size']) if cal else 0,'calibration_sample_size':int(cal['calibration_sample_size']) if cal else 0,'gates':gates,'reasons':[] if eligible else [state],'dataset_lineage_checksum':cal['dataset_checksum'] if cal else None,'lineage_checksum':self._hash({'candidate':str(candidate_id),'run':str(calibration_run_id),'state':state}),'evaluated_at':self.clock()};self.repository.persist_evaluation(e);return RecommendationResultV2(evaluation_id,state,eligible)
 def _bins(self,rows,p):
  buckets=[[] for _ in range(p.bin_count)]
  for r in rows:buckets[min(p.bin_count-1,int(Decimal(r['raw_score'])*p.bin_count))].append(r)
  result=[];last=Decimal(0)
  for i,b in enumerate(buckets):
   observed=sum((Decimal(1 if Decimal(x['realized_return'])>0 else 0) for x in b),Decimal(0))/len(b) if b else None;cal=max(last,observed) if observed is not None and p.method=='MONOTONIC_BINNING' else observed
   if cal is not None:last=cal
   result.append({'bin_number':i+1,'prediction_low':Decimal(i)/p.bin_count,'prediction_high':Decimal(i+1)/p.bin_count,'sample_count':len(b),'mean_uncalibrated_score':sum((Decimal(x['raw_score']) for x in b),Decimal(0))/len(b) if b else None,'calibrated_probability':cal,'observed_win_rate':observed})
  return result
 def _metrics(self,vals,bins,rows,p,test_values=()):
  if not vals:return {k:None for k in ('brier_score','log_loss','expected_calibration_error','maximum_calibration_error','confidence_interval_coverage','abstention_rate','recommendation_coverage','net_expected_value','realized_outcome_rate','return_prediction_low','return_prediction_high','expected_value_low','expected_value_high')}
  n=Decimal(len(vals));eps=Decimal('0.000001');errors=[abs(Decimal(b['calibrated_probability'])-Decimal(b['observed_win_rate'])) for b in bins if b['sample_count']]
  returns=[v[2] for v in vals];boot=self._bootstrap(returns,p.bootstrap_samples,p.seed)
  coverage=None
  if test_values:
   covered=0
   for probability,actual,_ in test_values:
    low,high=self._wilson(probability,len(vals));covered+=int(low<=actual<=high)
   coverage=Decimal(covered)/len(test_values)
  return {'brier_score':sum(((x-y)**2 for x,y,_ in vals),Decimal(0))/n,'log_loss':sum((-(y*Decimal(str(math.log(float(max(eps,min(1-eps,x))))))+(1-y)*Decimal(str(math.log(float(max(eps,min(1-eps,1-x))))))) for x,y,_ in vals),Decimal(0))/n,'expected_calibration_error':sum((e*Decimal(b['sample_count'])/n for e,b in zip(errors,[b for b in bins if b['sample_count']])),Decimal(0)),'maximum_calibration_error':max(errors),'confidence_interval_coverage':coverage,'abstention_rate':None,'recommendation_coverage':None,'net_expected_value':sum(returns,Decimal(0))/n,'realized_outcome_rate':sum((y for _,y,_ in vals),Decimal(0))/n,'return_prediction_low':self._q(returns,Decimal('.05')),'return_prediction_high':self._q(returns,Decimal('.95')),'expected_value_low':boot[0],'expected_value_high':boot[1]}
 @staticmethod
 def _predict(s,bins):
  for b in bins:
   if s<=Decimal(b['prediction_high']) and b['calibrated_probability'] is not None:return Decimal(b['calibrated_probability'])
  return Decimal(bins[-1]['calibrated_probability']) if bins else None
 @staticmethod
 def _wilson(prob,n):
  if n<1:return None,None
  z=Decimal('1.96');den=1+z*z/n;center=(prob+z*z/(2*n))/den;half=z*((prob*(1-prob)/n+z*z/(4*n*n)).sqrt())/den;return max(Decimal(0),center-half),min(Decimal(1),center+half)
 @staticmethod
 def _bootstrap(v,count,seed):
  if len(v)<2:return None,None
  rng=random.Random(seed);means=[sum((rng.choice(v) for _ in v),Decimal(0))/len(v) for _ in range(count)];return CalibrationV2Service._q(means,Decimal('.05')),CalibrationV2Service._q(means,Decimal('.95'))
 @staticmethod
 def _q(v,q):o=sorted(v);return o[int((len(o)-1)*q)] if o else None
 @staticmethod
 def _ess(r):
  w=[Decimal(x['evidence_weight']) for x in r];return sum(w,Decimal(0))**2/sum((x*x for x in w),Decimal(0)) if w and sum((x*x for x in w),Decimal(0)) else Decimal(0)
 @staticmethod
 def _hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
