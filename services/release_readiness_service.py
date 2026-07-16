from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from services.release_readiness_models import (
    AppliedMigration,
    AuditMetric,
    MigrationManifestEntry,
    ReleaseCheckResult,
    ReleaseCheckStatus,
    ReleaseReadinessReport,
)


class ReleaseReadinessRepositoryProtocol(Protocol):
    def database_identity(self) -> tuple[str, str, bool]: ...

    def applied_migrations(self) -> tuple[AppliedMigration, ...]: ...

    def audit_metrics(self) -> Mapping[str, AuditMetric]: ...


class ReleaseReadinessService:
    _AUDIT_CHECKS = (
        "option_chain_lineage",
        "decision_lineage",
        "evaluation_lineage",
        "alert_lineage",
        "paper_lineage",
        "operational_state",
        "feature_store_lineage",
        "historical_outcome_lineage",
        "similarity_lineage_and_leakage",
        "trade_opportunity_lineage",
        "news_event_lineage_and_leakage",
        "analyst_evidence_grounding",
        "historical_data_foundation_lineage",
        "continuous_collection_lineage",
        "outcome_v2_lineage_and_leakage",
        "feature_store_v2_lineage_and_leakage",
        "similarity_v2_lineage_and_leakage",
        "opportunity_v2_lineage_and_leakage",
        "calibration_v2_lineage_and_leakage",
        "live_validation_lineage_and_safety",
        "research_governance_lineage_and_safety",
        "v3_scale_operational_safety",
        "execution_schema_boundary",
    )

    def __init__(
        self,
        repository: ReleaseReadinessRepositoryProtocol,
        migration_manifest: Sequence[MigrationManifestEntry],
    ) -> None:
        self.repository = repository
        self.migration_manifest = tuple(migration_manifest)

    def verify(self) -> ReleaseReadinessReport:
        checks: list[ReleaseCheckResult] = []
        database_name: str | None = None

        try:
            database_name, database_user, in_recovery = (
                self.repository.database_identity()
            )
            checks.append(
                ReleaseCheckResult(
                    "database_connection",
                    ReleaseCheckStatus.PASS,
                    "PostgreSQL accepted a read-only readiness query.",
                    (
                        f"database={database_name}",
                        f"user={database_user}",
                        f"in_recovery={str(in_recovery).lower()}",
                    ),
                )
            )
        except Exception as exc:
            checks.append(self._error("database_connection", exc))
            return ReleaseReadinessReport(database_name, tuple(checks))

        try:
            applied = self.repository.applied_migrations()
            checks.extend(self._migration_checks(applied))
        except Exception as exc:
            checks.append(self._error("migration_inventory", exc))
            checks.append(
                ReleaseCheckResult(
                    "migration_checksums",
                    ReleaseCheckStatus.FAIL,
                    "Migration checksums could not be audited.",
                )
            )

        try:
            metrics = self.repository.audit_metrics()
            for name in self._AUDIT_CHECKS:
                metric = metrics.get(name)
                if metric is None:
                    checks.append(
                        ReleaseCheckResult(
                            name,
                            ReleaseCheckStatus.FAIL,
                            "The repository did not return this required audit metric.",
                        )
                    )
                else:
                    checks.append(self._metric_check(metric))
        except Exception as exc:
            for name in self._AUDIT_CHECKS:
                checks.append(self._error(name, exc))

        return ReleaseReadinessReport(database_name, tuple(checks))

    def _migration_checks(
        self,
        applied: Sequence[AppliedMigration],
    ) -> tuple[ReleaseCheckResult, ReleaseCheckResult]:
        expected_versions = [item.version for item in self.migration_manifest]
        applied_versions = [item.version for item in applied]
        inventory_ok = applied_versions == expected_versions
        inventory = ReleaseCheckResult(
            "migration_inventory",
            ReleaseCheckStatus.PASS if inventory_ok else ReleaseCheckStatus.FAIL,
            (
                f"All {len(expected_versions)} filesystem migrations are applied in order."
                if inventory_ok
                else "Applied migration versions do not match the filesystem manifest."
            ),
            (
                f"expected={','.join(expected_versions)}",
                f"applied={','.join(applied_versions)}",
            ),
        )

        applied_by_version = {item.version: item for item in applied}
        mismatches = []
        for expected in self.migration_manifest:
            actual = applied_by_version.get(expected.version)
            if actual is None:
                mismatches.append(f"{expected.version}:missing")
            elif actual.filename != expected.filename:
                mismatches.append(f"{expected.version}:filename")
            elif actual.checksum != expected.checksum:
                mismatches.append(f"{expected.version}:checksum")
        unexpected = sorted(set(applied_by_version) - set(expected_versions))
        mismatches.extend(f"{version}:unexpected" for version in unexpected)
        checksum_ok = not mismatches
        checksum = ReleaseCheckResult(
            "migration_checksums",
            ReleaseCheckStatus.PASS if checksum_ok else ReleaseCheckStatus.FAIL,
            (
                "Applied filenames and SHA-256 checksums match the filesystem."
                if checksum_ok
                else "One or more applied migrations differ from the filesystem manifest."
            ),
            tuple(mismatches),
        )
        return inventory, checksum

    @staticmethod
    def _metric_check(metric: AuditMetric) -> ReleaseCheckResult:
        evidence = (
            f"audited={metric.audited_count}",
            f"violations={metric.violation_count}",
        )
        if metric.violation_count:
            return ReleaseCheckResult(
                metric.name,
                ReleaseCheckStatus.FAIL,
                "Persisted records violated this release invariant.",
                evidence,
            )
        if metric.audited_count == 0:
            return ReleaseCheckResult(
                metric.name,
                ReleaseCheckStatus.SKIP,
                "No persisted records were available for this optional audit.",
                evidence,
            )
        return ReleaseCheckResult(
            metric.name,
            ReleaseCheckStatus.PASS,
            "All audited records satisfy this release invariant.",
            evidence,
        )

    @staticmethod
    def _error(name: str, exc: Exception) -> ReleaseCheckResult:
        return ReleaseCheckResult(
            name,
            ReleaseCheckStatus.FAIL,
            f"Readiness check could not complete: {type(exc).__name__}: {exc}",
        )
