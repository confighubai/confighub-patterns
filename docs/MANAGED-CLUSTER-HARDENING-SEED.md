# Managed Cluster Hardening Seed

This note narrows the managed-cluster follow-up from the external Rego-library
review into a small, repo-scoped candidate family for `confighub-patterns`.

It is intentionally a shortlist, not a promise to copy provider libraries
wholesale.

## Why This Family Is Worth Separating

The refreshed `kubescape/regolibrary` review showed one external area with real
breadth that we do not yet expose clearly here:
- private endpoint / private node posture
- managed-cluster network policy enablement
- provider-native identity and RBAC posture
- registry and image-scanning expectations
- external secret storage posture in managed environments

That does not mean we should copy provider-specific control libraries as-is.
It does mean we now have enough signal to treat managed-cluster hardening as a
distinct candidate family rather than burying it inside generic cluster
hardening.

## Proposed Family Shape

Start with one family:
- `managed-cluster-hardening`

Do not split into separate provider frameworks yet.

Reason:
- the first useful questions are cross-provider
- our current promoted taxonomy is still intentionally compact
- provider-specific frameworks would be harder to maintain before canonical
  pattern coverage is deeper

Revisit per-provider splits only if:
- EKS / AKS / GKE coverage diverges materially
- consumers need provider-specific bundle views
- we accumulate enough promoted controls that one shared framework becomes noisy

## First Candidate Control Themes

### 1. Control-plane endpoint exposure baseline

Candidate themes:
- private endpoint enabled
- public endpoint disabled or tightly bounded
- control-plane access intentionally narrowed

Why it matters:
- this is one of the clearest provider-managed posture defaults that operators
  routinely ask about
- it translates cleanly into an operator-facing "good baseline" control story

### 2. Private-node and workload-isolation baseline

Candidate themes:
- private nodes where the platform supports them
- restricted workload placement for untrusted or multi-tenant workloads
- container-optimized node posture when relevant

Why it matters:
- it is a durable operator choice, not just a one-off CVE workaround

### 3. Managed-cluster network policy baseline

Candidate themes:
- network policy engine enabled
- namespaces expected to be isolated actually have policy coverage
- provider-specific defaults do not silently leave east-west traffic open

Why it matters:
- this is where generic network controls and managed-cluster posture meet
- it belongs in a managed-cluster family only when the platform toggle or
  default matters

### 4. Provider-native identity boundary baseline

Candidate themes:
- dedicated service-account identity patterns
- provider-native RBAC or auth integration choices
- avoid over-broad registry or cluster access in managed IAM wiring

Why it matters:
- this is broader than generic RBAC and often needs provider-aware language

### 5. Registry and image-scanning posture

Candidate themes:
- provider registry access minimization
- image vulnerability scanning enabled through the native platform or an
  equivalent external provider

Why it matters:
- operators usually want a policy answer here, not just a catalog footnote

### 6. External secret storage preference

Candidate themes:
- prefer external secret storage over static in-cluster secret handling when the
  platform and operating model support it
- treat cloud secret-store posture as part of the managed-cluster baseline

Why it matters:
- this connects existing secrets guidance to real managed-environment defaults

## What Should Stay Out For Now

Do not treat the managed-cluster family as:
- a copy of EKS / AKS / GKE provider docs
- a second CIS-style control-plane checklist
- a place to mirror every external control-library ID

This family should stay small and promote only the controls that:
- map cleanly to canonical patterns
- have clear operator value
- fit our released bundle model

## Relationship To Existing Families

Keep these boundaries clear:

- generic Kubernetes API-server, kubelet, and certificate posture stays under
  `cluster-hardening`
- generic RBAC and service-account posture stays under `rbac-and-identity`
- generic secret handling stays under `secrets-and-credentials`
- generic Ingress / Gateway / exposure posture stays under `network-exposure`

Use the managed-cluster family only when provider-managed defaults or cloud
platform posture are the actual source of the control value.

## Framework Decision

If this family gets promoted, start with one framework candidate:
- `managed-cluster-hardening`

Do not start with:
- one framework per cloud
- one framework per registry
- one framework per identity provider

That can come later if the promoted control set becomes too wide.

## Promotion Rule For This Family

Promote controls here only when at least one of these is true:
- the pattern corpus already contains a clean canonical match
- the operator value is clearly cross-provider even if examples are provider-specific
- the control can be explained without importing an external execution model

If the underlying pattern or evidence surface is still missing, leave it as:
- a candidate here
- a follow-on for pattern growth in `confighub-scan`
