# controls

Promoted operator-facing controls belong here.

Controls are the stable, user-facing layer built from the broader pattern
corpus. A control may map to one or more patterns and should carry clear
remediation, supported-surface metadata, and example references when a
well-curated baseline or walkthrough exists in another repo.

The first seeded controls now live here for:
- GitOps and operator reliability
- workload hardening

Control definitions should validate against:
- `schema/control-definition-v1.schema.json`

Current seeded families now include:
- `gitops/` for Argo CD and Flux reliability controls
- `workload/` for workload security-context and resource-governance baselines
- `network/` for Ingress, Gateway/public exposure, and connectivity controls
- `cluster/` for admission, policy-control, and control-plane posture
- `rbac/` for privilege-boundary and service-account identity controls
- `secrets/` for secret-handling and external secret-store posture
