# Migration Status

## Current State

As of 2026-03-22:
- `confighub-patterns` exists locally as the first extraction bootstrap
- repo scope, bundle scope, and directory ownership docs are in place
- no canonical pattern source files have been moved yet
- `confighub-scan` is still the active authoring home for the corpus

## Why No Assets Have Moved Yet

The split should stay non-destructive until the shared consumer contract is
stable.

Move source-of-truth assets only after:
- the repo-boundary ADR is accepted as the migration contract
- bundle versioning and cache rules are stable
- consumers are ready to read released bundles
- the current migration guardrails remain intact

## First-Wave Move Candidates

When the move starts for real, the safest first copies are:
- pattern source files from `confighub-scan/risks/`
- mapping tables from `confighub-scan/risks/kyverno/` and `risks/trivy/`
- schema/taxonomy files from `confighub-scan/risks/schema/`
- pattern-quality inputs from `confighub-scan/risks/quality/`
- bundle builders and released runtime artifacts

## Explicit Non-Goals For Bootstrap

Do not move here yet:
- native Go rule implementations
- CLI or SDK integration code
- ConfigHub worker wrappers
- engine-only inventory, contract-diff, or live-state validation scripts
- engine-only tests, fixtures, benchmarks, or corpora

## Reference Plan

Until the split advances, the canonical migration details live in
`confighub-scan`:
- `docs/adr/0002-repo-boundaries-pattern-home-and-scan-surfaces.md`
- `planning/PATTERNS-REPO-MIGRATION-CHECKLIST.md`
- `planning/BUNDLE-CONTRACT-v1.md`
