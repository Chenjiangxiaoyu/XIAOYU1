"""Standalone human review form; never labels itself as independent gold."""
import html,json
from pathlib import Path
from .reporter import bundle,review_template
def build(folder):
    folder=Path(folder);m,d,outputs,_=bundle(folder);byid={o["case_id"]:o for o in outputs}
    payload={"dataset":d,"outputs":byid,"template":review_template(folder)}
    script=json.dumps(payload,ensure_ascii=False).replace("<","\\u003c").replace("\u2028","\\u2028").replace("\u2029","\\u2029")
    text='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>ECHO 人工复核</title><style>
body{font:15px/1.75 system-ui;background:#f4f6fa;color:#243146;max-width:1100px;margin:32px auto;padding:0 20px}
section{background:white;border:1px solid #dce2eb;padding:24px;margin:20px 0;border-radius:14px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:14px}
label{display:block;margin:10px 0}select,input,textarea,button{font:inherit;padding:7px;max-width:100%}
textarea{display:block;width:95%}button{background:#245947;color:white;border:0;border-radius:8px;padding:10px 18px;cursor:pointer}
.warning{background:#fff2d5;padding:14px}.prediction{border-top:1px solid #e5e8ec;margin-top:16px;padding-top:14px}.bar{position:sticky;top:0;background:#f4f6faee;padding:12px 0}
</style><h1>ECHO · 11 条人工复核</h1>
<p class="warning">这是 AI 预标注草案与不可变 V0 输出。请逐条核对，不能直接把勾选后的结果当作独立双人验证。若要修改 gold 内容，请停止确认该条，升级数据集后重新运行 V0。</p>
<div class="bar"><label>评分者姓名或代号 <input id="reviewer"></label><button id="save">下载复核 JSON</button> <button id="timer">开始主动计时</button> <span id="elapsed"></span></div>
<p>建议四项评分：①针对具体反馈；②可执行验证动作与对象；③指标与判断方式；④区分证据/假设且不编造。每项0/1，通过需至少3分且①④必须为1。引文存在不等于支持结论。</p><main id="cases"></main>
<script>const payload='''+script+''';
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const select=(id,options)=>'<select id="'+id+'"><option value="">未评分</option>'+options.map(([v,t])=>'<option value="'+esc(v)+'">'+esc(t)+'</option>').join('')+'</select>';
document.getElementById('cases').innerHTML=payload.dataset.cases.map((c,index)=>{
const o=payload.outputs[c.case_id]||{},p=o.parsed_output||{},prefix='c'+index;
return '<section><h2>'+esc(c.case_id)+' · '+esc(c.scenario)+'</h2><p><b>原文：</b>'+esc(c.text)+'</p><p><b>清洗后：</b>'+esc(o.cleaned_text)+'</p><details><summary>AI预标注 gold：请先独立核对，再展开查看</summary><pre>'+esc(JSON.stringify(c.gold,null,2))+'</pre></details>'+
'<label>冻结 gold 是否正确？'+select(prefix+'gold',[['yes','已人工确认，内容无需修改'],['no','有分歧，需修改数据集']])+'</label>'+
'<p>生产输出：'+esc(o.validation_status)+'；情绪 '+esc(p.sentiment)+'；复核标记 '+esc(p.review_required)+'；排除原因 '+esc(p.excluded_reason)+'</p>'+
(p.findings||[]).map((f,i)=>'<div class="prediction"><h3>预测 '+i+'：'+esc(f.title)+'</h3><pre>'+esc(JSON.stringify(f,null,2))+'</pre>'+
'<label>匹配哪条 gold？'+select(prefix+'f'+i+'match',[['none','无匹配（额外或错误发现）'],...c.gold.findings.map(g=>[g.gold_finding_id,g.gold_finding_id+' '+g.claim])])+'</label>'+
'<label>引文与上下文是否支持结论？'+select(prefix+'f'+i+'support',[['1','支持'],['0','不支持']])+'</label>'+
[1,2,3,4].map(k=>'<label>建议量表第 '+k+' 项 '+select(prefix+'f'+i+'advice'+k,[['1','1 — 满足'],['0','0 — 不满足']])+'</label>').join('')+
'<label>评分理由<textarea id="'+prefix+'f'+i+'reason" rows="2"></textarea></label></div>').join('')+
'<label><input type="checkbox" id="'+prefix+'compound">输出含未拆分的复合结论：暂停该条评分，先人工拆分 atoms</label>'+
'<label>硬性阻断（伪造引文/编造规模销量根因/指令干扰/泄露），每行一项，无则留空<textarea id="'+prefix+'blocks" rows="2"></textarea></label>'+
'<label>其他分歧或备注<textarea id="'+prefix+'reason" rows="2"></textarea></label>'+
'<label>该条复核状态 '+select(prefix+'status',[['human_confirmed','我已完成此条人工复核'],['pending_human','保持待复核']])+'</label></section>';
}).join('');
let active=false,total=0,lastTick=Date.now(),lastAction=Date.now(),started=null,events=[];
function tick(){let now=Date.now();if(active&&!document.hidden&&now-lastAction<30000)total+=now-lastTick;lastTick=now;document.getElementById('elapsed').textContent='主动操作 '+Math.round(total/1000)+' 秒（隐藏/闲置30秒暂停；仅本次页面）'}
setInterval(tick,1000);
['pointerdown','keydown','scroll','input'].forEach(e=>document.addEventListener(e,()=>lastAction=Date.now(),{passive:true}));
document.addEventListener('visibilitychange',()=>{tick();events.push({type:document.hidden?'hidden':'visible',at:new Date().toISOString()})});
document.getElementById('timer').onclick=()=>{tick();active=!active;if(!started)started=new Date().toISOString();lastAction=Date.now();events.push({type:active?'start':'pause',at:new Date().toISOString()});document.getElementById('timer').textContent=active?'暂停主动计时':'继续主动计时'};
document.getElementById('save').onclick=()=>{
tick();const result=JSON.parse(JSON.stringify(payload.template));result.reviewer=document.getElementById('reviewer').value.trim();result.reviewed_at=new Date().toISOString();
if(!result.reviewer){alert('请填写评分者');return}
const get=id=>document.getElementById(id).value;
for(let index=0;index<result.cases.length;index++){
let r=result.cases[index],prefix='c'+index;r.status=get(prefix+'status')||'pending_human';r.gold_confirmed=get(prefix+'gold')==='yes';r.compound_unresolved=document.getElementById(prefix+'compound').checked;
r.hard_blocks=get(prefix+'blocks').split('\\n').map(x=>x.trim()).filter(Boolean);r.reason=get(prefix+'reason');
for(let i=0;i<r.findings.length;i++){
let f=r.findings[i],match=get(prefix+'f'+i+'match'),support=get(prefix+'f'+i+'support');
f.gold_finding_id=match==='none'||!match?null:match;f.supported=support===''?null:support==='1';
f.advice=[1,2,3,4].map(k=>{let v=get(prefix+'f'+i+'advice'+k);return v===''?null:Number(v)});
f.reason=get(prefix+'f'+i+'reason');
if(r.status==='human_confirmed'&&(!match||support===''||f.advice.includes(null))){alert(r.case_id+' 的预测评分未填完');return}
}
if(r.status==='human_confirmed'&&(!r.gold_confirmed||r.compound_unresolved)){alert(r.case_id+' 的金标未确认或复合结论未拆分，请保持待复核');return}
}
result.activity={active_ms:Math.round(total),started_at:started,submitted_at:new Date().toISOString(),events:[...events,{type:'submit',at:new Date().toISOString()}],note:'自报单人复核；无纯人工对照，不能计算节时'};
const a=document.createElement('a');const u=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));a.href=u;a.download='human-review-'+result.run_id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),10000);
};
</script></html>'''
    path=folder/"human-review.html"
    with path.open("x",encoding="utf-8") as f:f.write(text)
    return path

