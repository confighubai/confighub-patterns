# Product Thesis

The long-term goal is not to be a generic scanner with more checks.

The long-term goal is to be the best system for understanding and fixing
configuration risk across intent, live state, and connected evidence.

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
- broad canonical patterns
- promoted controls
- framework views
- remediation and safety metadata
- release-ready bundles that other tools can consume consistently
