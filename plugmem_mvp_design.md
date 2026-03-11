# PlugMem 最小实现版设计文档（Python）

## 1. 目标与范围

本文档用于指导 **PlugMem 的 Python 最小实现（MVP）**。目标不是一次性完整复现论文全部实验与信息论评测，而是先构建一个 **可运行、可扩展、结构正确** 的原型系统，验证论文的核心主张：

1. 原始 episodic memory 需要先标准化。
2. 长期记忆的有效检索单位应是 **知识单元**，而非原始文本块。
3. 记忆需要区分：
   - episodic memory（经历）
   - semantic memory（事实知识）
   - procedural memory（策略知识）
4. 检索后需要再做压缩与任务适配，而不是直接把召回内容原样塞回 agent。

本次实现约束如下：

- 图结构：`networkx`
- 持久化与索引：`SQLite + relational index`
- 去重策略：**方案 B，基于 LLM 的语义去重**
- 优先级：**先做最小实现**
- 文档目的：支持工程落地，而非论文式描述

---

## 2. 本期最小实现要做什么

### 2.1 需要实现的核心闭环

最小实现必须打通以下链路：

```text
原始轨迹
  -> episodic standardization
  -> semantic extraction
  -> procedural extraction
  -> knowledge deduplication
  -> graph/index storage
  -> retrieval
  -> reasoning/compression
  -> 输出给 base agent 的 memory context
```

### 2.2 本期不做的内容

以下内容不纳入第一期：

- 复杂 utility-cost 曲线复现
- 论文完整信息论指标
- 多 benchmark 同时复现
- 分布式服务化部署
- Neo4j / JanusGraph 等重型图库
- 复杂在线增量训练
- UI 或可视化平台

---

## 3. 系统总体架构

系统分为五层：

1. **数据接入层**
   - 接收原始 episodic trace
   - 支持 conversation / QA / web-agent 三类输入格式的统一适配

2. **结构化层（Structuring Module）**
   - episodic standardization
   - semantic proposition extraction
   - procedural prescription extraction
   - LLM-based deduplication

3. **存储层**
   - `networkx` 维护内存图结构
   - `SQLite` 持久化节点、边、索引、embedding、元数据

4. **检索层（Retrieval Module）**
   - 候选召回
   - 图扩展
   - LLM relevance rerank

5. **推理层（Reasoning Module）**
   - 对召回知识做压缩、归纳、格式化
   - 产出最终 memory block

---

## 4. 技术选型

### 4.1 编程语言与基础依赖

- Python 3.11+
- pydantic：schema 定义
- networkx：图结构原型
- sqlite3 / SQLAlchemy：关系存储
- sentence-transformers：embedding
- litellm 或 openai SDK：统一 LLM 调用
- numpy / pandas：数值与表格处理
- tenacity：重试
- typer：CLI
- pytest：测试

### 4.2 为什么用 networkx + relational index

现阶段目标是论文思想复现，不是图数据库选型比赛。

`networkx + SQLite` 的优点：

- 开发快
- 调试简单
- 容易直接观察节点与边
- schema 调整成本低
- 适合前期快速验证图组织方式是否有效

缺点：

- 不适合超大规模图
- 并发与复杂图查询能力有限

但对 MVP 足够。

---

## 5. 记忆模型设计

PlugMem 最小实现采用三层记忆结构：

### 5.1 Episodic Memory

作用：保存原始经历及其结构化版本，作为 semantic / procedural 知识的证据来源。

最小单位：`EpisodeStep`

字段：

- `step_id`
- `episode_id`
- `t`
- `observation`
- `state`
- `action`
- `reward`
- `subgoal`
- `metadata`

### 5.2 Semantic Memory

作用：保存从 episodic step 中抽取的事实性知识。

最小单位：`Proposition`

字段：

- `proposition_id`
- `content`
- `concepts`
- `source_step_ids`
- `confidence`
- `metadata`

辅助索引单位：`Concept`

字段：

- `concept_id`
- `name`
- `aliases`
- `metadata`

### 5.3 Procedural Memory

作用：保存从 episode 片段中抽取的可复用策略性知识。

最小单位：`Prescription`

字段：

- `prescription_id`
- `intent`
- `workflow`
- `source_step_ids`
- `success_score`
- `metadata`

辅助索引单位：`Intent`

字段：

- `intent_id`
- `name`
- `metadata`

---

## 6. 图结构设计

### 6.1 节点类型

最小实现支持以下节点：

- `episode_step`
- `proposition`
- `concept`
- `prescription`
- `intent`

### 6.2 边类型

- `next`：step 与 step 的顺序关系
- `mentions`：proposition -> concept
- `proves_from`：proposition/prescription -> episode_step
- `solves`：prescription -> intent

### 6.3 图设计原则

1. `Proposition` 与 `Prescription` 是主要知识载荷节点。
2. `Concept` 与 `Intent` 是轻量索引节点。
3. 所有抽象知识都必须能回溯到 `EpisodeStep`。
4. 图查询优先服务于检索，不追求复杂图算法炫技。

---

## 7. 存储设计（SQLite）

### 7.1 表设计

建议建立以下核心表：

#### `episode_steps`

- `step_id` TEXT PRIMARY KEY
- `episode_id` TEXT
- `t` INTEGER
- `observation` TEXT
- `state` TEXT
- `action` TEXT
- `reward` REAL
- `subgoal` TEXT
- `metadata_json` TEXT

#### `propositions`

- `proposition_id` TEXT PRIMARY KEY
- `content` TEXT
- `confidence` REAL
- `metadata_json` TEXT
- `embedding_blob` BLOB / TEXT

#### `concepts`

- `concept_id` TEXT PRIMARY KEY
- `name` TEXT UNIQUE
- `aliases_json` TEXT
- `metadata_json` TEXT

#### `prescriptions`

- `prescription_id` TEXT PRIMARY KEY
- `intent_text` TEXT
- `workflow_json` TEXT
- `success_score` REAL
- `metadata_json` TEXT
- `embedding_blob` BLOB / TEXT

#### `intents`

- `intent_id` TEXT PRIMARY KEY
- `name` TEXT UNIQUE
- `metadata_json` TEXT

#### `edges`

- `edge_id` TEXT PRIMARY KEY
- `src_type` TEXT
- `src_id` TEXT
- `edge_type` TEXT
- `dst_type` TEXT
- `dst_id` TEXT
- `metadata_json` TEXT

#### `source_links`

用于 proposition / prescription 到 source step 的多对多映射。

#### `dedup_audit`

记录 LLM 去重决策，方便回溯：

- `item_type`
- `candidate_id`
- `existing_id`
- `judge_result`
- `reason`
- `created_at`

### 7.2 relational index 设计

SQLite 层至少建立如下索引：

- `episode_steps(episode_id, t)`
- `propositions(content)`
- `concepts(name)`
- `prescriptions(intent_text)`
- `edges(src_id, edge_type)`
- `edges(dst_id, edge_type)`
- `source_links(source_step_id)`

如果后面规模增大，再增加 embedding ANN 组件。

---

## 8. Structuring Module 详细设计

### 8.1 Episodic Standardization

#### 目标

将异构原始轨迹统一映射为：

```text
e_t = (observation, state, action, reward, subgoal)
```

#### 输入

- `raw_trace`
- `task_type`
- `instruction`
- `metadata`

#### 输出

- `Episode`
- `EpisodeStep[]`

#### 实现方式

定义一个 `EpisodicStandardizer` 类：

- 负责不同任务类型的适配
- 对每个 step 提取 observation/action
- 调用 LLM 补全 state/subgoal/reward

#### prompt 输出要求

必须输出严格 JSON：

```json
{
  "state": "...",
  "subgoal": "...",
  "reward": 1.0
}
```

#### MVP 约束

- `reward` 先使用离散值：`-1 / 0 / 1`
- observation 与 action 尽量保留原始信息
- state 只保留决策相关内容，不做冗长摘要

---

### 8.2 Semantic Extraction

#### 目标

从单个 `EpisodeStep` 中抽取高价值原子事实。

#### 输出约束

每条 proposition 需要：

- 单一事实
- 可独立理解
- 去掉指代歧义
- 控制长度
- 附带 concepts

#### 处理流程

```text
EpisodeStep
  -> LLM 抽取 proposition 列表
  -> 清洗与规范化
  -> LLM 去重
  -> 落库
  -> 建立 proposition/concept/source 边
```

#### prompt 输出示例

```json
[
  {
    "content": "The user prefers low-sugar desserts.",
    "concepts": ["user preference", "low-sugar desserts"]
  }
]
```

#### 数量控制

MVP 阶段建议每个 step 最多抽取 1~3 条 proposition。

---

### 8.3 Procedural Extraction

#### 目标

从 episode 的连续步骤中抽取环境无关的操作策略。

#### 两步法

1. **segment**：按 subgoal 相似度将 episode 切成若干片段
2. **extract**：从每段抽取 `(intent, workflow)`

#### 分段策略

- 使用 subgoal embedding 相似度
- 若相邻 step 的 subgoal 相似度低于阈值，则切段
- 阈值先设为可配置，比如 `0.72 ~ 0.80`

#### workflow 约束

workflow 必须：

- 面向目标
- 环境无关
- 保留因果结构
- 不照抄 UI 文案

#### 输出示例

```json
{
  "intent": "Find the cheapest relevant product",
  "workflow": [
    "Search for the target item using specific keywords",
    "Filter or sort results by price",
    "Inspect the top candidates for relevance",
    "Choose the lowest-priced valid option"
  ]
}
```

---

## 9. 去重设计：采用方案 B（LLM）

### 9.1 设计原因

本期明确使用 **LLM-based semantic deduplication**，原因如下：

- proposition / prescription 的表述差异大，纯 embedding 阈值容易误合并或漏合并
- 论文核心强调知识层抽象，语义对齐比表面字面更重要
- 前期规模不大，可以承受额外 LLM 成本

### 9.2 去重对象

- proposition
- concept（必要时）
- prescription
- intent（必要时）

### 9.3 去重流程

#### Proposition 去重

对于新 proposition：

1. 基于 embedding 或关键词从库中找 top-k 候选
2. 调用 LLM 判断：
   - 是否语义等价
   - 是否包含关系
   - 是否不同事实
3. 若等价：合并到已有 proposition
4. 若不同：新建节点

#### Prescription 去重

LLM 判断两条 prescription 是否：

- 实际上表达同一类 workflow
- 只是不同粒度
- 或属于不同 intent

### 9.4 LLM judge 输出格式

```json
{
  "decision": "duplicate",
  "confidence": 0.91,
  "reason": "Both propositions express the same user dietary preference."
}
```

其中 `decision` 允许：

- `duplicate`
- `related_but_distinct`
- `different`

### 9.5 合并策略

若判断为 `duplicate`：

- 保留 canonical 节点
- 新 source_step_id 追加到已有节点的 source list
- 记录 audit log

若为 `related_but_distinct`：

- 新建节点
- 可在后续扩展阶段增加 `related_to` 边（MVP 不强制）

---

## 10. Retrieval Module 设计

### 10.1 目标

根据当前任务上下文，从 semantic / procedural memory 中召回最有用的知识，而不是只看文本相似度。

### 10.2 输入

- 当前 user query
- 当前 task instruction
- 当前 state / local context

### 10.3 输出

- proposition 候选
- prescription 候选
- 必要时的 source evidence

### 10.4 检索流程

#### Step 1：Query planning

通过 LLM 将当前上下文拆成：

- semantic need
- procedural need

MVP 中可以只输出两个字符串，不做复杂 plan object。

#### Step 2：候选召回

- proposition：基于 content embedding + concept 名称匹配
- prescription：基于 intent/workflow embedding + intent 名称匹配

#### Step 3：图扩展

- proposition -> concept
- concept -> 相关 proposition
- prescription -> intent
- proposition/prescription -> source evidence

#### Step 4：LLM rerank

要求 LLM 判断：

- 哪些记忆对当前决策真正有帮助
- 哪些只是主题相似但无行动价值

### 10.5 MVP 的 top-k 建议

- semantic 初召回：10
- procedural 初召回：5
- rerank 后保留：semantic 3~5，procedural 1~3

---

## 11. Reasoning Module 设计

### 11.1 目标

将召回的知识进一步压缩成适合 base agent 直接消费的 memory context。

### 11.2 输入

- 当前任务上下文
- 召回 propositions
- 召回 prescriptions
- source evidence（可选）

### 11.3 输出

最终结构建议为：

```text
Relevant Facts:
1. ...
2. ...

Useful Procedures:
1. ...
2. ...

Grounding Evidence:
1. ...
```

### 11.4 约束

- 不引入未被支持的新事实
- procedure 必须可执行
- 优先保留会改变决策的内容
- 严格控制 token 数量

### 11.5 为什么这个模块必须做

如果没有 reasoning module，检索结果通常：

- 太散
- 太长
- 决策相关性不够高

论文中该模块的价值之一，就是 **降低 agent-side token cost**。

---

## 12. Base Agent 接口设计

定义插件接口：

```python
class PlugMem:
    def ingest(self, raw_trace, task_type, instruction, metadata=None):
        ...

    def retrieve(self, current_context):
        ...
```

### 12.1 写入场景

任务完成或阶段性结束后：

- 写入 episodic memory
- 生成 semantic / procedural knowledge
- 更新图和索引

### 12.2 读取场景

agent 决策前：

- 根据当前上下文检索
- 生成 memory block
- 拼入 base prompt

---

## 13. 模块划分与代码结构

建议目录如下：

```text
plugmem/
├── config/
├── core/
│   ├── schema/
│   ├── structuring/
│   ├── graph/
│   ├── storage/
│   ├── retrieval/
│   ├── reasoning/
│   └── llm/
├── app/
├── scripts/
└── tests/
```

### 13.1 `core/schema/`

- `episode.py`
- `semantic.py`
- `procedural.py`
- `memory_context.py`

### 13.2 `core/structuring/`

- `standardizer.py`
- `semantic_extractor.py`
- `segmenter.py`
- `procedural_extractor.py`
- `deduplicator.py`

### 13.3 `core/graph/`

- `graph_store.py`
- `graph_builder.py`
- `graph_query.py`

### 13.4 `core/storage/`

- `sqlite_store.py`
- `repositories.py`

### 13.5 `core/retrieval/`

- `planner.py`
- `retriever.py`
- `reranker.py`

### 13.6 `core/reasoning/`

- `memory_reasoner.py`
- `formatter.py`

---

## 14. 核心类职责说明

### `EpisodicStandardizer`

职责：
- 接受原始轨迹
- 输出标准化 `Episode`

### `SemanticExtractor`

职责：
- 从 `EpisodeStep` 抽 propositions
- 调用 deduplicator 处理重复

### `Segmenter`

职责：
- 按 subgoal 相似度切分 episode

### `ProceduralExtractor`

职责：
- 从 segment 抽 `(intent, workflow)`
- 调用 deduplicator 处理重复

### `LLMDeduplicator`

职责：
- 对 proposition/prescription 做语义层判重
- 记录 dedup 审计结果

### `MemoryGraphStore`

职责：
- 将节点和边同步到 networkx 与 SQLite
- 支持简单图查询

### `MemoryRetriever`

职责：
- 候选召回
- 图扩展
- 组织 rerank 输入

### `MemoryReasoner`

职责：
- 将召回结果压缩成最终 memory block

---

## 15. 关键算法流程

### 15.1 写入流程

```text
raw_trace
  -> EpisodicStandardizer
  -> EpisodeStep[]
  -> SemanticExtractor (逐 step)
  -> Segmenter (整 episode)
  -> ProceduralExtractor (逐 segment)
  -> LLMDeduplicator
  -> MemoryGraphStore.write()
```

### 15.2 检索流程

```text
current_context
  -> planner
  -> semantic retrieval
  -> procedural retrieval
  -> graph expansion
  -> LLM rerank
  -> MemoryReasoner
  -> final memory block
```

---

## 16. Prompt 设计要求

### 16.1 基本原则

所有 LLM 输出必须：

- 使用 JSON schema
- temperature 低
- 强制字段完整
- 尽量减少自由发挥

### 16.2 standardization prompt

输入：
- 当前 step 的 observation/action
- 前一状态摘要
- 全局 instruction

输出：
- `state`
- `subgoal`
- `reward`

### 16.3 proposition extraction prompt

要求：
- 提取原子事实
- 做指代消解
- 不重复 observation 原文废话
- concepts 用短词组表示

### 16.4 prescription extraction prompt

要求：
- 输出抽象 workflow
- 不能写环境私有按钮名
- 强调目标导向与可迁移性

### 16.5 dedup judge prompt

要求：
- 判断两条知识是否等价、相近但不同、完全不同
- 给出简短原因
- 输出机器可读 decision

---

## 17. 配置项设计

建议提供统一配置：

```yaml
llm:
  model: gpt-4.1-mini
  temperature: 0.1

embedding:
  model: sentence-transformers/all-MiniLM-L6-v2

retrieval:
  semantic_top_k: 10
  procedural_top_k: 5
  final_semantic_k: 5
  final_procedural_k: 3

segment:
  subgoal_similarity_threshold: 0.76

limits:
  max_propositions_per_step: 3
  max_workflow_steps: 6
  max_memory_tokens: 512
```

---

## 18. 测试计划

### 18.1 单元测试

至少覆盖：

- schema 校验
- episodic standardization 输出结构
- semantic extraction JSON 解析
- segmentation 逻辑
- dedup decision 处理逻辑
- graph write/read 一致性

### 18.2 集成测试

输入一段小型 raw trace，验证：

- 能写入 step
- 能生成 proposition
- 能生成 prescription
- 能落库
- 能检索
- 能产出 final memory block

### 18.3 评估测试

MVP 阶段先做人工+半自动评估：

- proposition 是否原子化
- workflow 是否抽象可迁移
- 去重是否合理
- 最终 memory block 是否比 raw retrieval 更短、更有用

---

## 19. 风险与对策

### 风险 1：LLM 抽取不稳定

对策：
- schema 强约束
- cache
- retry
- 对关键步骤保留审计日志

### 风险 2：去重成本高

对策：
- 先做候选预筛选，再调用 LLM judge
- 仅比较 top-k 候选

### 风险 3：prescription 容易退化成流水账

对策：
- prompt 强调环境无关
- 控制 workflow 步数
- 加一层 quality check

### 风险 4：networkx 与 SQLite 状态不一致

对策：
- 所有写入走统一 store 接口
- 以 SQLite 为持久化真源
- networkx 作为运行态镜像

---

## 20. 开发里程碑

### M1：结构化打通

交付：
- schema
- standardizer
- semantic extractor
- segmenter
- procedural extractor

### M2：存储与图打通

交付：
- SQLite schema
- networkx graph store
- 节点边写入与查询

### M3：检索闭环

交付：
- semantic/procedural retrieval
- LLM rerank
- reasoning output

### M4：MVP 端到端验证

交付：
- 一条完整 ingest + retrieve demo
- baseline 对比 raw retrieval

---

## 21. 第一阶段建议直接实现的文件清单

建议优先创建以下文件：

```text
plugmem/core/schema/episode.py
plugmem/core/schema/semantic.py
plugmem/core/schema/procedural.py
plugmem/core/structuring/standardizer.py
plugmem/core/structuring/semantic_extractor.py
plugmem/core/structuring/segmenter.py
plugmem/core/structuring/procedural_extractor.py
plugmem/core/structuring/deduplicator.py
plugmem/core/storage/sqlite_store.py
plugmem/core/graph/graph_store.py
plugmem/core/retrieval/retriever.py
plugmem/core/reasoning/memory_reasoner.py
```

---

## 22. 结论

本设计文档给出的不是论文全文等比例复刻，而是一个忠于论文核心思想、适合 Python 快速复现的 **最小可实现 PlugMem 架构**。

本期关键选择为：

- 使用 `networkx + SQLite relational index`
- 使用 **LLM 语义去重** 作为主要 dedup 手段
- 优先完成最小闭环
- 先验证“知识单元驱动记忆”优于 raw retrieval 的工程价值

在该 MVP 稳定后，再逐步加入：

- 更强图扩展策略
- 多 benchmark 迁移验证
- 论文中的 utility-cost 评测
- 更细的信息密度分析
