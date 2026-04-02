# Section-Targeted Patching v0.1

## 1. 目标

把 B2 从“统一在文末追加补丁段”推进到“按 section 定位插入补丁”。

这样做的好处：

- candidate 更像真正修过的 skill
- reviewer 更容易判断修改是否合理
- patch 与父 skill 原有结构更一致

---

## 2. v0.1 保守策略

第一版不做复杂 AST 或 markdown parser，而采用：

- 基于标题文本的 section 定位
- 找到 section 后插入一小段 `Evolution Patch Insert`
- 若找不到合适 section，再 fallback 到文末追加

---

## 3. 对 table-analysis-pro 的定位规则

### comparison patch
优先插入到：

1. `## Core rules`
2. `### 5. Validate before concluding`

### completeness patch
优先插入到：

1. `### 5. Validate before concluding`
2. `### 6. Present results cleanly`

### correction patch
优先插入到：

1. `## Gotchas`
2. `## Core rules`

### composition patch
默认仍保留在文末，作为高层 workflow hint。

---

## 4. 为什么先按 section 插，不直接重写原段落

因为 v0.1 的目标仍然是：

- 可审查
- 可回退
- 不破坏原 skill 可读性

直接重写父段落虽然更“像升级”，但风险更高，也更难对 diff 做解释。

所以 B2.1 采用折中策略：

> 在最相关 section 下插入明确标注的 patch block。

---

## 5. fallback 规则

如果找不到目标 section：

- 保留 `Directed Evolution Patch` 文末块
- 在 `DIFF.md` 中记录 fallback

这样不会因为 section 不匹配而丢失补丁内容。
