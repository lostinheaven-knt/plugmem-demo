# Skill Evolution 设计稿 v0.1

## 1. v0.1 相比 v0 的推进

v0 解决的是：

- 这套机制是什么
- 为什么采用 orchestrator + 模块化
- passive evolution 主流程是什么
- 中间状态需要哪些 schema

v0.1 进一步解决的是：

- 如何映射到 OpenClaw 类宿主
- MVP 文件结构如何落地
- hook 从哪里接、接什么
- candidate 和 lineage 元数据写到哪里
- 第一版如何做到“可人工审核、可部分执行、可逐步自动化”

因此 v0.1 的定位是：

> **可实施设计版本**，仍然保守，但已经足够支撑原型开发。

---

## 2. v0.1 总体结论

### 2.1 架构结论

采用：

- **一个主 skill：`skill-evolution`**
- **内部模块化**（归因、候选生成、验证、promotion、lineage）
- **宿主弱耦合 hook 接入**
- **本地文件化 transaction / candidate / lineage 元数据**
- **默认 human review gate**

### 2.2 演化目标

v0.1 只做三类演化：

1. **patch candidate**
   - 修补已有 skill 的说明、边界、引用、流程
2. **replacement candidate**
   - 用新候选替代旧 skill，但默认先 sibling 存放
3. **composition candidate**
   - 把反复成功的 ad-hoc 流程沉淀成高层 skill

v0.1 不做：

- 全自动 stable 覆盖
- 主动构造训练环境的 EvoMap 风格进化
- 多 agent 协作式大规模 search

---

## 3. MVP 文件结构（推荐落地）

### 3.1 skill 本体目录

```text
Skill_evolution_skill/
├── SKILL.md
├── references/
│   ├── design-v0.md
│   ├── design-v0.1.md
│   ├── mvp-implementation-v0.md
│   ├── openclaw-mapping-v0.1.md
│   ├── hook-integration-v0.md
│   ├── file-layout-v0.md
│   ├── decision-policy-v0.md
│   ├── one-vs-many.md
│   ├── passive-evolution-flow.md
│   ├── state-model.md
│   └── boundaries.md
├── schemas/
│   ├── evolution-transaction.schema.json
│   ├── evolution-report.schema.json
│   ├── skill-candidate.schema.json
│   └── validation-result.schema.json
├── scripts/
│   ├── emit_evolution_report.py
│   ├── create_candidate_stub.py
│   └── write_lineage_record.py
└── assets/
```

### 3.2 工作区数据目录（宿主无关建议）

推荐在 workspace 下新增：

```text
.skill-evolution/
├── transactions/
│   └── <transaction-id>.json
├── reports/
│   └── <report-id>.json
├── candidates/
│   ├── <candidate-id>/
│   │   ├── candidate.json
│   │   ├── VALIDATION.json
│   │   ├── DIFF.md
│   │   └── skill/
│   │       └── SKILL.md
├── lineage/
│   └── <skill-name>.json
└── inbox/
    └── hook-events.jsonl
```

这样即使宿主框架切换，这套演化数据也能保留。

---

## 4. OpenClaw 映射（简版结论）

在 OpenClaw-like 场景中，优先接入四类信号：

1. **skill/tool 执行失败**
2. **用户显式纠正**
3. **skill 文件被重复手工修改**
4. **重复成功的临时高层 workflow**

推荐通过：

- 日志 / trace 文件扫描
- heartbeat / maintenance 汇总
- 手动触发 skill evolution 审核

而不是一开始就侵入主 agent 核心。

---

## 5. v0.1 最小 hook 策略

### 5.1 Hook 原则

- hook 只负责上报信号，不负责做演化决策
- hook 可以异步，不阻塞主对话
- hook payload 必须尽量保留 trace id 和 skill identity

### 5.2 MVP 必接 hook

#### A. on_skill_failure
用于 patch / replacement 候选。

#### B. on_user_correction
用于 patch 候选与边界修正。

#### C. on_repeated_success_pattern
用于 composition 候选。

### 5.3 可延后 hook

#### D. on_skill_manual_edit_pattern
很有价值，但不一定是第一版必须。

---

## 6. v0.1 写回策略

### 6.1 不直接写回正式 skills/
第一版所有演化结果默认写入：

- `.skill-evolution/candidates/`

而不是直接改宿主正式 `skills/` 目录。

### 6.2 candidate 目录内容

每个 candidate 至少包含：

- `candidate.json`
- `VALIDATION.json`
- `DIFF.md`
- `skill/SKILL.md`

必要时还可以包含：

- `references/`
- `scripts/`
- `notes.md`

### 6.3 lineage 记录

每个原 skill 建一个 lineage 文件，记录：

- 当前 stable 版本引用
- 候选列表
- patch / replacement / composition 关系
- 最近触发 trace

---

## 7. v0.1 人工审核模型

第一版默认：

- 生成候选
- 跑最小验证
- 出 recommendation
- 等待人工审核/批准

人工审核至少判断：

1. 这个 candidate 真的是 skill 问题的修复吗？
2. 是否越界扩大权限？
3. 是否引入了不必要复杂度？
4. 是否值得进入 experimental？

---

## 8. v0.1 最小脚本化目标

为了让 v0.1 能开始落原型，建议先提供三个 helper script：

### `emit_evolution_report.py`
把 hook 事件规范化为 `EvolutionReport`。

### `create_candidate_stub.py`
创建 candidate 目录、candidate.json、空的 skill/SKILL.md、DIFF.md。

### `write_lineage_record.py`
把 transaction / report / candidate 关系写入 lineage 文件。

注意：

- v0.1 可以先只生成 stub，不必自动生成完整 skill 内容
- skill 内容仍可由 agent/人工共同完善

---

## 9. v0.1 状态推进方式

推荐：

1. `detected`
2. `normalized`
3. `attributed`
4. `candidate_generated`
5. `validated`
6. `review_required`
7. `finalized` 或 `rejected`

其中：

- 没有 candidate 的事务，也可以在 `rejected` 结束
- 需要人工审批的事务，不应视为流程卡死，而是正常中间态

---

## 10. v0.1 的最小可运行闭环

一次完整闭环如下：

1. 某个 skill 在真实任务中失败
2. hook 生成事件到 `.skill-evolution/inbox/hook-events.jsonl`
3. orchestrator 读取事件，生成 transaction + report
4. attribution 给出 patch/replacement/no-change 判断
5. 若值得进化，则创建 candidate stub
6. validation 产出最小结果
7. lineage 更新
8. 输出 human review recommendation

到这一步，即可认为 v0.1 成功。

---

## 11. 为什么这版仍然保守

因为 skill evolution 一旦过度自动化，就容易：

- 把环境问题误判成 skill 问题
- 让 stable skill 被低质量 patch 污染
- 把一次失败放大成长期能力退化

所以 v0.1 的立场是：

> **先把“结构化候选 + 验证 + 审核”链路打通，再考虑自动 promotion。**

---

## 12. v0.1 之后的自然演进

### v0.2
- 候选内容自动生成质量提升
- 回归测试 bundle 成型
- attribution / validation 外拆为高复用模块

### v0.3
- 引入 experimental 自动 promotion 条件
- 加入更稳定的宿主适配器
- 支持半自动写回到正式 skills/ 的提案流程

---

## 13. 一句话总结

**v0.1 的目标不是让 skill 自动成精，而是让 skill 进化第一次拥有可追踪、可验证、可审核、可迁移的实施骨架。**
