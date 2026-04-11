# Releasing

`confighub-patterns` releases a versioned bundle of data and schemas. It does
not publish an installable CLI, so there is no Homebrew step for this repo.

## What A Release Publishes

A tagged release publishes:
- the files referenced by `dist/bundle-manifest-v1.json`
- the matching release decision packet at `release/severity-decisions/<tag>.json`
- a GitHub release tarball and checksum

The automation lives in `.github/workflows/release.yml`.

## Before You Tag

1. Make sure `main` contains the intended bundle state.
2. Set `dist/bundle-manifest-v1.json` to the release version, for example
   `v0.1.1` or `v0.2.0-rc.1`.
3. Add the matching release decision packet:
   `release/severity-decisions/<tag>.json`.

## Local Verification

If you have a sibling `confighub-scan` checkout at `../confighub-scan`, run:

```bash
make validate FIRST_WAVE_SOURCE_REPO=../confighub-scan BUNDLE_VERSION=v0.1.1
python3 scripts/validate-severity-release-decision.py \
  --decision-file release/severity-decisions/v0.1.1.json \
  --review-sample dist/quality/severity-review-sample-v1.json \
  --policy quality/severity-release-decision-policy-v1.json \
  --release-version v0.1.1
```

If your sibling checkout is elsewhere, point `FIRST_WAVE_SOURCE_REPO` at it.

## Tagging

Push the release-prep commit to `main`, then create and push the tag:

```bash
git tag -a v0.1.1 -m "v0.1.1"
git push origin v0.1.1
```

For prereleases, use an `-rc.` suffix such as `v0.2.0-rc.1`.

## What The Workflow Does

On a `v*` tag, the release workflow:
- validates the matching release decision packet
- runs the repo validation floor
- packages the bundle files referenced by `dist/bundle-manifest-v1.json`
- publishes a GitHub release with the tarball and checksum
- marks `-rc.` tags as prereleases

If the workflow cannot check out the sibling `confighub-scan` repo, it falls
back to the repo-native validation path instead of failing immediately.

## Release Artifacts

Published release assets are named:
- `confighub-patterns-<tag>-bundle.tar.gz`
- `confighub-patterns-<tag>-bundle.tar.gz.sha256`

## Homebrew

Homebrew is not applicable here. `confighub-patterns` publishes bundle data and
schemas, not an installable executable.
