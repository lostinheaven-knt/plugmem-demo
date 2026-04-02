# Directed Patch Generation v0.1

## 1. 目标

在 v0.1 的 candidate 内容物化基础上，进一步实现**定向 patch 生成**：

- 不只复制父 skill
- 不只追加通用 patch notes
- 而是根据 `EvolutionReport` 的问题类型，生成更有针对性的补丁段

---

## 2. v0.1 设计原则

### 保守修改
第一版不直接重写父 skill 主体结构，而采用：

- 保留原 skill 原文
- 在候选中追加 `Directed Evolution Patch` 段
- 在 `DIFF.md` 中明确记录改动意图

### 面向 trigger
补丁段必须显式对应：

- observed failure
- user correction
- repeated success pattern

### 可审查
任何自动生成的 patch 都必须：

- 易读
- 可解释
- 可删除
- 不影响父 skill 的原始内容可见性

---

## 3. v0.1 适用的 patch 类型

### 3.1 Comparison patch
适用于 report 中出现：

- compare
- comparison
- previous period
- current vs previous

补丁目标：

- 明确要求先做 comparison 再下结论
- 要求比较口径一致性检查
- 要求输出显式列出 comparison findings

### 3.2 Completeness patch
适用于 report 中出现：

- missing
- incomplete
- omitted

补丁目标：

- 要求输出覆盖所有关键部分
- 在 self-check 中加入 completeness check

### 3.3 Correction patch
适用于 `user_correction`

补丁目标：

- 把用户纠正转为明确规则或 gate

### 3.4 Composition patch
适用于 repeated success pattern

补丁目标：

- 生成新的高层 workflow 草案
- 不强行修改父 skill 主结构

---

## 4. 对 table-analysis-pro 的第一版策略

优先支持两类：

- comparison patch
- completeness patch

因为这两类最符合该 skill 的常见失败模式：

- 缺少当前/上期比较
- 指标定义、解释或结论不完整

---

## 5. 产物

一次定向 patch 生成后，candidate 至少应包含：

- 复制后的父 skill 内容
- `## Directed Evolution Patch` 段
- 更具体的 `DIFF.md`
- 更新后的 `candidate.json`
- `PROMOTION_REVIEW.json` 草稿
