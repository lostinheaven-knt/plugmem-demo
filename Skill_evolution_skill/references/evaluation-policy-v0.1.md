# Evaluation Policy v0.1

## 1. 目的

定义 Skill Evolution v0.1 中“优化是否真的更好”的评估标准，避免把“看起来更完整”误当成“行为上更优”。

---

## 2. 核心原则

评估一个 candidate，不能只问：

- 是否通过结构检查
- 是否多写了内容
- 是否看起来更专业

而要分层回答四个问题：

1. 它还是合法 skill 吗？
2. 它是否对准了触发这次进化的问题？
3. 它在目标任务上是否真的改善了行为？
4. 它是否引入了不可接受的风险或副作用？

---

## 3. 四层评估模型

### 3.1 Structural Validity（结构正确性）

回答：candidate 是否仍是合法、可加载、可理解的 skill。

检查项：

- `SKILL.md` 存在
- frontmatter 含 `name` / `description`
- references 路径未损坏
- scripts 路径未损坏
- candidate 元数据完整
- schema 通过

结论：

- 这一层只能证明“没坏”，不能证明“更好”

---

### 3.2 Trigger Alignment（触发对齐度）

回答：candidate 是否真的响应了这次触发它演化的问题。

检查项：

- 是否明确对应 `EvolutionReport` 中的问题
- patch / replacement / composition 类型是否合理
- 是否修补了相关 section，而不是无关扩写
- `rationale` 与 `proposed_changes_summary` 是否自洽

结论：

- 如果不能对齐 trigger，就算结构合法，也不应 promotion

---

### 3.3 Behavioral Improvement（行为改进度）

回答：candidate 在目标任务与邻近任务上是否真的更优。

建议检查：

#### A. 定向回归
- 原失败案例是否被修复
- 原遗漏项是否被覆盖
- 用户纠正点是否体现在输出行为中

#### B. 邻域不退化
- 相似任务是否仍可正确完成
- 是否引入新的明显错误
- 是否显著增加不必要步骤

结论：

- 这是“更好”的核心证据层

---

### 3.4 Risk Delta（风险变化）

回答：candidate 是否通过扩大风险来换取表面改进。

检查项：

- 是否扩大工具权限
- 是否弱化确认/澄清 gate
- 是否扩大适用范围导致漂移
- 是否引入额外依赖
- 是否提升复杂度到难以维护的程度

结论：

- 如果风险显著上升，应拒绝 promotion，即使行为看起来更强

---

## 4. 综合判定

### 4.1 最低门槛

要进入 `review_required`，至少满足：

- Structural Validity: 通过
- Trigger Alignment: 基本通过
- Risk Delta: 无红线风险

### 4.2 进入 experimental 的建议条件

建议在未来 v0.2+ 中加入：

- 至少一个目标 case 明确改善
- 至少一个邻近 case 无明显退化
- diff 可解释
- lineage 完整
- rollback 可行

### 4.3 直接拒绝条件

以下情况建议直接 reject：

- 结构不合法
- 无法说明为何这次变更与 trigger 相关
- 风险显著上升
- 改动过大但缺乏验证

---

## 5. 评估输出建议

每个 candidate 最好形成一张 Evaluation Card：

- structural_validity: pass/fail
- trigger_alignment: strong/weak/fail
- behavioral_improvement: unknown/partial/pass/fail
- risk_delta: low/medium/high
- recommendation: reject/draft/review_required/experimental_candidate

---

## 6. v0.1 的现实取舍

v0.1 原型阶段，真正能自动化做到的主要是：

- Structural Validity
- 一部分 Trigger Alignment
- 一部分 Risk Delta

Behavioral Improvement 目前大多仍需要：

- 人工 spot check
- 目标 case 回放
- 或后续更完整 regression bundle

因此 v0.1 默认止步于 `review_required` 是合理设计。
