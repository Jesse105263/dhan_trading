from __future__ import annotations
import argparse
from datetime import datetime
from uuid import UUID
from services.option_contract_selection_models import OptionContractSelectionRequest
from services.option_contract_selection_repository import OptionContractSelectionRepository
from services.option_contract_selection_service import OptionContractSelectionService

def main():
    p=argparse.ArgumentParser(); p.add_argument("ranking_run_id",type=UUID); p.add_argument("--top",type=int,default=10); a=p.parse_args()
    result=OptionContractSelectionService(OptionContractSelectionRepository()).select_and_persist(OptionContractSelectionRequest(a.ranking_run_id,datetime.now(),top_underlyings=a.top))
    print("Option contract selection completed"); print(f"Selection run ID: {result.selection_run_id}"); print(f"Ranking run ID: {result.ranking_run_id}"); print(f"Selected contracts: {len(result.selections)}")
    for s in result.selections: print(f"{s.underlying_symbol} {s.expiry} {s.option_type} {s.trading_symbol} strike={s.strike} premium_per_lot={s.premium_per_lot} score={s.contract_score}")
if __name__=="__main__": main()
