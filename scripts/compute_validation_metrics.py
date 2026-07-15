import argparse
from datetime import datetime,timedelta
from decimal import Decimal

from services.live_validation_models import LiveValidationPolicy
from services.live_validation_service import LiveValidationService


class FixtureMetricsRepository:
    def __init__(self):self.saved=None
    def metric_records(self,start,end):return []
    def persist_metrics(self,policy,run,segments):self.saved=(policy,run,segments)


def main():
    parser=argparse.ArgumentParser(description='Compute immutable rolling shadow-validation metrics.');parser.add_argument('--fixture',action='store_true');args=parser.parse_args();now=datetime(2026,7,16,16) if args.fixture else datetime.now();start=now-timedelta(days=30);policy=LiveValidationPolicy('live-validation-v1')
    repository=FixtureMetricsRepository() if args.fixture else None;service=LiveValidationService(repository,clock=lambda:now) if args.fixture else LiveValidationService();records=repository.metric_records(start,now) if args.fixture else service.repository.metric_records(start,now);run,metrics=service.compute_metrics(records,policy,now,start,now)
    print(f'Validation metrics materialized | run={run} population={metrics["recommendation_count"]} trusted=false')
    return 0


if __name__=='__main__':raise SystemExit(main())
