import argparse
from datetime import datetime

from services.outcome_v2_service import OutcomeV2Service


def main() -> int:
    parser=argparse.ArgumentParser(description="Materialize versioned V3 canonical historical outcomes without provider access.")
    parser.add_argument("--limit",type=int)
    parser.add_argument("--as-of",help="Point-in-time availability cutoff (ISO timestamp).")
    args=parser.parse_args(); as_of=datetime.fromisoformat(args.as_of.replace("Z","+00:00")).replace(tzinfo=None) if args.as_of else None
    result=OutcomeV2Service().materialize(as_of=as_of,limit=args.limit)
    print(f"Outcome V2 materialized | run={result.run_id} anchors={result.anchor_count} outcomes={result.outcome_count} complete={result.complete_count} unknown={result.unknown_count} insufficient={result.insufficient_count} ambiguous={result.ambiguous_count}")
    return 0


if __name__=="__main__": raise SystemExit(main())
