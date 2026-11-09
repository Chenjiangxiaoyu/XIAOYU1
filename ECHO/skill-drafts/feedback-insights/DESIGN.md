# Feedback Insights 设计说明

## 原型
输入为 feedback-search 的授权检索结果及上游标签/方面情绪/质量标记。输出可追溯的事实发现：问题、正向价值、混合体验、用户群差异和证据限制。改进建议、风险、成功标准分别交给三个专职 Skill。

## 相较原版的改动
- 从“清理、分类、建议、风险、路线图”缩窄为证据归纳与发现分析，避免职责混叠。
- 报告每个发现的分子/分母、样本量、反馈 ID、反例和限制。
- 只有可比数据和基线存在才报告趋势；不把自发评论外推成全体用户。
- 明确输出契约，作为 improvement-planner 的可审计输入。

## GitHub 借鉴
- [Evidently](https://github.com/evidentlyai/evidently)：可借鉴数据质量、分布漂移和分层报告方法，监测渠道/主题样本变化；漂移本身不是业务因果证据。[项目示例](https://github.com/evidentlyai/evidently/tree/main/examples)。
- [Promptfoo](https://github.com/promptfoo/promptfoo)：可借鉴固定回归样本、结构断言和输出评估，检查发现是否有证据、分母和限制；模型裁判不能替代确定性校验或人工审阅。

## 未来改进
建立人工标注黄金集；测量群体差异的可比性和抽样偏差；完善跨语言方面分类；对低样本统计给出区间；将纠错结果回流评估集。MVP 不依赖联网或上述项目。
