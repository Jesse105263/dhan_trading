import argparse
from services.historical_outcome_service import HistoricalOutcomeService

def main():
    parser=argparse.ArgumentParser(description="Materialize objective outcomes from persisted feature vectors.")
    parser.add_argument("--limit",type=int)
    result=HistoricalOutcomeService().materialize(parser.parse_args().limit)
    print(f"Historical outcomes materialized | sources={result['source_count']} outcomes={result['materialized_count']}")
    return 0

if __name__=="__main__": raise SystemExit(main())
