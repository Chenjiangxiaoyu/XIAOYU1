import copy,json,io,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from evals.echo_scorer import calculate
from evals.dataset_validator import validate
from evals.schemas import digest,write_new,read
from evals import adapter

def fixtures():
    d={"dataset_version":"fixture-v1","cases":[{"case_id":"C1","group_id":"S1","source_kind":"synthetic",
       "source_ref":"fixture","product":"test","text":"太贵，续航短","scenario":"多方面","split":"development",
       "annotation_version":"fixture","annotator":"fixture","adjudication_status":"human_confirmed",
       "gold":{"keep":True,"excluded_reason":None,"sentiment":"负向","review_required":False,
               "findings":[{"gold_finding_id":"g1","subject":"test","aspect":"价格","type":"待改进","claim":"贵","quote":"太贵","forbidden_inferences":["销量"]},
                           {"gold_finding_id":"g2","subject":"test","aspect":"续航","type":"待改进","claim":"续航短","quote":"续航短","forbidden_inferences":["根因"]}]}}]}
    o=[{"case_id":"C1","final_success":True,"first_attempt_success":True,"validation_status":"accepted","attempts":[],
        "parsed_output":{"sentiment":"负向","review_required":False,"excluded_reason":None,"findings":[{"quote":"太贵"}]}}]
    r={"C1":{"status":"human_confirmed","hard_blocks":[],"findings":[{"prediction_id":"0","gold_finding_id":"g1","supported":True,"advice":[1,1,1,1]}]}}
    return d,o,r
def vals(d,o,r):return {m["name"]:m for m in calculate(d,o,r)["metrics"]}
class ScorerTests(unittest.TestCase):
    def test_precision_recall(self):
        d,o,r=fixtures();v=vals(d,o,r)
        self.assertEqual(v["finding_precision"]["value"],1)
        self.assertEqual(v["finding_recall"]["value"],.5)
        self.assertEqual(v["end_to_end_pass_rate"]["value"],0)
    def test_duplicate_fp(self):
        d,o,r=fixtures();o[0]["parsed_output"]["findings"]*=2
        r["C1"]["findings"].append({"prediction_id":"1","gold_finding_id":None,"supported":True,"advice":[1,1,1,1]})
        self.assertEqual(vals(d,o,r)["finding_precision"]["value"],.5)
        r["C1"]["findings"][1]["gold_finding_id"]="g1"
        with self.assertRaises(ValueError):calculate(d,o,r)
    def test_quote_is_not_support(self):
        d,o,r=fixtures();r["C1"]["findings"][0]["supported"]=False
        self.assertEqual(vals(d,o,r)["semantic_support_rate"]["value"],0)
    def test_missing_gold_pending(self):
        d,o,r=fixtures();d["cases"][0]["adjudication_status"]="pending_human"
        self.assertIsNone(vals(d,o,r)["finding_precision"]["value"])
    def test_failure_in_denominator(self):
        d,o,r=fixtures();o[0].update(final_success=False,first_attempt_success=False,parsed_output=None,validation_status="failed")
        r["C1"]["findings"]=[]
        v=vals(d,o,r);self.assertEqual(v["finding_recall"]["value"],0)
        self.assertEqual(v["sentiment_accuracy"]["value"],0)
        self.assertIsNone(v["finding_precision"]["value"])
    def test_zero_noise_and_absent_classes(self):
        d,o,r=fixtures();v=vals(d,o,r)
        self.assertIsNone(v["noise_filter_recall"]["value"])
        self.assertIsNone(v["sentiment_macro_f1"]["value"])
    def test_guideline_constraints(self):
        d,o,r=fixtures();r["C1"]["findings"][0]["advice"]=[0,1,1,1]
        self.assertEqual(vals(d,o,r)["advice_pass_rate"]["value"],0)
        r["C1"]["hard_blocks"]=["fabricated root cause"]
        self.assertEqual(calculate(d,o,r)["verdict"],"不通过")
    def test_split_and_quote_validation(self):
        d,o,r=fixtures();validate(d)
        c=copy.deepcopy(d["cases"][0]);c["case_id"]="C2";c["split"]="blind";d["cases"].append(c)
        with self.assertRaises(ValueError):validate(d)
    def test_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"f.json";write_new(p,{"x":1})
            with self.assertRaises(FileExistsError):write_new(p,{"x":2})
            self.assertEqual(read(p),{"x":1})

class FakeResponse:
    status=200
    def __init__(self,payload):self.payload=payload
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def read(self,limit):return json.dumps(self.payload,ensure_ascii=False).encode()[:limit]
class Transport:
    def __init__(self,failures=0,badquote=False,truncated=False):
        self.failures=failures;self.requests=[];self.badquote=badquote;self.truncated=truncated
    def open(self,req,timeout=30):
        self.requests.append(json.loads(req.data))
        if self.failures:self.failures-=1;raise urllib.error.HTTPError(req.full_url,503,"fixture",{},io.BytesIO())
        result={"sentiment":"负向","review_required":False,"excluded_reason":None,
            "findings":[{"type":"待改进","title":"贵","summary":"价格反馈","quote":"编造" if self.badquote else "太贵",
                        "recommendation":"验证价格","validation":"访谈","risk":"样本小","success":"待定"}]}
        return FakeResponse({"model":"fixture","choices":[{"message":{"content":'{"sentiment":' if self.truncated else json.dumps(result,ensure_ascii=False)},
                    "finish_reason":"length" if self.truncated else "stop"}],"usage":{"prompt_tokens":10,"completion_tokens":10,"total_tokens":20}})
class AdapterTests(unittest.TestCase):
    def execute(self,t):
        with tempfile.TemporaryDirectory() as temp,patch.dict("os.environ",{"DEEPSEEK_API_KEY":"SECRET-TEST-KEY"}),patch("pipeline.time.sleep"):
            # Intentionally pass extra gold: adapter's request construction must ignore it.
            o=adapter.execute({"case_id":"C1","product":"test","text":"太贵","gold":{"secret_gold":"NEVER_SEND_GOLD"}},"run",Path(temp),transport=t)
            files=list(Path(temp).glob("*.json"))
            self.assertNotIn("SECRET-TEST-KEY","".join(p.read_text(encoding="utf-8") for p in files))
            return o
    def test_real_production_path_and_no_gold(self):
        t=Transport();o=self.execute(t)
        self.assertTrue(o["final_success"])
        self.assertNotIn("NEVER_SEND_GOLD",json.dumps(t.requests))
    def test_retry_all_attempts(self):
        o=self.execute(Transport(failures=1))
        self.assertFalse(o["first_attempt_success"]);self.assertTrue(o["final_success"])
        self.assertEqual(len(o["attempts"]),2);self.assertEqual(o["attempts"][0]["http_status"],503)
    def test_quote_reject(self):
        o=self.execute(Transport(badquote=True))
        self.assertFalse(o["final_success"]);self.assertEqual(o["quote_rejections"],1)
    def test_truncated_retained(self):
        o=self.execute(Transport(truncated=True))
        self.assertFalse(o["final_success"]);self.assertEqual(o["attempts"][0]["finish_reason"],"length")
    def test_cancel_retained(self):
        class Cancel:
            def open(self,*a,**k):raise KeyboardInterrupt()
        o=self.execute(Cancel())
        self.assertEqual(o["validation_status"],"cancelled")
if __name__=="__main__":unittest.main()


class RunProtocolTests(unittest.TestCase):
    def test_two_runs_and_mismatch(self):
        from evals.runner import run
        from evals.reporter import bundle,compare
        d,outputs,r=fixtures();d.update(project="ECHO",split="development",mode="synthetic")
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);dataset=base/"data.json";write_new(dataset,d)
            def fake(case,run_id,folder):
                return {**outputs[0],"run_id":run_id,"latency_ms":1,"quote_rejections":0}
            with patch("evals.runner.adapter.load_runtime"),patch("evals.runner.adapter.execute",side_effect=fake):
                first=run(dataset,root=base/"runs")
                second=run(dataset,root=base/"runs")
                self.assertNotEqual(first,second)
                before=(first/"C1.json").read_bytes()
                compare(first,second)
                self.assertEqual(before,(first/"C1.json").read_bytes())
                d["dataset_version"]="fixture-v2";dataset2=base/"data2.json";write_new(dataset2,d)
                third=run(dataset2,root=base/"runs")
                with self.assertRaises(ValueError):compare(first,third)


