# Hook Integration v0

## 1. 目的

定义一个**弱耦合 hook 接入面**，让不同宿主框架都能把真实运行中的 signal 输送给 Skill Evolution。

v0 只定义接口与事件类型，不假设特定 runtime。

---

## 2. 推荐 hook 类型

### 2.1 on_skill_failure
当某个 skill 或 skill 驱动流程失败时触发。

建议 payload：

- skill_name
- skill_version (optional)
- task_summary
- input_excerpt
- output_excerpt
- error_summary
- trace_id
- tool_results (optional)
- environment_notes (optional)

### 2.2 on_user_correction
当用户明确纠正某个 skill 的行为时触发。

建议 payload：

- skill_name (if known)
- task_summary
- original_behavior_summary
- user_correction
- evidence
- trace_id

### 2.3 on_skill_manual_edit_pattern
当某个 skill 被反复人工修改时触发。

建议 payload：

- skill_name
- edit_count_window
- recent_edit_summaries[]
- changed_sections[]
- trace_ids[]

### 2.4 on_repeated_success_pattern
当某个临时 workflow 多次成功复用时触发。

建议 payload：

- workflow_summary
- participating_skills[]
- success_count_window
- evidence[]
- trace_ids[]

---

## 3. Hook 处理原则

### 3.1 Hook 只报信号，不做重决策
宿主 hook 只负责上报，不负责决定 patch / replacement / composition。

### 3.2 Hook 要保留 trace id
任何可演化事件都应尽量保留 trace id，便于 lineage 和审核。

### 3.3 Hook 输出可异步处理
skill evolution 可以异步吃这些事件，不要求阻塞用户主流程。

---

## 4. 最小宿主适配接口

宿主至少需要提供以下能力：

### `get_skill_source(skill_name)`
返回 skill 原始内容、路径、版本信息。

### `get_trace(trace_id)`
返回某次任务的最小运行上下文。

### `write_candidate(candidate)`
把候选写入宿主认可的位置。

### `write_metadata(transaction, report, validation)`
写入 transaction / report / validation 元数据。

---

## 5. v0 接入建议

### OpenClaw-like 环境
优先考虑以下弱侵入信号源：

- skill 调用失败日志
- 用户显式纠正消息
- 本地 skill 文件重复编辑记录
- heartbeat / maintenance 中发现的重复模式

### Memento-Skills-like 环境
优先接入：

- reflection 后的失败事件
- skill execution response
- candidate writeback hooks

---

## 6. 设计原则

好的 hook 接入应满足：

- 不要求大改宿主核心架构
- 不阻塞主对话路径
- 不假设同一种 skill 文件格式
- 不把宿主状态模型硬塞进 evolution core
