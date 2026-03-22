# Migration Status

## Current State

As of 2026-03-22:
- `confighub-patterns` exists locally as the first extraction bootstrap
- the bootstrap repo is now published at `https://github.com/confighubai/confighub-patterns`
- repo scope, bundle scope, directory ownership docs, and taxonomy docs are in place
- first-wave copy readiness is now machine-checked by
  `scripts/build-first-wave-copy-manifest.py`
- the first partial copy wave is now in progress
- the first seeded control and framework definitions now exist in-repo
- control/framework summary generation is now machine-checked by
  `scripts/build-control-taxonomy-summary.py`
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

The current readiness artifact is:
- `dist/first-wave-copy-manifest-v1.json`

At the time this bootstrap was created, the manifest found 39 planned first-wave
items and 0 missing sources in the sibling `confighub-scan` checkout.

Current copy state:
- all 39 planned first-wave items are copied into `confighub-patterns` and
  match source bytes
- the raw pattern corpus, archive, pattern-facing builders, released bundle
  artifacts, mappings, schemas, and policy inputs are all now present locally
- this is still a non-destructive copy wave; `confighub-scan` remains the
  active write home until consumers switch to released bundles
- the copied wave now includes schema files, mapping JSONs, pattern-quality
  policy inputs, pattern-facing builders, released bundle artifacts, and the
  source corpus README

The target taxonomy is now explicit:
- `patterns/` for broad canonical risk knowledge
- `controls/` for promoted operator-facing checks
- `frameworks/` for grouped views over controls

The first seeded implementation slice is now explicit too:
- 4 seeded controls
- 2 seeded frameworks
- a summary artifact at `dist/control-taxonomy-summary-v1.json`
- an initial promoted-taxonomy bundle at `dist/control-framework-bundle-v1.json`

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
