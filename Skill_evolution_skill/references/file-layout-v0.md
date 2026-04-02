# File Layout v0

## 1. 设计目标

定义一个既适合单 skill MVP，又方便后续外拆为 skill suite 的目录结构。

---

## 2. 当前推荐布局

```text
Skill_evolution_skill/
├── SKILL.md
├── references/
│   ├── design-v0.md
│   ├── mvp-implementation-v0.md
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
└── assets/
```

---

## 3. 为什么这么布局

### SKILL.md
只保留：

- 适用场景
- 总体设计立场
- 核心流程
- 引导阅读 references

### references/
存放设计正文与策略细节。

### schemas/
存放宿主无关的中间结构定义，便于未来脚本化。

### scripts/
为未来 helper script 预留，不在 v0 提前塞实现。

---

## 4. 后续外拆路径

如果未来把高复用模块外拆，建议保留本目录作为 orchestrator，并新增：

- `skill-failure-attribution/`
- `skill-candidate-test/`

其余模块在协议稳定后再考虑外拆。
