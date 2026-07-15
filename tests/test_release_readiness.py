from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from scripts import verify_release
from services.release_readiness_models import (
    AppliedMigration,
    AuditMetric,
    MigrationManifestEntry,
    ReleaseCheckStatus,
    ReleaseReadinessReport,
)
from services.release_readiness_service import ReleaseReadinessService


class FakeReleaseReadinessRepository:
    def __init__(self) -> None:
        self.identity = ("isolated_release_test", "tester", False)
        self.migrations = (
            AppliedMigration("001", "001_first.sql", "checksum-1"),
            AppliedMigration("002", "002_second.sql", "checksum-2"),
        )
        self.metrics = {
            name: AuditMetric(name, 1, 0)
            for name in ReleaseReadinessService._AUDIT_CHECKS
        }

    def database_identity(self):
        return self.identity

    def applied_migrations(self):
        return self.migrations

    def audit_metrics(self):
        return self.metrics


class ReleaseReadinessServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeReleaseReadinessRepository()
        self.manifest = (
            MigrationManifestEntry("001", "001_first.sql", "checksum-1"),
            MigrationManifestEntry("002", "002_second.sql", "checksum-2"),
        )

    def test_all_valid_checks_pass(self) -> None:
        report = ReleaseReadinessService(
            self.repository,
            self.manifest,
        ).verify()

        self.assertTrue(report.ready)
        self.assertEqual(len(report.checks), 20)
        self.assertTrue(
            all(check.status is ReleaseCheckStatus.PASS for check in report.checks)
        )

    def test_empty_optional_dataset_is_skipped(self) -> None:
        self.repository.metrics["paper_lineage"] = AuditMetric(
            "paper_lineage", 0, 0
        )

        report = ReleaseReadinessService(
            self.repository,
            self.manifest,
        ).verify()
        check = next(item for item in report.checks if item.name == "paper_lineage")

        self.assertIs(check.status, ReleaseCheckStatus.SKIP)
        self.assertTrue(report.ready)

    def test_violation_fails_release(self) -> None:
        self.repository.metrics["decision_lineage"] = AuditMetric(
            "decision_lineage", 3, 1
        )

        report = ReleaseReadinessService(
            self.repository,
            self.manifest,
        ).verify()
        check = next(item for item in report.checks if item.name == "decision_lineage")

        self.assertIs(check.status, ReleaseCheckStatus.FAIL)
        self.assertFalse(report.ready)

    def test_migration_checksum_drift_fails_without_database_mutation(self) -> None:
        self.repository.migrations = (
            AppliedMigration("001", "001_first.sql", "changed"),
            AppliedMigration("002", "002_second.sql", "checksum-2"),
        )

        report = ReleaseReadinessService(
            self.repository,
            self.manifest,
        ).verify()
        check = next(
            item for item in report.checks if item.name == "migration_checksums"
        )

        self.assertIs(check.status, ReleaseCheckStatus.FAIL)
        self.assertEqual(check.evidence, ("001:checksum",))

    def test_unexpected_migration_fails_inventory_and_checksum(self) -> None:
        self.repository.migrations += (
            AppliedMigration("018", "018_unexpected.sql", "checksum-18"),
        )

        report = ReleaseReadinessService(
            self.repository,
            self.manifest,
        ).verify()

        statuses = {check.name: check.status for check in report.checks}
        self.assertIs(statuses["migration_inventory"], ReleaseCheckStatus.FAIL)
        self.assertIs(statuses["migration_checksums"], ReleaseCheckStatus.FAIL)

    def test_database_failure_stops_database_dependent_checks(self) -> None:
        self.repository.database_identity = unittest.mock.Mock(
            side_effect=RuntimeError("unavailable")
        )

        report = ReleaseReadinessService(
            self.repository,
            self.manifest,
        ).verify()

        self.assertFalse(report.ready)
        self.assertEqual(len(report.checks), 1)
        self.assertIs(report.checks[0].status, ReleaseCheckStatus.FAIL)

    def test_missing_metric_fails_closed(self) -> None:
        self.repository.metrics.pop("alert_lineage")

        report = ReleaseReadinessService(
            self.repository,
            self.manifest,
        ).verify()
        check = next(item for item in report.checks if item.name == "alert_lineage")

        self.assertIs(check.status, ReleaseCheckStatus.FAIL)


class VerifyReleaseCliTest(unittest.TestCase):
    def test_cli_returns_zero_for_pass_and_skip(self) -> None:
        report = ReleaseReadinessReport(
            "isolated_release_test",
            (),
        )
        service = unittest.mock.Mock()
        service.verify.return_value = report

        with patch("scripts.verify_release.build_service", return_value=service):
            with redirect_stdout(io.StringIO()) as output:
                exit_code = verify_release.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("Release ready.", output.getvalue())

    def test_cli_returns_nonzero_for_failure(self) -> None:
        repository = FakeReleaseReadinessRepository()
        repository.metrics["paper_lineage"] = AuditMetric("paper_lineage", 1, 1)
        report = ReleaseReadinessService(repository, (
            MigrationManifestEntry("001", "001_first.sql", "checksum-1"),
            MigrationManifestEntry("002", "002_second.sql", "checksum-2"),
        )).verify()
        service = unittest.mock.Mock()
        service.verify.return_value = report

        with patch("scripts.verify_release.build_service", return_value=service):
            with redirect_stdout(io.StringIO()) as output:
                exit_code = verify_release.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("[FAIL] paper_lineage", output.getvalue())


class SafetyBoundarySourceTest(unittest.TestCase):
    def test_release_verifier_has_no_mutating_sql(self) -> None:
        from pathlib import Path

        source = Path("services/release_readiness_repository.py").read_text(
            encoding="utf-8"
        ).upper()
        forbidden = ("INSERT INTO", "UPDATE ", "DELETE FROM", "TRUNCATE ", "DROP ")

        for statement in forbidden:
            self.assertNotIn(statement, source)

    def test_product_boundaries_do_not_import_execution_dependencies(self) -> None:
        from pathlib import Path

        boundaries = {
            "app/read_api.py": ("dhan", "paper_trading", "psycopg"),
            "app/dashboard.py": ("dhan", "services.database", "psycopg"),
            "services/copilot_service.py": ("dhan", "paper_trading", "psycopg"),
            "services/copilot_provider.py": ("dhan", "paper_trading", "psycopg"),
            "services/paper_trading_service.py": ("dhan", "broker"),
            "services/paper_trading_repository.py": ("dhan", "broker"),
            "services/trading_analyst.py": ("dhan", "paper_trading", "psycopg", "services.database"),
        }
        for filename, forbidden in boundaries.items():
            source = Path(filename).read_text(encoding="utf-8").lower()
            for dependency in forbidden:
                self.assertNotIn(
                    f"import {dependency}",
                    source,
                    f"{filename} imports forbidden dependency {dependency}",
                )

    def test_analyst_refuses_before_evidence_or_provider(self) -> None:
        from uuid import UUID

        from services.trading_analyst import AnalystRequest, TradingAnalystService

        class Sentinel:
            name = "sentinel"
            def __getattr__(self, name):
                raise AssertionError(f"Safety refusal crossed boundary: {name}")

        result = TradingAnalystService(Sentinel(), Sentinel()).ask(
            AnalystRequest("Submit to Dhan and execute a trade", (
                UUID("11111111-1111-4111-8111-111111111111"),
            ))
        )
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["evidence"], [])


if __name__ == "__main__":
    unittest.main()
