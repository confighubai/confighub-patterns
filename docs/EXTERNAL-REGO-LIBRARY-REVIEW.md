# External Rego Library Review

This note captures what is worth borrowing from public Kubernetes control
libraries that organize content as frameworks, controls, and executable rules.

Primary comparison target reviewed in March 2026:
- `kubescape/regolibrary`

Observed structure in the March 23, 2026 checkout:
- 16 frameworks
- 302 controls
- 2391 rules
- category skew led by Control plane, Workload, Access control, and Network

Observed product-shape signal:
- strong breadth in generic control-plane and CIS-style checks
- meaningful workload, RBAC, secrets, and exposure coverage
- very little GitOps/operator-specific depth in the public control library
  surface

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

### 3. Curated baseline frameworks

The strongest framework idea is not standards-only packaging. The useful part
is curated operator-facing baseline views like:
- broad platform best-practice bundles
- workload-focused bundles
- security posture bundles

That is a good fit for our own `frameworks/` layer, especially for a
cross-family `platform-best` view and future GitOps/operator workflow bundles.

### 4. Frameworks as views, not the source of truth

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

### 4. Do not chase broad control-plane parity as the near-term goal

The external library is rich in:
- kube-bench-style control-plane flag and file-permission checks
- cloud-provider hardening variants
- generic CIS-aligned posture breadth

That is useful as a backlog reference, but it is not where we should try to
differentiate first.

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
- platform-best framework views that combine the strongest promoted controls

### Candidate ideas worth importing into our backlog

- policy-control presence and admission baseline controls
  - examples: "at least one active policy mechanism", Pod Security Admission
    posture, safe exception surfaces for hostPath/hostPort/capabilities
- service-account and secret-access hygiene
  - default service account usage, token mounting, and broad secret read access
- service exposure coverage beyond Ingress
  - gateway-style exposure and controller-specific public surface risks
- external secret management posture
  - using external secret stores as a promoted baseline, not just a catalog note

## March 24 Follow-On Priorities

The external Rego review should stay connected to two concrete follow-ons:

### 1. Keep Kubescape as an intake source for non-GitOps control families

The strongest near-term Kubescape-style intake areas remain:
- policy-control and admission baseline controls
- service-account and secret-access hygiene
- gateway and public exposure coverage beyond classic Ingress
- external secret management posture

Near-term intake queue to keep explicit while GitOps work continues:
- admission coverage that answers "is there at least one active policy layer?"
- service account token-mount and broad secret-read controls
- gateway and public exposure controls outside classic Ingress-only thinking
- external secret store posture controls that can become promoted baselines

Concrete follow-on now landed from that queue:
- `CTRL-NET-0004` in `controls/network/gateway-api-route-and-tls-baseline.yaml`
  promotes the first Gateway/public-exposure baseline built from native
  Gateway API scanner coverage we already have

That is where the public control library has useful breadth we can review for
candidate promoted controls in `confighub-patterns`.

### 2. Keep GitOps good+bad baselines repo-owned

For Argo CD and Flux specifically, our primary reference set should remain the
owned examples in `confighub-scan`:
- `examples/gitops-good-baselines/`
- `examples/gitops-bad-baselines/`

That keeps our GitOps operator story anchored in:
- repo-vs-live reasoning,
- Argo/Flux-specific intent and reconcile behavior,
- promoted controls tied back to our own examples,
- scanner-backed examples that we can use in demos, docs, AI explainers, and
  future benchmark work.

In other words:
- use Kubescape/Rego libraries to expand backlog ideas for generic control
  families,
- keep Argo CD and Flux baseline ownership in our own examples and promoted
  controls.

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
