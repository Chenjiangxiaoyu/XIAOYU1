# ECHO 可执行评测层 · V0

本次按《ECHO评测与量化落地方案》建立独立评测命名空间，运行用户给出的11条华为手机/鸿蒙6评论。不是正式30/150条验收；没有修改生产提示词或清洗算法，没有把测试数据写入 backend/feedback.sqlite3。

## 使用

从 D:\ChatGPT\评价反馈 执行（Python标准库，无新依赖）：

    python -m unittest evals.test_evals -v
    python -m evals validate-dataset evals/datasets/harmony6-pilot11-v1.json
    python -m evals run evals/datasets/harmony6-pilot11-v1.json
    python -m evals annotate evals/runs/RUN_ID --output human-review.json
    python -m evals score evals/runs/RUN_ID --review human-review.json
    python -m evals export evals/runs/RUN_ID --review human-review.json
    python -m evals compare evals/runs/RUN_A evals/runs/RUN_B --first-review review-a.json --second-review review-b.json

真实 run 使用已有 backend/.env 中 DeepSeek 配置。gold不发送给模型；adapter只向生产 analyze 传递 product/cleaned_text。Cookie不参与本评测。读取密钥仅为授权的DeepSeek调用，不写日志。

## 存储和复现

每次run有随机唯一ID和独立目录；manifest、dataset、每条输出、每次HTTP尝试和completion均以排他创建写入，不覆盖。
manifest中的running是启动事件，最终状态看completion.json；无completion表示中断/partial，不能当成功。
记录源码哈希（无可用git提交则commit为null）、清洗函数hash、实际系统prompt hash、模型参数、请求体hash、真实响应、token usage、耗时、首次和最终状态及失败阶段。
raw response已遮蔽常见个人信息和运行时密钥；这里不存在浏览器Cookie日志。源代码快照只保存ingestion.py/pipeline.py，绝不复制.env。
评测框架是逐次文件存储namespace，未引入数据库迁移；正式反馈库保持不动。
输出加密、文件ACL防篡改或签名尚未实现；“不可变”指应用层禁止覆盖，并非操作系统阻止手动编辑。报告哈希检测当前输入/人工复核所绑定输出；不要手工改run文件。

## 人工复核

本轮run目录有human-review.html。浏览器打开即可核对全部11条、AI gold草案和实际模型输出，选择匹配gold、语义支持与4项建议分，填写评分者，下载JSON。
打开页面不会向网络传输内容。它只提供人工判断入口，不自动确认金标。
gold内容无误时逐条确认；有异议就保持pending，修改数据集并升级dataset_version，再用相同V0重跑，不能静默改旧gold。
确认相同冻结gold不改变dataset；人工确认记录保存到review。人工分数与output_hash绑定，不修改原输出。
如果输出含多个独立结论，勾选“未拆分复合结论”并保持待复核。可在JSON中增加atoms=[{atom_id, prediction_index}]，并按atom_id填写findings.prediction_id，保证每个父输出覆盖且一对一匹配。
缺人工gold或评分时全部语义质量指标N/A，不在成功子集上偷算总准确率。
四类情绪macro-F1要求四类均有gold支持，否则N/A。噪声等零分母N/A。单一来源组不伪造bootstrap区间。
主动操作计时需点击开始，页面隐藏/闲置30秒暂停；仅作复核操作记录，不等于已完成与纯人工的效率对照。

## 固定运行预算

每条调用一次生产analyze；它的request_json允许最多4次HTTP尝试，每次30秒，有限退避（Retry-After最多60秒）。
不增加解析失败或引文失败的重试。每条失败都保留分母。完成一轮后若再运行，生成新run，不择优覆盖旧结果。
本轮没有冻结价格表，estimated_cost/price_version为null；实际token用量可查，不凭空估价。

## 确定性验收

测试覆盖：P=100%/R=50%、重复预测FP、一对一冲突拒绝、逐字存在但语义不支持、失败计FN、缺gold和零分母、四类缺失、建议必过项、硬阻断、分组分割、输出不可覆盖、真实生产调用不泄露gold/密钥、503后成功完整记录、引用拒收、截断、取消、两次run不覆盖和不同数据集拒绝比较。
这批fixture属于工程测试，不混入11条真实语义结果。

## 本轮未做（不冒充完成）

- 30条校准、150条正式开发/回归/盲测，2–3个型号及多来源采样；
- 双人独立标注、争议裁决、正式端到端准确率；
- 20个固定追问题与跨版本聊天存档、20代表样本×3稳定性测试；
- 纯人工对照、3–5名真实用户效率实验、市场需求/竞品因果结论；
- 修改生产算法或V1优化；先由人裁决本轮坏例再选择一个变量；
- 完整产品内评测导航、人工编辑/删除/补充发现的工作流。当前提供CLI、独立HTML报告与复核页。

删除/保留：评测文件默认本地保留；可通过文件管理器删除指定evals/runs/RUN_ID目录，生产数据库不受影响。删除会失去该轮复现证据，程序不自动清理。

