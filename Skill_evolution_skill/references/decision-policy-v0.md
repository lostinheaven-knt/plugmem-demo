# Decision Policy v0

## 1. 目的

定义 v0 阶段 Skill Evolution 的保守决策策略，避免把一次失败直接演化成一次灾难。

---

## 2. 默认决策顺序

### 先判断：是不是 skill 问题
优先排除：

- 权限问题
- 凭证问题
- 外部 API 抖动
- 本地环境临时异常
- 宿主框架 bug

### 再判断：是哪类 skill 问题
候选类型优先级：

1. patch
2. replacement
3. composition

默认优先 patch，除非：

- 原 skill 结构明显失衡
- 说明与实际用途严重漂移
- 需要引入全新高层流程

---

## 3. Promotion Policy

### stable skill
如果父 skill 当前为 stable：

- 不直接覆盖
- 只生成 sibling candidate 或 patch proposal
- 默认进入 `draft` 或 `experimental`

### experimental skill
可在验证充分时继续保留 experimental，仍建议保留父版本。

### draft candidate
若证据不足或验证失败，维持 draft 或 reject。

---

## 4. Human Review Gate

以下情况默认要求人工审核：

- 涉及权限/安全边界变化
- allowed tools 范围扩大
- skill 指令语义大幅变化
- 从低风险 skill 变为可执行强动作 skill
- 覆盖已有 stable 行为路径

---

## 5. Rejection Conditions

以下情况应直接 reject 或标记 insufficient evidence：

- 只有一次模糊失败，且无 trace
- 无法确认关联 skill
- 明显是外部系统问题
- candidate 无法通过最小结构验证

---

## 6. Success-driven Composition Policy

如果一个高层 workflow 多次成功，且满足：

- 有稳定步骤模式
- 多次复用价值高
- 不只是一次性任务脚本

则可以考虑生成 `composition` candidate。
