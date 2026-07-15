import json
from psycopg.types.json import Jsonb
from services.database import get_connection


class ResearchGovernanceRepository:
    JSON_KEYS={'policy','source_versions','lineage','reproducibility','configuration','source_lineage','evaluation_plan','metrics','audits','multiple_testing','limitations','rollback_procedure','details'}
    def persist_registry(self,prepared):
        with get_connection() as c:
            try:
                with c.cursor() as q:
                    self._insert(q,'governance_policies_v3',prepared['policy'])
                    q.execute('SELECT policy_checksum FROM governance_policies_v3 WHERE policy_version=%s',(prepared['policy']['policy_version'],))
                    if q.fetchone()[0]!=prepared['policy']['policy_checksum']:raise ValueError('Governance policy is immutable.')
                    self._insert(q,'research_datasets_v3',prepared['dataset'])
                    q.execute('SELECT dataset_checksum FROM research_datasets_v3 WHERE dataset_id=%s',(prepared['dataset']['dataset_id'],))
                    if q.fetchone()[0]!=prepared['dataset']['dataset_checksum']:raise ValueError('Dataset version is immutable.')
                    for model in prepared['models']:
                        self._insert(q,'governed_models_v3',model);q.execute('SELECT definition_checksum FROM governed_models_v3 WHERE model_id=%s',(model['model_id'],))
                        if q.fetchone()[0]!=model['definition_checksum']:raise ValueError('Governed model version is immutable.')
                    self._insert(q,'research_experiments_v3',prepared['experiment'])
                    q.execute('SELECT definition_checksum FROM research_experiments_v3 WHERE experiment_id=%s',(prepared['experiment']['experiment_id'],))
                    if q.fetchone()[0]!=prepared['experiment']['definition_checksum']:raise ValueError('Experiment definition is immutable.')
                    for role in prepared['roles']:self._insert(q,'model_role_assignments_v3',role)
                    for audit in prepared['audits']:self._insert(q,'governance_audit_history_v3',audit)
                c.commit()
            except Exception:c.rollback();raise
    def experiment(self,experiment_id):
        rows=self._dicts('SELECT e.*,d.dataset_version,d.dataset_checksum,d.test_start,d.test_end FROM research_experiments_v3 e JOIN research_datasets_v3 d ON d.dataset_id=e.dataset_id WHERE e.experiment_id=%s',(experiment_id,));return rows[0] if rows else None
    def persist_evaluation(self,run,observations,comparison,report,audit):
        with get_connection() as c:
            with c.cursor() as q:
                self._insert(q,'research_experiment_runs_v3',run)
                for row in observations:self._insert(q,'research_replay_observations_v3',row)
                self._insert(q,'model_comparisons_v3',comparison);self._insert(q,'research_evaluation_reports_v3',report);self._insert(q,'governance_audit_history_v3',audit)
            c.commit()
    def report(self,report_id):
        rows=self._dicts('SELECT r.*,x.experiment_id,e.champion_model_id,e.challenger_model_id FROM research_evaluation_reports_v3 r JOIN research_experiment_runs_v3 x ON x.run_id=r.run_id JOIN research_experiments_v3 e ON e.experiment_id=x.experiment_id WHERE r.report_id=%s',(report_id,));return rows[0] if rows else None
    def persist_proposal(self,policy,proposal,audit):
        with get_connection() as c:
            with c.cursor() as q:self._insert(q,'governance_policies_v3',policy);self._insert(q,'model_promotion_proposals_v3',proposal);self._insert(q,'governance_audit_history_v3',audit)
            c.commit()
    def proposal(self,proposal_id):
        rows=self._dicts('SELECT p.*,r.promotion_eligible FROM model_promotion_proposals_v3 p JOIN research_evaluation_reports_v3 r ON r.report_id=p.report_id WHERE p.proposal_id=%s',(proposal_id,));return rows[0] if rows else None
    def approvals(self,proposal_id):return self._dicts('SELECT * FROM governance_approvals_v3 WHERE proposal_id=%s ORDER BY approval_role,approver_id',(proposal_id,))
    def persist_approval(self,approval,audit):
        with get_connection() as c:
            with c.cursor() as q:self._insert(q,'governance_approvals_v3',approval);self._insert(q,'governance_audit_history_v3',audit)
            c.commit()
    def release_ready(self):
        from scripts.verify_release import build_service
        return build_service().verify().ready
    def persist_decision(self,decision,assignments,rollback,audit):
        with get_connection() as c:
            with c.cursor() as q:
                self._insert(q,'model_promotion_decisions_v3',decision)
                for row in assignments:self._insert(q,'model_role_assignments_v3',row)
                if rollback:self._insert(q,'model_rollback_metadata_v3',rollback)
                self._insert(q,'governance_audit_history_v3',audit)
            c.commit()
    @classmethod
    def _insert(cls,q,table,row):
        keys=tuple(row);values=tuple(Jsonb(json.loads(json.dumps(v,default=str))) if k in cls.JSON_KEYS else v for k,v in row.items());q.execute(f"INSERT INTO {table}({','.join(keys)}) VALUES({','.join(['%s']*len(keys))}) ON CONFLICT DO NOTHING",values)
    @staticmethod
    def _dicts(sql,params):
        with get_connection() as c:
            with c.cursor() as q:q.execute(sql,params);names=[x.name for x in q.description or ()];return [dict(zip(names,row,strict=True)) for row in q.fetchall()]
