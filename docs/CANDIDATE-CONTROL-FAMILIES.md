# Candidate Control Families

This document captures initial promoted control families that are worth shaping
out of the broader pattern corpus.

These are not all implemented as first-class controls yet. They are the first
families to make explicit as the taxonomy matures.

They were seeded from:
- the current `confighub-scan` native rule corpus
- the broader CCVE pattern corpus
- a March 2026 review of an external control-library model

## 1. Workload Hardening Baseline

Candidate control themes:
- privileged containers
- allow privilege escalation
- non-root execution
- immutable or read-only root filesystem
- added capabilities and host namespace access
- liveness and readiness probes
- resource requests and limits
- image pinning and latest-tag avoidance

## 2. RBAC And Secret Access

Candidate control themes:
- cluster-admin bindings
- wildcard roles and broad verbs
- secret read access
- service account token minting
- node proxy access
- pod exec access
- impersonate, bind, and escalate privileges

## 3. Network And Exposure Baseline

Candidate control themes:
- missing or weak NetworkPolicy
- ingress TLS gaps
- ingress class and controller routing gaps
- exposed sensitive interfaces
- host network exposure
- unnecessary east-west communication

## 4. Secrets And Credential Hygiene

Candidate control themes:
- hardcoded secret-like values in config
- missing or stale secret references
- secret rotation lag
- service account token misuse
- external secret storage posture

## 5. GitOps And Operator Reliability

Candidate control themes:
- Argo sync and health failure states
- automated sync without prune
- ApplicationSet generator and naming pitfalls
- Flux HelmRelease timeout and reconciliation failures
- Kustomization dependency cycles
- source readiness failures
- reconcile-path problems that only appear in live state

Seeded controls now in `controls/gitops/`:
- `argocd-application-reconciliation-health`
- `argocd-sync-policy-baseline`
- `applicationset-generator-safety`
- `flux-reconciliation-reliability`
- `flux-intent-and-reconcile-baseline`

## 6. Cluster And Node Hardening

Candidate control themes:
- secret encryption posture
- audit log posture
- API server hardening
- kubelet hardening
- control-plane endpoint exposure
- host hardening posture

## 7. Framework Candidates

Likely early framework views:
- workload-hardening
- rbac-and-identity
- network-exposure
- secrets-and-credentials
- gitops-operators
- cluster-hardening
- platform-best

## Promotion Rule

Use controls when we want a stable, operator-facing check.

Keep items as patterns only when they are:
- still exploratory
- too narrow or low confidence
- not yet mapped to a clear promoted control surface
