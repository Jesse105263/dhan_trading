from dataclasses import asdict
from decimal import Decimal
import hashlib,json,math,random,sys
from uuid import UUID,uuid5

from services.research_governance_models import ExperimentResult,PromotionResult
from services.research_governance_repository import ResearchGovernanceRepository


class ResearchGovernanceService:
    NAMESPACE=UUID('b1a77daa-78b8-4c7c-b1ba-5d71e23c3c4e')
    def __init__(self,repository=None,clock=None):
        from datetime import datetime
        self.repository=repository or ResearchGovernanceRepository();self.clock=clock or datetime.now

    def register(self,definition,policy):
        required=('dataset_version','source_versions','periods','champion_model','challenger_model','experiment_version','hypothesis')
        if any(k not in definition for k in required):raise ValueError('Experiment definition is incomplete.')
        periods=definition['periods'];test=periods['TEST'];dataset_checksum=self._hash({'version':definition['dataset_version'],'sources':definition['source_versions'],'periods':periods,'lineage':definition.get('dataset_lineage',{})});dataset_id=uuid5(self.NAMESPACE,f"dataset:{definition['dataset_version']}:{dataset_checksum}")
        dataset={'dataset_id':dataset_id,'dataset_version':definition['dataset_version'],'dataset_checksum':dataset_checksum,'source_versions':definition['source_versions'],'train_start':periods.get('TRAIN',[None,None])[0],'train_end':periods.get('TRAIN',[None,None])[1],'validation_start':periods.get('VALIDATION',[None,None])[0],'validation_end':periods.get('VALIDATION',[None,None])[1],'calibration_start':periods.get('CALIBRATION',[None,None])[0],'calibration_end':periods.get('CALIBRATION',[None,None])[1],'test_start':test[0],'test_end':test[1],'purge_days':definition.get('purge_days',45),'embargo_days':definition.get('embargo_days',7),'lineage':definition.get('dataset_lineage',{}),'reproducibility':self._repro(policy),'created_at':self.clock()}
        models=[]
        for spec in (definition['champion_model'],definition['challenger_model']):
            checksum=self._hash(spec);models.append({'model_id':uuid5(self.NAMESPACE,f"model:{spec['model_version']}:{checksum}"),'model_version':spec['model_version'],'model_type':spec['model_type'],'definition_checksum':checksum,'artifact_checksum':spec.get('artifact_checksum'),'configuration':spec.get('configuration',{}),'source_lineage':spec.get('source_lineage',{}),'created_at':self.clock()})
        experiment_doc={'dataset':dataset_checksum,'champion':models[0]['definition_checksum'],'challenger':models[1]['definition_checksum'],'hypothesis':definition['hypothesis'],'plan':definition.get('evaluation_plan',{})};checksum=self._hash(experiment_doc);experiment_id=uuid5(self.NAMESPACE,f"experiment:{definition['experiment_version']}:{checksum}");experiment={'experiment_id':experiment_id,'experiment_version':definition['experiment_version'],'definition_checksum':checksum,'dataset_id':dataset_id,'champion_model_id':models[0]['model_id'],'challenger_model_id':models[1]['model_id'],'hypothesis':definition['hypothesis'],'evaluation_plan':definition.get('evaluation_plan',{}),'reproducibility':self._repro(policy),'created_at':self.clock()};policy_row=self._policy(policy);audits=[self._audit('DATASET',dataset_id,'REGISTERED',{'checksum':dataset_checksum}),self._audit('EXPERIMENT',experiment_id,'REGISTERED',{'checksum':checksum})]
        roles=[{'assignment_id':uuid5(self.NAMESPACE,f"assignment:{experiment_id}:{role}"),'model_id':model['model_id'],'role':role,'effective_at':self.clock(),'source_decision_id':None,'previous_assignment_id':None,'lineage_checksum':self._hash({'experiment':str(experiment_id),'model':str(model['model_id']),'role':role})} for model,role in zip(models,('CHAMPION','CHALLENGER'))]
        self.repository.persist_registry({'policy':policy_row,'dataset':dataset,'models':models,'experiment':experiment,'roles':roles,'audits':audits});return experiment_id

    def evaluate(self,experiment_id,observations,cutoff,policy,comparison_count=1):
        experiment=self.repository.experiment(experiment_id)
        if experiment is None:raise ValueError('Experiment was not found.')
        included=[];excluded=[];seen=set();replay=[]
        for row in observations:
            reason=None;key=row.get('episode_id',row.get('observation_id'))
            if row.get('period')!='TEST':reason='NON_TEST_PARTITION'
            elif row.get('terminal_at') is None or row['terminal_at']>cutoff:reason='FUTURE_OR_UNMATURE_OUTCOME'
            elif row.get('champion_return') is None or row.get('challenger_return') is None:reason='UNSUPPORTED_OUTCOME'
            elif row.get('leakage_flag') or row.get('survivorship_flag') or row.get('selection_flag'):reason='AUDIT_EXCLUSION'
            elif key in seen:reason='OVERLAPPING_EPISODE'
            if reason:excluded.append({'id':row.get('observation_id'),'reason':reason})
            else:included.append(row);seen.add(key)
            replay.append({'observation_id':str(row.get('observation_id')),'period_name':row.get('period','UNKNOWN'),'included':reason is None,'exclusion_reason':reason,'terminal_at':row.get('terminal_at'),'champion_return':row.get('champion_return'),'challenger_return':row.get('challenger_return'),'source_lineage':row.get('source_lineage',{})})
        replay_checksum=self._hash(replay);run_id=uuid5(self.NAMESPACE,f"run:{experiment_id}:{cutoff.isoformat()}:{replay_checksum}");differences=[Decimal(x['challenger_return'])-Decimal(x['champion_return']) for x in included];n=len(differences);adjusted=policy.alpha/max(1,comparison_count)
        enough=n>=policy.minimum_test_sample;champion=self._avg(included,'champion_return');challenger=self._avg(included,'challenger_return');mean=sum(differences,Decimal(0))/n if n else None;low=high=stat=pvalue=effect=None
        if enough:
            variance=sum(((x-mean)**2 for x in differences),Decimal(0))/(n-1);sd=variance.sqrt();se=sd/Decimal(n).sqrt() if sd else Decimal(0);stat=mean/se if se else (Decimal('Infinity') if mean>0 else Decimal(0));pvalue=Decimal(str(math.erfc(abs(float(stat))/math.sqrt(2)))) if stat.is_finite() else Decimal(0);effect=mean/sd if sd else None;low,high=self._bootstrap(differences,policy)
        superior=bool(enough and mean>0 and low is not None and low>0 and pvalue is not None and pvalue<=adjusted);state='PASS' if superior else 'INSUFFICIENT_EVIDENCE' if not enough else 'FAIL';comparison_id=uuid5(self.NAMESPACE,f"comparison:{run_id}");lineage=self._hash({'replay':replay_checksum,'excluded':excluded,'dataset':experiment['dataset_checksum']})
        run={'run_id':run_id,'experiment_id':experiment_id,'cutoff_at':cutoff,'state':state,'observation_count':len(observations),'test_count':n,'excluded_count':len(excluded),'replay_checksum':replay_checksum,'started_at':self.clock(),'completed_at':self.clock()};comparison={'comparison_id':comparison_id,'run_id':run_id,'champion_model_id':experiment['champion_model_id'],'challenger_model_id':experiment['challenger_model_id'],'sample_size':n,'mean_champion_return':champion,'mean_challenger_return':challenger,'mean_difference':mean,'confidence_low':low,'confidence_high':high,'test_statistic':stat,'p_value':pvalue,'adjusted_alpha':adjusted,'effect_size':effect,'superiority_state':'SUPERIOR' if superior else 'INSUFFICIENT_EVIDENCE' if not enough else 'NOT_SUPERIOR','lineage_checksum':lineage}
        audits={'leakage_passed':not any(x.get('leakage_flag') for x in observations),'survivorship_passed':not any(x.get('survivorship_flag') for x in observations),'selection_passed':not any(x.get('selection_flag') for x in observations),'overlap_exclusions':sum(x['reason']=='OVERLAPPING_EPISODE' for x in excluded),'test_only':all(x.get('period')=='TEST' for x in included),'cutoff_passed':all(x['terminal_at']<=cutoff for x in included)};metrics={'sample_size':n,'champion_mean':champion,'challenger_mean':challenger,'mean_difference':mean,'confidence_low':low,'confidence_high':high,'p_value':pvalue,'effect_size':effect};report_body={'metrics':metrics,'audits':audits,'multiple_testing':{'comparison_count':comparison_count,'method':'BONFERRONI','adjusted_alpha':adjusted},'reproducibility':self._repro(policy),'limitations':[] if superior else ['Challenger promotion is unsupported.']};report_checksum=self._hash(report_body);report_id=uuid5(self.NAMESPACE,f"report:{run_id}:v1:{report_checksum}");audit_passed=audits['leakage_passed'] and audits['survivorship_passed'] and audits['selection_passed'] and audits['test_only'] and audits['cutoff_passed'];report={'report_id':report_id,'run_id':run_id,'report_version':'research-evaluation-v1','metrics':metrics,'audits':audits,'multiple_testing':report_body['multiple_testing'],'reproducibility':report_body['reproducibility'],'promotion_eligible':superior and audit_passed,'limitations':report_body['limitations'],'report_checksum':report_checksum,'created_at':self.clock()};audit=self._audit('EXPERIMENT',experiment_id,'EVALUATED',{'run_id':str(run_id),'report_id':str(report_id),'state':state})
        replay_rows=[{'run_id':run_id,**row} for row in replay];self.repository.persist_evaluation(run,replay_rows,comparison,report,audit);return ExperimentResult(experiment_id,run_id,report_id,state)

    def propose(self,report_id,shadow_sessions,policy):
        report=self.repository.report(report_id)
        if report is None:raise ValueError('Evaluation report was not found.')
        checksum=self._hash({'report':str(report_id),'challenger':str(report['challenger_model_id']),'sessions':shadow_sessions,'policy':policy.policy_version});proposal_id=uuid5(self.NAMESPACE,f"proposal:{checksum}");row={'proposal_id':proposal_id,'report_id':report_id,'challenger_model_id':report['challenger_model_id'],'current_champion_model_id':report['champion_model_id'],'policy_version':policy.policy_version,'shadow_session_count':shadow_sessions,'proposal_checksum':checksum,'created_at':self.clock()};self.repository.persist_proposal(self._policy(policy),row,self._audit('PROMOTION',proposal_id,'PROPOSED',{'report':str(report_id)}));return proposal_id

    def approve(self,proposal_id,role,approver_id,decision,rationale):
        if role not in {'RESEARCH_OWNER','RISK_OWNER','DATA_OWNER'} or decision not in {'APPROVE','REJECT'} or not approver_id or not rationale:raise ValueError('Explicit governance approval is required.')
        approval_id=uuid5(self.NAMESPACE,f"approval:{proposal_id}:{role}:{approver_id}:{decision}:{rationale}");row={'approval_id':approval_id,'proposal_id':proposal_id,'approval_role':role,'approver_id':approver_id,'decision':decision,'rationale':rationale,'approved_at':self.clock(),'lineage_checksum':self._hash({'proposal':str(proposal_id),'role':role,'approver':approver_id,'decision':decision})};self.repository.persist_approval(row,self._audit('PROMOTION',proposal_id,'APPROVAL_RECORDED',{'approval_id':str(approval_id),'role':role,'decision':decision},'HUMAN_APPROVER'));return approval_id

    def decide(self,proposal_id,policy):
        proposal=self.repository.proposal(proposal_id)
        if proposal is None:raise ValueError('Promotion proposal was not found.')
        approvals=self.repository.approvals(proposal_id);by_role={x['approval_role']:x for x in approvals};roles_ok=all(role in by_role and by_role[role]['decision']=='APPROVE' for role in policy.required_approval_roles);no_reject=all(x['decision']!='REJECT' for x in approvals);ready=self.repository.release_ready();approved=bool(proposal['promotion_eligible'] and proposal['shadow_session_count']>=policy.minimum_shadow_sessions and roles_ok and no_reject and ready);state='APPROVED' if approved else 'REJECTED';reason='All frozen evidence, shadow, approval and readiness gates passed.' if approved else 'One or more promotion gates failed closed.';decision_id=uuid5(self.NAMESPACE,f"decision:{proposal_id}:{state}");decision={'decision_id':decision_id,'proposal_id':proposal_id,'state':state,'reason':reason,'approval_count':len(approvals),'readiness_passed':ready,'decided_at':self.clock(),'lineage_checksum':self._hash({'proposal':str(proposal_id),'state':state,'approvals':[str(x['approval_id']) for x in approvals]})};assignments=[];rollback=None
        if approved:
            retired=uuid5(self.NAMESPACE,f"assignment:{decision_id}:retired");champion=uuid5(self.NAMESPACE,f"assignment:{decision_id}:champion");assignments=[{'assignment_id':retired,'model_id':proposal['current_champion_model_id'],'role':'RETIRED','effective_at':self.clock(),'source_decision_id':decision_id,'previous_assignment_id':None,'lineage_checksum':self._hash({'decision':str(decision_id),'role':'RETIRED'})},{'assignment_id':champion,'model_id':proposal['challenger_model_id'],'role':'CHAMPION','effective_at':self.clock(),'source_decision_id':decision_id,'previous_assignment_id':None,'lineage_checksum':self._hash({'decision':str(decision_id),'role':'CHAMPION'})}];rollback_id=uuid5(self.NAMESPACE,f"rollback:{decision_id}");rollback={'rollback_id':rollback_id,'promotion_decision_id':decision_id,'from_model_id':proposal['challenger_model_id'],'to_model_id':proposal['current_champion_model_id'],'trigger_condition':'Future governed drift or validation breach after explicit review.','rollback_procedure':{'mode':'OFFLINE_ROLE_ASSIGNMENT','automatic':False,'requires_new_approval':True},'state':'PLANNED','created_at':self.clock(),'lineage_checksum':self._hash({'decision':str(decision_id),'from':str(proposal['challenger_model_id']),'to':str(proposal['current_champion_model_id'])})}
        self.repository.persist_decision(decision,assignments,rollback,self._audit('PROMOTION',proposal_id,'DECIDED',{'decision_id':str(decision_id),'state':state}));return PromotionResult(proposal_id,decision_id,state)

    def _bootstrap(self,values,policy):
        rng=random.Random(policy.seed);n=len(values);means=[sum((rng.choice(values) for _ in range(n)),Decimal(0))/n for _ in range(policy.bootstrap_samples)];means.sort();return means[int((len(means)-1)*.025)],means[int((len(means)-1)*.975)]
    @staticmethod
    def _avg(rows,key):return sum((Decimal(x[key]) for x in rows),Decimal(0))/len(rows) if rows else None
    def _policy(self,p):
        doc=json.loads(json.dumps(asdict(p),default=str));return {'policy_version':p.policy_version,'policy_checksum':self._hash(doc),'policy':doc,'created_at':self.clock()}
    def _repro(self,p):return {'algorithm_version':'institutional-research-v1','python':f'{sys.version_info.major}.{sys.version_info.minor}','seed':p.seed,'bootstrap_samples':p.bootstrap_samples,'dependency_free':True}
    def _audit(self,entity_type,entity_id,event_type,details,actor='OFFLINE_SERVICE'):
        checksum=self._hash(details);return {'audit_id':uuid5(self.NAMESPACE,f"audit:{entity_type}:{entity_id}:{event_type}:{checksum}"),'entity_type':entity_type,'entity_id':entity_id,'event_type':event_type,'event_at':self.clock(),'actor_type':actor,'details':details,'previous_audit_id':None,'lineage_checksum':checksum}
    @staticmethod
    def _hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
