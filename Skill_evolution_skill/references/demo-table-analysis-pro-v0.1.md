# Demo: table-analysis-pro (v0.1)

## 1. 目的

使用工作区中的 `table-analysis-pro` 作为真实父 skill，验证 Skill Evolution v0.1 的两步：

- A: demo 闭环跑通
- B: candidate 内容从父 skill 物化，而不只是空 stub

---

## 2. 前提

确认以下路径存在：

```text
/root/.openclaw/workspace_coder/table-analysis-pro
```

---

## 3. 初始化 demo 运行目录

在 workspace 根目录执行：

```bash
python Skill_evolution_skill/scripts/init_runtime_demo.py .skill-evolution
```

这会：

- 建立 `.skill-evolution/` 目录结构
- 写入示例事件
- 预填 `hook-events.jsonl`

---

## 4. 运行 prototype

执行：

```bash
python Skill_evolution_skill/scripts/consume_hook_events.py .skill-evolution
```

---

## 5. 预期效果

如果事件命中了 `table-analysis-pro`：

- 创建 `candidates/<cand-id>/`
- 自动复制 `table-analysis-pro` 的结构到 `candidate/skill/`
- 在 `candidate/skill/SKILL.md` 末尾追加 `Candidate Patch Notes`
- 写出 `DIFF.md`
- 更新 `candidate.json`
- 更新 `lineage/table-analysis-pro.json`

---

## 6. 建议重点检查

### A. 候选 skill 内容
看：

```text
.skill-evolution/candidates/<cand-id>/skill/SKILL.md
```

确认：

- 已复制父 skill 内容
- 已追加 patch notes

### B. 差异说明
看：

```text
.skill-evolution/candidates/<cand-id>/DIFF.md
```

### C. 候选元数据
看：

```text
.skill-evolution/candidates/<cand-id>/candidate.json
```

### D. 谱系记录
看：

```text
.skill-evolution/lineage/table-analysis-pro.json
```

---

## 7. 当前含义

这还不是“高质量自动修 skill”，但它已经实现：

- 真实父 skill 接入
- 事件驱动 candidate 生成
- 基于父 skill 的内容物化
- 最小验证 + review gate

这说明 v0.1 已经从纯骨架走到了**带真实样本的原型闭环**。
