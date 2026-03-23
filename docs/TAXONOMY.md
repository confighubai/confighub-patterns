# Taxonomy

This repo uses three primary content layers:
- patterns
- controls
- frameworks

They are related, but they are not interchangeable.

## Pattern

A pattern is the broad canonical risk-knowledge entry.

Patterns:
- describe a configuration or live-state risk
- can exist before a native rule or promoted control exists
- may be candidate, curated, or launch-validated
- carry aliases, evidence, references, mappings, and remediation metadata

Patterns answer:
- what problem do we know about?

## Control

A control is a promoted, operator-facing assertion over one or more patterns.

Controls:
- are stable user-facing checks
- should have a clear purpose, remediation, and supported scan surfaces
- may map to one or more patterns
- should be the main layer exposed in standards, scorecards, and policy-style
  views

Controls answer:
- what should a user check or enforce?

## Framework

A framework is a curated grouping of controls.

Frameworks:
- package controls for a standard, platform, or workflow
- can represent standards like hardening baselines
- can also represent operational views like GitOps or operator-specific bundles
- should not be a second source of truth for the underlying risk metadata

Frameworks answer:
- which controls matter for this context?

## Why We Need All Three

The pattern corpus is intentionally broader than the currently promoted control
set.

That lets us:
- keep knowledge breadth without pretending every pattern is fully promoted
- expose a cleaner operator-facing control layer
- publish multiple framework views without duplicating the underlying risk data

## Relationship To Runtime Execution

- `confighub-patterns` owns pattern, control, and framework metadata
- `confighub-scan` owns native rule execution and evidence normalization
- ConfigHub/SDK own connected worker execution

Controls and frameworks are metadata and grouping layers, not a second rule
engine.
