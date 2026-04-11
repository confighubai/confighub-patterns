# External Rego Library Review

This note captures what is worth borrowing from public Kubernetes control
libraries that organize content as frameworks, controls, and executable rules.

Primary comparison target refreshed on April 11, 2026:
- `kubescape/regolibrary`

Observed structure in the April 11, 2026 checkout:
- 16 frameworks
- 265 controls
- 274 rule directories
- 5 attack-track bundles
- category skew led by Control plane, Workload, Access control, and Network
- scanning scopes still skew heavily toward cluster and file, with much smaller
  AKS/EKS/cloud coverage pockets

Current local comparison point in `confighub-patterns`:
- 25 promoted controls
- 7 framework views
- one explicit split between broad canonical patterns and a smaller promoted
  control/framework surface

Observed product-shape signal:
- strong breadth in generic control-plane and CIS-style checks
- meaningful workload, RBAC, secrets, and exposure coverage
- meaningful provider-managed cluster posture coverage for EKS and AKS
- very little GitOps/operator-specific depth in the public control-library
  surface beyond isolated CVE or Argo-centric checks

## What Is Worth Borrowing

### 1. Clear promoted taxonomy

The strongest idea is the visible separation between:
- framework views
- control metadata
- executable rule logic

That reinforces the shape we want here:
- `patterns/` as the broad canonical corpus
- `controls/` as the stable operator-facing promoted subset
- `frameworks/` as grouped views for standards, platforms, and workflows

### 2. Stable IDs instead of stringly framework membership

One structural detail is worth copying carefully, not literally.

Kubescape makes framework membership and control-library layering very visible,
but many of its framework references still depend on control names or active
control lists that are less stable than IDs.

We should keep our current direction:
- stable `CTRL-*` identifiers for control membership
- stable `FRM-*` identifiers for framework views
- explicit projections in `dist/` for released consumers

Borrow the layered shape, not the name-coupling.

### 3. Metadata-rich controls

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

### 4. Curated baseline frameworks

The strongest framework idea is not standards-only packaging. The useful part
is curated operator-facing baseline views like:
- broad platform best-practice bundles
- workload-focused bundles
- security posture bundles

That is a good fit for our own `frameworks/` layer, especially for a
cross-family `platform-best` view and future GitOps/operator workflow bundles.

### 5. Frameworks as views, not the source of truth

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

### 4. Do not adopt attack tracks as a top-level taxonomy layer yet

The `attack-tracks/` directory in `regolibrary` is interesting, but it is not a
good near-term fit for this repo's current contract.

For now, we should prefer:
- stable patterns
- promoted controls
- lightweight frameworks
- compact operator recipes

If we ever revisit attack-track style packaging, it should come later as a
derived projection, not as a new source-of-truth layer.

### 5. Do not chase broad control-plane parity as the near-term goal

The external library is rich in:
- kube-bench-style control-plane flag and file-permission checks
- cloud-provider hardening variants
- generic CIS-aligned posture breadth

That is useful as a backlog reference, but it is not where we should try to
differentiate first.

## Concrete Takeaways For This Repo

### Keep now

- keep growing `controls/` and `frameworks/` as first-class top-level layers
- make framework bundles easy to publish in `dist/`
- keep control metadata rich enough for operator UX and AI explanations
- keep external-library overlap as mapping data, not copied execution or copied
  control taxonomies

### What already landed from this review

- `#12` is done: policy-control and admission baseline posture is now visible as
  promoted controls under `controls/cluster/`
- `#13` is done: Gateway/public service-edge coverage is now part of the
  promoted network family
- `#3` is now a PR-backed bundle-projection contract instead of a vague future
  cleanup
- `#15` and `#14` are now PR-backed recipe/schema work instead of loose prose
  ideas

### Mapping guidance

When an external control library clearly overlaps with our canonical corpus, the
preferred path is:
- map external control IDs to canonical `CCVE-*` IDs
- keep that mapping in `mappings/`
- avoid importing the external control object as a second source of truth

Today that already exists for imported Kubescape control IDs in:
- `mappings/kubescape/kubescape-ccve-mappings-v1.json`

That should remain the model for overlap: explicit mappings, not copied
taxonomy.

### Next follow-on from the refreshed review

The strongest remaining family exposed by the refreshed `regolibrary` checkout
is provider-managed cluster hardening:
- private endpoint and private node posture
- managed-cluster network policy enablement
- provider-specific identity and registry posture
- external secret storage and image-scanning expectations

That is now captured as:
- `#18` Review managed-cluster hardening families from external control libraries

### Keep GitOps good+bad baselines repo-owned

For Argo CD and Flux specifically, our primary reference set should remain the
owned examples in `confighub-scan`:
- `examples/gitops-good-baselines/`
- `examples/gitops-bad-baselines/`

That keeps our GitOps operator story anchored in:
- repo-vs-live reasoning
- Argo/Flux-specific intent and reconcile behavior
- promoted controls tied back to our own examples
- scanner-backed examples that we can use in demos, docs, AI explainers, and
  future benchmark work

In other words:
- use Kubescape/Rego libraries to expand backlog ideas for generic control
  families
- keep Argo CD and Flux baseline ownership in our own examples and promoted
  controls

### Gaps that reinforce our product wedge

The external library had very little public control coverage for:
- Flux `GitRepository`, `Kustomization`, and `HelmRelease` baselines
- Argo CD `ApplicationSet` generator safety and reconcile-path reasoning
- intent-vs-live comparison as a first-class workflow concept

That reinforces the decision to make GitOps/operator-specific depth a primary
long-term edge for this repo family.

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
