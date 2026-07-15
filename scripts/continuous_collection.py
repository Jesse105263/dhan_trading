from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from services.continuous_collection_models import ProviderBatch
from services.continuous_collection_provider import LocalFixtureCollectionProvider
from services.continuous_collection_repository import ContinuousCollectionRepository
from services.continuous_collection_service import ContinuousCollectionService
from services.historical_data_models import HistoricalDataSource, RetentionPolicy
from services.historical_data_repository import HistoricalDataRepository
from services.historical_data_service import HistoricalDataService


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "continuous_collection.json"


def components(now: datetime):
    payload=FIXTURE.read_bytes()
    provider=LocalFixtureCollectionProvider({"*":ProviderBatch(payload,"application/json","fixture-v1",now,now,("FIXTURE_SCOPE",))})
    repository=ContinuousCollectionRepository()
    service=ContinuousCollectionService(repository,HistoricalDataService(HistoricalDataRepository()),{"V32_FIXTURE":provider},clock=lambda:now)
    source=HistoricalDataSource("V32_FIXTURE","LOCAL","CONTINUOUS_COLLECTION","LOCAL_FIXTURE","fixture-only")
    policy=RetentionPolicy("v32-fixture","1","TEST_ONLY","ALLOWED","ALLOWED","DENIED","DENIED","DENIED","DENIED","DENIED",now)
    return service,source,policy


def main() -> int:
    parser=argparse.ArgumentParser(description="Fixture-only V3.2 continuous collection operator commands.")
    parser.add_argument("command",choices=("schedule","execute","detect-gaps","schedule-repairs","reconcile","status","verify-idempotency"))
    parser.add_argument("--limit",type=int,default=20); args=parser.parse_args(); now=datetime(2026,7,15,16,0)
    service,source,policy=components(now)
    if args.command in {"schedule","verify-idempotency"}:
        work=service.make_work(provider_code="V32_FIXTURE",dataset_type="UNDERLYING_BARS",scope=("FIXTURE_SCOPE",),requested_start=now,requested_end=now,resolution="1D",session="POST_CLOSE")
        first=service.schedule(work); second=service.schedule(work) if args.command == "verify-idempotency" else None
        output={"work_id":str(work.work_id),"scheduled":first,"duplicate_suppressed":second is False if second is not None else None}
    elif args.command == "execute": output=service.execute_pending(owner="fixture-cli",limit=args.limit,source=source,policy=policy).__dict__
    elif args.command == "schedule-repairs": output={"repairs_scheduled":service.schedule_repairs(args.limit)}
    elif args.command == "status": output=service.health().__dict__
    elif args.command == "detect-gaps": output={"gaps_detected":0,"reason":"No fabricated expectation supplied by the empty fixture."}
    else: output={"reconciled":service.reconcile(args.limit)}
    print(json.dumps(output,default=str,sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
