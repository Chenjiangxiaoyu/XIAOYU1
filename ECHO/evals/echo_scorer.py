"""Human-confirmed, one-to-one scoring. Pending labels never become accuracy."""
from .schemas import EVALUATOR_VERSION,digest,file_hash,read
SENTIMENTS=("正向","中性","负向","混合")
THRESHOLDS={"end_to_end_pass_rate":.8,"valid_comment_pass_rate":.8,"finding_precision":.9,
 "finding_recall":.85,"sentiment_accuracy":.85,"sentiment_macro_f1":.8,
 "valid_comment_false_exclusion":.05,"noise_filter_recall":.9,
 "semantic_support_rate":.95,"advice_pass_rate":.8,"required_review_recall":.95,
 "reliable_completion_rate":.98,"human_net_time_saved":.3}
QUALITY=("end_to_end_pass_rate","valid_comment_pass_rate","finding_precision","finding_recall","finding_f1",
 "sentiment_accuracy","sentiment_macro_f1","valid_comment_false_exclusion","noise_filter_recall",
 "semantic_support_rate","advice_pass_rate","required_review_recall","review_false_positive_rate")
def calculate(dataset,outputs,reviews=None):
    cases=dataset["cases"];byid={o["case_id"]:o for o in outputs};n=len(cases);groups=len({c["group_id"] for c in cases})
    metrics=[]
    def metric(name,num,den,missing=0,scope="all_inputs",unit="ratio",value_override=None):
        value=None if not den or missing else num/den
        if value_override is not None and not missing:value=value_override
        limit=THRESHOLDS.get(name)
        passed=None if value is None or limit is None else (value<=limit if name=="valid_comment_false_exclusion" else value>=limit)
        metrics.append({"name":name,"value":value,"unit":unit,"numerator":num,"denominator":den,
            "n_cases":n,"n_groups":groups,"scope":scope,"missing_count":missing,"threshold":limit,"pass":passed,
            "dataset_version":dataset["dataset_version"],"evaluator_version":EVALUATOR_VERSION})
    successful=sum(byid.get(c["case_id"],{}).get("final_success",False) for c in cases)
    metric("structured_completion_rate",successful,n)
    metric("first_attempt_success_rate",sum(byid.get(c["case_id"],{}).get("first_attempt_success",False) for c in cases),n)
    attempts=[a for o in outputs for a in o.get("attempts",[])]
    metric("generation_quote_rejection_rate",sum(o.get("quote_rejections",0) for o in outputs),len(attempts))
    pending_local=sum(byid.get(c["case_id"],{}).get("validation_status")=="local_excluded" and c.get("adjudication_status")!="human_confirmed" for c in cases)
    reliable=sum(o.get("validation_status")=="accepted" for o in outputs)+sum(
        byid.get(c["case_id"],{}).get("validation_status")=="local_excluded" and c["adjudication_status"]=="human_confirmed" and not c["gold"]["keep"] for c in cases)
    metric("reliable_completion_rate",reliable,n,missing=pending_local)
    metric("human_net_time_saved",None,None,missing=n,scope="not_measured")
    reviews=reviews or {}
    pending_gold=sum(c.get("adjudication_status")!="human_confirmed" for c in cases)
    pending_review=sum(c["case_id"] not in reviews or reviews[c["case_id"]].get("status")!="human_confirmed" for c in cases)
    if pending_gold or pending_review:
        for name in QUALITY:metric(name,None,None,missing=max(pending_gold,pending_review),scope="pending_human_gold_and_review")
        return {"metrics":metrics,"case_scores":[{"case_id":c["case_id"],"pass":None,"reason":"待人工确认 gold 和评分"} for c in cases],
            "hard_blocks_confirmed":None,"verdict":"待人工复核；不能宣称质量通过","pending_gold":pending_gold,"pending_reviews":pending_review}
    tp=pred_total=gold_total=valid=valid_pass=passed=wrong_exclusion=noise=noise_tp=sent_n=sent_correct=required=required_tp=review_fp=not_required=support=advice_ok=blocks=0
    confusion={s:{"tp":0,"fp":0,"fn":0,"support":0} for s in SENTIMENTS};scores=[]
    for c in cases:
        cid=c["case_id"];g=c["gold"];o=byid.get(cid,{})
        result=o.get("parsed_output") or {};r=reviews[cid]
        generated=result.get("findings",[])
        if r.get("compound_unresolved"):raise ValueError(cid+":先拆分复合结论再评分")
        # Reviewer can split a compound generated finding into multiple atoms; each retains its parent index.
        atoms=r.get("atoms",[{"prediction_index":i,"atom_id":str(i)} for i in range(len(generated))])
        if {a["prediction_index"] for a in atoms}!=set(range(len(generated))):raise ValueError(cid+":原子评分未覆盖所有输出")
        atom_ids=[a["atom_id"] for a in atoms]
        if len(set(atom_ids))!=len(atom_ids):raise ValueError(cid+":重复原子ID")
        items=r.get("findings",[])
        if {f["prediction_id"] for f in items}!=set(atom_ids) or len(items)!=len(atoms):raise ValueError(cid+":每个输出原子必须有且只有一个评分")
        matched=set();local_tp=0;all_supported=True;all_advice=True
        known={f["gold_finding_id"] for f in g["findings"]}
        for f in items:
            gid=f.get("gold_finding_id")
            if gid is not None:
                if gid not in known:raise ValueError(cid+":gold 映射不存在")
                if gid in matched:raise ValueError(cid+":一对一匹配被违反")
                matched.add(gid);local_tp+=1
            if not isinstance(f.get("supported"),bool):raise ValueError(cid+":缺少语义支持评分")
            rubric=f.get("advice")
            if not isinstance(rubric,list) or len(rubric)!=4 or any(type(x)!=int or x not in (0,1) for x in rubric):raise ValueError(cid+":建议需四项0/1评分")
            good=sum(rubric)>=3 and rubric[0]==rubric[3]==1
            support+=f["supported"];advice_ok+=good
            all_supported&=f["supported"];all_advice&=good
        hard=r.get("hard_blocks")
        if not isinstance(hard,list):raise ValueError(cid+":缺少硬阻断复核")
        blocks+=len(hard)
        pred_keep=not bool(result.get("excluded_reason")) if o.get("final_success") else None
        keep_ok=pred_keep==g["keep"]
        if g["keep"]:
            valid+=1;wrong_exclusion+=pred_keep is False
        else:noise+=1;noise_tp+=pred_keep is False
        sentiment_ok=True
        if g.get("sentiment") is not None:
            sent_n+=1;true=g["sentiment"];pred=result.get("sentiment")
            sentiment_ok=pred==true;sent_correct+=sentiment_ok
            for s in SENTIMENTS:
                confusion[s]["support"]+=true==s
                confusion[s]["tp"]+=true==s and pred==s
                confusion[s]["fn"]+=true==s and pred!=s
                confusion[s]["fp"]+=true!=s and pred==s
        if g["review_required"]:required+=1;required_tp+=result.get("review_required") is True
        else:not_required+=1;review_fp+=result.get("review_required") is True
        ok=bool(o.get("final_success") and keep_ok and sentiment_ok and local_tp==len(g["findings"])==len(atoms)
             and all_supported and all_advice and result.get("review_required")==g["review_required"] and not hard)
        passed+=ok;valid_pass+=bool(ok and g["keep"]);tp+=local_tp;pred_total+=len(atoms);gold_total+=len(g["findings"])
        scores.append({"case_id":cid,"pass":ok,"tp":local_tp,"fp":len(atoms)-local_tp,"fn":len(g["findings"])-local_tp})
    metric("end_to_end_pass_rate",passed,n);metric("valid_comment_pass_rate",valid_pass,valid)
    metric("finding_precision",tp,pred_total);metric("finding_recall",tp,gold_total)
    metric("finding_f1",2*tp,pred_total+gold_total)
    metric("sentiment_accuracy",sent_correct,sent_n)
    per_class={s:None if not x["support"] else (2*x["tp"]/(2*x["tp"]+x["fp"]+x["fn"]) if 2*x["tp"]+x["fp"]+x["fn"] else None) for s,x in confusion.items()}
    missing=sum(v is None for v in per_class.values())
    metric("sentiment_macro_f1",sum(v or 0 for v in per_class.values()),4,missing=missing,scope="fixed_four_classes")
    metric("valid_comment_false_exclusion",wrong_exclusion,valid);metric("noise_filter_recall",noise_tp,noise)
    metric("semantic_support_rate",support,pred_total);metric("advice_pass_rate",advice_ok,pred_total)
    metric("required_review_recall",required_tp,required);metric("review_false_positive_rate",review_fp,not_required)
    limits=[m for m in metrics if m["threshold"] is not None]
    verdict="不通过" if blocks or any(m["pass"] is False for m in limits) else ("数据不足/存在未测指标" if any(m["pass"] is None for m in limits) else "本轮离线门槛通过")
    return {"metrics":metrics,"case_scores":scores,"hard_blocks_confirmed":blocks,"verdict":verdict,"sentiment_classes":per_class}

