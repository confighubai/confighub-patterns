# confighub-patterns

`confighub-patterns` is the planned source-of-truth repo for ConfigHub pattern
data and released runtime bundles.

This repo exists to separate data-like pattern assets from the scanner engine.
It should become the authoring home for:
- canonical CCVE and related pattern definitions,
- promoted controls derived from the broader corpus,
- framework views that group controls for standards and workflows,
- third-party mapping tables,
- remediation metadata and safety classes,
- taxonomy and bundle schemas,
- pattern-quality and promotion policy inputs,
- released bundle artifacts.

It should not become a second engine repo. Executable Go rules, scan
orchestration, worker wrappers, CLI code, and engine-only quality reports stay
in `confighub-scan`.

## Primary Consumers

This repo exists to support three clear user stories:

1. ConfigHub built-in functions
   - function workers use `confighub-scan` for execution and this repo for catalog, controls, mappings, and remedies
2. Standalone cub-based scan
   - today the local entry point is `cub-scan`
   - later the same engine may be exposed as `cub scan` or a `cub` plugin
3. Wrapper CLIs and TUIs
   - `cub-scout` and similar tools wrap the same engine and consume the same bundle contract

## Near-Term Product Goal

This repo is not just a migration bucket. In the next wave it needs to support
three practical outcomes:

1. make ConfigHub built-in functions easy to consume through released bundles
2. make local CLI and AI-assisted scan flows easy to consume through the same
   bundles
3. make the database bigger every week through mined patterns, borrowed external
   patterns, mappings, and promoted controls

## Status

Bootstrap plus active bundle/control growth.

As of 2026-03-22:
- this repo has been created locally as the first extraction step,
- the repo is now also pushed to GitHub at `confighubai/confighub-patterns`,
- no canonical pattern source files have been moved yet,
- `confighub-scan` remains the active authoring home until the migration
  checklist is executed,
- the shared bundle contract and migration sequence still live in
  `confighub-scan` planning docs.
- first-wave readiness is now captured by
  `scripts/build-first-wave-copy-manifest.py` and
  `dist/first-wave-copy-manifest-v1.json`
- the full first-wave copy set is now present:
  - all 39 planned items are present in `confighub-patterns`
  - the copy manifest now tracks both `copied_matching` and `copied_drifted` states as repo-native files intentionally evolve
  - the raw pattern corpus and archive are copied locally
  - `confighub-scan` still remains the active write home until consumer cutover
- the first seeded controls and frameworks now live in this repo and validate
  through `scripts/build-control-taxonomy-summary.py`
- the first generated promoted-taxonomy bundle now exists at
  `dist/control-framework-bundle-v1.json`
- the first generated framework coverage view now exists at
  `dist/framework-coverage-report-v1.json`
- the repo-native release manifest now exists at `dist/bundle-manifest-v1.json`
- the release manifest now advertises Kyverno, Trivy, and Kubescape mapping
  files as first-class runtime bundle assets
- the promoted taxonomy now includes 25 controls, 7 frameworks, and 214 covered
  pattern IDs
- the repo now has native validation plumbing via `make validate` and
  `.github/workflows/validate.yml`
- near-term success is not only "move files"; it is also "grow the reusable
  database while keeping bundle consumers easy to support"

## Intended Layout

- `patterns/`
  - canonical CCVE and related pattern definitions
- `controls/`
  - promoted operator-facing controls derived from patterns
- `frameworks/`
  - grouped views over controls for standards, platforms, and workflows
- `mappings/`
  - Kyverno, Trivy, and Kubescape external mapping tables
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

See also:
- `docs/TAXONOMY.md`
- `docs/PRODUCT-THESIS.md`
- `docs/CANDIDATE-CONTROL-FAMILIES.md`
- `docs/EXTERNAL-REGO-LIBRARY-REVIEW.md`
- `dist/control-taxonomy-summary-v1.json`
- `dist/control-framework-bundle-v1.json`
- `dist/framework-coverage-report-v1.json`
- `dist/bundle-manifest-v1.json`

## Consumer Model

The expected interaction model is:
- `confighub-patterns` publishes versioned bundles,
- ConfigHub built-in functions consume those bundles through `confighub-scan`,
- standalone cub-based scan consumes those bundles locally and in CI,
- wrapper CLIs/TUIs consume the same bundle cache contract.

The initial shared cache contract is:
- `~/.confighub/pattern-bundles/current/`
- compatibility path: `~/.confighub/risk-catalog-v1.json`

## Validation

Local validation now runs natively in this repo:

```bash
make validate
```

If the sibling `confighub-scan` checkout is not at `../confighub-scan`, point the
copy-manifest check at it explicitly:

```bash
make validate FIRST_WAVE_SOURCE_REPO=/path/to/confighub-scan
```

## Current References

Until the migration is complete, the active planning contract remains in
`confighub-scan`:
- `docs/adr/0002-repo-boundaries-pattern-home-and-scan-surfaces.md`
- `planning/PATTERNS-REPO-MIGRATION-CHECKLIST.md`
- `planning/BUNDLE-CONTRACT-v1.md`
