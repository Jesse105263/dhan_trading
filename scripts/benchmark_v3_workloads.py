from __future__ import annotations

import argparse,json,time,tracemalloc
from services.v3_scale_models import ScalePolicy
from services.v3_scale_service import V3ScaleService


def fixture_benchmark():
    records=[{"record_id":f"r-{i:05d}","partition_key":i//100} for i in range(2000)];service=V3ScaleService(policy=ScalePolicy(batch_size=250))
    tracemalloc.start();start=time.perf_counter_ns();batches=service.bulk_batches(records,250);elapsed=time.perf_counter_ns()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    return {"mode":"fixture_verification","row_count":len(records),"batch_count":len(batches),"elapsed_ms":round(elapsed/1e6,3),"rows_per_second":round(len(records)/(elapsed/1e9),1),"batch_memory_estimate_bytes":peak,"external_calls":0,"claims":{"million_record_performance":False,"production_scale":False}}
def main(argv=None):
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument("--fixture",action="store_true");g.add_argument("--postgres",action="store_true");a=p.parse_args(argv)
    if a.fixture: result=fixture_benchmark()
    else:
        from services.v3_scale_repository import V3ScaleRepository
        start=time.perf_counter_ns();plan=V3ScaleRepository().benchmark_plan();result={"mode":"measured_local_postgresql","query_plan":plan,"elapsed_ms":round((time.perf_counter_ns()-start)/1e6,3),"claims":{"million_record_performance":False,"production_scale":False}}
    print(json.dumps(result,sort_keys=True,default=str));return 0
if __name__=="__main__":raise SystemExit(main())
