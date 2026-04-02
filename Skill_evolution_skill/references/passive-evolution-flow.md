# Passive Evolution Flow

## 目标

定义一个宿主依赖较低、适合 OpenClaw 类系统的 MVP 被动进化流程。

## 触发信号

- skill 执行失败
- 用户明确纠正
- 同一 skill 被重复手工调整
- 某个临时高层 workflow 多次成功复用

## 主流程

1. Capture signal
2. Normalize into `EvolutionReport`
3. Run failure attribution
4. Decide patch / replacement / composition / no-change
5. Generate candidate metadata and draft content
6. Run minimum validation
7. Produce promotion recommendation
8. Write back candidate + lineage metadata

## 为什么优先被动进化

- 更贴近真实使用
- 个性化价值高
- 宿主适配成本低
- 不依赖大型 benchmark 或任务生成系统

## MVP 输出

至少输出：

- 是否值得进化
- 候选类型
- 候选摘要
- 最小验证结果
- 推荐状态
- 是否需要人工审核
