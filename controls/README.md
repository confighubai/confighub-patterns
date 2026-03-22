# controls

Promoted operator-facing controls belong here.

Controls are the stable, user-facing layer built from the broader pattern
corpus. A control may map to one or more patterns and should carry clear
remediation and supported-surface metadata.

The first seeded controls now live here for:
- GitOps and operator reliability
- workload hardening

Control definitions should validate against:
- `schema/control-definition-v1.schema.json`

Current seeded examples:
- `gitops/argocd-application-reconciliation-health.yaml`
- `gitops/flux-reconciliation-reliability.yaml`
- `workload/workload-security-context-baseline.yaml`
- `workload/workload-resource-governance-baseline.yaml`
