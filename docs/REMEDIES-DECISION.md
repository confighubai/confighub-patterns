# Remedies Decision

Issue `#5` asked whether remedies should become a top-level taxonomy layer in
`confighub-patterns`.

## Decision

For the current bootstrap and first released-bundle phase:

- keep remedies as metadata attached to patterns and controls
- do not add a top-level `remedies/` directory yet
- do not assign stable standalone remedy IDs yet

In other words, `confighub-patterns` should keep owning remediation metadata,
but not a separate remedy taxonomy.

## Why

### 1. Remedy meaning is still context-heavy

The current model already has two useful layers:

- `patterns/` carry richer remediation detail, optional example commands, and
  optional function references
- `controls/` carry compact operator-facing remediation strategy, safety class,
  and guidance

That works because remediation meaning is often specific to:
- the exact pattern
- the operator workflow
- the supported scan surfaces

Lifting that into a standalone remedy object too early would duplicate meaning
that still depends on the pattern or control context.

### 2. Reuse is not proven enough yet

Some patterns already reference similarly named fix functions or operational
moves, but that is not the same as proving we have a stable shared remedy
catalog.

We should wait for stronger evidence of:
- many-to-one reuse across unrelated patterns
- repeated operator guidance that wants one maintained source
- consumers asking for remedy lookup independent of finding or control lookup

### 3. The current bundle contract already gets the useful parts out

Today we already project the high-value remedy shape into released artifacts:
- remedy type / strategy
- safety class
- human guidance
- optional function linkage or commands through the pattern/control context

That means current consumers can still answer:
- what is the safest next move?
- is this a config fix or a diagnose-then-fix path?
- should this be automated or reviewed?

without needing a fourth top-level taxonomy.

### 4. A top-level remedy layer would blur repo boundaries too early

If we add `remedies/` now, it becomes tempting to move more executable or
workflow logic here.

That would be the wrong direction.

The clean split remains:
- `confighub-patterns`: pattern, control, framework, mapping, and remediation
  metadata
- `confighub-scan`: execution, findings model, explain surfaces, and fix-plan
  orchestration

## Source Of Truth By Layer

### Patterns

Patterns remain the source of truth for:
- detailed remediation description
- example commands or fix snippets
- remedy type and safety classification
- optional function references when a known helper exists

### Controls

Controls remain the source of truth for:
- operator-facing remediation strategy
- safety class at the promoted-control layer
- short guidance tied to a stable control bundle

### Generated artifacts

Generated bundles and catalogs may continue to normalize or project:
- remedy class
- safety class
- linked function name
- compact guidance fields

but those projections should stay derived, not become the authoring source.

## What We Are Explicitly Not Doing Yet

- no top-level `remedies/` directory
- no standalone `RMD-*` or equivalent remedy IDs
- no separate remedy bundle projection as a first-class release surface
- no migration of executable fix functions into this repo

## Revisit Triggers

We should revisit this decision only if one or more of these become true:

- the same remedy guidance is reused across many patterns or controls and
  duplication becomes hard to maintain
- consumers need remedy lookup independent of pattern or control lookup
- remedy safety / automation contracts need their own versioned surface
- we introduce a real release artifact whose primary consumer is remedy-centric
  rather than finding- or control-centric

Until then, the simplest and safest answer is:
- keep remedies here as metadata
- keep execution elsewhere
- keep the bundle contract focused on patterns, controls, frameworks, mappings,
  and derived projections
