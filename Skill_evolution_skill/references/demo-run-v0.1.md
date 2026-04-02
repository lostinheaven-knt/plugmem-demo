# Demo Run v0.1

## 1. 目的

这份文档用于把 Skill Evolution v0.1 原型真正跑起来，验证以下最小闭环：

1. 写入 hook 事件
2. 消费事件
3. 生成 transaction / report
4. 产出 candidate stub
5. materialize 父 skill
6. 运行结构与内容级 validation
7. 写入 promotion review 与 lineage

---

## 2. 初始化运行目录

在 workspace 根目录执行：

```bash
mkdir -p .skill-evolution/inbox .skill-evolution/transactions .skill-evolution/reports .skill-evolution/candidates .skill-evolution/lineage
```

或者使用：

```bash
python Skill_evolution_skill/scripts/init_runtime_demo.py .skill-evolution
```

初始化脚本现在还会写入：

- `.skill-evolution/config.json`
- 示例事件中的 `skill_path`（绝对路径）

这样 demo 不再依赖“刚好把 parent skill 放在某个神秘相对目录下”。

---

## 3. 写入示例事件

可以用初始化脚本自动写入，也可以手工追加到：

`.skill-evolution/inbox/hook-events.jsonl`

示例事件见：

- `.skill-evolution/examples/skill_failure.json`
- `.skill-evolution/examples/user_correction.json`
- `.skill-evolution/examples/repeated_success_pattern.json`

### 3.1 推荐事件字段

最小推荐字段：

- `event_type`
- `skill_name`
- `trace_id` 或 `trace_ids`
- `task_summary`
- `ts`
- `host_framework`

若要可靠 materialize 父 skill，优先提供以下其一：

- `skill_path`
- `source_skill_path`
- `parent_skill_path`

也可以在 `.skill-evolution/config.json` 里提供：

- `skills_root`
- `parent_skill_paths`

路径解析优先级：

1. 事件里的显式路径
2. `config.json` 中对 skill 的映射
3. `config.json.skills_root / <skill_name>`
4. 兼容性回退路径

---

## 4. 运行原型

执行：

```bash
python Skill_evolution_skill/scripts/consume_hook_events.py .skill-evolution
```

---

## 5. 预期产物

执行后应看到：

```text
.skill-evolution/
├── config.json
├── inbox/
│   ├── hook-events.jsonl                  # 已被清空
│   └── hook-events.processed.jsonl
├── transactions/
├── reports/
├── candidates/
└── lineage/
```

如果事件触发了演化，还会在 `candidates/` 下看到候选目录：

- `candidate.json`
- `VALIDATION.json`
- `PROMOTION_REVIEW.json`
- `DIFF.md`
- `skill/SKILL.md`

若成功 materialize，还会看到从 parent skill 拷贝来的其他文件。

---

## 6. 建议检查点

### 6.1 检查 transaction
看 `recommended_action`、`status`、`decision_summary` 是否符合预期。

### 6.2 检查 report
看归一化结果是否保留了足够证据。

### 6.3 检查 candidate
看 candidate 类型是否合理，是否成功从 parent skill materialize，而不是停留在 stub。

### 6.4 检查 validation
重点看：

- 是否还有 `TBD`
- 是否存在 `proposed_changes_summary`
- 是否比较了 parent
- warning 是否只是“行为未验证”而不是结构损坏

### 6.5 检查 promotion review
现在默认语义是：

- `candidate.promotion_status = experimental`
- `candidate.promotion_recommendation = review_required`

也就是说：

- **候选本体状态** 是“实验态”
- **流程决策建议** 是“需要人工审核”

别再把两种状态揉成一锅胡辣汤。

### 6.6 检查 lineage
看是否正确挂到了原 skill 名下。

---

## 7. 已知限制

- 当前不会自动生成高质量行为级候选 skill 内容
- 当前 validation 已强于最早版，但仍主要是结构/内容 smoke checks
- 当前 promotion 默认不会自动 stable
- 当前 `review_required` 属于 **review recommendation**，不是 candidate schema 中的稳定状态枚举

所以这一步的目标是：

1. 证明闭环存在
2. 证明 parent skill 能被可靠解析和 materialize
3. 证明 validation 能挡住明显空壳 candidate

而不是证明“进化质量已经等于生产级智能优化器”。
