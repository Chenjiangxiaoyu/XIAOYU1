# Entity Resolver — 优化说明与原型

## 用途与接口
输入 `feedback-ingest` 的 `analysis_text`、原文标签提及/跨度、语言、目录版本及来源 ID；输出实体/主题提及、候选映射、评价对象、关系、问题主题、证据跨度和审核状态，供 `aspect-sentiment` 使用。原文只读保留，跨度统一 Unicode code point 索引（若工程采用其他索引单位需在 API 声明）。

## 原型流程
1. 按 `#连续无空格文字` 解析标签；前端格式有效的标签蓝色、空格后的正文白色。颜色只反映语法。
2. 先分类为 entity / aspect / issue / scenario / ambiguous，再查各自本地目录。
3. 以审核通过的精确别名、规范名优先；模糊检索只召回候选，不直接合并。
4. 用正文抽取多个 evaluation claims，分别关联 target、relation、issue 和证据；标签共现不构成关系或责任归因。
5. 高置信已审核别名自动映射；其余保留候选或 unresolved 并进入审核队列。
6. 所有目录变更版本化、可撤销；纠正合并后可重算并展示影响范围。

## 核心输出
`mentions[]`（raw_tag、span、type、entity_id/topic_id、status、candidates）、`evaluation_claims[]`（target_entity_ids、issue_topic_ids、relation、attribution_entity_ids、evidence_spans、confidence）、`directory_version`、`resolver_version`、`review_events[]`。
实体别名与父子层级严格分离：`#18promax` 型号与 `#苹果18` 系列可以汇总，但不互为别名。兼容问题可以将微信与鸿蒙共同列为目标，华为只作为提及；除非正文明示，不推断华为责任。

## 评估与护栏
使用固定回归集和未见别名留出集；覆盖错别字、中英混写、型号近似、多个实体仅一个目标、实体交互、仅问题标签、歧义新实体、撤销/拆分和格式边界。分别报告标签抽取 F1、类型 macro-F1、实体链接精确率/召回率、错误合并率、错误拆分率、目标/关系 F1、无证据归责率和审核负载。错误合并优先控制；阈值由标注集校准，不能使用统一拍脑袋阈值。

## 在线能力
当前默认离线，本地目录不完整也能运行并给出 unresolved。未来只有调用方显式配置联网搜索时才对未知项增强查证；记录来源和时间，外部结果只能成为审核候选，不能自动写入确认别名。失败回退本地。
