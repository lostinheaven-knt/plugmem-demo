# One Skill vs Many Skills

## 结论

默认采用：**一个 orchestrator skill + 内部模块化 + 后续选择性外拆**。

## 为什么不用纯单 skill

纯单 skill 的问题：

- 变成巨无霸说明书
- 局部能力难以复用
- 归因/测试/谱系等模块难独立升级

## 为什么不用纯平级多 skill

纯多 skill 的问题：

- 中间状态易丢失
- 调用顺序依赖强
- schema 胶水增多
- 最终决策口缺失
- 协作容易断裂

## 适合纯多 skill 的条件

只有当模块之间：

- 中间状态很少
- 可以独立调用
- 调用顺序弱
- 不需要统一决策口

才适合纯平级拆分。

Skill evolution 通常不满足这些条件。

## 推荐方案

### Phase 1
- 对外：1 个 skill
- 对内：references / schemas / scripts 模块化

### Phase 2
外拆高复用模块：
- skill-failure-attribution
- skill-candidate-test

### Phase 3
形成完整 skill suite，但保留 orchestrator。

## 判断口诀

- 强流程、强状态、强统一决策 → 主 orchestrator
- 高复用、低状态、低顺序依赖 → 可拆成子 skill
