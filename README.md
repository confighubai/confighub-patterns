# confighub-patterns

`confighub-patterns` is the shared data and bundle repo used by
`confighub-scan` and ConfigHub-connected scanning flows.

If `confighub-scan` is the engine, this repo is the data it runs on.

## What This Repo Is For

This repo holds the reusable assets behind scanning and validation:

- pattern definitions
- promoted controls
- framework views
- third-party mapping tables
- external evidence schemas
- bundle manifests and release artifacts

It exists so the scanner and ConfigHub integrations can share one pattern and
bundle source instead of copying data logic into multiple places.

## What This Repo Is Not

This is not a second scanner.

It does not own:

- executable Go rules
- CLI behavior
- worker processes
- scan orchestration
- ConfigHub integration code

Those stay in `confighub-scan`.

## How It Gets Used

### Outside ConfigHub

`cub-scan` uses bundle assets from this repo for:

- risk and pattern metadata
- promoted controls
- imported-evidence mappings
- external evidence schema contracts

### Inside ConfigHub

ConfigHub function workers use `confighub-scan` for execution and this repo for:

- pattern and CCVE data
- controls and framework views
- mapping tables
- released bundle artifacts

### For Evidence Contracts

The canonical external evidence schema also lives here, so advisory evidence
export can stay consistent across tools.

## What Lives Here

The intended layout is:

- `patterns/`
  Canonical pattern definitions.
- `controls/`
  Operator-facing promoted controls.
- `frameworks/`
  Grouped views for standards, platforms, and workflows.
- `mappings/`
  Kyverno, Trivy, Kubescape, and other external mappings.
- `schema/`
  Bundle and evidence schemas.
- `scripts/`
  Bundle and release builders.
- `dist/`
  Generated bundle artifacts.
- `docs/`
  Authoring and release guidance.

## Current Status

As of 2026-04-02:

- this repo is active and used as the shared bundle home
- the release manifest exists at `dist/bundle-manifest-v1.json`
- the promoted taxonomy includes 25 controls, 7 frameworks, and 214 covered
  pattern IDs
- Kyverno, Trivy, and Kubescape mappings are published as bundle assets
- the external evidence schema is published here
- local validation is wired through `make validate`

`confighub-scan` remains the engine and integration repo.

## How To Work On It

Validate the repo locally with:

```bash
make validate
```

If your sibling `confighub-scan` checkout is not at `../confighub-scan`, point
the copy-manifest check at it explicitly:

```bash
make validate FIRST_WAVE_SOURCE_REPO=/path/to/confighub-scan
```

## The Relationship To `confighub-scan`

Use this simple split:

| Concern | Repo |
|---|---|
| Scan engine and Go rules | `confighub-scan` |
| ConfigHub workers and SDK integration | `confighub-scan` |
| Local CLI behavior | `confighub-scan` |
| Pattern, control, mapping, and schema data | `confighub-patterns` |
| Bundle artifacts | `confighub-patterns` |

If you are looking for "how do I scan something?" go to `confighub-scan`.
If you are looking for "where does the shared pattern and bundle data live?" you
are in the right repo.

## Best Related References

- `../confighub-scan/README.md`
- `../confighub-scan/docs/START-HERE.md`
- `docs/MIGRATION-STATUS.md`
- `docs/TAXONOMY.md`
- `docs/EXTERNAL-REGO-LIBRARY-REVIEW.md`
- `dist/bundle-manifest-v1.json`
