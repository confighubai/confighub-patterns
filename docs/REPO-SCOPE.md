# Repo Scope

`confighub-patterns` owns the pattern corpus and the released runtime bundles.

## In Scope

- canonical CCVE and related pattern definitions
- aliases, source references, and metadata overlays
- Kyverno, Trivy, and future external mapping tables
- remediation metadata and safety classes
- schema and taxonomy files
- quality, promotion, severity, and release-policy inputs
- released bundle artifacts and their manifests
- authoring and release documentation for the pattern corpus

## Out Of Scope

- native deterministic Go rules
- scan orchestration and evidence normalization code
- CLI entry points
- ConfigHub worker runtime code
- engine-only reports like rule inventory or live-state contract reports
- engine-only tests, fixtures, benchmarks, and corpus harnesses

## Repo Boundary

Expected long-term split:
- `confighub-patterns`: corpus, mappings, remedies, schema, quality inputs,
  runtime bundles
- `confighub-scan`: engine, adapters, findings model, local bundle consumption,
  engine quality reports
- ConfigHub/SDK: connected worker execution and orchestration

## Migration Notes

- first-wave moves should be data-like assets only
- consumers should switch to released bundles before local sources are deleted
- compatibility with `~/.confighub/risk-catalog-v1.json` must remain during the
  migration wave
