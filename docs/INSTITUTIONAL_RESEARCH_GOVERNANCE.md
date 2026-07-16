# Institutional Research, Validation, and Model Governance

Version 3.9 is offline governance. It registers frozen datasets, models and
experiments; replays paired champion/challenger evidence; records statistical
reports; and requires approvals before changing the offline champion registry.
It cannot deploy, retrain, change recommendations or execute trades.

Dataset versions freeze sources, research periods, purge, embargo, lineage and
reproducibility. Experiments bind a dataset, champion, challenger, hypothesis and
plan. Every replay row records inclusion/exclusion and exact source lineage. Only
mature untouched-test evidence enters comparison; leakage, survivorship, selection
and overlapping episodes fail closed.

The dependency-free framework uses paired net returns, deterministic bootstrap
intervals, a transparent normal approximation, effect size where supported and
Bonferroni-adjusted alpha. Unsupported statistics remain null.

Promotion also requires sufficient shadow sessions, release readiness and explicit
`RESEARCH_OWNER`, `RISK_OWNER` and `DATA_OWNER` approvals. Approval appends only
offline model roles and a non-automatic rollback plan. All history is immutable.

```bash
python -m scripts.register_research_experiment --fixture
python -m scripts.run_offline_research --fixture
python -m scripts.evaluate_model_promotion --fixture
```

The fixture comparison passes, but promotion is deliberately `REJECTED` because
shadow sessions and human approvals are absent. Migration `031` adds immutable
registries, replay, reports, approvals, decisions, roles, rollback and audit.
Licensed population evidence and deployment remain absent. V3.10 is next.

V3.10 adds dependency checkpoints for governance artifacts and query indexing but
does not change experiments, comparisons, approvals, promotion or rollback. The
Version 3 sequence is now ready for owner review; licensed evidence and offline
validation remain prerequisites to any future explicit promotion decision.
