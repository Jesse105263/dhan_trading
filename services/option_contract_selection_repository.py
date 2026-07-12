from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from psycopg.types.json import Jsonb
from services.database import get_connection
from services.option_contract_selection_models import RankedUnderlying, ContractCandidate, OptionContractSelectionResult

class OptionContractSelectionRepository:
    def list_ranked_underlyings(self, ranking_run_id: UUID, limit: int) -> list[RankedUnderlying]:
        q="""SELECT r.ranking_id,r.ranking_run_id,r.analytics_id,a.source_run_id,r.underlying_symbol,r.expiry,r.source_captured_at,r.rank_position,r.total_score,a.spot_price
        FROM option_rankings r JOIN option_chain_analytics a ON a.analytics_id=r.analytics_id
        WHERE r.ranking_run_id=%s ORDER BY r.rank_position LIMIT %s"""
        with get_connection() as c:
            with c.cursor() as cur: cur.execute(q,(ranking_run_id,limit)); rows=cur.fetchall()
        return [RankedUnderlying(*[Decimal(v) if i in (8,9) else v for i,v in enumerate(row)]) for row in rows]

    def list_contract_candidates(self, ranked: RankedUnderlying) -> list[ContractCandidate]:
        q="""SELECT %s,%s,%s,q.underlying_symbol,q.expiry,q.option_type,dc.security_id,dc.trading_symbol,q.strike,%s,q.last_price,q.bid_price,q.ask_price,COALESCE(q.open_interest,0),COALESCE(q.volume,0),dc.lot_size
        FROM option_chain_quotes q JOIN derivative_contracts dc ON dc.underlying_symbol=q.underlying_symbol AND dc.expiry=q.expiry AND dc.strike=q.strike AND dc.option_type=q.option_type AND dc.instrument_type='OPTSTK' AND dc.is_active=TRUE
        WHERE q.run_id=%s ORDER BY q.option_type,q.strike"""
        with get_connection() as c:
            with c.cursor() as cur: cur.execute(q,(ranked.ranking_id,ranked.analytics_id,ranked.source_run_id,ranked.spot_price,ranked.source_run_id)); rows=cur.fetchall()
        out=[]
        for row in rows:
            vals=list(row)
            for i in (8,9,10,11,12):
                if vals[i] is not None: vals[i]=Decimal(vals[i])
            out.append(ContractCandidate(*vals))
        return out

    def persist(self, result: OptionContractSelectionResult) -> OptionContractSelectionResult:
        with get_connection() as c:
            with c.cursor() as cur:
                cur.execute("INSERT INTO option_contract_selection_runs (selection_run_id,ranking_run_id,as_of,calculated_at,requested_underlying_count,selected_contract_count,methodology_version) VALUES (%s,%s,%s,%s,%s,%s,%s)",(result.selection_run_id,result.ranking_run_id,result.as_of,result.calculated_at,result.requested_underlying_count,len(result.selections),result.methodology_version))
                for s in result.selections:
                    cur.execute("""INSERT INTO option_contract_selections (selection_id,selection_run_id,ranking_id,analytics_id,source_run_id,underlying_symbol,expiry,option_type,security_id,trading_symbol,strike,spot_price,last_price,bid_price,ask_price,open_interest,volume,lot_size,distance_pct,spread_pct,premium_per_lot,contract_score,explanation) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(s.selection_id,s.selection_run_id,s.ranking_id,s.analytics_id,s.source_run_id,s.underlying_symbol,s.expiry,s.option_type,s.security_id,s.trading_symbol,s.strike,s.spot_price,s.last_price,s.bid_price,s.ask_price,s.open_interest,s.volume,s.lot_size,s.distance_pct,s.spread_pct,s.premium_per_lot,s.contract_score,Jsonb(s.explanation)))
            c.commit()
        return result
