---
name: aspect-sentiment
description: 从用户自由文本评价中抽取多个方面、观点跨度及各自的情绪极性，识别一段评价中并存的好评和差评，并将结果关联到已归一的产品实体或问题主题。用于产品反馈的细粒度情感分析。
---

# Aspect Sentiment

## 目标与边界
分析脱敏后的用户评价，拆成一条或多条可追溯的方面级评价单元。每个单元应说明用户在评价什么、原文如何表达、情绪朝向如何；同一段文本可同时产生正向和负向单元。

不得把整段评价压成一个正面/负面标签，不得根据星级替代文本证据，也不得将情绪强度当成问题严重程度或用户比例。

输入来自 Feedback Ingest 的 `analysis_text`、稳定 `feedback_id` 和跨度映射；Entity Resolver 提供 `target_entity_ids`、`issue_topic_ids`、标签提及、实体关系和证据。标签只是线索，不能直接假设每个标签都是评价对象。本 Skill 输出情绪和方面分析，不负责产品标签归一、删除评论、整体趋势报告或改进风险决策。

## 分析流程
1. **定位评价单元**：按转折、并列、因果、条件等语义把长文本拆成可独立判断的主张；一条评论中可有多条正负评价，也可有多方面同一极性评价。
2. **抽取方面和观点**：对每个主张识别显式方面（如电池、相机、通知、同步）或隐式方面（如“等半天才出来”可能涉及速度/延迟）。保留观点词的原文跨度，如“太顶了”“糊得离谱”“省了好多时间”。若无法可靠推断隐式方面，使用 `unknown` 或待复核，不编造方面。
3. **关联目标对象**：优先使用 Entity Resolver 已提供的目标对象和关系，再用当前主张中的文字证据确认。标签共现本身不能建立目标关系；不同主张可以针对不同实体。责任归因与评价对象分开，除非文本明确归责，不输出 `attributed_to`。
4. **判定每个方面的极性**：对方面—观点对独立标记 `positive`、`negative`、`neutral` 或 `uncertain`。一段评价可同时有正负结果；仅当同一个方面确有正负并存且无法拆成不同主张时，才将该方面标记为 `mixed` 并保留两边证据。
5. **处理语境**：检查否定、转折、程度词、比较、反问、讽刺、引用、条件句、emoji、重复标点和中英文混写。例如“不是不卡，是根本打不开”不能因为出现“不卡”就标正面；“相机不错，但夜景完全不行”要拆为不同方面或不同场景主张。
6. **估计情绪强度和情绪类别**：极性回答“好或坏”，强度回答文本表达得多强，二者分别输出。强度使用经标注校准的有序等级（建议 `low`/`medium`/`high`）；无法校准前可输出未校准的模型分数，但必须标明不是概率。可选的情绪类别（如愤怒、喜悦、失望）只有在证据足够时输出，不能从差评自动推断愤怒。
7. **表达不确定性**：分别记录方面抽取、目标关联、极性和强度的置信/状态。置信值未经过校准时称为 `model_score`，不能声称是准确概率。低置信、反讽、隐式方面或多个解释竞争时标为 `needs_review`。
8. **保留证据并交接**：输出原文证据跨度及可回到原始文本的索引映射；下游报告只能引用脱敏文本。不得补写原文中不存在的事实、原因、用户属性或产品影响。

## 结构化输出
字段应由服务端固化为 JSON Schema/类型定义。以下为示意：

```json
{
  "feedback_id": "feedback-123",
  "analysis_text": "#iPhone18 电池太顶了，出门一天还有电；但相机夜景糊得离谱，气死我了。",
  "units": [
    {
      "aspect_surface": "电池续航",
      "aspect_span": "电池",
      "aspect_span_analysis": [10, 12],
      "topic_id": "topic_battery_life",
      "target_entity_ids": ["entity_iphone_18"],
      "opinion_span": "出门一天还有电",
      "opinion_span_analysis": [12, 15],
      "polarity": "positive",
      "intensity": "high",
      "emotion": null,
      "evidence_span": "电池真的太顶了，出门一天还有电",
      "evidence_span_analysis": [10, 23],
      "model_score": null,
      "status": "resolved"
    },
    {
      "aspect_surface": "相机夜景",
      "aspect_span": "相机夜景",
      "aspect_span_analysis": [25, 29],
      "topic_id": "topic_camera_night_mode",
      "target_entity_ids": ["entity_iphone_18"],
      "opinion_span": "糊得离谱，气死我了",
      "opinion_span_analysis": [29, 38],
      "polarity": "negative",
      "intensity": "high",
      "emotion": "anger",
      "evidence_span": "相机夜景糊得离谱，气死我了",
      "evidence_span_analysis": [25, 38],
      "model_score": null,
      "status": "resolved"
    }
  ],
  "review_level_summary": {"polarity": "mixed", "derived_from_units": true},
  "analysis_version": "version-id"
}
```

`review_level_summary.polarity` 只能从 `units` 推导，不能替代或覆盖方面级结果。跨度使用 Feedback Ingest 约定的同一索引单位和 offset map；若使用其他索引单位，必须在接口中明确。

## 质量约束
- 一条方面级结果必须有观点证据；若方面是隐式推断，标明 `aspect_inference` 及其证据。
- 不把未提及的方面标为 `neutral`；应使用 `not_mentioned`（在方面分类任务中）或不输出该方面。
- 不把无评价、无法辨认和中性评价混为一类。
- 不因重复评论或高情绪就提高单条情绪置信度。
- 评分字段（若有）只作为旁证；文本与评分冲突时分别保留并标记，不强行让一方覆盖另一方。
- 不把负面极性等同于高严重程度；严重程度属于后续问题优先级分析。

## 开源实现和数据集参考
实现参考与其适用限制见配套的 `DESIGN.md`。优先先用开源框架跑通 baseline 和评测，不立即训练自有模型；任何模型都需用本产品真实风格样本验证。

## 评估指标
在人工标注样本上分别评估：
- 方面跨度和观点跨度 extraction precision/recall/F1；
- 方面—观点配对及目标实体关联准确率；
- polarity macro-F1、各类混淆矩阵和 mixed/uncertain 处理准确率；
- 强度等级一致性/加权 F1 和校准误差；
- 否定、转折、讽刺、emoji、隐式方面、多方面混合正负样本的分层表现；
- `needs_review` 的精确率、覆盖率和人工复核负担；
- 文本证据跨度对齐率和无证据断言率。

按产品类别、语言、渠道、方面频率和显式/隐式方面切片报告。测试集应留出未见过的产品词和表达方式，避免只测训练中见过的模板。优先控制把强烈负面误判为正面、把不同方面情绪错误配对、以及无依据生成情绪/对象的错误。



