# Safety Gate v0.1

## 1. 目的

定义 Skill Evolution v0.1 的安全把关机制。

核心原则：

> candidate generator 负责提案，但不能负责批准自己上线。

---

## 2. 三层安全 gate

### 2.1 Static Safety Gate（静态安全门）

关注文件与声明层面的风险。

检查项：

- 是否扩大 `allowed_tools`
- 是否新增危险脚本
- 是否引入新的外部依赖
- 是否修改敏感路径指向
- 是否把只读 skill 改成可执行强动作 skill
- 是否新增潜在高风险 references / instructions

这层应尽量脚本化。

---

### 2.2 Behavioral Safety Gate（行为安全门）

关注 skill 行为语义是否越界。

检查项：

- 是否删除了必要确认步骤
- 是否弱化了澄清条件
- 是否降低了不确定场景下的谨慎度
- 是否把“分析建议”漂移成“直接执行”
- 是否放大了原本不该扩大的适用范围

这层目前适合：

- heuristic 检查
- diff 审查
- 人工 review

---

### 2.3 Human Review Gate（人工审核门）

v0.1 默认必须存在。

人工审核应至少检查：

1. 这次 candidate 是否真的在修 trigger 对应的问题？
2. 是否越界扩大权限或行为范围？
3. 是否引入了不必要复杂度？
4. 是否值得进入 `experimental`，还是应保持 `draft`？

---

## 3. 红线条件

以下情况应默认禁止自动 promotion：

- 扩大权限范围
- 新增高风险脚本或执行说明
- 从低风险 skill 漂移为高风险执行 skill
- 移除重要确认/澄清门槛
- 重大行为改变但无验证

---

## 4. 默认安全策略

### v0.1 默认策略

- 不自动 stable
- validation 通过也只到 `review_required`
- 涉及边界变化的一律人工审核

### 为什么保守

因为 skill evolution 的最大风险不是“没进化”，而是：

- 错误地进化
- 越界地进化
- 污染 stable

---

## 5. 责任分层

### Candidate generation
职责：
- 提出改法
- 写清 rationale

### Validation / safety check
职责：
- 检查结构与风险
- 标记明显红线

### Human reviewer
职责：
- 做最终判断
- 决定 reject / keep draft / review_required / experimental

---

## 6. 与 rollback 的关系

安全 gate 不等于 rollback。

- safety gate 负责“别轻易把坏变更放进去”
- rollback 负责“如果已经放进去且证明不好，能恢复”

两者必须同时存在。
