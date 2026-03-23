# External Rego Library Review

This note captures what is worth borrowing from public Kubernetes control
libraries that organize content as frameworks, controls, and executable rules.

Primary comparison target reviewed in March 2026:
- `kubescape/regolibrary`

## What Is Worth Borrowing

### 1. Clear promoted taxonomy

The strongest idea is the separation between:
- framework views
- control metadata
- executable rule logic

That reinforces the shape we want here:
- `patterns/` as the broad canonical corpus
- `controls/` as the stable operator-facing promoted subset
- `frameworks/` as grouped views for standards, platforms, and workflows

### 2. Metadata-rich controls

The useful control-library pattern is not just "a check exists", but:
- stable IDs
- summary and description
- severity or score
- remediation guidance
- scanning scope or supported surfaces
- framework membership

That maps well to the control-definition shape we already adopted, especially
for supported surfaces, consumers, evidence expectations, and remediation
safety.

### 3. Frameworks as views, not the source of truth

Frameworks are useful when they stay lightweight and opinionated:
- platform views
- standards bundles
- operator workflow bundles

They should stay derived from stable promoted controls, not become the place
where semantics only exist implicitly.

## What We Should Not Copy

### 1. Do not move native execution into `confighub-patterns`

Public Rego control libraries often keep rules beside control metadata because
their execution model is policy-library-centric.

That is not our boundary.

For us:
- `confighub-patterns` should stay data-like
- `confighub-scan` should stay the native engine and normalization layer

### 2. Do not narrow the corpus to only shipped controls

Our long-term value is broader than a promoted control library:
- candidate patterns
- curated and launch-validated patterns
- mappings and aliases
- remediation safety metadata
- promotion and quality artifacts

So `controls/` should be a promoted subset, not the whole story.

### 3. Do not give up the evidence model

A control library alone does not solve:
- repo-vs-live comparison
- imported evidence normalization
- connected worker validation
- corroboration across tools and environments

We should keep one canonical evidence model across those surfaces.

## Concrete Takeaways For This Repo

### Adopt now

- keep growing `controls/` and `frameworks/` as first-class top-level layers
- make framework bundles easy to publish in `dist/`
- keep control metadata rich enough for operator UX and AI explanations

### Prioritize next

- GitOps and operator reliability controls
- RBAC and identity controls
- network and exposure baseline controls
- secrets and credential hygiene controls
- cluster and node hardening controls

### Use external libraries as idea sources, not authorities

The best way to use external Rego libraries is:
- borrow structural clarity
- review candidate control families
- map overlapping controls back to canonical pattern IDs where useful
- avoid cloning their execution/runtime assumptions

## Where Our Edge Should Remain

The differentiators to preserve are:
- GitOps and operator-specific depth
- intent-vs-live reasoning
- evidence unification across native, imported, and connected surfaces
- remediation and safety metadata
- canonical corpus quality and promotion discipline

That is the part a generic control library does not give us for free.
