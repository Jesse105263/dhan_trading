import argparse
from uuid import UUID

from services.similarity_service import SimilarityService


def main():
    parser=argparse.ArgumentParser(description="Persist a deterministic historical-similarity analysis.")
    parser.add_argument("--vector-id",required=True,type=UUID)
    parser.add_argument("--limit",type=int,default=20)
    parser.add_argument("--same-symbol",action="store_true")
    parser.add_argument("--same-expiry",action="store_true")
    parser.add_argument("--historical-cutoff")
    arguments=parser.parse_args()
    query={"limit":str(arguments.limit),"same_symbol":str(arguments.same_symbol).lower(),
           "same_expiry":str(arguments.same_expiry).lower()}
    if arguments.historical_cutoff: query["historical_cutoff"]=arguments.historical_cutoff
    result=SimilarityService().analyze(arguments.vector_id,query,persist=True)
    if result is None: parser.error("feature vector was not found")
    print(f"Similarity run materialized | run_id={result['run_id']} candidates={result['candidate_count']} matches={result['match_count']} evidence={result['evidence_state']}")
    return 0


if __name__=="__main__": raise SystemExit(main())
