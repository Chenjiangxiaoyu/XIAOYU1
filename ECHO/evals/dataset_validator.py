from .schemas import digest
def validate(data,strict=False):
    errors=[];warnings=[];ids=set();groups={};text_groups={}
    if not data.get("dataset_version"):errors.append("缺少 dataset_version")
    cases=data.get("cases")
    if not isinstance(cases,list) or not cases:raise ValueError("需要非空 cases 数组")
    for c in cases:
        cid=c.get("case_id","?")
        for k in ("case_id","group_id","source_kind","source_ref","product","text","scenario","split","annotation_version","annotator","adjudication_status"):
            if not c.get(k):errors.append(cid+":缺少 "+k)
        if cid in ids:errors.append(cid+":重复 case_id")
        if not isinstance(cid,str) or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for ch in cid):
            errors.append("case_id 仅允许字母数字连字符下划线")
        ids.add(cid)
        if c.get("source_kind") not in ("real","synthetic"):errors.append(cid+":source_kind 无效")
        group=c.get("group_id");split=c.get("split")
        if group in groups and groups[group]!=split:errors.append(cid+":同源组跨 split")
        groups[group]=split
        text=c.get("text")
        if not isinstance(text,str) or not text.strip():errors.append(cid+":文本为空");continue
        if text in text_groups and text_groups[text]!=group:errors.append(cid+":重复文本应属于同一 group")
        text_groups[text]=group
        g=c.get("gold")
        if not isinstance(g,dict):
            errors.append(cid+":缺少 gold 草案");continue
        if not isinstance(g.get("keep"),bool) or not isinstance(g.get("review_required"),bool):errors.append(cid+":gold 布尔标签无效")
        if g.get("sentiment") not in ("正向","负向","中性","混合",None):errors.append(cid+":情绪标签无效")
        if not g.get("keep") and not g.get("excluded_reason"):errors.append(cid+":排除缺少原因")
        gf=g.get("findings")
        if not isinstance(gf,list):errors.append(cid+":gold.findings 必须为数组");continue
        fids=set()
        for f in gf:
            for k in ("gold_finding_id","subject","aspect","type","claim","quote","forbidden_inferences"):
                if not f.get(k):errors.append(cid+":发现缺少 "+k)
            if f.get("gold_finding_id") in fids:errors.append(cid+":重复 gold_finding_id")
            fids.add(f.get("gold_finding_id"))
            if f.get("quote") not in text:errors.append(cid+":gold 引文不在原文")
        if c.get("adjudication_status")!="human_confirmed":
            warnings.append(cid+":AI草案，等待人工确认")
    if strict and warnings:errors+=warnings
    if errors:raise ValueError("\n".join(errors))
    return {"n_cases":len(cases),"n_groups":len(groups),"dataset_hash":digest(data),"warnings":warnings}

