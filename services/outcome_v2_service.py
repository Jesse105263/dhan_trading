from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

from services.outcome_v2_models import (
    OutcomeAnchor, OutcomeHorizon, OutcomeMaterializationResult, OutcomePathBar, OutcomePolicy,
)
from services.outcome_v2_repository import OutcomeV2Repository


class OutcomeV2Service:
    NAMESPACE=UUID("cecbabbd-aa8e-4ec9-bfbd-d631db5677a8")
    DEFAULT_POLICY=OutcomePolicy(
        model_version="canonical-path-outcome-v2",
        horizons=(OutcomeHorizon("30M",duration_seconds=1800),OutcomeHorizon("SESSION",trading_sessions=1),
                  OutcomeHorizon("5_SESSIONS",trading_sessions=5),OutcomeHorizon("EXPIRY",through_expiry=True)),
    )

    def __init__(self, repository=None, clock=datetime.now):
        self.repository=repository or OutcomeV2Repository(); self.clock=clock

    def materialize(self, policy: OutcomePolicy=DEFAULT_POLICY, *, as_of: datetime|None=None, limit: int|None=None, batch_size: int=250) -> OutcomeMaterializationResult:
        if limit is not None and limit<1: raise ValueError("limit must be positive.")
        if not 1<=batch_size<=1000: raise ValueError("batch_size must be between 1 and 1000.")
        materialized_as_of=(as_of or self.clock()).replace(tzinfo=None)
        started=self.clock(); policy_document=self._canonical(asdict(policy)); policy_checksum=hashlib.sha256(policy_document).hexdigest()
        run_id=uuid5(self.NAMESPACE,f"run:{policy.model_version}:{materialized_as_of.isoformat()}:{policy_checksum}")
        anchors=[]; after_at=after_id=None
        while limit is None or len(anchors)<limit:
            size=min(batch_size,limit-len(anchors)) if limit is not None else batch_size
            page=self.repository.anchors(materialized_as_of,size,after_at,after_id)
            if not page: break
            anchors.extend(page); after_at=page[-1].available_at; after_id=page[-1].bar_revision_id
            if len(page)<size: break
        outcomes=[]; counts={key:0 for key in ("complete_count","unknown_count","insufficient_count","ambiguous_count")}
        for anchor in anchors:
            path=self.repository.path(anchor,materialized_as_of)
            for horizon in policy.horizons:
                outcome,used=self._calculate(anchor,path,horizon,policy,policy_checksum,run_id,materialized_as_of)
                outcomes.append((outcome,used)); counts[outcome["outcome_state"].lower()+"_count"]+=1
        counts["outcome_count"]=len(outcomes); completed=self.clock()
        self.repository.persist({"run_id":run_id,"model_version":policy.model_version,"policy_checksum":policy_checksum,
            "policy":json.loads(policy_document),"as_of":materialized_as_of,"anchor_count":len(anchors),"counts":counts,
            "outcomes":outcomes,"started_at":started,"completed_at":completed})
        return OutcomeMaterializationResult(run_id,len(anchors),len(outcomes),counts["complete_count"],counts["unknown_count"],counts["insufficient_count"],counts["ambiguous_count"])

    def _calculate(self, anchor: OutcomeAnchor, path: list[OutcomePathBar], horizon: OutcomeHorizon, policy: OutcomePolicy,
                   policy_checksum: str, run_id: UUID, as_of: datetime) -> tuple[dict[str,Any],tuple[OutcomePathBar,...]]:
        horizon_end,eligible,coverage_reason=self._horizon_path(anchor,path,horizon)
        actions=self.repository.corporate_actions(anchor.instrument_id,anchor.session_date,horizon_end.date() if horizon_end else anchor.session_date,as_of) if horizon_end else []
        state="COMPLETE"; terminal_reason="TIMEOUT" if not horizon.through_expiry else "EXPIRY"; missing=None
        if anchor.close_price is None or anchor.close_price<=0:
            state="UNKNOWN"; terminal_reason="MISSING_DATA"; missing="ENTRY_PRICE_UNAVAILABLE"
        elif coverage_reason:
            state="UNKNOWN"; terminal_reason="MISSING_DATA"; missing=coverage_reason
        elif len(eligible)<policy.minimum_path_observations:
            state="INSUFFICIENT"; terminal_reason="MISSING_DATA"; missing="INSUFFICIENT_PATH_OBSERVATIONS"
        if actions:
            state="INSUFFICIENT"; terminal_reason="CORPORATE_ACTION"; missing="UNADJUSTED_CORPORATE_ACTION_IN_PATH"
        terminal=eligible[-1] if eligible else None
        barrier_terminal=None
        if state=="COMPLETE" and policy.target_return_pct is not None:
            for bar in eligible:
                high=self._pct(anchor.close_price,bar.high_price); low=self._pct(anchor.close_price,bar.low_price)
                target_hit=high is not None and high>=policy.target_return_pct; stop_hit=low is not None and low<=policy.stop_return_pct
                if target_hit and stop_hit:
                    state="AMBIGUOUS"; terminal_reason="AMBIGUOUS_BARRIER"; missing="INTRABAR_BARRIER_ORDER_UNKNOWN"; barrier_terminal=bar; break
                if target_hit: terminal_reason="TARGET"; barrier_terminal=bar; break
                if stop_hit: terminal_reason="STOP"; barrier_terminal=bar; break
            if barrier_terminal:
                terminal=barrier_terminal; eligible=eligible[:eligible.index(barrier_terminal)+1]
        terminal_price=None
        if terminal is not None:
            terminal_price=anchor.close_price*(Decimal(1)+(policy.target_return_pct/100)) if terminal_reason=="TARGET" else anchor.close_price*(Decimal(1)+(policy.stop_return_pct/100)) if terminal_reason=="STOP" else terminal.close_price
        gross=self._pct(anchor.close_price,terminal_price) if state=="COMPLETE" else None
        net=gross-policy.total_cost_bps/Decimal(100) if gross is not None else None
        highs=[bar.high_price for bar in eligible]; lows=[bar.low_price for bar in eligible]; closes=[anchor.close_price]+[bar.close_price for bar in eligible]
        mfe=max([Decimal(0)]+[self._pct(anchor.close_price,value) for value in highs]) if highs and state=="COMPLETE" else None
        mae=min([Decimal(0)]+[self._pct(anchor.close_price,value) for value in lows]) if lows and state=="COMPLETE" else None
        drawdown=self._max_drawdown(closes) if len(closes)>1 and state=="COMPLETE" else None
        volatility=self._volatility(closes) if len(closes)>2 and state=="COMPLETE" else None
        adjusted=net/volatility if net is not None and volatility not in (None,0) else None
        lineage={"anchor":str(anchor.bar_revision_id),"path":[str(item.bar_revision_id) for item in eligible],"actions":[str(item['action_revision_id']) for item in actions],"as_of":as_of.isoformat()}
        lineage_checksum=hashlib.sha256(self._canonical(lineage)).hexdigest()
        outcome_id=uuid5(self.NAMESPACE,f"outcome:{policy.model_version}:{anchor.bar_revision_id}:{horizon.code}")
        return ({"outcome_id":outcome_id,"run_id":run_id,"model_version":policy.model_version,"horizon_code":horizon.code,
            "subject_type":"OPTION" if anchor.instrument_class=="OPTION" else "UNDERLYING","instrument_id":anchor.instrument_id,
            "underlying_instrument_id":anchor.underlying_instrument_id,"anchor_bar_revision_id":anchor.bar_revision_id,
            "terminal_bar_revision_id":terminal.bar_revision_id if terminal else None,"entry_manifest_id":anchor.manifest_id,
            "terminal_manifest_id":terminal.manifest_id if terminal else None,"observed_at":anchor.bar_close_at,"available_at":anchor.available_at,
            "horizon_end_at":horizon_end,"terminal_at":terminal.bar_close_at if terminal else None,"outcome_state":state,
            "terminal_reason":terminal_reason,"missing_reason":missing,"corporate_action_count":len(actions),"entry_price":anchor.close_price,
            "terminal_price":terminal_price if state in {"COMPLETE","AMBIGUOUS"} else None,"gross_return_pct":gross,"net_return_pct":net,
            "maximum_favourable_excursion_pct":mfe,"maximum_adverse_excursion_pct":mae,"maximum_drawdown_pct":drawdown,
            "realized_volatility_pct":volatility,"volatility_adjusted_return":adjusted,
            "holding_duration_seconds":int((terminal.bar_close_at-anchor.bar_close_at).total_seconds()) if terminal else None,
            "path_observation_count":len(eligible),"target_return_pct":policy.target_return_pct,"stop_return_pct":policy.stop_return_pct,
            "policy_checksum":policy_checksum,"lineage_checksum":lineage_checksum,"materialized_at":self.clock()},tuple(eligible))

    @staticmethod
    def _horizon_path(anchor: OutcomeAnchor,path:list[OutcomePathBar],horizon:OutcomeHorizon):
        if horizon.duration_seconds is not None:
            end=anchor.bar_close_at+timedelta(seconds=horizon.duration_seconds); eligible=[bar for bar in path if bar.bar_close_at<=end]
            return end,eligible,None if eligible and eligible[-1].bar_close_at==end else "HORIZON_NOT_OBSERVED"
        if horizon.through_expiry:
            if anchor.expiry is None:return None,[],"EXPIRY_UNAVAILABLE"
            end=datetime.combine(anchor.expiry,time.max); eligible=[bar for bar in path if bar.session_date<=anchor.expiry]
            return end,eligible,None if eligible and eligible[-1].session_date==anchor.expiry else "EXPIRY_OBSERVATION_MISSING"
        sessions=[]
        for bar in path:
            if bar.session_date not in sessions:sessions.append(bar.session_date)
        if len(sessions)<horizon.trading_sessions:return None,path,"SESSION_HORIZON_INCOMPLETE"
        final_session=sessions[horizon.trading_sessions-1]; eligible=[bar for bar in path if bar.session_date<=final_session]
        return eligible[-1].bar_close_at,eligible,None

    @staticmethod
    def _pct(entry,value): return ((Decimal(value)-Decimal(entry))/Decimal(entry))*100 if entry and value is not None else None

    @classmethod
    def _max_drawdown(cls,values):
        peak=values[0]; worst=Decimal(0)
        for value in values[1:]: peak=max(peak,value); worst=min(worst,cls._pct(peak,value))
        return worst

    @classmethod
    def _volatility(cls,values):
        returns=[cls._pct(values[index-1],values[index]) for index in range(1,len(values))]
        mean=sum(returns,Decimal(0))/len(returns); variance=sum(((item-mean)**2 for item in returns),Decimal(0))/len(returns)
        return variance.sqrt()

    @staticmethod
    def _canonical(value):
        return json.dumps(value,sort_keys=True,separators=(",",":"),default=lambda item:item.isoformat() if hasattr(item,"isoformat") else str(item)).encode()
