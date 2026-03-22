# AI README First

Read this file before making changes in `confighub-patterns`.

## Purpose

This repo is for pattern data and released pattern bundles.

Keep here:
- CCVE and related pattern definitions,
- third-party mapping tables,
- remediation metadata and safety classes,
- schema and taxonomy files,
- pattern-quality and promotion inputs,
- bundle/release builders,
- released runtime bundle artifacts.

Do not add here:
- native Go scan rules,
- CLI code,
- ConfigHub worker wrappers,
- SDK integration code,
- engine-only benchmarks or adversarial harnesses.

Those remain in `confighub-scan`.

## Migration Rule

This repo is in bootstrap mode.

Until the migration is further along:
- do not delete pattern assets from `confighub-scan`,
- do not move engine-only reports or tests here,
- prefer copying or documenting first-wave moves,
- keep the bundle contract compatible with current `confighub-scan` and
  `cub-scout` consumers.

## Current Source Of Truth

The migration plan still lives in `confighub-scan`:
- `docs/adr/0002-repo-boundaries-pattern-home-and-scan-surfaces.md`
- `planning/PATTERNS-REPO-MIGRATION-CHECKLIST.md`
- `planning/BUNDLE-CONTRACT-v1.md`
