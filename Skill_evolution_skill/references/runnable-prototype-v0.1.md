# Runnable Prototype v0.1

## 1. 目标

把 v0.1 从“可实施设计”推进到“可运行原型”。

这版原型的目标不是高智能，而是把最小闭环跑通：

1. 读取 hook 事件
2. 生成 report
3. 做最小 attribution
4. 如有必要，创建 candidate stub
5. 做最小 validation
6. 写 lineage
7. 产出 recommendation

---

## 2. 原型脚本

当前原型建议包含：

- `emit_evolution_report.py`
- `create_candidate_stub.py`
- `write_lineage_record.py`
- `consume_hook_events.py`
- `attribute_candidate.py`
- `validate_candidate.py`
- `promote_candidate.py`

---

## 3. 运行目录

在 workspace 下准备：

```text
.skill-evolution/
├── inbox/
│   └── hook-events.jsonl
├── transactions/
├── reports/
├── candidates/
└── lineage/
```

---

## 4. 推荐最小运行顺序

### Step 1
向 `hook-events.jsonl` 追加一条事件。

### Step 2
运行：

```bash
python Skill_evolution_skill/scripts/consume_hook_events.py .skill-evolution
```

### Step 3
脚本会：

- 读取未处理事件
- 创建 transaction
- 生成 report
- 做 attribution
- 若值得进化，则创建 candidate stub
- 做最小 validation
- 写 lineage
- 生成 recommendation

---

## 5. 当前 attribution 策略

仅做保守启发式：

- `user_correction` → patch
- `skill_failure` → patch 或 replacement（依赖 error_summary）
- `repeated_success_pattern` → composition
- 明显环境问题 → no_change

---

## 6. 当前 validation 策略

仅做最小检查：

- candidate.json 是否存在
- skill/SKILL.md 是否存在
- SKILL.md 是否包含 frontmatter 风格 name/description
- candidate 类型是否合法

不做真实任务回归测试。

---

## 7. 当前 promotion 策略

默认：

- validation 失败 → `rejected`
- validation 成功 → `review_required`
- 不自动 stable

---

## 8. 预期输出

每次消费后，应该能看到：

- `transactions/<txn>.json`
- `reports/<report>.json`
- `candidates/<cand>/...`（如果触发演化）
- `lineage/<skill>.json`
- 事务中的 recommendation 字段

---

## 9. 局限

这是原型，不解决：

- 高质量 candidate 内容自动生成
- 精确 failure attribution
- 自动 merge 到正式 skills/
- 大规模任务评测

它只证明：

> Skill evolution 可以先作为一个文件化、可回放、可审核的外挂闭环跑起来。
