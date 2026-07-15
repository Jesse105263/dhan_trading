import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from services.research_baseline import (
    RESEARCH_CONTRACT,
    ResearchBaselineService,
    ResearchContract,
    ResearchPeriod,
)


class Repository:
    def __init__(self, rows):
        self.rows = rows
        self.request = None

    def observations(self, start, end, outcome_model):
        self.request = (start, end, outcome_model)
        return self.rows


def row(identifier, observed_at, **changes):
    value = {
        "vector_id": UUID(f"00000000-0000-4000-8000-{identifier:012d}"),
        "observed_at": observed_at,
        "ranking_id": None,
        "spot_price_change": None,
        "outcome_type": "EXPIRY_COMPLETE",
        "closing_return": Decimal("10"),
        "won": True,
        "opportunity_state": None,
        "predicted_win_rate": None,
        "predicted_expected_value": None,
    }
    value.update(changes)
    return value


class ResearchBaselineServiceTest(unittest.TestCase):
    def test_contract_manifest_and_checksum_are_deterministic(self):
        first = RESEARCH_CONTRACT.checksum()
        second = RESEARCH_CONTRACT.checksum()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertEqual(RESEARCH_CONTRACT.manifest()["periods"][0]["start"], "2020-01-01")

    def test_reports_registered_baselines_by_fixed_period(self):
        repository = Repository([
            row(1, datetime(2025, 7, 2), ranking_id=UUID(int=1),
                spot_price_change=Decimal("2"), opportunity_state="ELIGIBLE",
                predicted_win_rate=Decimal("0.8")),
            row(2, datetime(2025, 7, 3), spot_price_change=Decimal("-2"),
                closing_return=Decimal("-5"), won=False),
            row(3, datetime(2025, 7, 4), outcome_type="PARTIAL",
                closing_return=Decimal("1"), won=None),
        ])
        report = ResearchBaselineService(repository).report()
        test_period = next(period for period in report["periods"] if period["name"] == "TEST")
        baselines = {item["name"]: item for item in test_period["baselines"]}

        self.assertEqual(test_period["population_count"], 3)
        self.assertEqual(baselines["always_long"]["evaluated_count"], 2)
        self.assertEqual(baselines["always_long"]["win_rate"], Decimal("0.5"))
        self.assertEqual(baselines["always_long"]["precision"], Decimal("0.5"))
        self.assertEqual(baselines["always_long"]["expected_value"], Decimal("2.5"))
        self.assertEqual(baselines["always_long"]["average_realized_return"], Decimal("2.5"))
        self.assertEqual(baselines["momentum_positive"]["selected_count"], 1)
        self.assertEqual(baselines["mean_reversion_negative"]["selected_count"], 1)
        self.assertEqual(baselines["v2_ranked"]["selected_count"], 1)
        self.assertEqual(baselines["v2_opportunity"]["brier_score"], Decimal("0.04"))
        self.assertEqual(baselines["v2_opportunity"]["calibration_error"], Decimal("0.2"))
        self.assertIsNone(baselines["v2_opportunity"]["cost_adjusted_return"])
        self.assertIsNone(baselines["v2_opportunity"]["prediction_interval_coverage"])
        self.assertEqual(baselines["v2_opportunity"]["evidence_state"], "INSUFFICIENT")
        self.assertEqual(repository.request, (
            RESEARCH_CONTRACT.periods[0].start, RESEARCH_CONTRACT.periods[-1].end,
            RESEARCH_CONTRACT.outcome_model,
        ))

    def test_sparse_and_empty_evidence_never_fabricate_metrics(self):
        report = ResearchBaselineService(Repository([])).report()
        baseline = report["periods"][0]["baselines"][0]
        for field in (
            "coverage", "abstention_rate", "precision", "win_rate", "expected_value",
            "average_realized_return", "worst_realized_return", "tail_loss",
            "maximum_drawdown", "brier_score", "calibration_error",
            "cost_adjusted_return", "turnover", "prediction_interval_coverage",
        ):
            self.assertIsNone(baseline[field])
        self.assertEqual(baseline["evidence_state"], "INSUFFICIENT")

    def test_maximum_drawdown_uses_chronological_compounded_returns(self):
        result = ResearchBaselineService._maximum_drawdown([
            Decimal("10"), Decimal("-20"), Decimal("5")
        ])
        self.assertEqual(result, Decimal("-20.0"))

    def test_rejects_overlapping_or_invalid_contracts(self):
        invalid = ResearchContract(
            version="test", decision_boundary="point-in-time", outcome_model="test",
            purge_days=1, embargo_days=1, minimum_effective_sample_size=1,
            periods=(
                ResearchPeriod("ONE", RESEARCH_CONTRACT.periods[0].start,
                               RESEARCH_CONTRACT.periods[0].end),
                ResearchPeriod("TWO", RESEARCH_CONTRACT.periods[0].end,
                               RESEARCH_CONTRACT.periods[1].end),
            ),
            baseline_names=("always_long",),
        )
        with self.assertRaises(ValueError):
            ResearchBaselineService(Repository([]), invalid)

    def test_unknown_baseline_fails_closed(self):
        with self.assertRaises(ValueError):
            ResearchBaselineService._selected("unknown", row(1, datetime(2025, 7, 2)))

    def test_repository_boundary_is_select_only_and_execution_is_absent(self):
        source = (Path(__file__).resolve().parents[1] / "services" / "research_baseline.py").read_text()
        upper = source.upper()
        for statement in ("INSERT INTO", "UPDATE ", "DELETE FROM", "ALTER TABLE", "DROP TABLE"):
            self.assertNotIn(statement, upper)
        for dependency in ("collector", "dhan_option_chain", "paper_trading", "option_signal"):
            self.assertNotIn(f"services.{dependency}", source)


if __name__ == "__main__":
    unittest.main()
