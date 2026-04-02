---
name: skill-evolution
description: Use when designing, evaluating, or operating a cross-framework skill evolution mechanism for agent skills. Activate for tasks involving skill failure attribution, patch generation, candidate testing, lineage/version management, promotion gates, passive evolution hooks, or discussion of whether to use one orchestrator skill versus multiple collaborating skills.
---

# Skill Evolution

Design and operate a **skill evolution system** that treats skills as mutable assets instead of static instructions.

This skill is for **design and workflow definition**, especially in OpenClaw-like systems where we want a portable evolution mechanism that survives host-framework changes.

## What this skill is for

Use this skill when the task is about any of the following:

- designing a skill-evolution architecture
- deciding whether to use one skill or multiple skills
- defining passive evolution hooks from real task failures
- defining skill candidate generation and regression testing
- designing skill lineage, promotion, demotion, and archival
- separating framework-specific runtime concerns from framework-agnostic evolution logic
- comparing Memento-Skills style capability evolution with self-improvement / memory logging skills

## Core stance

Treat **skill evolution** as a different layer from:

- self-improvement logs
- preference memory
- behavior guidelines
- static skill authoring

This skill focuses on improving the **skill asset itself**:

- repair a weak skill
- generate a stronger replacement candidate
- compose a higher-level skill from repeated successful practice
- validate whether a candidate should be promoted

## Recommended architecture

Default recommendation:

**One orchestrator skill, internally modular, with optional externalized sub-skills later.**

Do **not** start with:

- one giant monolithic skill with no internal boundaries, or
- a flat bag of peer skills with no single orchestration point

The orchestrator should own:

- evolution transaction state
- decision flow
- final recommendations
- promotion safety gates

Internal modules or future sub-skills should cover:

1. failure attribution
2. patch / candidate generation
3. candidate testing
4. lineage + version tracking
5. promotion / demotion / archive decisions

## Design principles

### 1. Separate framework-dependent and framework-agnostic logic
Keep these **framework-dependent** concerns outside the evolution core:

- session and context management
- tool dispatch runtime details
- sandbox implementation details
- UI / chat integrations
- storage adapters tied to a specific host

Keep these **framework-agnostic** concerns in the evolution core:

- failure attribution
- candidate generation
- evaluation and regression checks
- lineage tracking
- promotion gating
- state schema for evolution transactions

### 2. Prefer passive evolution first
Start with **passive evolution** driven by real use:

- failed executions
- user corrections
- repeated manual skill edits
- repeated emergence of ad-hoc high-level workflows

Do not begin with active synthetic evolution unless the host system already has strong eval infrastructure.

### 3. Keep one decision owner
A multi-step evolution flow must have one explicit decision owner. That owner should decide:

- whether the issue is really a skill problem
- whether to patch, replace, compose, or do nothing
- whether a candidate can be promoted automatically or must wait for review

### 4. Preserve lineage
Every candidate should preserve links to:

- parent skill
- triggering failure or success trace
- applied patch rationale
- validation results
- current status: draft / experimental / stable / deprecated / archived

### 5. Favor reversible evolution
Prefer operations that are easy to review and roll back:

- draft candidate creation
- patch proposal files
- side-by-side evaluation
- promotion gates
- archival instead of hard deletion

## Workflow summary

1. Detect an evolution signal
2. Build a normalized failure/success report
3. Decide whether this is a skill problem
4. Generate one or more candidate changes
5. Run validation or regression checks
6. Produce a promotion decision
7. Write back candidate metadata and lineage
8. Optionally escalate for human review

## What to read next

- Read `references/design-v0.md` for the full design draft
- Read `references/state-model.md` for the transaction and candidate state model
- Read `references/passive-evolution-flow.md` for the MVP passive-evolution workflow
- Read `references/one-vs-many.md` when deciding between one orchestrator skill vs multiple collaborating skills
- Read `references/boundaries.md` for the boundary between evolution, self-improvement, and host runtime concerns

## Deliverables this skill should produce

Good outputs from this skill include:

- a concrete design draft
- a proposed directory structure
- a state schema for evolution transactions
- a passive-evolution workflow
- a recommendation on orchestration boundaries
- a migration path from one-skill MVP to modular skill suite

## Constraints

- Do not assume a specific host framework unless explicitly required
- Do not collapse memory logging and skill evolution into the same layer
- Do not recommend automatic promotion to stable without validation or review gates
- Do not optimize for benchmark-only synthetic evolution unless the user asks for an active-evolution design
