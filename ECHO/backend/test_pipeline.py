import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import pipeline

class Tests(unittest.TestCase):
    def test_clean_and_preserve(self):
        self.assertEqual(pipeline.clean("[捂脸]😂")[1], "empty_or_expression_only")
        self.assertEqual(pipeline.clean("太贵了但很好用[微笑]")[0], "太贵了但很好用")
        self.assertNotIn("13812345678", pipeline.clean("联系13812345678")[0])
        self.assertEqual(pipeline.clean("续航一般")[1], None)

    def test_end_to_end_resume_retry(self):
        received, source_calls, source_cookies, sink_cookies = {}, [], [], []
        failures = [1]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def send(self, status, payload):
                raw = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(raw)
            def do_GET(self):
                source_calls.append(self.path)
                source_cookies.append(self.headers.get("Cookie"))
                second = "cursor=1" in self.path
                rows = [{"id":"1","text":"价格贵但很好用","video":"v"}]
                if second:
                    rows += [{"id":"2","text":"😂","video":"v"},
                             {"id":"3","text":"续航一般","video":"v"}]
                self.send(200, {"items":rows,"more":not second,"cursor":2 if second else 1})
            def do_POST(self):
                sink_cookies.append(self.headers.get("Cookie"))
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                identifier = self.headers["Idempotency-Key"]
                if failures[0]:
                    failures[0] -= 1
                    self.send(503,{})
                    return
                received[identifier] = payload
                self.send(200,{"accepted":True,"external_id":identifier})
        server = ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                url = "http://127.0.0.1:" + str(server.server_port)
                config = {"sources":[{
                    "type":"http","url":url+"/comments","cookie_env":"TEST_COOKIE",
                    "product":"A","items_path":"items","has_more_path":"more",
                    "next_cursor_path":"cursor","max_pages_per_run":1,"page_delay_seconds":0,
                    "fields":{"id":"id","text":"text","video_id":"video"}
                }],"sink":{"url":url+"/import"}}
                path=base/"config.json"
                path.write_text(json.dumps(config),encoding="utf-8")
                with patch.dict("os.environ",{"TEST_COOKIE":"test-only"}), patch("pipeline.time.sleep"):
                    self.assertEqual(pipeline.run(path),{"delivered":1})
                    self.assertEqual(pipeline.run(path),{"delivered":2,"excluded":1})
                    self.assertEqual(pipeline.run(path),{"delivered":2,"excluded":1})
                self.assertEqual(len(source_calls),2)
                self.assertEqual(len(received),2)
                self.assertEqual(source_cookies,["test-only","test-only"])
                self.assertTrue(all(c is None for c in sink_cookies))
                self.assertTrue(all("original_text" not in p for p in received.values()))
        finally:
            server.shutdown()
            server.server_close()

    def test_bad_page_does_not_advance(self):
        source={"type":"file","path":"rows.json","product":"A","items_path":"items",
                "fields":{"id":"id","text":"text"}}
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            (base/"rows.json").write_text('{"items":[{"id":"1","text":"有效"},{"text":"缺ID"}]}',encoding="utf-8")
            db=pipeline.connect(base/"state.db")
            with self.assertRaises(pipeline.PipelineError):
                pipeline.ingest(db,source,base)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM comments").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0],0)
            db.close()

    def test_sink_failure_is_retriable(self):
        with tempfile.TemporaryDirectory() as directory:
            db=pipeline.connect(Path(directory)/"state.db")
            payload={"external_id":"test","original_text":"原文","cleaned_text":"原文"}
            db.execute("INSERT INTO comments(id,payload,state) VALUES(?,?,'pending')",
                       ("test",json.dumps(payload)))
            db.commit()
            with patch("pipeline.request_json",return_value={"accepted":True,"external_id":"wrong"}):
                with self.assertRaises(pipeline.PipelineError):
                    pipeline.deliver(db,{"url":"http://localhost/import"})
            self.assertEqual(db.execute("SELECT state FROM comments").fetchone()[0],"failed")
            with patch("pipeline.request_json",return_value={"accepted":True,"external_id":"test"}):
                pipeline.deliver(db,{"url":"http://localhost/import"})
            self.assertEqual(db.execute("SELECT state FROM comments").fetchone()[0],"delivered")
            db.close()

if __name__=="__main__":
    unittest.main()

