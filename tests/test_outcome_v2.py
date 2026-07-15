import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from services.outcome_v2_models import OutcomeAnchor, OutcomeHorizon, OutcomePathBar, OutcomePolicy
from services.outcome_v2_service import OutcomeV2Service


ANCHOR_ID=UUID("11111111-1111-4111-8111-111111111111")
INSTRUMENT=UUID("22222222-2222-4222-8222-222222222222")
MANIFEST=UUID("33333333-3333-4333-8333-333333333333")
NOW=datetime(2026,7,15,10)


class Repository:
    def __init__(self,anchor,path,actions=()): self.anchor=anchor; self.path_rows=path; self.actions=actions; self.prepared=[]
    def anchors(self,as_of,limit,after_at=None,after_id=None): return [self.anchor][:limit] if after_at is None and self.anchor.available_at<=as_of else []
    def path(self,anchor,as_of): return [row for row in self.path_rows if row.available_at<=as_of]
    def corporate_actions(self,*args): return list(self.actions)
    def persist(self,prepared): self.prepared.append(prepared)


def anchor(instrument_class="EQUITY",expiry=None):
    return OutcomeAnchor(ANCHOR_ID,INSTRUMENT,instrument_class,None,"15M",date(2026,7,15),NOW,NOW,expiry,Decimal("100"),MANIFEST)


def bar(number,minutes,close,high=None,low=None,session=date(2026,7,15),available=None):
    value=Decimal(close); opened=NOW+timedelta(minutes=minutes-15); closed=NOW+timedelta(minutes=minutes)
    return OutcomePathBar(UUID(f"{number:08d}-0000-4000-8000-000000000000"),MANIFEST,session,opened,closed,available or closed,
        value,Decimal(high or close),Decimal(low or close),value)


class OutcomeV2ServiceTest(unittest.TestCase):
    def policy(self,*horizons,**kwargs): return OutcomePolicy("test-outcome-v2",tuple(horizons),**kwargs)

    def test_multiple_horizons_metrics_and_determinism(self):
        repo=Repository(anchor(),[bar(1,15,"105","106","99"),bar(2,30,"110","112","104")])
        policy=self.policy(OutcomeHorizon("15M",duration_seconds=900),OutcomeHorizon("30M",duration_seconds=1800),total_cost_bps=Decimal("10"))
        service=OutcomeV2Service(repo,clock=lambda:datetime(2026,7,16)); first=service.materialize(policy,as_of=datetime(2026,7,16)); second=service.materialize(policy,as_of=datetime(2026,7,16))
        self.assertEqual(first.run_id,second.run_id); self.assertEqual(first.outcome_count,2); self.assertEqual(first.complete_count,2)
        outcome=repo.prepared[0]["outcomes"][1][0]
        self.assertEqual(outcome["gross_return_pct"],Decimal("10.0")); self.assertEqual(outcome["net_return_pct"],Decimal("9.9"))
        self.assertEqual(outcome["maximum_favourable_excursion_pct"],Decimal("12.00")); self.assertEqual(outcome["maximum_adverse_excursion_pct"],Decimal("-1.00"))
        self.assertEqual(outcome["maximum_drawdown_pct"],Decimal("0")); self.assertIsNotNone(outcome["realized_volatility_pct"])
        self.assertEqual(len(repo.prepared[0]["outcomes"][1][1]),2)

    def test_option_subject_and_missing_horizon_are_explicit(self):
        repo=Repository(anchor("OPTION",date(2026,7,30)),[bar(1,15,"102")]); policy=self.policy(OutcomeHorizon("30M",duration_seconds=1800))
        result=OutcomeV2Service(repo,clock=lambda:datetime(2026,7,16)).materialize(policy,as_of=datetime(2026,7,16))
        outcome=repo.prepared[0]["outcomes"][0][0]
        self.assertEqual(result.unknown_count,1); self.assertEqual(outcome["subject_type"],"OPTION")
        self.assertEqual(outcome["missing_reason"],"HORIZON_NOT_OBSERVED"); self.assertIsNone(outcome["gross_return_pct"])

    def test_expiry_and_session_horizons_require_observed_evidence(self):
        expiry=date(2026,7,16); next_day=bar(1,24*60,"103",session=expiry,available=datetime(2026,7,16,15,30))
        repo=Repository(anchor(expiry=expiry),[next_day]); policy=self.policy(OutcomeHorizon("SESSION",trading_sessions=1),OutcomeHorizon("EXPIRY",through_expiry=True))
        result=OutcomeV2Service(repo,clock=lambda:datetime(2026,7,17)).materialize(policy,as_of=datetime(2026,7,17))
        self.assertEqual(result.complete_count,2)

    def test_barrier_order_ambiguity_never_fabricates_first_touch(self):
        repo=Repository(anchor(),[bar(1,15,"100","106","94")]); policy=self.policy(OutcomeHorizon("15M",duration_seconds=900),target_return_pct=Decimal("5"),stop_return_pct=Decimal("-5"))
        result=OutcomeV2Service(repo,clock=lambda:datetime(2026,7,16)).materialize(policy,as_of=datetime(2026,7,16))
        outcome=repo.prepared[0]["outcomes"][0][0]
        self.assertEqual(result.ambiguous_count,1); self.assertEqual(outcome["terminal_reason"],"AMBIGUOUS_BARRIER")
        self.assertIsNone(outcome["net_return_pct"])

    def test_corporate_action_path_is_insufficient_not_adjusted_silently(self):
        action={"action_revision_id":UUID("44444444-4444-4444-8444-444444444444")}
        repo=Repository(anchor(),[bar(1,15,"50")],[action]); policy=self.policy(OutcomeHorizon("15M",duration_seconds=900))
        result=OutcomeV2Service(repo,clock=lambda:datetime(2026,7,16)).materialize(policy,as_of=datetime(2026,7,16))
        outcome=repo.prepared[0]["outcomes"][0][0]
        self.assertEqual(result.insufficient_count,1); self.assertEqual(outcome["terminal_reason"],"CORPORATE_ACTION")
        self.assertIsNone(outcome["gross_return_pct"])

    def test_policy_validation(self):
        with self.assertRaises(ValueError): OutcomeHorizon("bad",duration_seconds=1,through_expiry=True)
        with self.assertRaises(ValueError): OutcomePolicy("x",(OutcomeHorizon("a",duration_seconds=1),),target_return_pct=Decimal("1"))


if __name__=="__main__": unittest.main()
