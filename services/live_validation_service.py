from dataclasses import asdict
from datetime import timedelta
from decimal import Decimal
import hashlib,json,math
from uuid import UUID,uuid5

from services.live_validation_models import DriftResult,ValidationResult
from services.live_validation_repository import LiveValidationRepository


class LiveValidationService:
    NAMESPACE=UUID('723395fd-6119-45df-b42b-5a17c9c50f38')
    def __init__(self,repository=None,clock=None):
        from datetime import datetime
        self.repository=repository or LiveValidationRepository();self.clock=clock or datetime.now

    def snapshot(self,evaluation_id,policy):
        source=self.repository.recommendation_source(evaluation_id)
        if source is None:raise ValueError('Recommendation-policy evaluation was not found.')
        recommendation_id=uuid5(self.NAMESPACE,f"recommendation:{evaluation_id}");now=self.clock()
        evaluation_state=source.get('evaluation_state',source.get('state'));validation_state='ELIGIBLE' if evaluation_state=='ELIGIBLE' else ('REJECTED' if evaluation_state in {'INELIGIBLE','ILLIQUID','NEGATIVE_CONSERVATIVE_EV','DATA_QUALITY_FAILURE','DRIFT_SUSPENDED'} else 'ABSTAINED')
        lineage={'evaluation_id':source['evaluation_id'],'candidate_id':source['candidate_id'],'calibration_run_id':source['calibration_run_id'],'opportunity_run_id':source['run_id'],'similarity_run_id':source['similarity_run_id'],'query_vector_id':source['query_vector_id'],'instrument_revision_id':source['instrument_revision_id'],'feature_lineage_checksum':source['feature_lineage_checksum'],'similarity_lineage_checksum':source['similarity_lineage_checksum'],'contract_lineage_checksum':source['contract_lineage_checksum'],'opportunity_lineage_checksum':source['lineage_checksum'],'calibration_dataset_checksum':source['dataset_checksum']}
        evaluation_reasons=source.get('evaluation_reasons',source.get('reasons',[]));row={'recommendation_id':recommendation_id,'evaluation_id':evaluation_id,'candidate_id':source['candidate_id'],'recommendation_at':source['evaluated_at'],'instrument_id':source['instrument_id'],'instrument_revision_id':source['instrument_revision_id'],'expiry':source['expiry'],'strike':source['strike'],'option_type':source['option_type'],'strategy_code':source['strategy_code'],'direction':source['direction'],'holding_horizon':source['holding_horizon'],'market_regime':str((source.get('feature_contributions') or {}).get('regime','UNKNOWN')),'liquidity_tier':'REJECTED' if evaluation_state=='ILLIQUID' else 'SUPPORTED','entry_zone_low':source['entry_zone_low'],'entry_zone_high':source['entry_zone_high'],'stop_price':source['stop_price'],'target_prices':source['target_prices'],'predicted_win_probability':source['calibrated_win_probability'],'predicted_expected_value':source['conservative_expected_value'],'prediction_low':source['win_probability_low'],'prediction_high':source['win_probability_high'],'evidence_quality_tier':source['uncertainty_tier'],'effective_sample_size':source.get('evaluation_effective_sample_size',source['effective_sample_size']),'reasons_for':source['reasons_for'],'reasons_against':source['reasons_against'],'feature_contributions':source['feature_contributions'],'eligibility_state':evaluation_state,'recommendation_policy_reason':','.join(evaluation_reasons) if evaluation_reasons else 'ALL_GATES_PASSED','dataset_version':source['dataset_checksum'],'feature_version':source['feature_version'],'outcome_model_version':source['outcome_model_version'],'similarity_model_version':source['similarity_model_version'],'opportunity_policy_version':source['opportunity_policy_version'],'calibration_policy_version':source['calibration_policy_version'],'validation_state':validation_state,'operationally_trusted':False,'lineage':lineage,'lineage_checksum':self._hash(lineage),'snapshotted_at':now}
        self.repository.persist_snapshot(self._policy(policy),row);return ValidationResult(recommendation_id,None,validation_state)

    def materialize(self,recommendation_id,as_of,policy):
        snapshot=self.repository.snapshot(recommendation_id)
        if snapshot is None:raise ValueError('Recommendation snapshot was not found.')
        path=self.repository.path(snapshot,as_of);observations=[{'observation_id':uuid5(self.NAMESPACE,f"observation:{recommendation_id}:{b['bar_revision_id']}"),'recommendation_id':recommendation_id,'bar_revision_id':b['bar_revision_id'],'manifest_id':b['manifest_id'],'observed_at':b['observed_at'],'available_at':b['available_at'],'open_price':b['open_price'],'high_price':b['high_price'],'low_price':b['low_price'],'close_price':b['close_price'],'lineage_checksum':self._hash({'recommendation':str(recommendation_id),'bar':str(b['bar_revision_id'])})} for b in path]
        outcome_id=uuid5(self.NAMESPACE,f"outcome:{recommendation_id}:{as_of.isoformat()}");state='UNRESOLVED';fill=None;values={'entry_reached':None,'fill_id':None,'terminal_reason':None,'target_hit':None,'stop_hit':None,'first_touch':None,'terminal_at':None,'mfe_pct':None,'mae_pct':None,'realized_return_pct':None,'net_return_pct':None,'time_to_target_seconds':None,'time_to_stop_seconds':None,'time_under_water_seconds':None};classification='INSUFFICIENT_EVIDENCE'
        if snapshot['validation_state'] in {'REJECTED','ABSTAINED'}:
            state=snapshot['validation_state'];classification='LIQUIDITY_FAILURE' if snapshot['eligibility_state']=='ILLIQUID' else 'DATA_FAILURE' if snapshot['eligibility_state']=='DATA_QUALITY_FAILURE' else 'CALIBRATION_FAILURE' if snapshot['eligibility_state']=='UNCALIBRATED' else 'POLICY_REJECTION'
        elif not path:state='INSUFFICIENT_PATH';classification='DATA_FAILURE'
        else:
            entry=next((b for b in path if Decimal(b['low_price'])<=Decimal(snapshot['entry_zone_high']) and Decimal(b['high_price'])>=Decimal(snapshot['entry_zone_low'])),None)
            values['entry_reached']=entry is not None
            if entry is None:
                expired=bool(snapshot.get('expiry') and as_of.date()>snapshot['expiry']);state='EXPIRED' if expired else ('UNFILLED' if as_of-snapshot['recommendation_at']>=timedelta(seconds=policy.timeout_seconds) else 'UNRESOLVED');classification='FILL_FAILURE' if state in {'EXPIRED','UNFILLED'} else 'INSUFFICIENT_EVIDENCE'
            else:
                recorded=self.repository.user_fill(recommendation_id,as_of) if hasattr(self.repository,'user_fill') else None;fill_price=Decimal(recorded['fill_price']) if recorded else Decimal(snapshot['entry_zone_high']);fill_id=recorded['fill_id'] if recorded else uuid5(self.NAMESPACE,f"fill:{recommendation_id}:{entry['observed_at'].isoformat()}:{fill_price}");mid=(Decimal(snapshot['entry_zone_low'])+Decimal(snapshot['entry_zone_high']))/2;slippage=(fill_price-mid)/mid*100
                fill=None if recorded else {'fill_id':fill_id,'recommendation_id':recommendation_id,'fill_type':'SIMULATED','fill_at':entry['observed_at'],'fill_price':fill_price,'fill_quality':max(Decimal(0),Decimal(1)-abs(slippage)/100),'slippage_pct':slippage,'source':'SHADOW_CANONICAL_PATH','lineage_checksum':self._hash({'entry':str(entry['bar_revision_id']),'price':str(fill_price)})};values['fill_id']=fill_id
                tail=path[path.index(entry):];targets=[Decimal(x) for x in snapshot['target_prices']];stop=Decimal(snapshot['stop_price']);touch=None;ambiguous=False
                for b in tail:
                    hit_targets=[i+1 for i,t in enumerate(targets) if Decimal(b['high_price'])>=t];hit_stop=Decimal(b['low_price'])<=stop
                    if hit_targets and hit_stop:ambiguous=True;touch=b;break
                    if hit_targets or hit_stop:touch=b;values['target_hit']=max(hit_targets) if hit_targets else None;values['stop_hit']=hit_stop;values['first_touch']='TARGET' if hit_targets else 'STOP';break
                highs=[Decimal(b['high_price']) for b in tail];lows=[Decimal(b['low_price']) for b in tail];values['mfe_pct']=(max(highs)-fill_price)/fill_price*100;values['mae_pct']=(min(lows)-fill_price)/fill_price*100
                values['time_under_water_seconds']=sum(max(0,int((b['observed_at']-tail[i-1]['observed_at']).total_seconds())) for i,b in enumerate(tail) if i and Decimal(b['close_price'])<fill_price)
                if ambiguous:state='INSUFFICIENT_PATH';values['first_touch']='AMBIGUOUS';values['terminal_at']=touch['observed_at'];classification='INSUFFICIENT_EVIDENCE'
                elif touch:
                    state='FILLED';values['terminal_at']=touch['observed_at'];values['terminal_reason']=values['first_touch'];terminal=targets[values['target_hit']-1] if values['target_hit'] else stop;values['realized_return_pct']=(terminal-fill_price)/fill_price*100;values['net_return_pct']=values['realized_return_pct']-policy.cost_bps/100;seconds=int((touch['observed_at']-entry['observed_at']).total_seconds());values['time_to_target_seconds']=seconds if values['target_hit'] else None;values['time_to_stop_seconds']=seconds if values['stop_hit'] else None;classification='UNCLASSIFIED' if values['net_return_pct']>=0 else 'MARKET_FAILURE'
                elif as_of-entry['observed_at']>=timedelta(seconds=policy.timeout_seconds):
                    state='FILLED';last=tail[-1];values['terminal_reason']='TIMEOUT';values['terminal_at']=last['observed_at'];values['realized_return_pct']=(Decimal(last['close_price'])-fill_price)/fill_price*100;values['net_return_pct']=values['realized_return_pct']-policy.cost_bps/100;classification='UNCLASSIFIED' if values['net_return_pct']>=0 else 'MODEL_FAILURE'
        outcome={'outcome_id':outcome_id,'recommendation_id':recommendation_id,'as_of':as_of,'state':state,**values,'path_count':len(path),'failure_classification':classification,'lineage_checksum':self._hash({'recommendation':str(recommendation_id),'bars':[str(b['bar_revision_id']) for b in path],'state':state}),'materialized_at':self.clock()}
        failure={'classification_id':uuid5(self.NAMESPACE,f"classification:{outcome_id}"),'outcome_id':outcome_id,'recommendation_id':recommendation_id,'classification':classification,'reason':'Deterministic validation state classification; unsupported causality remains UNCLASSIFIED.','evidence':{'outcome_state':state,'terminal_reason':values['terminal_reason'],'eligibility_state':snapshot['eligibility_state']},'lineage_checksum':self._hash({'outcome':str(outcome_id),'classification':classification}),'classified_at':self.clock()}
        self.repository.persist_validation(observations,fill,outcome,failure);return ValidationResult(recommendation_id,outcome_id,state)

    def record_user_fill(self,recommendation_id,fill_at,fill_price,source_reference):
        if self.repository.snapshot(recommendation_id) is None:raise ValueError('Recommendation snapshot was not found.')
        price=Decimal(fill_price)
        if price<=0 or not source_reference:raise ValueError('An explicit positive fill and source reference are required.')
        fill_id=uuid5(self.NAMESPACE,f"user-fill:{recommendation_id}:{fill_at.isoformat()}:{price}:{source_reference}");row={'fill_id':fill_id,'recommendation_id':recommendation_id,'fill_type':'USER_RECORDED','fill_at':fill_at,'fill_price':price,'fill_quality':None,'slippage_pct':None,'source':source_reference,'lineage_checksum':self._hash({'recommendation':str(recommendation_id),'source':source_reference,'at':fill_at,'price':price})};self.repository.persist_fill(row);return fill_id

    def compute_metrics(self,records,policy,as_of,window_start,window_end):
        metrics=self._metrics(records,policy);checksum=self._hash(records);run_id=uuid5(self.NAMESPACE,f"metrics:{policy.policy_version}:{window_start}:{window_end}:{checksum}");run={'run_id':run_id,'policy_version':policy.policy_version,'as_of':as_of,'window_start':window_start,'window_end':window_end,'population_count':len(records),'metric_checksum':checksum,'created_at':self.clock()};segments=[{'run_id':run_id,'segment_type':'ALL','segment_value':'ALL','sample_size':len(records),'metrics':metrics}]
        for field,label in (('strategy_code','STRATEGY'),('instrument_id','SYMBOL'),('market_regime','REGIME'),('holding_horizon','HORIZON'),('liquidity_tier','LIQUIDITY'),('evidence_quality_tier','EVIDENCE_QUALITY'),('calibration_policy_version','RECOMMENDATION_POLICY')):
            for value in sorted({str(r.get(field)) for r in records}):
                subset=[r for r in records if str(r.get(field))==value];segments.append({'run_id':run_id,'segment_type':label,'segment_value':value,'sample_size':len(subset),'metrics':self._metrics(subset,policy)})
        self.repository.persist_metrics(self._policy(policy),run,segments);return run_id,metrics

    def evaluate_drift(self,current,baseline,shadow_sessions,policy,as_of):
        names=('calibration','win_rate','expected_value','feature','population','fill_quality','liquidity','data_quality');drifts={n:(None if current.get(n) is None or baseline.get(n) is None else abs(Decimal(str(current[n]))-Decimal(str(baseline[n])))) for n in names};valid=[x for x in drifts.values() if x is not None]
        if shadow_sessions<policy.minimum_shadow_sessions or not valid:state='INSUFFICIENT_EVIDENCE'
        else:
            peak=max(valid);state='SUSPENDED' if peak>=policy.suspended_drift else 'DEGRADED' if peak>=policy.degraded_drift else 'WATCH' if peak>=policy.watch_drift else 'HEALTHY'
        lineage=self._hash({'current':current,'baseline':baseline,'sessions':shadow_sessions});evaluation_id=uuid5(self.NAMESPACE,f"drift:{policy.policy_version}:{as_of}:{lineage}");evaluation={'evaluation_id':evaluation_id,'policy_version':policy.policy_version,'as_of':as_of,'shadow_session_count':shadow_sessions,'state':state,'drift_metrics':drifts,'reasons':[k for k,v in drifts.items() if v is not None and v>=policy.watch_drift],'lineage_checksum':lineage,'created_at':self.clock()};suspension=None
        if state=='SUSPENDED':suspension={'suspension_id':uuid5(self.NAMESPACE,f"suspension:{evaluation_id}"),'drift_evaluation_id':evaluation_id,'policy_version':policy.policy_version,'state':'SUSPENDED','reason':'Versioned drift threshold exceeded.','effective_at':as_of,'lineage_checksum':self._hash({'evaluation':str(evaluation_id)})}
        self.repository.persist_drift(self._policy(policy),evaluation,suspension);return DriftResult(evaluation_id,state,state=='SUSPENDED')

    def _metrics(self,records,policy):
        n=len(records);eligible=sum(r.get('validation_state')=='ELIGIBLE' for r in records);resolved=[r for r in records if r.get('net_return_pct') is not None];filled=[r for r in records if r.get('fill_id') is not None];quality_fills=[r for r in filled if r.get('fill_quality') is not None];supported=len(resolved)>=policy.minimum_metric_sample
        probability=[r for r in resolved if r.get('predicted_win_probability') is not None];actual=lambda r:Decimal(1 if Decimal(r['net_return_pct'])>0 else 0)
        realized=sum((Decimal(r['net_return_pct']) for r in resolved),Decimal(0))/len(resolved) if supported else None;predicted=sum((Decimal(r['predicted_expected_value']) for r in resolved if r.get('predicted_expected_value') is not None),Decimal(0))/len(resolved) if supported and all(r.get('predicted_expected_value') is not None for r in resolved) else None
        return {'recommendation_count':n,'eligible_count':eligible,'rejected_count':sum(r.get('validation_state')=='REJECTED' for r in records),'abstention_rate':Decimal(sum(r.get('validation_state')=='ABSTAINED' for r in records))/n if n else None,'fill_rate':Decimal(len(filled))/eligible if eligible else None,'win_rate':sum((actual(r) for r in resolved),Decimal(0))/len(resolved) if supported else None,'realized_net_expected_value':realized,'predicted_expected_value':predicted,'expected_value_error':predicted-realized if predicted is not None and realized is not None else None,'brier_score':sum(((Decimal(r['predicted_win_probability'])-actual(r))**2 for r in probability),Decimal(0))/len(probability) if supported and len(probability)==len(resolved) else None,'calibration_error':abs(sum((Decimal(r['predicted_win_probability'])-actual(r) for r in probability),Decimal(0))/len(probability)) if supported and probability else None,'interval_coverage':Decimal(sum(Decimal(r['prediction_low'])<=actual(r)<=Decimal(r['prediction_high']) for r in probability if r.get('prediction_low') is not None and r.get('prediction_high') is not None))/len(probability) if supported and probability and all(r.get('prediction_low') is not None and r.get('prediction_high') is not None for r in probability) else None,'average_mfe':self._avg(resolved,'mfe_pct') if supported else None,'average_mae':self._avg(resolved,'mae_pct') if supported else None,'average_slippage':self._avg(quality_fills,'slippage_pct') if len(quality_fills)>=policy.minimum_metric_sample else None,'average_fill_quality':self._avg(quality_fills,'fill_quality') if len(quality_fills)>=policy.minimum_metric_sample else None,'target_hit_rate':self._rate(resolved,'terminal_reason','TARGET') if supported else None,'stop_hit_rate':self._rate(resolved,'terminal_reason','STOP') if supported else None,'timeout_rate':self._rate(resolved,'terminal_reason','TIMEOUT') if supported else None,'unresolved_rate':Decimal(sum(r.get('outcome_state') in {'UNRESOLVED','INSUFFICIENT_PATH'} for r in records))/n if n else None,'failure_counts':{name:sum(r.get('failure_classification')==name for r in records) for name in ('MARKET_FAILURE','MODEL_FAILURE','CALIBRATION_FAILURE','LIQUIDITY_FAILURE','FILL_FAILURE','EVENT_SHOCK','DATA_FAILURE','POLICY_REJECTION','UNCLASSIFIED','INSUFFICIENT_EVIDENCE')}}

    @staticmethod
    def _avg(rows,key):
        values=[Decimal(r[key]) for r in rows if r.get(key) is not None];return sum(values,Decimal(0))/len(values) if values else None
    @staticmethod
    def _rate(rows,key,value):return Decimal(sum(r.get(key)==value for r in rows))/len(rows) if rows else None
    @staticmethod
    def _hash(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
    def _policy(self,p):
        doc=json.loads(json.dumps(asdict(p),default=str));return {'policy_version':p.policy_version,'policy_checksum':self._hash(doc),'policy':doc}
