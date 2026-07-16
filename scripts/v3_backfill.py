from __future__ import annotations

import argparse, json
from datetime import datetime
from services.v3_scale_models import BackfillSpec, ScalePolicy
from services.v3_scale_repository import V3ScaleRepository
from services.v3_scale_service import V3ScaleService


def fixture_records(): return [{"record_id":f"fixture-{i:03d}","partition_key":"2026-07-16"} for i in range(12)]
def parser():
    p=argparse.ArgumentParser(description="Fixture-safe V3.10 backfill orchestration")
    p.add_argument("action",choices=("schedule","execute","pause","resume","recover","status","verify-idempotency"));p.add_argument("--fixture",action="store_true");p.add_argument("--job-id");p.add_argument("--batch-size",type=int,default=5);return p
def main(argv=None):
    a=parser().parse_args(argv);now=datetime(2026,7,16,9,15);service=V3ScaleService(policy=ScalePolicy(batch_size=a.batch_size),clock=lambda:now)
    spec=BackfillSpec("CANONICAL","LOCAL_FIXTURE",("NIFTY",),now,now,"1m")
    if a.fixture:
        job=service.job(spec);result=service.execute_fixture(job,fixture_records());repeat=service.execute_fixture(job,fixture_records())
        print(json.dumps({"mode":"fixture","shadow_only":True,"action":a.action,"job_id":str(job['job_id']),"processed":result.processed,"checkpoint":result.checkpoint,"idempotent":result==repeat,"external_calls":0},sort_keys=True));return 0
    repo=V3ScaleRepository();service.repository=repo
    if a.action in ("schedule","verify-idempotency"):
        first=service.schedule(spec);second=service.schedule(spec);payload={"job_id":str(first),"idempotent":first==second}
    elif a.action=="recover": payload={"recovered":[str(x) for x in repo.recover_stale(datetime.utcnow())]}
    elif a.action=="status": payload=repo.health(datetime.utcnow())
    else:
        if not a.job_id: raise SystemExit("--job-id is required")
        changed=getattr(repo,a.action)(a.job_id,datetime.utcnow());payload={"job_id":a.job_id,"changed":changed}
    print(json.dumps(payload,sort_keys=True,default=str));return 0
if __name__=="__main__": raise SystemExit(main())
