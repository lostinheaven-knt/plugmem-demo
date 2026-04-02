# MVP Implementation v0

## 1. 目标

把 Skill Evolution 从概念稿推进为**可实施的 v0 方案**，但仍保持：

- 宿主框架弱耦合
- 以被动进化为主
- 默认保守 promotion gate
- 先支持人工审核，再逐步自动化

---

## 2. MVP 成功标准

v0 不追求“完全自动自我进化”，而追求以下能力稳定成立：

1. 能从真实失败或纠正中识别出一批值得进化的事件
2. 能把事件规范化为统一 `EvolutionReport`
3. 能区分：
   - 不是 skill 问题
   - 需要 patch
   - 需要 replacement
   - 需要 composition
4. 能生成**结构化 candidate**，而不是只给聊天建议
5. 能做最小验证并给出 promotion recommendation
6. 能把候选与原 skill 的 lineage 记录下来
7. 能在不修改宿主核心架构的前提下接入

---

## 3. v0 设计边界

### v0 要做

- passive evolution
- orchestrator skill
- normalized state model
- candidate proposal generation
- minimum validation
- review gate
- writeback metadata

### v0 不做

- 大规模主动训练场
- 完全自动替换 stable skill
- benchmark 驱动批量进化
- 多 agent 自博弈式演化
- 框架强绑定的复杂 UI

---

## 4. 推荐目录结构

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
│   └── (reserved for future helpers)
└── assets/
    └── (optional, future)
```

---

## 5. v0 顶层组件

### 5.1 Orchestrator

唯一对外入口。

职责：

- 接收 evolution request
- 读取输入材料
- 创建 `EvolutionTransaction`
- 决定要走哪条演化路径
- 协调归因、candidate 生成、验证、决策
- 输出最终建议和写回结果

### 5.2 Attribution module

职责：

- 判断是否为 skill 问题
- 区分 skill 缺陷类型
- 过滤环境/依赖/瞬时错误

### 5.3 Candidate generation module

职责：

- 生成 patch candidate
- 生成 replacement candidate
- 生成 composed high-level candidate

### 5.4 Validation module

职责：

- 结构检查
- 最小完整性检查
- smoke validation
- 与父 skill 的最小对比

### 5.5 Promotion gate

职责：

- 把 candidate 标记为 draft / experimental / review_required / rejected
- 默认不直接 stable

### 5.6 Host adapter

职责：

- 从宿主拿 skill 内容
- 从宿主拿 trace / logs / feedback
- 把结果写回宿主可理解的位置

---

## 6. v0 状态机

建议事务状态：

1. `detected`
2. `normalized`
3. `attributed`
4. `candidate_generated`
5. `validated`
6. `review_required`
7. `finalized`
8. `rejected`

说明：

- `review_required` 是正常终态之一，不视为失败
- `rejected` 应保留原因，不要吞掉历史

---

## 7. v0 主流程

### Phase A: Detect
接收一个触发信号：

- skill failure
- explicit correction
- repeated manual edit
- repeated successful ad-hoc workflow

### Phase B: Normalize
生成 `EvolutionReport`：

- skill identity
- triggering context
- observed problem / success pattern
- evidence snippets
- environment notes
- user feedback

### Phase C: Attribute
做一阶判断：

- not a skill problem
- patch candidate needed
- replacement candidate needed
- composition candidate needed
- insufficient evidence

### Phase D: Generate
基于 attribution 产生 0..N 个 candidate。

### Phase E: Validate
对 candidate 做最小验证。

### Phase F: Decide
输出：

- reject
- keep as draft
- promote to experimental
- requires human review

### Phase G: Writeback
写回：

- transaction metadata
- candidate metadata
- validation summary
- lineage links

---

## 8. v0 的默认保守策略

### 8.1 不自动覆盖 stable
所有 stable skill 变更默认产出：

- patch proposal
- sibling candidate
- experimental candidate

而不是直接替换原 skill。

### 8.2 环境性失败优先排除
以下情况优先视为非 skill 问题：

- 临时 API 超时
- 凭证缺失
- 宿主工具权限不足
- 外部服务抖动
- 本地依赖暂时损坏

### 8.3 缺证据时不强行进化
如果没有足够上下文，就输出 `insufficient_evidence`。

### 8.4 成功也可以触发进化
如果某个临时 workflow 多次成功复用，可尝试生成 composed candidate。

---

## 9. v0 与 self-improvement 的协作方式

允许 self-improvement 提供：

- 近期重复纠错
- 同类行为问题历史
- 用户对某类执行风格的偏好

但 skill evolution 不直接承担：

- 用户偏好长期记忆
- 沟通习惯沉淀
- 行为规则管理

推荐接口方式：

- self-improvement 提供附加 evidence
- skill evolution 决定是否影响 skill candidate

---

## 10. v0 交付物

一次完整 v0 运行，至少应生成：

1. `EvolutionTransaction`
2. `EvolutionReport`
3. `SkillCandidate`（如果值得进化）
4. `ValidationResult`
5. final recommendation

---

## 11. 路线图

### v0
- 设计与 schema 完成
- passive flow 定稿
- host hook 接口定稿

### v0.1
- 生成 candidate 草案文件
- 可人工 review
- 可最小 smoke validate

### v0.2
- 引入可重复运行的 regression bundle
- 拆 attribution / validation 为高复用模块

### v0.3
- 形成 orchestrator + subskills 混合体系
- 引入有限自动 promotion 条件
