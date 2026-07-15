import argparse
from datetime import datetime

from services.feature_store_v2_service import FeatureStoreV2Service


def main()->int:
    parser=argparse.ArgumentParser(description="Materialize point-in-time canonical Feature Store V2 vectors without provider access.")
    parser.add_argument("--limit",type=int); parser.add_argument("--as-of",help="Availability cutoff as ISO timestamp.")
    args=parser.parse_args(); cutoff=datetime.fromisoformat(args.as_of.replace("Z","+00:00")).replace(tzinfo=None) if args.as_of else None
    result=FeatureStoreV2Service().materialize(as_of=cutoff,limit=args.limit)
    print(f"Feature Store V2 materialized | run={result.run_id} anchors={result.anchor_count} vectors={result.vector_count} complete={result.complete_count} partial={result.partial_count} insufficient={result.insufficient_count}")
    return 0


if __name__=="__main__": raise SystemExit(main())
