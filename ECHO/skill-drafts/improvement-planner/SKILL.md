---
name: improvement-planner
description: 将有证据的用户反馈发现转成可执行、可验证的产品改进选项，并按影响、证据强度、成本和可逆性排序。
---

# Improvement Planner

## 输入与职责
接收 `feedback-insights` 输出的发现包、产品目标/约束、已有路线图或成本信息（若可用）。把发现转成待验证的产品方案，不把用户建议原样当作产品需求，也不代替 change-risk-assessor 和 success-criteria。

## 工作方式
1. 校验每项发现有样本证据、分母、目标群体和局限；将无证据或低置信发现标记为“先补研究”，不要直接据此承诺功能。
2. 将发现转成清晰的问题陈述：哪个用户在什么场景遇到什么阻碍/获得什么价值。区分观察事实、根因假设和产品动作。
3. 为每个问题提出可比较的选项：不改/继续观察、低成本可逆试验、较大改动。正向价值可考虑扩大可发现性、场景覆盖或容量；负向问题先验证复现和根因。不得默认“增加功能”就是最佳解。
4. 每个选项列目标群体、证据 IDs、假设、方案范围、依赖、估算成本（只有输入支持才给数值；否则用未知/粗粒度）、预期收益方向、实施复杂度、可逆性和未决问题。
5. 排序时说明维度和理由，至少考虑证据强度、影响范围/严重度、策略契合、成本、可逆性和不确定性。数据不足时给定性分档，不虚构精确 ROI、用户数量或分数。
6. 建议拆成可交付的验证步骤与后续选项，不制定虚构排期/负责人。将每个候选方案交给 `change-risk-assessor` 和 `success-criteria`，待两者结果返回后再汇总决策卡。

## 输出契约
每个 `option` 包含：`option_id`, `source_finding_ids`, `evidence_feedback_ids`, `problem_statement`, `observed_facts`, `hypotheses`, `target_segments`, `change_proposal`, `scope`, `dependencies`, `expected_benefit_direction`, `cost_estimate{value_or_unknown,basis}`, `reversibility`, `priority{rank_or_band,dimensions,rationale}`, `open_questions`, `risk_assessment_status`, `success_criteria_status`。明确标注建议而非事实。

## 防空泛检查
若只写“优化体验/提升满意度/加强稳定性”，视为不合格。必须说明要改变什么行为或体验、针对谁、依据哪些反馈、如何先验证。如果根因、成本或目标冲突尚不清楚，输出待确认问题和最小研究步骤。
