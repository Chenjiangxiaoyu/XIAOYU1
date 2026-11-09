# Success Criteria 设计说明

## 原型
为候选改进定义“用户结果—指标口径—基线—目标—护栏—观察窗口—决策门槛”。不把功能是否上线等同于是否有效；目标缺依据时明确待产品负责人确定。

## 优化重点
- 将模糊愿望转成主指标、辅助指标、护栏和诊断指标。
- 要求每个指标写分子/分母、数据源、用户切片和窗口。
- 区分目标值的提出者与计算依据；没有基线或业务门槛时不捏造数字。
- 将 scale / iterate / stop-or-rollback 规则与 change-risk-assessor 的风险监控对接。

## GitHub 借鉴
- [GrowthBook Agent Skills](https://github.com/growthbook/skills)：其 experiment-design 指南强调假设、主指标、护栏和样本量检查；可借鉴实验规格结构。指标门槛和具体统计方法仍须结合项目数据/产品决策，不能照抄默认值。
- [GrowthBook](https://github.com/growthbook/growthbook)：开源实验与 feature flag 平台可用于后续执行、记录曝光和分析实验；Skill 只产出标准，不要求当前接入该平台。
- [Unleash](https://github.com/Unleash/unleash)：渐进发布/kill switch 思路可用于将达标标准和扩大覆盖、停止发布连接；不会自动定义产品成功。

## 未来改进
从业务事件字典自动读取指标定义；基于历史波动估计最小可检测效果与样本需求；处理新奇效应、季节性、多重检验和分群公平性；沉淀跨实验的成功/失败依据；提供人工审批与监测平台集成。
