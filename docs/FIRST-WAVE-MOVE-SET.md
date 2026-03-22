# First-Wave Move Set

This document records the safest first assets to copy from `confighub-scan`
into `confighub-patterns`.

The goal of the first wave is not to finish the split. The goal is to move the
data-like pattern assets that clearly belong here while leaving engine/runtime
code in place.

## Rules For This Wave

- copy first, then verify consumers, then switch authoring
- do not delete source-of-truth assets from `confighub-scan` in the same step
- do not move engine-only scripts, tests, fixtures, or benchmarks here
- keep released bundle compatibility with existing local cache paths

## Copy First

### Pattern source

From `confighub-scan`:
- `risks/*.yaml`
- `risks/archive/`
- `risks/README.md`

To here:
- `patterns/`
- `docs/`

### External mappings

From `confighub-scan`:
- `risks/kyverno/kyverno-ccve-mappings-v1.json`
- `risks/trivy/trivy-ccve-mappings-v1.json`
- `scripts/build-cross-tool-mapping.py`
- `risks/quality/cross-tool-mapping-policy-v1.json`

To here:
- `mappings/`
- `scripts/`
- `quality/`

### Schema and taxonomy

From `confighub-scan`:
- `risks/schema/ccve-taxonomy-v1.yaml`
- `risks/schema/risk-catalog-v1.schema.json`
- `risks/schema/helm-pattern-database-v1.schema.json`

To here:
- `schema/`

### Pattern-quality and promotion inputs

From `confighub-scan`:
- `risks/quality/launch-rules-v1.json`
- `risks/quality/promotion-quality-policy-v1.json`
- `risks/quality/risk-function-link-thresholds-v1.json`
- `risks/quality/severity-calibration-policy-v1.json`
- `risks/quality/severity-calibration-policy-v2.json`
- `risks/quality/severity-calibration-baseline-v1.json`
- `risks/quality/severity-review-sample-policy-v1.json`
- `risks/quality/severity-release-decision-policy-v1.json`
- `risks/quality/unresolved-external-findings-input-v1.json`
- `risks/quality/unresolved-external-findings-policy-v1.json`
- `risks/quality/mining-candidate-policy-v1.json`
- `risks/quality/mining-query-templates-v1.json`
- `risks/quality/pattern-inventory-overrides-v1.json`

To here:
- `quality/`

### Pattern-facing builders

From `confighub-scan`:
- `scripts/classify-remedies.py`
- `scripts/build-risk-function-links.py`
- `scripts/build-severity-review-sample.py`
- `scripts/validate-risk-function-links.py`
- `scripts/validate-severity-calibration.py`
- `scripts/validate-severity-release-decision.py`

To here:
- `scripts/`

### Released bundle outputs

From `confighub-scan`:
- `dist/risk-catalog-v1.json`
- `dist/risk-function-links-v1.json`
- `dist/helm-pattern-database-v1.json`
- `dist/quality/cross-tool-mapping-v1.json`
- `dist/quality/pattern-inventory-v1.json`
- `dist/quality/pattern-inventory-summary-v1.json`
- `dist/quality/pattern-queue-report-v1.json`
- `dist/quality/mining-candidate-queue-v1.json`
- `dist/quality/severity-review-sample-v1.json`
- `dist/quality/unresolved-external-findings-rollout-v1.json`

To here:
- `dist/`

## Keep In `confighub-scan`

Do not move these in the first wave:
- `pkg/`
- `cmd/`
- `plugins/`
- `compat/`
- `test/`
- `fixtures/`
- `benchmarks/`
- `corpus/`
- `confighub/`
- engine-only quality inputs
- engine-only inventory and contract-check scripts

## Done Means

The first wave is successful when:
- copied assets exist here with no content drift
- `confighub-scan` can still run using local artifacts
- bundle consumers can point at released outputs without behavior changes
- no source deletion happens until the dual-read period is complete
