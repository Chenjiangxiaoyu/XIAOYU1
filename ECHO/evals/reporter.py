import csv, html, json, math, statistics
from pathlib import Path
from .schemas import read,write_new,digest,file_hash,now,EVALUATOR_VERSION
from .echo_scorer import calculate
LABELS={"structured_completion_rate":"结构化完成率","first_attempt_success_rate":"首次尝试成功率",
"generation_quote_rejection_rate":"生成阶段引文拒收率","reliable_completion_rate":"可靠完成率",
"human_net_time_saved":"人工净节时","end_to_end_pass_rate":"端到端评论合格率",
"valid_comment_pass_rate":"有效评论合格率","finding_precision":"发现精确率","finding_recall":"发现召回率",
"finding_f1":"发现 F1","sentiment_accuracy":"情绪准确率","sentiment_macro_f1":"四类情绪 macro-F1",
"valid_comment_false_exclusion":"有效评论误排率","noise_filter_recall":"噪声过滤召回率",
"semantic_support_rate":"证据语义支持率","advice_pass_rate":"建议通过率","required_review_recall":"必须复核召回率",
"review_false_positive_rate":"复核误报率"}
def bundle(folder):
    folder=Path(folder);manifest=read(folder/"manifest.json");data=read(folder/"dataset.json")
    if digest(data)!=manifest["dataset_hash"]:raise ValueError("冻结数据集哈希不匹配")
    outputs=[read(folder/(c["case_id"]+".json")) for c in data["cases"] if (folder/(c["case_id"]+".json")).exists()]
    completion=read(folder/"completion.json") if (folder/"completion.json").exists() else {"status":"partial","error":"未写入完成记录，可能中断"}
    return manifest,data,outputs,completion
def review_template(folder):
    folder=Path(folder);m,d,outputs,_=bundle(folder);byid={o["case_id"]:o for o in outputs}
    return {"run_id":m["run_id"],"dataset_hash":m["dataset_hash"],"evaluator_version":EVALUATOR_VERSION,"reviewer":None,"reviewed_at":None,
        "instruction":"独立复核 gold 后填写 gold_confirmed；若修改标签，升级数据集并重跑V0。supported 是语义支持，不是逐字匹配。advice 四项依次为针对性/验证动作/指标与判据/证据边界。不要把预标注当人工确认。",
        "cases":[{"case_id":c["case_id"],"output_hash":digest(byid.get(c["case_id"],{})),
                  "status":"pending_human","gold_confirmed":False,"compound_unresolved":False,
                  "hard_blocks":[],"reason":"","findings":[{"prediction_id":str(i),"gold_finding_id":None,
                    "supported":None,"advice":[None]*4,"reason":""} for i in range(len((byid.get(c["case_id"],{}).get("parsed_output") or {}).get("findings",[])))]} for c in d["cases"]]}

def score(folder,review_path=None):
    m,d,outputs,completion=bundle(folder);reviews={}
    if review_path:
        r=read(review_path)
        if r.get("run_id")!=m["run_id"] or r.get("dataset_hash")!=m["dataset_hash"] or r.get("evaluator_version")!=EVALUATOR_VERSION:
            raise ValueError("评分文件与冻结运行不匹配")
        if any(c.get("status")=="human_confirmed" for c in r["cases"]) and (not r.get("reviewer") or not r.get("reviewed_at")):
            raise ValueError("缺少人工评分者或时间")
        if len({c["case_id"] for c in r["cases"]})!=len(r["cases"]):raise ValueError("重复评分case")
        byid={o["case_id"]:o for o in outputs}
        for c in r["cases"]:
            if c["output_hash"]!=digest(byid.get(c["case_id"],{})):raise ValueError("不可变输出的哈希不匹配")
            reviews[c["case_id"]]=c
        for c in d["cases"]:
            if reviews.get(c["case_id"],{}).get("gold_confirmed") is True and reviews[c["case_id"]].get("status")=="human_confirmed":
                c["adjudication_status"]="human_confirmed"
    result=calculate(d,outputs,reviews)
    latencies=sorted(o["latency_ms"] for o in outputs if o.get("latency_ms") is not None)
    usage={};missing=0
    for o in outputs:
        for a in o.get("attempts",[]):
            u=a.get("token_usage")
            if not isinstance(u,dict):missing+=1;continue
            for k in ("prompt_tokens","completion_tokens","total_tokens","prompt_cache_hit_tokens","prompt_cache_miss_tokens"):
                if isinstance(u.get(k),(int,float)):usage[k]=usage.get(k,0)+u[k]
    result.update(run_id=m["run_id"],manifest=m,completion=completion,
        review_hash=digest(read(review_path)) if review_path else None,
        usage=usage,usage_missing_attempts=missing,
        cost={"value":None,"price_version":None,"reason":"未冻结价格表；不估造费用","per_100":None,"per_qualified_case":None},
        latency_ms={"p50":statistics.median(latencies) if latencies else None,
                    "p95":latencies[max(0,math.ceil(.95*len(latencies))-1)] if latencies else None,
                    "definition":"逐条端到端，包括HTTP重试和退避；p95采用nearest-rank"},
        confidence_interval={"value":None,"reason":"仅1个来源组，来源分组bootstrap无法估计跨来源不确定性；展示全部单例"},
        limitations=d.get("notes",[]))
    return result

def export(folder,review_path=None):
    folder=Path(folder);m,d,outputs,_=bundle(folder);result=score(folder,review_path)
    out=folder/("report-"+now().replace(":","").replace(".",""));out.mkdir()
    write_new(out/"metrics.json",result);write_new(out/"raw-results.json",{"manifest":m,"dataset":d,"outputs":outputs})
    if review_path:write_new(out/"review-used.json",read(review_path))
    with (out/"metrics.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(result["metrics"][0]));writer.writeheader();writer.writerows(result["metrics"])
    byid={o["case_id"]:o for o in outputs}
    rows=[]
    for c in d["cases"]:
        o=byid.get(c["case_id"],{});p=o.get("parsed_output") or {}
        rows.append({"case_id":c["case_id"],"source_kind":c["source_kind"],"scenario":c["scenario"],"state":o.get("validation_status","missing"),
            "sentiment":p.get("sentiment"),"review_required":p.get("review_required"),"findings":len(p.get("findings",[])),
            "latency_ms":o.get("latency_ms"),"attempts":len(o.get("attempts",[])),"failure_stage":o.get("failure_stage"),
            "raw_text":c["text"],"cleaned_text":o.get("cleaned_text","")})
    with (out/"cases.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=["# ECHO V0 · 华为手机 / 鸿蒙 6 · 11 条试跑","","> 真实模型运行；人工 gold 与语义评分未确认时，质量指标保持 N/A。产品背景由用户指定，不代表评论者实际版本已核实。",
        "",f"- Run：{m['run_id']}",f"- 模型：{m['config']['model_id']}",
        f"- 源码：{m['app_version']}",f"- 状态：{result['completion']['status']}",f"- 结论：{result['verdict']}",
        f"- 耗时 P50/P95：{result['latency_ms']['p50']} / {result['latency_ms']['p95']} ms",
        f"- 实际返回 token：{json.dumps(result['usage'],ensure_ascii=False)}；缺失用量尝试：{result['usage_missing_attempts']}",
        "- 成本：unknown（未冻结价格表）。人工节时：N/A（未做对照）。",
        "- 来源：1组；不计算误导性的来源bootstrap区间，不宣称统计显著。","","## 指标","",
        "|指标|值|分子 / 分母|待确认或缺失|","|---|---:|---:|---:|"]
    for x in result["metrics"]:
        val="N/A" if x["value"] is None else f'{x["value"]:.2%}'
        lines.append(f'|{LABELS.get(x["name"],x["name"])}|{val}|{x["numerator"]} / {x["denominator"]}|{x["missing_count"]}|')
    lines+=["","## 全部单例（原模型输出，不代表已证实的产品事实）",""]
    parts=[]
    for c in d["cases"]:
        o=byid.get(c["case_id"],{});p=o.get("parsed_output") or {}
        lines += [f'### {c["case_id"]}',"",f'原文：{c["text"]}',f'清洗后：{o.get("cleaned_text","未完成")}',
            f'状态：{o.get("validation_status","missing")}；情绪：{p.get("sentiment")}；需复核：{p.get("review_required")}；尝试数：{len(o.get("attempts",[]))}',""]
        if o.get("error"):lines.append("失败："+o["error"])
        if p.get("excluded_reason"):lines.append("排除原因："+str(p["excluded_reason"]))
        for i,f in enumerate(p.get("findings",[])):
            lines += [f'{i+1}. **{f["title"]}**（{f["type"]}）',f'   - 观察：{f["summary"]}',f'   - 引文：{f["quote"]}',
                      f'   - 建议：{f["recommendation"]}',f'   - 验证：{f["validation"]}',f'   - 风险：{f["risk"]}',f'   - 成功标准：{f["success"]}']
        lines+=["","AI预标注 gold（待你确认）："]
        for g in c["gold"]["findings"]:lines.append(f'- {g["gold_finding_id"]}：{g["claim"]}；证据：{g["quote"]}')
        if not c["gold"]["findings"]:lines.append("- 暂无可确认的直接产品体验事实；观点/传闻需人工裁决。")
        lines.append("")
    lines+=["## 范围与局限",""]+["- "+x for x in d.get("notes",[])]
    lines+=["","## 下一步","", "先人工确认 gold 及逐条语义/建议评分，再生成准确率。修改标签需要升级数据集并重跑基线。未同时优化提示词。"]
    text="\n".join(lines)
    (out/"report.md").write_text(text,encoding="utf-8")
    # Safe self-contained report: no external resources, no untrusted HTML execution.
    htmltext='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>ECHO V0 评测报告</title><style>body{max-width:1100px;margin:40px auto;padding:0 24px;background:#f5f7fa;color:#1d2834;font:15px/1.8 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;border:1px solid #dde3ec;padding:28px;border-radius:16px}h1{font-size:28px}a{color:#395f99}</style><h1>ECHO · V0 可复核报告</h1><p>11条开发试跑 · 单一来源 · 非正式验收</p><pre>'+html.escape(text)+'</pre></html>'
    (out/"report.html").write_text(htmltext,encoding="utf-8")
    (out/"interview-summary.md").write_text("已建立11条用户转贴评论的开发试跑集，复用生产清洗与分析逻辑，保留逐次响应、失败、引用拒收与token用量。当前尚无人工确认金标、版本提升或用户节时结果，不能宣称准确率或业务收益。实测结果见 report.md。\n",encoding="utf-8")
    print("REPORT_PATH "+str(out),flush=True);return out

def compare(first,second,first_review=None,second_review=None):
    if bool(first_review)!=bool(second_review):raise ValueError("请同时提供两个版本的人工评分")
    a=score(first,first_review);b=score(second,second_review)
    for key in ("dataset_hash","evaluator_version","config_hash"):
        if a["manifest"][key]!=b["manifest"][key]:raise ValueError("比较条件不一致："+key+"；请统一条件重跑基线")
    result=[]
    for x,y in zip(a["metrics"],b["metrics"]):
        result.append({"name":x["name"],"before":x["value"],"after":y["value"],
            "delta_percentage_points":None if x["value"] is None or y["value"] is None else (y["value"]-x["value"])*100})
    return {"first":a["run_id"],"second":b["run_id"],"metrics":result,"note":"N/A不生成提升结论。模型或参数变化默认拒绝直接对比，需冻结对照协议。"}

