import argparse
from uuid import UUID

from services.trade_opportunity_service import TradeOpportunityService


def main():
    parser=argparse.ArgumentParser(description="Materialize deterministic opportunities from persisted similarity evidence.")
    parser.add_argument("--similarity-run-id",type=UUID); parser.add_argument("--limit",type=int,default=100)
    arguments=parser.parse_args()
    result=TradeOpportunityService().materialize(arguments.similarity_run_id,arguments.limit)
    print(f"Trade opportunities materialized | run_id={result['run_id']} opportunities={result['opportunity_count']} eligible={result['eligible_count']}")
    return 0


if __name__=="__main__": raise SystemExit(main())
