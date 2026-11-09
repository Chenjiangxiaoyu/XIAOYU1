"""Versioned evaluation contracts and append-only filesystem helpers."""
import hashlib, json, os, re
from datetime import datetime, timezone
from pathlib import Path
EVALUATOR_VERSION="echo-evaluator-v1.0.0"
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"evals"/"runs"
def now():return datetime.now(timezone.utc).isoformat()
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def digest(obj):return hashlib.sha256(canonical(obj).encode()).hexdigest()
def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def write_new(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def redact(value):
    if isinstance(value,dict):
        return {k:("[REDACTED]" if any(w in k.lower() for w in ("authorization","cookie","api_key","access_token","sessionid")) else redact(v)) for k,v in value.items()}
    if isinstance(value,list):return [redact(v) for v in value]
    if isinstance(value,str):
        text=value
        for k in ("DEEPSEEK_API_KEY","DOUYIN_COOKIE"):
            secret=os.environ.get(k,"")
            if secret:text=text.replace(secret,"[REDACTED]")
        text=re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)","[手机号]",text)
        return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}","[邮箱]",text)
    return value

