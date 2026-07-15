import argparse
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from services.similarity_v2_models import SimilarityPolicyV2
from services.similarity_v2_service import SimilarityV2Service


def main():
    parser=argparse.ArgumentParser(description="Materialize provider-free Similarity Engine V2 evidence.")
    parser.add_argument("--vector-id",required=True,type=UUID); parser.add_argument("--model-version",default="canonical-similarity-v2")
    parser.add_argument("--distance-model",default="WEIGHTED_MANHATTAN",choices=("WEIGHTED_MANHATTAN","WEIGHTED_EUCLIDEAN","COSINE"))
    parser.add_argument("--ranking-strategy",default="DISTANCE",choices=("DISTANCE","EVIDENCE_QUALITY","TEMPORAL_DIVERSITY"))
    parser.add_argument("--cutoff"); parser.add_argument("--maximum-matches",type=int,default=20)
    args=parser.parse_args(); policy=SimilarityPolicyV2(args.model_version,args.distance_model,args.ranking_strategy,maximum_matches=args.maximum_matches)
    result=SimilarityV2Service().materialize(args.vector_id,policy,cutoff=datetime.fromisoformat(args.cutoff) if args.cutoff else None)
    print(f"Similarity V2 materialized | run={result.run_id} candidates={result.candidate_count} matches={result.match_count} evidence={result.evidence_state}")
    return 0


if __name__=="__main__": raise SystemExit(main())
