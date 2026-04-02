# MVP File Structure v0.1

## 1. Skill package structure

```text
Skill_evolution_skill/
├── SKILL.md
├── references/
│   ├── design-v0.md
│   ├── design-v0.1.md
│   ├── mvp-implementation-v0.md
│   ├── openclaw-mapping-v0.1.md
│   ├── mvp-file-structure-v0.1.md
│   ├── hook-integration-v0.md
│   ├── file-layout-v0.md
│   ├── decision-policy-v0.md
│   ├── one-vs-many.md
│   ├── passive-evolution-flow.md
│   ├── state-model.md
│   └── boundaries.md
├── schemas/
│   ├── evolution-transaction.schema.json
│   ├── evolution-report.schema.json
│   ├── skill-candidate.schema.json
│   └── validation-result.schema.json
├── scripts/
│   ├── emit_evolution_report.py
│   ├── create_candidate_stub.py
│   └── write_lineage_record.py
└── assets/
```

## 2. Workspace runtime structure

```text
workspace/
├── skills/
├── .skill-evolution/
│   ├── inbox/
│   │   └── hook-events.jsonl
│   ├── transactions/
│   ├── reports/
│   ├── candidates/
│   │   └── <candidate-id>/
│   │       ├── candidate.json
│   │       ├── VALIDATION.json
│   │       ├── DIFF.md
│   │       └── skill/
│   │           ├── SKILL.md
│   │           ├── references/
│   │           └── scripts/
│   └── lineage/
│       └── <skill-name>.json
```

## 3. Why this split

- `Skill_evolution_skill/` 是设计与协议包
- `.skill-evolution/` 是运行时数据与候选产物
- `skills/` 仍是正式稳定 skill 库

## 4. Promotion path

默认流程：

- 正式 skill 在 `skills/`
- 候选先在 `.skill-evolution/candidates/`
- 审核通过后，才考虑同步到正式 `skills/`
