from __future__ import annotations

from datetime import datetime

from services.option_ranking_models import OptionRankingRequest
from services.option_ranking_repository import OptionRankingRepository
from services.option_ranking_service import OptionRankingService


def main() -> None:
    now = datetime.now().replace(microsecond=0)
    result = OptionRankingService(OptionRankingRepository()).rank_and_persist(
        OptionRankingRequest(as_of=now)
    )
    print("Option ranking completed")
    print(f"Ranking run ID: {result.ranking_run_id}")
    print(f"As of: {result.as_of}")
    print(f"Eligible underlyings: {len(result.rankings)}")
    for row in result.rankings[:20]:
        print(
            f"{row.rank_position}. {row.underlying_symbol} {row.expiry} "
            f"score={row.total_score} liquidity={row.liquidity_score} "
            f"activity={row.activity_score} volatility={row.volatility_score} "
            f"directional={row.directional_score}"
        )


if __name__ == "__main__":
    main()
