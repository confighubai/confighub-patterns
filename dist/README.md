# dist

Released runtime bundle artifacts will be written here.

This directory should eventually contain versioned outputs such as:
- `bundle-manifest-v1.json`
- `risk-catalog-v1.json`
- `risk-function-links-v1.json`
- `cross-tool-mapping-v1.json`
- `control-taxonomy-summary-v1.json`
- `control-framework-bundle-v1.json`
- `framework-coverage-report-v1.json`

Projection guidance:
- `control-taxonomy-summary-v1.json` is the authoring and CI summary view
- `control-framework-bundle-v1.json` is the released projection for
  control/framework consumers
- `framework-coverage-report-v1.json` is the compact derived report for
  coverage and discovery surfaces
