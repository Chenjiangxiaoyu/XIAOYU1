import json, sys, tempfile, unittest, threading, time
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ingestion, pipeline, server

def analysis(payload):
    return {"sentiment":"混合","review_required":False,"excluded_reason":None,
        "findings":[{"type":"待改进","title":"价格反馈","summary":"该样本认为价格偏高","quote":"太贵",
        "recommendation":"验证价格接受度","validation":"补充样本","risk":"样本小","success":"建立基线"}]}

class Integration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.dbpatch=patch.object(ingestion,"DB",Path(self.temp.name)/"state.sqlite3")
        self.dbpatch.start()
    def tearDown(self):
        self.dbpatch.stop();self.temp.cleanup()
    def test_idempotent_and_analysis(self):
        x={"text":"太贵但很好用😂","product":"A","external_id":"id1"}
        first=ingestion.add(x);self.assertEqual(first,ingestion.add(x))
        ingestion.add({"text":"[捂脸]😂","product":"B"})
        conn=ingestion.db()
        with patch.object(ingestion,"analyze",side_effect=analysis):ingestion.process(conn)
        conn.close()
        data=ingestion.snapshot()
        self.assertEqual(data["counts"],{"analyzed":1,"excluded":1})
        self.assertEqual(data["findings"][0]["evidence_ids"],[first])
        self.assertEqual(data["products"]["A"]["mixed"],1)
        self.assertNotIn("original_text",json.dumps(data))
    def test_failure_retry(self):
        ingestion.add({"text":"太贵","product":"A"})
        conn=ingestion.db()
        with patch.object(ingestion,"analyze",side_effect=pipeline.PipelineError("模拟失败")):
            with self.assertRaises(pipeline.PipelineError):ingestion.process(conn)
        self.assertEqual(ingestion.snapshot()["counts"],{"failed":1})
        with patch.object(ingestion,"analyze",side_effect=analysis):ingestion.process(conn)
        self.assertEqual(ingestion.snapshot()["counts"],{"analyzed":1})
        conn.close()
    def test_quote_validation(self):
        result=analysis(None);result["findings"][0]["quote"]="编造的内容"
        with patch.dict("os.environ",{"DEEPSEEK_API_KEY":"fake"}),patch.object(pipeline,"request_json",return_value={"choices":[{"message":{"content":json.dumps(result)}}]}):
            with self.assertRaises(pipeline.PipelineError): ingestion.analyze({"product":"A","cleaned_text":"太贵"})
    def test_api_and_static(self):
        http=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        url="http://127.0.0.1:"+str(http.server_port)
        try:
            with patch.object(ingestion,"analyze",side_effect=analysis):
                req=Request(url+"/api/reviews",data=json.dumps({"text":"太贵","product":"A","external_id":"stable"}).encode(),headers={"Content-Type":"application/json"})
                with urlopen(req) as r:self.assertTrue(json.load(r)["accepted"])
                for _ in range(100):
                    if not ingestion.LOCK.locked():break
                    time.sleep(.02)
                with urlopen(url+"/api/pipeline") as r:self.assertEqual(json.load(r)["counts"],{"analyzed":1})
                with urlopen(url) as r:self.assertIn(b'id="pipelinePanel"',r.read())
        finally:http.shutdown();http.server_close()
    def test_config_rejects_secret(self):
        with self.assertRaises(ValueError): ingestion.validate_source({"type":"http","product":"A","url":"https://example.com?cookie=secret"})
if __name__=="__main__":unittest.main()

