# Product Thesis

The long-term goal is not merely to be a generic scanner with more checks.

The long-term goal is to pair a large, reusable, well-organized configuration
risk database with the best system for understanding and fixing risk across
intent, live state, and connected evidence.

## Pillar 0: Database Breadth With Structure

Database breadth is part of the moat when it stays organized.

This repo should keep growing through:
- mined canonical patterns
- borrowed external patterns and control ideas
- third-party mappings
- promoted controls and framework views

The point is not to pretend every borrowed pattern is immediately a native rule.
The point is to keep making the database broader, more reusable, and easier for
consumers to benefit from quickly.

## Pillar 1: GitOps And Operator Depth

Focus deeply on the configuration systems where teams actually lose time:
- Argo CD
- Flux
- HelmRelease, Kustomization, Application, ApplicationSet, GitRepository
- reconcile failures and degraded live state
- configuration that is syntactically valid but operationally bad

The output should answer:
- what is wrong?
- where is it wrong?
- why did it fail in practice?

## Pillar 2: Multi-Surface Evidence Unification

Use one canonical evidence model across:
- native scanner findings
- imported third-party findings
- connected worker validation
- live snapshot results
- intent-vs-live comparisons

The product should help users distinguish:
- bad desired configuration
- broken rollout or reconciliation
- drift that only exists in live state
- findings that are corroborated across multiple evidence sources

## Pillar 3: AI And Operator Usability

The product should help operators ask and answer practical questions:
- what is wrong with this Flux app?
- what does good Argo configuration look like?
- why is this broken in prod but not in git?
- what is the safest next fix?

This means the corpus must support:
- explanation
- prioritization
- fix guidance
- safety-aware remediation

## Implication For This Repo

`confighub-patterns` should become more than a data dump.

It should provide:
- broad canonical patterns that keep growing over time
- borrowed and normalized external pattern knowledge where useful
- promoted controls
- framework views
- remediation and safety metadata
- release-ready bundles that other tools can consume consistently
