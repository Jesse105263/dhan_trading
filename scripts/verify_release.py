from __future__ import annotations

from services.migration_runner import MigrationRunner
from services.release_readiness_models import (
    MigrationManifestEntry,
    ReleaseCheckStatus,
)
from services.release_readiness_repository import ReleaseReadinessRepository
from services.release_readiness_service import ReleaseReadinessService


def build_service() -> ReleaseReadinessService:
    migrations = MigrationRunner._discover_migrations()
    manifest = tuple(
        MigrationManifestEntry(
            migration.version,
            migration.filename,
            migration.checksum,
        )
        for migration in migrations
    )
    return ReleaseReadinessService(ReleaseReadinessRepository(), manifest)


def main() -> int:
    report = build_service().verify()
    print("DHAN PLATFORM VERSION 1.0 RELEASE READINESS")
    print("=" * 60)
    if report.database_name is not None:
        print(f"Database: {report.database_name}")
    print("")

    for check in report.checks:
        print(f"[{check.status.value}] {check.name}: {check.summary}")
        for evidence in check.evidence:
            print(f"       {evidence}")

    print("")
    print(
        "Summary: "
        f"PASS={report.count(ReleaseCheckStatus.PASS)} "
        f"FAIL={report.count(ReleaseCheckStatus.FAIL)} "
        f"SKIP={report.count(ReleaseCheckStatus.SKIP)}"
    )
    print("Release ready." if report.ready else "Release is not ready.")
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
