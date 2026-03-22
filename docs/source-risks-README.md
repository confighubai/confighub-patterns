# Risk Catalog Guide

This directory is the canonical risk data store for `confighub-scan`.

## Data Layers

| Layer | Path | Notes |
|------|------|-------|
| Canonical corpus | `CCVE-2025-*.yaml` | Full set of maintained risk definitions |
| Legacy runtime subset | `index.json` | Curated subset used for legacy runtime compatibility |
| Normalized catalog | `../dist/risk-catalog-v1.json` | Primary machine contract for plugin consumers |
| Risk/function links | `../dist/risk-function-links-v1.json` | Cross-link health report for remedies and functions |
| Schema | `schema/risk-catalog-v1.schema.json` | Catalog contract validation |
| Taxonomy contract | `schema/ccve-taxonomy-v1.yaml` | Allowed category/severity/confidence vocabulary |
| Source imports | `kyverno/` and others | Source-native datasets not yet canonical CCVEs |

Operational rule:
- canonical corpus can be larger than runtime subset,
- runtime subset entries must always resolve to valid canonical IDs.

## Quality Maturity and Promotion

The CCVE corpus contains mixed-maturity entries. Some early mined patterns are intentionally preserved as candidates, while newer entries are more deeply validated.

Use this promotion ladder:
1. Candidate (mined/seeded): keep `confidence` at `low` or `unknown` until evidence and reproducibility are strong.
2. Curated: upgrade to `medium`/`high` only after source verification and deterministic detection/remediation content are present.
3. Launch-validated: treat as launch-grade only when scanner rules and benchmark/quality gates cover the pattern class.

Important:
1. `confidence` is an evidence-quality signal, not a substitute for benchmark validation.
2. Catalog size indicates knowledge coverage; it does not imply equal detector readiness across entries.
3. See `../planning/CCVE-QUALITY-CRITERIA.md` for acceptance criteria and quality tier definitions.

## Contract Semantics

- `../dist/risk-catalog-v1.json` is the primary consumer contract.
- `index.json` remains supported as a legacy subset contract.
- plugins should integrate through normalized catalog/runtime exports, not raw source imports.
- remediation safety classes are normalized into `remedy.safety_class`:
  - `manual_only`
  - `safe_auto`
  - `unsafe_auto`

Index validation:

```bash
python3 test/validate-risk-index.py
```

## Build and Verify

Build artifacts:

```bash
python3 scripts/build-risk-catalog.py
python3 scripts/build-risk-function-links.py
```

Check mode for CI:

```bash
python3 scripts/build-risk-catalog.py --check
```

Golden fixture tests:

```bash
python3 test/test-catalog-scripts.py
```

Runtime feed export:

```bash
python3 scripts/export-runtime-feed.py --output -
```

Launch quality/determinism gate:

```bash
go run ./cmd/validate-risk-quality \
  --catalog dist/risk-catalog-v1.json \
  --policy risks/quality/launch-rules-v1.json \
  --fixtures-dir fixtures \
  --report-out dist/quality/launch-quality-report.json
```

Risk/function link non-regression gate:

```bash
python3 scripts/validate-risk-function-links.py \
  --report dist/risk-function-links-v1.json \
  --policy risks/quality/risk-function-link-thresholds-v1.json
```

Expected runtime feed fields:
- `schema_version: risk-runtime-feed-v1`
- `source_format: risk-catalog-v1 | risk-index-v3`
- `entries[]` with runtime keys (`id`, `name`, `category`, `severity`, `tool`, `track`)

## Pattern Authoring Format

Each canonical pattern is a `CCVE-2025-*.yaml` document with structured detection and remediation content.

```yaml
id: CCVE-2025-0001
category: SOURCE|RENDER|APPLY|DRIFT|STATE|CONFIG|DEPEND|ORPHAN
track: misconfiguration|advisory
severity: critical|warning|info
title: "Human-readable title"
description: |
  Explain the configuration fault and resulting risk.
detection:
  conditions:
    - field: "kind"
      value: "ResourceType"
remediation:
  description: |
    Explain the safe fix path.
  commands:
    - "kubectl command to remediate"
remedy:
  type: config_fix
  safety_class: safe_auto
sources:
  - url: https://github.com/org/repo/issues/123
    type: github_issue
```

## Fast Scaffold Workflow

Use one command to create a new risk, optional remediation function, and optional runtime subset entry:

```bash
python3 scripts/new-risk.py \
  --id CCVE-2025-9001 \
  --name "Example deterministic misconfiguration" \
  --category CONFIG \
  --severity warning \
  --tool flux \
  --with-function fix-example-timeout \
  --add-to-index
```

Generated files:
- `risks/CCVE-2025-9001.yaml`
- `functions/fix-example-timeout.yaml` (when `--with-function` is set)
- `risks/index.json` entry (when `--add-to-index` is set)

## Authoring Workflow

1. Scaffold with `scripts/new-risk.py` or add/update canonical YAML manually in `risks/`.
2. Replace scaffold TODOs with deterministic detection and safe remediation.
3. Set `confidence` conservatively (`low`/`unknown` first, promote with evidence).
4. Rebuild catalog artifacts.
5. Run validation and golden fixture tests.
6. Add ID to `index.json` only if it belongs in runtime subset.
7. Record provenance in `MINING-LOG.md`.

## Third-Party Sources

Third-party scanners are evidence inputs that can seed or enrich canonical patterns.

- Kyverno and Trivy runbook: `THIRD-PARTY-TOOLS.md`

## Suggesting New Patterns

If you are not opening a code PR, use the GitHub issue form:

- `Pattern Suggestion (Risk/CCVE)`

Contribution requirements and acceptance criteria:

- `../CONTRIBUTING.md`
- `../planning/CCVE-QUALITY-CRITERIA.md`

## Categories

| Category | Description |
|----------|-------------|
| SOURCE | Source and registry access failures |
| RENDER | Template and render pipeline failures |
| APPLY | Resource apply and admission failures |
| DRIFT | Desired/live state divergence |
| STATE | Controller stuck states and reconcile deadlocks |
| CONFIG | Unsafe or invalid configuration states |
| DEPEND | Dependency and ordering failures |
| ORPHAN | Unmanaged resources and ownership loss |
| OVER_PROVISION | Resource right-sizing and over-allocation advisory signals |

## Related Files

| File | Purpose |
|------|---------|
| `MINING-LOG.md` | Provenance log for mined patterns |
| `KUBERNETES-ISSUE-MINING.md` | Mining source methodology |
| `INDEX.md` | Current operator index for risk data and artifacts |
| `archive/` | Historical and exploratory risk notes |
| `quality/launch-rules-v1.json` | Launch-track quality metadata and fixture expectations |
| `schema/ccve-taxonomy-v1.yaml` | Category/severity/confidence taxonomy contract |

Planning docs are in `../planning/`; treat `../planning/INDEX.md` as the status authority.
