# OpenClaw Mapping v0.1

## 1. 目的

把 Skill Evolution 机制映射到 OpenClaw-like 环境，尽量做到：

- 弱侵入
- 不强改主 agent 核心
- 优先复用现有日志、memory、heartbeat、workspace 文件

---

## 2. OpenClaw 中最适合接入的信号源

### 2.1 技能/工具失败
可来自：

- 任务执行中显式失败
- 工具调用报错
- skill 运行结果明显不达预期

用途：

- patch candidate
- replacement candidate

### 2.2 用户显式纠正
可来自：

- “不对”
- “这里应该是……”
- “这个 skill 老有这个问题”

用途：

- patch candidate
- 边界收紧
- prompt/流程修正

### 2.3 反复成功的临时 workflow
可来自：

- 类似请求被多次成功用相同步骤解决
- 人工反复把多个 skill 组合成一个小套路

用途：

- composition candidate

### 2.4 skill 重复手工修改
可来自：

- git diff / workspace 变更
- skill 文件被反复编辑

用途：

- replacement 或 patch 候选

---

## 3. OpenClaw MVP 建议接入方式

### 优先方案：文件化事件入口

推荐先不碰主 agent runtime，而是采用：

- `.skill-evolution/inbox/hook-events.jsonl`

任何来源都把事件写进这里。随后由 orchestrator skill 或 helper script 消费。

优点：

- 宿主无感
- 好调试
- 可回放
- 易跨框架

---

## 4. OpenClaw 侧最小目录建议

```text
workspace/
├── skills/
├── .skill-evolution/
│   ├── inbox/
│   │   └── hook-events.jsonl
│   ├── transactions/
│   ├── reports/
│   ├── candidates/
│   └── lineage/
```

说明：

- 正式 skill 仍在 `skills/`
- 所有候选与元数据都先放在 `.skill-evolution/`
- 这样可以避免污染正式 skill 库

---

## 5. 与 self-improvement 的协作

推荐协作方式：

### self-improvement 提供
- 某个问题已重复发生
- 用户明确纠正过多次
- 某类风格/流程是用户稳定偏好

### skill evolution 负责
- 是否要生成/修补 skill candidate
- 如何记录 lineage
- 是否需要 review gate

即：

- self-improvement 管“行为知识”
- skill evolution 管“能力资产”

---

## 6. OpenClaw v0.1 推荐 hook payload

### Failure event

```json
{
  "event_type": "skill_failure",
  "skill_name": "example-skill",
  "trace_id": "trace-123",
  "task_summary": "Generate report",
  "error_summary": "Missing section in output",
  "evidence": ["..."],
  "ts": "2026-03-26T11:00:00+08:00"
}
```

### Correction event

```json
{
  "event_type": "user_correction",
  "skill_name": "example-skill",
  "trace_id": "trace-124",
  "task_summary": "Summarize design",
  "user_correction": "Should compare v0 and v0.1 explicitly",
  "evidence": ["..."],
  "ts": "2026-03-26T11:05:00+08:00"
}
```

### Success-pattern event

```json
{
  "event_type": "repeated_success_pattern",
  "workflow_summary": "Read repo -> inspect failures -> draft design note",
  "participating_skills": ["github", "skill-creator"],
  "trace_ids": ["trace-a", "trace-b"],
  "success_count_window": 3,
  "ts": "2026-03-26T11:10:00+08:00"
}
```

---

## 7. OpenClaw v0.1 推荐人工入口

除了自动 hook 外，建议保留一个手动入口：

- “对这个 skill 发起一次 evolution review”
- “根据最近三次失败给这个 skill 产出 patch candidate”

这样可以避免第一版过度依赖自动采集。

---

## 8. 推荐实施顺序

1. 建立 `.skill-evolution/` 目录
2. 定义 `hook-events.jsonl` 事件格式
3. 做 `emit_evolution_report.py`
4. 做 `create_candidate_stub.py`
5. 做 `write_lineage_record.py`
6. 再考虑自动化消费与审核工作流

---

## 9. 结论

OpenClaw v0.1 最适合的接法不是深嵌到主框架，而是：

> **以文件化 hook 事件 + 本地候选目录 + 人工审核 gate 的方式，先跑通 skill evolution 外挂闭环。**
