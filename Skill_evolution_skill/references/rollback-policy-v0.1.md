# Rollback Policy v0.1

## 1. 目的

定义 Skill Evolution v0.1 中 candidate、experimental、未来 promoted 版本的回退策略。

核心原则：

> 所有进化都必须是可回退的；不能回退的进化，不应被 promotion。

---

## 2. 为什么 v0.1 天然适合回退

当前设计中：

- candidate 与正式 skill 分离
- stable skill 不直接被覆盖
- lineage 独立记录
- promotion 默认止步于 `review_required`

因此 v0.1 的默认“回退”通常很简单：

- 不 promote
- 或把 experimental 候选降级为 rejected/deprecated

---

## 3. 三类回退场景

### 3.1 Candidate rollback
适用于：

- candidate 尚未进入正式使用路径
- validation 失败
- 人工审核否决

操作：

- 标记 candidate 为 `rejected`
- 记录 `rollback_reason`
- 保留 lineage 历史，不删除证据

---

### 3.2 Experimental rollback
适用于：

- candidate 被试用后暴露问题
- 行为退化
- 风险上升

操作：

- 解除 experimental 引用
- 恢复 `stable_ref`
- 标记 candidate 为 `deprecated` 或 `rejected`
- 写入 `rollback_reason`

---

### 3.3 Promoted rollback（未来阶段）
适用于：

- 后续版本允许 stable promotion 后
- 新 stable 被证明不如旧 stable

操作：

- 当前 stable 降级
- 恢复 `last_good_ref`
- 记录谁批准、谁回退、为什么回退

---

## 4. 推荐的状态字段

建议在 lineage 中逐步引入：

- `stable_ref`
- `experimental_refs[]`
- `last_good_ref`
- `rollback_history[]`

`rollback_history[]` 每条建议包括：

- candidate_id
- from_status
- to_status
- rollback_reason
- triggered_by
- timestamp

---

## 5. 回退触发条件

以下情况建议触发 rollback：

- 原触发问题未解决
- 引入新的高频失败
- 风险等级上升
- 用户明确否定 candidate 行为
- 相邻任务退化明显

---

## 6. 回退与删除不是一回事

不要直接删除坏 candidate。原因：

- 删除会丢失演化历史
- 无法复盘为什么失败
- 无法避免将来重复生成同类坏候选

正确做法是：

- 标记状态
- 保留 lineage
- 写清 rollback_reason

---

## 7. v0.1 默认策略

v0.1 阶段建议：

- 候选默认只到 `review_required`
- 若审核不通过，直接 `rejected`
- 不需要复杂回退动作，因为 stable 尚未被替换

也就是说，v0.1 的 rollback 重点在于：

> **保留失败候选的历史，而不是让坏 candidate 进入正式路径。**

---

## 8. 为什么这很重要

如果没有 rollback policy，skill evolution 系统就会：

- 越改越脏
- 无法知道哪个版本是最后一个可信版本
- 无法安全做更激进的自动化 promotion

rollback policy 是所有后续自动化的前提条件之一。
