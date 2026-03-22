# Bundle Scope

This repo is expected to publish the runtime-consumed pattern bundle used by
`confighub-scan`, `cub-scout`, and worker packaging.

## Required Bundle Files

The first bundle release set should include:
- `bundle-manifest-v1.json`
- `risk-catalog-v1.json`
- `risk-function-links-v1.json`
- `cross-tool-mapping-v1.json`

Optional alongside the same release set:
- `helm-pattern-database-v1.json`
- `control-taxonomy-summary-v1.json`
- `control-framework-bundle-v1.json`

Current state:
- the repo now generates `dist/bundle-manifest-v1.json`
- the manifest already advertises the promoted-taxonomy artifacts alongside the
  existing runtime catalog files

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
- no consumer should silently replace the full catalog with a legacy subset.
