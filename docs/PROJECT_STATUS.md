# Project Status

## Current state

Versions 1, 2 and 3 are implemented. Version 3 release closure has passed the
repository verification matrix and is pending repository-owner approval.
Migrations `001`–`032` are authoritative; there is no migration `033` and no
approved Version 4 roadmap.

Version 3 milestones are complete:

- V3.0 Research Contract (`a3ed736`)
- V3.0.5 Data Provider Strategy (`e1c3618`)
- V3.1 Historical Data Foundation (`fc20734`)
- V3.2 Continuous Market Collection (`885883c`)
- V3.3 Outcome Engine V2 (`ed0bb63`)
- V3.4 Feature Store V2 (`b4c72f0`)
- V3.5 Similarity Engine V2 (`fcb81a5`)
- V3.6 Opportunity Engine V2 (`bb5e07b`)
- V3.7 Calibration and Recommendation Policy (`254e6bf`)
- V3.8 Live Recommendation Validation (`67ed31c`)
- V3.9 Institutional Research Governance (`874ef1f`)
- V3.10 Scale and Operational Hardening (`c5f01c9`)

Closure verification on 2026-07-17 passed compileall; 340 standard Python tests
with 55 expected database-gated skips; 340 PostgreSQL-enabled tests with five
documented evidence/isolated-database skips; frontend lint, 39 tests, build and
formatting; migration checksum/idempotency; fixture operators; and release
readiness with 13 PASS, zero FAIL and 13 optional empty-data SKIPs.

## Safety and evidence status

No licensed historical population has been acquired. No live provider, trusted
operational recommendation or live execution is active. Fixture success is not
population validation. The 60-session shadow target, licensed coverage targets,
million-scale validation, 20-session collection soak and isolated recovery drill
remain unresolved.

## Next decision

After owner approval of this closure, make a separate explicit decision on
licensed data acquisition and the bounded operational-validation programme. That
decision may authorize procurement, historical evidence collection, shadow
sessions, populated-scale benchmarks and a recovery drill; this document does not
authorize them and does not define Version 4.
