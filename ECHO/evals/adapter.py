"""Observe real production clean/analyze without copying or modifying its prompt.
Run only in the standalone evaluation process, never inside the business server.
"""
import inspect, json, os, sys, time, urllib.error
from pathlib import Path
from unittest.mock import patch
from .schemas import ROOT, now, digest, redact, write_new
sys.path.insert(0,str(ROOT/"backend"))
import ingestion, pipeline, server

def load_runtime():
    server.load_env()

def implementation():
    return {"analyze_hash":digest(inspect.getsource(ingestion.analyze)),
            "cleaner_version":digest(inspect.getsource(pipeline.clean)),
            "transport_hash":digest(inspect.getsource(pipeline.request_json))}

def execute(case,run_id,folder,model_id=None,transport=None):
    begin=now();clock=time.perf_counter()
    cleaned,excluded=pipeline.clean(case["text"])
    payload={"product":case["product"],"cleaned_text":cleaned}
    output={"run_id":run_id,"case_id":case["case_id"],"input_hash":digest(case["text"]),
            "cleaned_text":cleaned,"cleaned_text_hash":digest(cleaned),
            "started_at":begin,"attempts":[],"parsed_output":None,"failure_stage":None,
            "validation_status":None,"estimated_cost":None,"price_version":None,
            "cleaner_changed":cleaned!=case["text"],"implementation":implementation()}
    if excluded:
        output.update(validation_status="local_excluded",parsed_output={"excluded_reason":excluded,"findings":[],"sentiment":None,"review_required":False})
    else:
        opener_factory=pipeline.build_opener
        def observed_factory(*args,**kwargs):
            real=opener_factory(*args,**kwargs) if transport is None else transport
            class Observed:
                def open(self,req,timeout=30):
                    # Headers and credentials are deliberately never recorded.
                    body=json.loads(req.data.decode())
                    meta={"attempt_id":len(output["attempts"])+1,"started_at":now(),
                          "model_id":body.get("model"),"prompt_hash":digest(body["messages"][0]),
                          "request_body_hash":digest(body),"request_body":redact(body),
                          "parameters":{k:v for k,v in body.items() if k!="messages"},
                          "timeout_seconds":timeout,"token_usage":None,"estimated_cost":None,
                          "price_version":None,"http_status":None,"failure_stage":None}
                    stamp=time.perf_counter();output["attempts"].append(meta)
                    name=f'{case["case_id"]}-attempt-{meta["attempt_id"]:02d}.json'
                    def persist(raw=None):
                        if raw is not None:meta["raw_response"]=redact(raw)
                        meta["finished_at"]=now();meta["latency_ms"]=round((time.perf_counter()-stamp)*1000,2)
                        write_new(folder/name,meta)
                        meta["raw_response_ref"]=name
                    try:
                        response=real.open(req,timeout=timeout)
                        meta["http_status"]=getattr(response,"status",200)
                    except (Exception, KeyboardInterrupt) as exc:
                        meta["http_status"]=getattr(exc,"code",None)
                        meta["failure_stage"]="cancelled" if isinstance(exc,KeyboardInterrupt) else ("http" if isinstance(exc,urllib.error.HTTPError) else "network")
                        meta["error_type"]=type(exc).__name__
                        persist()
                        raise
                    class Response:
                        def __enter__(self):response.__enter__();return self
                        def __exit__(self,*args):return response.__exit__(*args)
                        def read(self,limit):
                            try:
                                raw=response.read(limit)
                                try:
                                    decoded=json.loads(raw.decode("utf-8"))
                                    meta["token_usage"]=decoded.get("usage")
                                    meta["response_model_id"]=decoded.get("model")
                                    meta["finish_reason"]=decoded.get("choices",[{}])[0].get("finish_reason")
                                    persist(decoded)
                                except (ValueError,UnicodeError,AttributeError,IndexError):
                                    meta["failure_stage"]="response_decode"
                                    persist({"unparsed_text":raw.decode("utf-8",errors="replace")})
                                return raw
                            except Exception as exc:
                                if "finished_at" not in meta:
                                    meta["failure_stage"]="network_read";meta["error_type"]=type(exc).__name__;persist()
                                raise
                    return Response()
            return Observed()
        try:
            with patch.object(pipeline,"build_opener",observed_factory):
                output["parsed_output"]=ingestion.analyze(payload)
            output["validation_status"]="accepted"
        except KeyboardInterrupt:
            output["validation_status"]="cancelled";output["failure_stage"]="cancelled"
        except Exception as exc:
            output["validation_status"]="failed"
            raw=output["attempts"][-1] if output["attempts"] else {}
            output["failure_stage"]=raw.get("failure_stage") or ("configuration" if not output["attempts"] else "parse_or_validation")
            output["error_type"]=type(exc).__name__
            output["error"]=redact(str(exc)) if isinstance(exc,pipeline.PipelineError) else "生产逻辑异常："+type(exc).__name__
        # Record pre-validation outputs and quote rejection separately from format errors.
        output["quote_rejections"]=0
        for a in output["attempts"]:
            try:
                content=a["raw_response"]["choices"][0]["message"]["content"]
                parsed=json.loads(content)
                a["generated_output"]=redact(parsed)
                invalid=[i for i,f in enumerate(parsed.get("findings",[])) if not isinstance(f.get("quote"),str) or not f["quote"] or f["quote"] not in cleaned]
                a["quote_rejection_indexes"]=invalid
                output["quote_rejections"]+=bool(invalid)
            except (KeyError,ValueError,TypeError,AttributeError,IndexError):
                a["generated_output"]=None
    output["finished_at"]=now();output["latency_ms"]=round((time.perf_counter()-clock)*1000,2)
    output["retry_count"]=max(0,len(output["attempts"])-1)
    output["first_attempt_success"]=output["validation_status"] in ("accepted","local_excluded") and len(output["attempts"])<=1
    output["final_success"]=output["validation_status"] in ("accepted","local_excluded")
    return output

