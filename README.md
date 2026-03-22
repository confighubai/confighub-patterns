# confighub-patterns

`confighub-patterns` is the planned source-of-truth repo for ConfigHub pattern
data and released runtime bundles.

This repo exists to separate data-like pattern assets from the scanner engine.
It should become the authoring home for:
- canonical CCVE and related pattern definitions,
- third-party mapping tables,
- remediation metadata and safety classes,
- taxonomy and bundle schemas,
- pattern-quality and promotion policy inputs,
- released bundle artifacts.

It should not become a second engine repo. Native Go rules, scan orchestration,
worker wrappers, CLI code, and engine-only quality reports stay in
`confighub-scan`.

## Status

Bootstrap only.

As of 2026-03-22:
- this repo has been created locally as the first extraction step,
- no canonical pattern source files have been moved yet,
- `confighub-scan` remains the active authoring home until the migration
  checklist is executed,
- the shared bundle contract and migration sequence still live in
  `confighub-scan` planning docs.

## Intended Layout

- `patterns/`
  - canonical CCVE and related pattern definitions
- `mappings/`
  - Kyverno, Trivy, and future external mapping tables
- `schema/`
  - taxonomy and bundle schemas
- `quality/`
  - quality, promotion, severity, and release-policy inputs
- `scripts/`
  - bundle and release-artifact builders
- `dist/`
  - released bundle artifacts
- `docs/`
  - authoring, taxonomy, and release guidance

## Consumer Model

The expected interaction model is:
- `confighub-patterns` publishes versioned bundles,
- `confighub-scan` consumes those bundles locally and in CI,
- `cub-scout` consumes the same bundle cache contract,
- ConfigHub/SDK worker packaging consumes released runtime assets where needed.

The initial shared cache contract is:
- `~/.confighub/pattern-bundles/current/`
- compatibility path: `~/.confighub/risk-catalog-v1.json`

## Current References

Until the migration is complete, the active planning contract remains in
`confighub-scan`:
- `docs/adr/0002-repo-boundaries-pattern-home-and-scan-surfaces.md`
- `planning/PATTERNS-REPO-MIGRATION-CHECKLIST.md`
- `planning/BUNDLE-CONTRACT-v1.md`
