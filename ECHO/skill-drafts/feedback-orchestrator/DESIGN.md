# Feedback Orchestrator：原型与改进路线

## 1. 定位

总控 Skill 把八个专项 Skill 串成可恢复、可追踪的反馈工作流。它自己不分析产品意见，也不决定实体或情绪；它根据应用事件选择该跑哪些步骤、传递版本化结果并检查质量。

专项能力包括：`feedback-ingest`、`entity-resolver`、`feedback-search`、`aspect-sentiment`、`feedback-insights`、`improvement-planner`、`change-risk-assessor`、`success-criteria`。总控是第九个 Skill。

## 2. 原型工作流

### 评价者提交

```text
提交事件
 → ingest 清洗/脱敏/质量与重复标记
 → entity-resolver 归一话题、对象和关系
 → aspect-sentiment 拆解多方面混合情绪
 → 服务端校验与持久化
```

### 老板搜索并生成报告

```text
老板搜索事件
 → 后端验证产品/数据访问权限
 → feedback-search 用离线目录匹配老板标签并检索评价
 → 复用兼容版本的方面情绪结果，必要时补跑
 → insights 汇总有证据的发现
 → improvement-planner 产出候选方案和排序
 → change-risk-assessor 评估副作用、缓解与回滚
 → success-criteria 定义基线、目标、护栏和决策门槛
 → 汇总发现、方案与验证标准
```

每个步骤返回结构化输出和版本，不依赖模型记忆或聊天上下文作为数据库。状态可暂停为人工复核，或以 `partial` 返回明确的部分结果。

## 3. 相较初稿的改进内容

本原型将常见“总控 Skill 就是让一个 Agent 自己判断并调用所有东西”的做法，收紧为由应用事件和代码定义流程、模型负责需要语言理解的局部任务：

1. 定义两条清晰触发路径：评价者提交与老板搜索/报告，不对每个请求都重复跑所有 Skill。
2. 对老板路径加入后端权限检查，模型不负责授权；搜索阶段离线优先，联网以后仅作为显式的可选增强。
3. 为每一步定义输入/输出契约、版本、状态、ID 和负责的专项 Skill，减少职责重叠。
4. 加入持久化任务状态、有限重试、幂等键和从失败/人工复核处恢复，避免重复保存、重复统计和重复费用。
5. 设置跨步骤质量门：脱敏完成才能交给模型；schema/跨度/ID 校验后才能保存；不确定结果不能伪装成完整结论。
6. 区分 `complete`、`complete_with_review`、`partial`、`failed` 和 `no_results`，让 UI 准确展示状态。
7. 追踪延迟、成本、错误和版本，但默认不把评论原文/PII 写入 trace。
8. 将专项模型准确率与流程运行可靠性分开评估。

## 4. GitHub 项目借鉴

### OpenAI Agents SDK

[openai/openai-agents-python](https://github.com/openai/openai-agents-python) 提供 agents、handoffs、guardrails、sessions 和 tracing 等运行时原语。可借鉴 manager/协调者拥有最终流程、将专门任务交给清晰边界的 specialist、工具输入输出检查及端到端 trace 的设计。

本原型主要借鉴其“明确区分代码编排和 LLM 决策”的思想，不要求每个 Skill 都独立成为一个 Agent，也不把任何工具框架作为 Skill 的硬依赖。对固定的提交/报告流程，代码编排更容易审计和重跑；LLM 只处理需要文本理解的节点。[Agent orchestration 指南](https://github.com/openai/openai-agents-python/blob/main/docs/multi_agent.md)、[guardrails 指南](https://github.com/openai/openai-agents-python/blob/main/docs/guardrails.md)、[tracing 指南](https://github.com/openai/openai-agents-python/blob/main/docs/tracing.md)

### LangGraph / LangGraph.js

[langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) 及 [LangGraph.js](https://github.com/langchain-ai/langgraphjs) 提供状态图、checkpoint、失败恢复和人工 interrupt/resume。可借鉴：每一步保存状态、审核时暂停后恢复、失败后从检查点续跑。对于当前流程，只有在任务可能长时间等待审核、批量分析或需要可靠恢复时才引入工作流运行器；小规模 MVP 可用数据库任务状态和明确的代码状态机实现。

## 5. 未来可能需要改进

### 流程和工程
- 设计正式状态机及数据库表/事件格式，包含版本兼容、超时、取消、部分结果和重跑语义。
- 当任务量或复核等待增长时，再比较自建状态机、LangGraph.js、OpenAI Agents SDK 等执行运行时；评估部署方式、持久化后端、观测数据权限和总成本。
- 增加队列并发、背压、每产品限流、批量作业和优先级策略。
- 明确每个步骤最大重试次数、超时和死信/人工处理流程。
- 建立结构化 Trace UI，能定位是哪一步导致某条建议或漏召回，同时避免日志泄露用户内容。

### 质量和安全
- 对关键边界建立端到端回归场景：PII 脱敏服务不可用、产品标签未知、多个实体同时出现、只有部分评价命中、情绪低置信、检索无结果、越权查询、目录版本变更、步骤超时和重试。
- 加入数据权限按产品/租户的自动验证与审计，确保 search、缓存、报告和 checkpoint 都隔离。
- 管理 prompt/Skill/模型/目录的独立版本；升级后能比较输出差异和回退。
- 定义报告生成门槛，例如最小样本量、未解析标签比例和数据陈旧状态；不足时拒绝给强结论。
- 支持成本/延迟预算、取消后清理、部分完成状态下用户可理解的提示。

### 产品流程
- 增加老板查看搜索条件、匹配路径、报告覆盖范围与复核项的界面。
- 为低置信实体、重要情绪主张和别名变更提供人工审核队列。
- 明确新评价到报告的更新时效，以及旧报告是否冻结或按新目录重算。

## 6. 当前边界

这是总控 Skill 的行为规范和工作流原型，不是已经运行的 Agent 编排代码。它不自动触发专项 Skills、不连接评价数据库、不验证真实账号权限，也没有持久化任务状态或 trace 后端；这些需由 App 服务实现。当前工作区 Skill 草稿保存在 `skill-drafts`，之后仍需安装/加载到实际运行环境。


