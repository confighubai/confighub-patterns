# Bundle Projections

This repo now publishes three different control/framework JSON views, and they
do not all play the same role.

## Source Of Truth

The source of truth is still the YAML authoring layer:
- `controls/**/*.yaml`
- `frameworks/**/*.yaml`
- `dist/risk-catalog-v1.json` for pattern metadata carried into the projections

Those source files are promoted and grouped into the generated JSON artifacts
below.

## Projection Roles

### 1. `dist/control-taxonomy-summary-v1.json`

Use this as the **authoring and CI summary**.

It is useful for:
- coverage summaries
- quick diffs during repo work
- builders that need a compact inventory first

It is **not** the main released consumer contract for control/framework users.

### 2. `dist/control-framework-bundle-v1.json`

Use this as the **canonical released projection** for consumers that want the
promoted control and framework layer.

It packages:
- normalized control documents
- normalized framework documents
- pattern references pulled from the risk catalog

This is the projection that answers:
- what are the current promoted controls?
- which frameworks group them?
- which canonical pattern IDs do those controls cover?

### 3. `dist/framework-coverage-report-v1.json`

Use this as the **compact derived report** for discovery, coverage, and UI-like
summary surfaces.

It is intentionally smaller than the full control/framework bundle and focuses
on:
- framework-level pattern coverage
- cross-family framework detection
- summarized supported surfaces / consumers / detection modes

## Release Rule

For the current migration wave:
- `control-framework-bundle-v1.json` is the released control/framework payload
- `framework-coverage-report-v1.json` is the released compact report that sits
  beside it
- both are advertised in `dist/bundle-manifest-v1.json`
- both are additive to the existing risk-catalog contract, not replacements for it

## Compatibility Rule

Existing `risk-catalog-v1.json` consumers can ignore these projections.

That compatibility matters because:
- `confighub-scan` still has consumers that only need catalog + mapping assets
- the migration wave is intentionally additive and non-destructive
- control/framework consumers should not force older risk-catalog readers to
  change behavior

## Validation Rule

The released projection pair now has explicit schemas and validation:
- `schema/control-framework-bundle-v1.schema.json`
- `schema/framework-coverage-report-v1.schema.json`
- `scripts/validate-control-projections.py`

Run:

```bash
make validate
```

That validation checks:
- both schemas are valid JSON Schema
- both generated artifacts match their schemas
- bundle counts and ID inventories match the underlying rows
- framework report counts and cross-family IDs match the underlying bundle
