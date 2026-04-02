# Skill Evolution Skill

最小可运行说明，给未来的你和现在的我都省点命。

这个项目的目标不是一步登天做出全自动技能进化大魔王，而是先把 **skill evolution 的最小闭环** 跑通：

1. 读取 hook 事件
2. 归一化成 evolution report
3. 做最小 attribution
4. 按需创建 candidate
5. 做结构化 validation
6. 生成保守 promotion recommendation
7. 写回 lineage 记录

当前版本是 **v0.1 runnable prototype + P1 基础契约接入版**。

---

## 1. 当前项目包含什么

```text
Skill_evolution_skill/
├── README.md
├── SKILL.md
├── config/
│   └── default.json
├── references/
├── schemas/
├── scripts/
│   ├── common.py
│   ├── init_runtime_demo.py
│   ├── consume_hook_events.py
│   ├── emit_evolution_report.py
│   ├── attribute_candidate.py
│   ├── create_candidate_stub.py
│   ├── materialize_candidate_from_skill.py
│   ├── validate_candidate.py
│   ├── promote_candidate.py
│   ├── generate_promotion_review.py
│   └── write_lineage_record.py
└── tests/
    └── test_p0_scripts.py
```

### 目录职责

- `references/`：设计文档、边界、流程说明
- `schemas/`：JSON schema 协议文件（P1 已接入核心输出校验）
- `config/default.json`：最小配置入口（日志、状态值、runtime 目录）
- `scripts/`：原型执行脚本
- `tests/`：当前最小 smoke tests

---

## 2. 依赖和环境

### 必要环境

- Python 3.10+
- 标准库即可运行当前原型（暂不依赖第三方包）

### 工作区假设

当前 demo 默认假设 workspace 下存在一个父 skill：

- `../table-analysis-pro`

也就是在本机上应能找到：

```text
/root/.openclaw/workspace_coder/table-analysis-pro
```

如果你不用这个 skill，也可以在 runtime 里的 `config.json` 里改成别的路径。

---

## 3. 当前原型能做什么

### 支持的事件类型

- `skill_failure`
- `user_correction`
- `repeated_success_pattern`

### 当前 attribution 策略

非常保守，先求不乱判：

- `user_correction` → `patch`
- `repeated_success_pattern` → `composition`
- `skill_failure` → `patch` 或 `replacement`
- 明显环境问题（如 timeout / auth / network / quota）→ `no_change`

### 当前 validation 策略

只做最小结构检查，不做真实回归评测：

- `candidate.json` 是否存在
- `skill/SKILL.md` 是否存在
- frontmatter 是否有 `name` / `description`
- 是否仍是 stub 内容
- candidate type 是否合法
- 是否存在最小 patch 痕迹（如 `DIFF.md` / `Candidate Patch Notes`）

### 当前 promotion 策略

默认保守：

- validation 失败 → `reject`
- validation 通过 → `review_required`
- **不会自动升到 stable**

---

## 4. 运行时目录结构

推荐单独准备一个 runtime 目录，例如 `.skill-evolution/`：

```text
.skill-evolution/
├── inbox/
│   ├── hook-events.jsonl
│   └── hook-events.processed.jsonl
├── transactions/
├── reports/
├── candidates/
├── lineage/
├── examples/
└── config.json
```

说明：

- `inbox/`：待消费事件和已处理事件
- `transactions/`：每次演化事务的状态记录
- `reports/`：归一化 report 和 event 快照
- `candidates/`：候选 skill 产物
- `lineage/`：每个 skill 的 lineage 记录
- `examples/`：demo 初始化生成的示例事件
- `config.json`：runtime 级别配置（覆盖 skill 路径解析）

---

## 5. 最小运行方式

### 方式 A：直接跑 demo（推荐先这么试）

在项目根目录执行：

```bash
python scripts/init_runtime_demo.py /tmp/skill-evolution-demo
python scripts/consume_hook_events.py /tmp/skill-evolution-demo
```

这会做两件事：

#### 第一步：初始化 demo runtime
会创建：

- runtime 目录结构
- `config.json`
- 3 个示例事件
- `inbox/hook-events.jsonl`

#### 第二步：消费事件
会依次执行：

1. 读取 inbox 里的事件
2. 生成 transaction
3. 生成 evolution report
4. 做 attribution
5. 生成 candidate stub
6. 从 parent skill materialize candidate
7. 做 validation
8. 生成 promotion review
9. 写 lineage

---

## 6. 手动运行单个脚本

### 1）生成 report

```bash
python scripts/emit_evolution_report.py event.json report.json
```

### 2）做 attribution

```bash
python scripts/attribute_candidate.py report.json
```

### 3）创建 candidate stub

```bash
python scripts/create_candidate_stub.py /tmp/candidates table-analysis-pro patch
```

### 4）校验 candidate

```bash
python scripts/validate_candidate.py /path/to/candidate_dir
```

### 5）生成 promotion recommendation

```bash
python scripts/promote_candidate.py /path/to/candidate_dir
python scripts/generate_promotion_review.py /path/to/candidate_dir
```

### 6）写 lineage

```bash
python scripts/write_lineage_record.py /tmp/lineage table-analysis-pro /path/to/candidate.json
```

---

## 7. 事件格式示例

最小 `skill_failure` 示例：

```json
{
  "event_type": "skill_failure",
  "skill_name": "table-analysis-pro",
  "trace_id": "trace-demo-001",
  "task_summary": "Analyze sales table and produce metric summary",
  "error_summary": "Output missing comparison section and incomplete metric explanation",
  "evidence": [
    "Expected a comparison section between current and previous period",
    "Metric definition explanation was incomplete"
  ],
  "ts": "2026-03-26T14:40:00+08:00",
  "host_framework": "openclaw-like",
  "skill_path": "/root/.openclaw/workspace_coder/table-analysis-pro"
}
```

runtime 级配置文件 `config.json` 可写成：

```json
{
  "skills_root": "/root/.openclaw/workspace_coder",
  "parent_skill_paths": {
    "table-analysis-pro": "/root/.openclaw/workspace_coder/table-analysis-pro"
  }
}
```

事件里的 `skill_path` / `source_skill_path` / `parent_skill_path` 优先级高于 runtime config。

---

## 8. 测试

运行当前最小测试集：

```bash
python -m unittest discover -s tests -v
```

当前测试覆盖：

- report 生成 happy path
- 非法 candidate type 拒绝
- user correction → patch attribution
- stub candidate 校验失败
- demo runtime 端到端流水线
- schema 校验对非法 candidate 数据的拦截

注意：
当前测试已经覆盖 **P0 smoke tests + P1 基础端到端/契约校验**，但仍不是完整回归测试网。

---

## 9. 日志和配置

### 日志

默认从 `config/default.json` 读取：

- `logging.level`
- `logging.format`

也支持临时用环境变量覆盖：

```bash
SKILL_EVOLUTION_LOG_LEVEL=DEBUG python scripts/consume_hook_events.py /tmp/skill-evolution-demo
```

### 配置

当前全局配置文件：

```text
config/default.json
```

主要包含：

- logging 配置
- runtime 必需目录
- allowed candidate / promotion / validation 状态值

---

## 10. 当前局限

这版原型**故意不做**这些事：

- 高质量 candidate 内容自动生成
- 真正的任务级离线回归评测
- 自动合并到正式 skill 库
- 在线 canary / shadow evaluation
- 高精度 failure attribution
- 生产级监控和告警

所以别把它当成“已经能自动养成技能生态”的 fully-armed 机器。
它现在证明的是：

> skill evolution 这件事，可以先作为一个文件化、可追踪、可审核、可回放的外挂闭环跑起来。

---

## 11. 推荐阅读顺序

如果你是第一次接手这个项目，建议按这个顺序看：

1. `README.md`（就是你现在看的这个）
2. `SKILL.md`
3. `references/design-v0.1.md`
4. `references/passive-evolution-flow.md`
5. `references/state-model.md`
6. `references/runnable-prototype-v0.1.md`

如果你要继续补工程化，再看：

- `references/mvp-file-structure-v0.1.md`
- `references/evaluation-policy-v0.1.md`
- `references/rollback-policy-v0.1.md`

---

## 12. 下一步建议

如果继续往前推，推荐顺序：

1. 补更完整的 README / usage examples（当前这个已经够最小可用了）
2. 扩测试覆盖，特别是端到端和异常路径
3. 把 schema 校验真正接进运行流
4. 再做更强的 candidate-vs-parent evaluation
5. 最后再拆 repo scaffold / sample artifacts / promotion workflow

一句话：

**先别急着造宇宙飞船，先把这台拖拉机保养到不掉轮子。**
