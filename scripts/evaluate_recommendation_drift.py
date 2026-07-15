import argparse
from datetime import datetime,timedelta
from services.live_validation_models import LiveValidationPolicy
from services.live_validation_service import LiveValidationService


class FixtureDriftRepository:
    def __init__(self):self.saved=None
    def persist_drift(self,policy,evaluation,suspension):self.saved=(policy,evaluation,suspension)


def main():
    parser=argparse.ArgumentParser(description='Evaluate deterministic live-validation drift.');parser.add_argument('--fixture',action='store_true');parser.add_argument('--shadow-sessions',type=int,default=0);args=parser.parse_args();now=datetime(2026,7,16,16);repository=FixtureDriftRepository() if args.fixture else None
    service=LiveValidationService(repository,clock=lambda:now) if args.fixture else LiveValidationService();policy=LiveValidationPolicy('live-validation-v1')
    if args.fixture:current,baseline,sessions={'calibration':'.15','win_rate':'.5'},{'calibration':'.05','win_rate':'.5'},args.shadow_sessions
    else:
        current_rows=service.repository.metric_records(now-timedelta(days=30),now);baseline_rows=service.repository.metric_records(now-timedelta(days=60),now-timedelta(days=30));cm=service._metrics(current_rows,policy);bm=service._metrics(baseline_rows,policy)
        current={'calibration':cm['calibration_error'],'win_rate':cm['win_rate'],'expected_value':cm['realized_net_expected_value'],'fill_quality':cm['average_fill_quality']};baseline={'calibration':bm['calibration_error'],'win_rate':bm['win_rate'],'expected_value':bm['realized_net_expected_value'],'fill_quality':bm['average_fill_quality']};sessions=len({r['recommendation_at'].date() for r in current_rows})
    result=service.evaluate_drift(current,baseline,sessions,policy,now)
    print(f'Drift evaluated | evaluation={result.evaluation_id} state={result.state} suspended={str(result.suspended).lower()} trusted=false')
    return 0


if __name__=='__main__':raise SystemExit(main())
