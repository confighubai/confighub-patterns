# Repo Scope

`confighub-patterns` owns the pattern corpus, promoted control views, framework
views, and the released runtime bundles used by ConfigHub functions,
standalone cub-based scan, and wrapper CLIs.

## In Scope

- canonical CCVE and related pattern definitions
- pattern-growth work that borrows or normalizes external sources into canonical
  patterns, mappings, or promoted controls
- promoted controls built from those pattern definitions
- framework views that group controls for standards and workflow surfaces
- aliases, source references, and metadata overlays
- Kyverno, Trivy, and future external mapping tables
- remediation metadata and safety classes
- schema and taxonomy files
- quality, promotion, severity, and release-policy inputs
- released bundle artifacts and their manifests
- authoring and release documentation for the pattern corpus
- documentation that explains how consumers use patterns, controls, and mappings

## Out Of Scope

- native deterministic Go rules
- executable detector implementations in any language
- scan orchestration and evidence normalization code
- CLI entry points
- ConfigHub worker runtime code
- engine-only reports like rule inventory or live-state contract reports
- engine-only tests, fixtures, benchmarks, and corpus harnesses

## Repo Boundary

Expected long-term split:
- `confighub-patterns`: patterns, controls, frameworks, mappings, remediation
  metadata, schema, quality inputs, runtime bundles
- `confighub-scan`: engine, adapters, findings model, local bundle consumption,
  engine quality reports
- ConfigHub/SDK: connected worker execution and orchestration

Consumer model:
- ConfigHub built-in functions use `confighub-scan` + `confighub-patterns`
- standalone cub-based scan uses `confighub-scan` + `confighub-patterns`
- wrapper CLIs/TUIs wrap the same engine and bundle contract

## Migration Notes

- first-wave moves should be data-like assets only
- consumers should switch to released bundles before local sources are deleted
- compatibility with `~/.confighub/risk-catalog-v1.json` must remain during the
  migration wave
