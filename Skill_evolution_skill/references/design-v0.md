# Skill Evolution 设计稿 v0

## 1. 目标

构建一套**跨框架可迁移**的 Skill Evolution 机制，用于让 agent skill 在真实使用中逐步进化，而不是只依赖人工维护或一次性设计。

该机制的目标不是替代宿主框架，而是从宿主框架中剥离出一层**框架无关的技能进化协议与工作流**，使其可以在 OpenClaw、Memento-Skills 风格系统、甚至其他 agent runtime 中复用。

---

## 2. 核心判断

### 2.1 Skill Evolution 不等于 Self-Improvement

需要明确区分三层：

1. **Self-improvement / memory layer**
   - 记录纠错
   - 记录偏好
   - 沉淀行为规则
   - 目标是“以后做事更稳”

2. **Skill authoring / composition layer**
   - 编写或新增 skill
   - 组合已有 skill 为更高层 skill
   - 目标是“把能力组织好”

3. **Skill evolution layer**
   - 根据失败或重复成功信号，修补、替换、衍生 skill
   - 目标是“让 skill 资产自己演化”

本设计稿聚焦第 3 层。

### 2.2 默认采用：一个 orchestrator skill + 内部模块化

不建议起步就做成纯平级的一组 skill，也不建议做成毫无边界的单一巨 skill。

建议采用：

- **一个主 skill**：作为 orchestrator / decision owner
- **内部模块化结构**：将 failure attribution、candidate generation、testing、promotion、lineage 分层
- **后续再外拆高复用模块**：如 attribution 与 candidate testing

原因：

- skill evolution 具有强流程、强状态、强决策口
- 纯平级拆分容易协作断裂
- 单 skill 对外更易使用，对内仍保留演进空间

---

## 3. 设计原则

### 3.1 先做被动进化，再考虑主动进化

优先基于真实使用信号触发进化：

- skill 执行失败
- 用户纠正
- 同一类 skill 被反复手工修改
- 某种 ad-hoc 高层流程被反复成功复用

原因：

- 宿主依赖更低
- 个性化价值更高
- 更适合 OpenClaw 类系统
- 风险和复杂度都更可控

主动进化（主动制造环境批量训练/评测）应视为后续扩展，而非 MVP。

### 3.2 将“进化机制”与“宿主运行骨架”解耦

宿主框架负责：

- session / context 管理
- 工具执行
- sandbox
- UI / channel 集成
- 本地存储适配

Skill Evolution 核心负责：

- 归因
- 候选生成
- 验证
- 谱系管理
- promotion gate

### 3.3 把 skill 当成可演化资产

skill 不应被视为静态说明文件，而应具备以下生命周期状态：

- draft
- experimental
- stable
- deprecated
- archived

并保留清晰谱系：

- parent
- derived_from_trace
- replacement_of
- composed_from

### 3.4 优先可回滚与可审计

MVP 阶段不建议直接静默替换 stable skill。优先采用：

- patch proposal
- candidate side-by-side
- regression result snapshot
- human review gate

---

## 4. 目标能力边界

本设计要支持以下问题：

1. 这个失败是不是 skill 本身的问题？
2. 如果是 skill 问题，应 patch 旧 skill，还是生成 replacement candidate？
3. 如果不是 skill 问题，是环境、工具、依赖还是用户需求变化？
4. 某类临时成功 workflow 是否应沉淀成新高层 skill？
5. 新旧 candidate 如何验证？
6. 候选 skill 何时 promotion 为 stable？

不强求在 MVP 阶段支持：

- 自动全量 benchmark 进化
- 大规模主动制造环境训练
- 完整自治的无审查 skill 替换

---

## 5. 顶层架构

建议结构：

### 5.1 主 orchestrator

主 skill：`skill-evolution`

职责：

- 接收 evolution request
- 读取 trigger context
- 组装 evolution transaction
- 调用内部模块/未来子 skill
- 聚合结果
- 产出最终建议

### 5.2 内部模块

内部模块建议分为五类：

1. **Failure Attribution**
   - 判断是否为 skill 问题
   - 识别问题类型：prompt / structure / missing reference / unsafe freedom / dependency assumption / environment mismatch

2. **Candidate Generation**
   - patch existing skill
   - generate replacement skill
   - compose new higher-level skill

3. **Candidate Testing**
   - 最小回归测试
   - 对比旧 skill 与候选 skill
   - 记录 validation result

4. **Lineage / Versioning**
   - parent-child 关系
   - candidate id
   - status transitions
   - replacement history

5. **Promotion Gate**
   - draft → experimental
   - experimental → stable
   - stable → deprecated
   - archive recommendation

### 5.3 宿主适配层

宿主框架只需要提供：

- current skill source
- trace / logs / user correction
- optional test runner
- storage adapter

即可接入这套进化机制。

---

## 6. 建议的最小工作流（Passive Evolution MVP）

### Step 1. 捕获演化信号

触发来源：

- tool/skill failure
- 用户明确纠正
- 人工对同一 skill 的重复修改
- 多次成功的临时高层 workflow

### Step 2. 归一化报告

生成 `EvolutionReport`，统一描述：

- 触发事件
- 相关 skill
- 输入/输出摘要
- 错误摘要
- 环境因素
- 用户反馈
- 证据片段

### Step 3. 归因

输出：

- `not_a_skill_problem`
- `patch_candidate_needed`
- `replacement_candidate_needed`
- `new_composed_skill_candidate_needed`
- `insufficient_evidence`

### Step 4. 生成候选

候选类型：

- patch
- replacement
- composition
- no-change recommendation

### Step 5. 最小验证

MVP 中至少包含：

- 结构检查
- references 完整性检查
- prompt / instruction consistency 检查
- 最小 smoke test（若宿主提供）

### Step 6. Promotion Decision

输出：

- keep as draft
- promote to experimental
- requires human review
- reject candidate

### Step 7. 写回元数据

至少写回：

- candidate metadata
- parent linkage
- trigger trace id
- validation summary
- recommended status

---

## 7. 为什么不是纯多 skill 平铺

如果一开始就拆成一组平级 skill，会出现：

- 中间状态分散
- schema 胶水增多
- 最终责任口缺失
- 协作链断裂

因此本设计坚持：

- 先由一个 orchestrator skill 持有 evolution transaction
- 再逐步把高复用能力模块外拆

---

## 8. 外拆路线图

### 阶段 A：单 skill，对内模块化

适合 MVP。

### 阶段 B：拆出高复用模块

优先外拆：

- `skill-failure-attribution`
- `skill-candidate-test`

### 阶段 C：形成 skill suite

待协议稳定后，可发展为：

- `skill-evolution`
- `skill-failure-attribution`
- `skill-patch-generator`
- `skill-candidate-test`
- `skill-lineage-manager`
- `skill-promotion-gate`

但 orchestrator 仍保留。

---

## 9. 与 Self-Improvement Skill 的边界

Self-improvement 负责：

- learnings
- corrections
- preferences
- workflow rules

Skill evolution 负责：

- skill patch / replacement / composition
- validation
- lineage
- promotion

两者可协作，但不应混层。

推荐关系：

- self-improvement 提供长期“问题模式”和“行为规则”
- skill-evolution 负责把可执行能力沉淀为 skill 资产更新

---

## 10. MVP 判断标准

如果以下问题可以被稳定回答，就说明 v0 成功：

1. 某个失败是否应被视为 skill 演化机会？
2. 是否能形成结构化 candidate，而不只是聊天式建议？
3. 是否能给 candidate 一个最小验证结果？
4. 是否能记录 parent/child/trigger 关系？
5. 是否能做出“草稿 / 实验 / 审核 / 拒绝”的明确决策？

---

## 11. 一句话总结

**Skill Evolution 的核心不是框架壳，而是“失败 → 归因 → 候选生成 → 验证 → 写回”的可迁移机制。**

MVP 应先做成：

- 一个 orchestrator skill
- 内部模块化
- 被动进化优先
- promotion gate 保守
- 与宿主框架通过适配层连接
