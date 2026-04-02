# Candidate Content Generation v0.1

## 1. 目标

在 v0.1 runnable prototype 的基础上，增加一层**候选内容生成**能力，使 candidate 不再只有空 stub，而能基于父 skill 产出一个第一版候选内容。

## 2. 输入

- 父 skill 目录
- `EvolutionReport`
- attribution 决策
- candidate 类型

## 3. v0.1 的保守生成策略

第一版不追求自动大改，只做：

- 复制父 skill 结构
- 对 `SKILL.md` 做轻量 patch 草案
- 生成 `DIFF.md` 草稿
- 在 candidate metadata 中记录“为什么改”

## 4. 对 `table-analysis-pro` 的推荐用途

`table-analysis-pro` 很适合作为第一批真实父 skill：

- 结构相对清晰
- 容易模拟 patch 场景
- 可以用来验证 skill patch / replacement 候选流程

## 5. v0.1 生成策略建议

### patch
- 复制父 skill 到 candidate/skill/
- 在 `SKILL.md` 中追加 `## Candidate Patch Notes`
- 根据 report 写入修补理由

### replacement
- 复制父 skill
- 保留原结构
- 在头部加入 replacement rationale

### composition
- 生成新的 `SKILL.md` 骨架
- 记录参与 skill 与 workflow summary

## 6. 下一步

在 runnable prototype 基础上新增脚本：

- `materialize_candidate_from_skill.py`

并在 `consume_hook_events.py` 里接入：

- candidate stub 创建后
- validation 前

完成第一版 candidate 内容注入。
