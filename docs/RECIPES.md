# Recipes

Task-oriented recipes for working with `confighub-patterns`. Every recipe follows the same shape: **task → command → expected output → verification**.

This repo owns the shared data (patterns, controls, frameworks, mappings, schemas, bundles). It does not own the scan engine — for engine and CLI recipes, see `../confighub-scan/docs/RECIPES.md`.

Terminology: `../confighub-scan/docs/GLOSSARY.md`.

---

## Prerequisites

**Task:** Confirm you can run repo validation.
**Command:**
```bash
make validate
```
**Output:** All gates green.
**Verify:** Exit code 0; `dist/` artifacts regenerated.

---

## Discovery

### Find a specific CCVE by ID

**Task:** Look up one risk by CCVE ID.
**Command:**
```bash
jq --arg id "CCVE-2025-4075" '.entries[] | select(.id==$id)' \
  ../confighub-scan/dist/risk-catalog-v1.json
```
**Output:** JSON object with id, name, severity, category, references, remediation.
**Verify:** Non-empty result.

### List all patterns for a keyword

**Task:** Find every pattern touching "ingress" (or any topic).
**Command:**
```bash
jq '.entries[] | select(.name | test("ingress"; "i")) | {id, name, severity}' \
  ../confighub-scan/dist/risk-catalog-v1.json
```
**Output:** Array of matching entries.
**Verify:** Result count > 0.

### List all controls

**Task:** See promoted operator-facing controls.
**Command:**
```bash
find controls -name '*.yaml' -print
```
**Output:** YAML files for each promoted control.
**Verify:** `find controls -name '*.yaml' | wc -l` matches the count in `docs/TAXONOMY.md`.

### List all frameworks

**Task:** See framework views (CIS, NSA, Argo, Flux, etc.).
**Command:**
```bash
find frameworks -name '*.yaml' -print
```
**Output:** Framework YAML files.
**Verify:** Each references controls that exist in `controls/`.

### Read the current bundle manifest

**Task:** See what's in the current released bundle.
**Command:**
```bash
jq '.version, .controls | length, .patterns | length' dist/bundle-manifest-v1.json
```
**Output:** Version, control count, pattern count.
**Verify:** Matches the claims in `README.md`.

---

## Mappings

### Inspect the Kyverno mapping table

**Task:** See which Kyverno policies map to which CCVEs.
**Command:**
```bash
jq '.mappings[] | {policy, rule, ccve_id}' mappings/kyverno/kyverno-ccve-mappings-v1.json
```
**Output:** Array of mapping entries.
**Verify:** Each `ccve_id` exists in the catalog.

### Inspect the Trivy mapping table

**Task:** See which Trivy check IDs map to which CCVEs.
**Command:**
```bash
jq '.mappings[] | {check_id, ccve_id}' mappings/trivy/trivy-ccve-mappings-v1.json
```
**Output:** Array of mappings.
**Verify:** Each `ccve_id` resolves in the catalog.

### Inspect the Kubescape mapping table

**Task:** See which Kubescape controls map to which CCVEs.
**Command:**
```bash
jq '.mappings[] | {control_id, control_name, ccve_id}' \
  mappings/kubescape/kubescape-ccve-mappings-v1.json
```
**Output:** Array of control-to-CCVE mappings.
**Verify:** Count matches the "Kubescape coverage" metric in the sibling repo's handoff.

---

## Authoring

### Add a new pattern

**Task:** Propose a new canonical risk pattern.
**Steps:**
1. Draft the pattern YAML under `patterns/` following an existing example.
2. Assign a CCVE ID from the next available slot in `docs/TAXONOMY.md`.
3. Add a fixture pair (positive + negative) in the **sibling repo** (`confighub-scan/fixtures/`) so a Go rule can detect it.
4. Run `make validate` here and `make validate` in the sibling repo.
**Verify:**
```bash
jq --arg id "CCVE-YYYY-NNNN" '.entries[] | select(.id==$id)' \
  ../confighub-scan/dist/risk-catalog-v1.json
```

### Add a new control (promote patterns)

**Task:** Promote a family of related patterns into an operator-facing control.
**Steps:**
1. Draft the control YAML under `controls/` referencing existing pattern IDs.
2. Update `docs/TAXONOMY.md` with the new control entry.
3. Run `make validate`.
**Verify:** Control YAML loads without errors; referenced patterns all exist.

### Add a new mapping entry (Kyverno/Trivy/Kubescape)

**Task:** Map an external tool's finding ID to a CCVE.
**Steps:**
1. Edit the appropriate `mappings/<tool>/<tool>-ccve-mappings-v1.json`.
2. Confirm the CCVE exists in the catalog.
3. Run `make validate`.
**Verify:**
```bash
jq '.mappings[] | select(.ccve_id=="CCVE-YYYY-NNNN")' mappings/<tool>/<tool>-ccve-mappings-v1.json
```

---

## Release

### Build the pattern bundle manifest

**Task:** Regenerate the released bundle manifest.
**Command:**
```bash
make validate FIRST_WAVE_SOURCE_REPO=../confighub-scan
```
**Output:** `dist/bundle-manifest-v1.json` updated.
**Verify:**
```bash
jq '.version, .patterns | length' dist/bundle-manifest-v1.json
```

### Cross-repo parity check

**Task:** Confirm the pattern assets in this repo match what the sibling scan repo expects.
**Command:**
```bash
make validate FIRST_WAVE_SOURCE_REPO=../confighub-scan
```
**Output:** Validation report with no diffs.
**Verify:** Exit code 0.

---

## For AI agents

### Discover what's in the bundle

**Task:** Understand what this repo provides, from minimal context.
**Command:**
```bash
cat AGENTS.md
cat AI-README-FIRST.md
cat docs/REPO-SCOPE.md
```
**Output:** Discovery index, AI contributor rules, repo scope.

### Cross-reference with the engine

**Task:** Understand where data ends and engine begins.
**Command:**
```bash
cat ../confighub-scan/AGENTS.md
cat ../confighub-scan/docs/GLOSSARY.md
```

### Verify the two repos agree

**Task:** Confirm the catalog in the engine matches the patterns here.
**Command:**
```bash
diff <(jq -S '.entries[].id' ../confighub-scan/dist/risk-catalog-v1.json) \
     <(find patterns -name '*.yaml' -exec yq '.id' {} \; 2>/dev/null | sort)
```
**Output:** Minimal diff; anything here that's missing from the engine catalog indicates a promotion or build gap.

---

## See also

- `AGENTS.md` — AI agent entry point
- `AI-README-FIRST.md` — AI contributor rules
- `docs/REPO-SCOPE.md` — what lives here and why
- `docs/BUNDLE-SCOPE.md` — bundle contract
- `docs/TAXONOMY.md` — controls, frameworks, promoted patterns
- `../confighub-scan/docs/GLOSSARY.md` — shared terminology
- `../confighub-scan/docs/RECIPES.md` — engine/CLI recipes
