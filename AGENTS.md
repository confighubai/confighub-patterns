# AGENTS.md — AI Agent Entry Point

**Read this first if you are an AI agent (Claude, Codex, Cursor, Copilot, Aider, or any LLM with shell access).**

This file is the discovery index. `AI-README-FIRST.md` holds the "don't do this here" contract for AI contributors — read that before making changes. This file tells you what exists and where to look.

## What this repo is

`confighub-patterns` is the shared data and bundle repo for `confighub-scan` and ConfigHub-connected scanning flows.

If `confighub-scan` is the engine, this repo is the data it runs on.

It holds:

- pattern definitions
- promoted controls
- framework views (CIS, NSA, Argo, Flux, etc.)
- third-party mapping tables (Kyverno, Trivy, Kubescape)
- external evidence schemas
- bundle manifests and release artifacts

**This is not a second scanner.** It does not own executable Go rules, CLI behavior, worker processes, scan orchestration, or ConfigHub integration code. Those live in `confighub-scan`.

## Task → File / Tool Map

| If the user wants to... | Look at |
|---|---|
| Find a specific CCVE definition | `patterns/` (source YAML) or bundle artifacts in `dist/` |
| See promoted controls | `controls/` and `docs/TAXONOMY.md` |
| See a framework view | `frameworks/` |
| Find an operator recipe or recipe contract | `recipes/` and `schema/operator-recipe-v1.schema.json` |
| See a third-party mapping | `mappings/kyverno/`, `mappings/trivy/`, `mappings/kubescape/` |
| Understand the bundle contract | `schema/` and `docs/BUNDLE-SCOPE.md` |
| Find the current released bundle | `dist/bundle-manifest-v1.json` |
| Run local validation | `make validate` |
| Know what belongs here vs in `confighub-scan` | `AI-README-FIRST.md` and `docs/REPO-SCOPE.md` |

## Canonical Files

| What | Where |
|---|---|
| AI contributor rules | `AI-README-FIRST.md` |
| Repo scope and boundaries | `docs/REPO-SCOPE.md` |
| Bundle scope | `docs/BUNDLE-SCOPE.md` |
| Taxonomy of controls and frameworks | `docs/TAXONOMY.md` |
| Migration status from `confighub-scan` | `docs/MIGRATION-STATUS.md` |
| Product thesis | `docs/PRODUCT-THESIS.md` |
| Candidate control families | `docs/CANDIDATE-CONTROL-FAMILIES.md` |
| Operator recipe pack seed | `recipes/README.md` |
| Operator recipe schema | `schema/operator-recipe-v1.schema.json` |
| Release bundle manifest | `dist/bundle-manifest-v1.json` |
| First-wave copy manifest | `dist/first-wave-copy-manifest-v1.json` |

## Terminology Anchor

For the precise meanings of **risk**, **pattern**, **rule**, **finding**, **control**, **framework**, **bundle**, **surface**, **lane**, **track**, **evidence**, see the glossary in the sibling repo: `../confighub-scan/docs/GLOSSARY.md`.

The distinction that matters most here:
- **Pattern** — a reusable detection spec (YAML) that lives in this repo
- **Rule** — a Go function in `confighub-scan/pkg/scan/rules_*.go` that implements the detection
- **Risk** — a catalog entry with a CCVE ID
- **Control** — an operator-facing grouping of patterns

This repo owns patterns, controls, and frameworks. The sibling repo owns rules.

## Before You Edit

1. Read `AI-README-FIRST.md` — the bootstrap-mode rules. Do not move engine code here; do not delete pattern assets from `confighub-scan`.
2. Read `docs/REPO-SCOPE.md` for what belongs here.
3. Read `docs/MIGRATION-STATUS.md` for where things currently live.
4. If editing patterns or controls, run `make validate` before committing.

## Companion Repo

`confighub-scan` — the engine and integration repo. Look there for:

- Go rule implementations
- `cub-scan` CLI
- ConfigHub worker functions (`validate-unit`, `scan-unit`, etc.)
- Adapters (Kyverno, Trivy, Kubescape)
- Benchmarks and test fixtures

Its entry point for AI agents: `../confighub-scan/AGENTS.md`.

## What This Repo Is Not

- It is not a scanner. It has no executable detection code.
- It is not the place for CLI changes.
- It is not where ConfigHub worker glue lives.
- It is not a duplicate of `confighub-scan/risks/` — those assets are in migration (see `docs/MIGRATION-STATUS.md`).

## Verification Floor

```bash
make validate
```

For cross-repo parity (pointing at a sibling `confighub-scan` checkout):

```bash
make validate FIRST_WAVE_SOURCE_REPO=../confighub-scan
```

## Related AI Docs

- `AI-README-FIRST.md` — AI contributor rules (read before editing)
- `README.md` — human-facing overview
- `docs/REPO-SCOPE.md` — what lives here and why
- `docs/TAXONOMY.md` — controls, frameworks, promoted patterns
- `../confighub-scan/AGENTS.md` — companion repo entry point
- `../confighub-scan/docs/GLOSSARY.md` — shared terminology
