# Bundle Scope

This repo is expected to publish the runtime-consumed pattern bundle used by:
- ConfigHub built-in scan functions
- standalone cub-based scan (`cub-scan` today, future `cub scan` or plugin possible)
- wrapper CLIs/TUIs such as `cub-scout`

## Required Bundle Files

The first bundle release set should include:
- `bundle-manifest-v1.json`
- `risk-catalog-v1.json`
- `risk-function-links-v1.json`
- `mappings/kyverno/kyverno-ccve-mappings-v1.json`
- `mappings/trivy/trivy-ccve-mappings-v1.json`
- `cross-tool-mapping-v1.json`

Optional alongside the same release set:
- `helm-pattern-database-v1.json`
- `control-taxonomy-summary-v1.json`
- `control-framework-bundle-v1.json`
- `framework-coverage-report-v1.json`

Projection rule:
- `control-taxonomy-summary-v1.json` is the authoring/CI summary
- `control-framework-bundle-v1.json` is the canonical released projection for
  control/framework consumers
- `framework-coverage-report-v1.json` is the compact derived coverage report

See also:
- `docs/BUNDLE-PROJECTIONS.md`

Current state:
- the repo now generates `dist/bundle-manifest-v1.json`
- the manifest now advertises the imported-evidence mapping files alongside the
  runtime catalog/link artifacts and the promoted-taxonomy artifacts
- the control/framework projections now have explicit schemas and validation

## Cache Layout

Target shared cache root:
- `~/.confighub/pattern-bundles/`

Selected active bundle:
- `~/.confighub/pattern-bundles/current/`

Compatibility bridge during migration:
- `~/.confighub/risk-catalog-v1.json`

## Publishing Rule

Bundles must be published with:
- a manifest,
- digests for runtime files,
- a bundle version independent from the scanner binary version.

## Consumer Rule

After the split:
- this repo is the source of truth for runtime pattern data,
- consumers read released bundle artifacts,
- controls remain bundle metadata while executable rules stay in
  `confighub-scan`,
- no consumer should silently replace the full catalog with a legacy subset.
