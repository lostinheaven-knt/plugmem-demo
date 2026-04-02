# Boundaries

## Skill Evolution vs Self-Improvement

### Self-Improvement handles
- corrections
- preferences
- recurring workflow lessons
- behavior and communication rules

### Skill Evolution handles
- patching skills
- generating replacement candidates
- composing new higher-level skills
- validating candidate skills
- managing lineage and promotion states

## Skill Evolution vs Host Runtime

### Host runtime handles
- session/context lifecycle
- tool execution plumbing
- sandbox details
- chat/UI integration
- storage adapters

### Skill Evolution core handles
- normalized evolution transactions
- attribution logic
- candidate generation logic
- validation policies
- promotion decisions

## Design rule

If a component must change every time the host framework changes, keep it outside the evolution core.
If a component still makes sense after changing host frameworks, it belongs inside the evolution core.
