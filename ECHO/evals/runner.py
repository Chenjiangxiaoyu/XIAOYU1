import json, os, platform, subprocess, sys, uuid
from pathlib import Path
from . import adapter
from .dataset_validator import validate
from .schemas import DATA,ROOT,EVALUATOR_VERSION,read,write_new,file_hash,digest,now

def version():
    files={str(p.relative_to(ROOT)).replace("\\","/"):file_hash(p) for p in sorted((ROOT/"backend").glob("*.py")) if not p.name.startswith("test_")}
    try:
        commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,timeout=5,check=True).stdout.strip()
    except Exception:commit=None
    return {"app_commit":commit,"app_version":"source-sha256:"+digest(files),"source_files":files}

def run(dataset_path,root=DATA,parent=None):
    dataset=read(dataset_path);info=validate(dataset);adapter.load_runtime()
    run_id=now().replace(":","").replace(".","")+"-"+uuid.uuid4().hex[:8]
    folder=Path(root)/run_id;folder.mkdir(parents=True,exist_ok=False)
    config={"generation_calls_per_case":1,"http_attempts_per_call":4,"http_timeout_seconds":30,
            "retry_policy":"production: 429/500/502/503/504 + network errors, backoff <=60s",
            "parallelism":1,"model_id":os.environ.get("DEEPSEEK_MODEL","deepseek-flash"),
            "parameters":{"response_format":{"type":"json_object"},"stream":False,"max_tokens":1600,"temperature":0.2},
            "seed":None,"price_version":None,"price_table":None,
            "failure_policy":"retain all; no parse/quote retry beyond production behavior",
            "generation_budget_note":"11 generation calls maximum; HTTP retry cost fully counted"}
    manifest={"run_id":run_id,"project":"ECHO","dataset_version":dataset["dataset_version"],
              "dataset_hash":info["dataset_hash"],"evaluator_version":EVALUATOR_VERSION,
              "config_hash":digest(config),"config":config,"split":dataset["split"],
              "mode":dataset.get("mode","real"),"started_at":now(),"status":"running",
              "environment":{"python":sys.version.split()[0],"platform":platform.platform()},
              "seed":None,"parent_run_id":parent,**version(),"implementation":adapter.implementation()}
    write_new(folder/"manifest.json",manifest);write_new(folder/"dataset.json",dataset)
    # Freeze production source as evidence, never .env, DBs or secrets.
    src=folder/"source";src.mkdir()
    for name in ("ingestion.py","pipeline.py"):
        (src/name).write_bytes((ROOT/"backend"/name).read_bytes())
    outputs=[];cancelled=False
    try:
        for case in dataset["cases"]:
            if cancelled:
                output={"run_id":run_id,"case_id":case["case_id"],"validation_status":"cancelled",
                        "failure_stage":"not_attempted_after_cancel","attempts":[],"parsed_output":None,
                        "final_success":False,"first_attempt_success":False,"latency_ms":None,"quote_rejections":0}
            else:
                print("START "+case["case_id"],flush=True)
                output=adapter.execute({k:case[k] for k in ("case_id","product","text")},run_id,folder)
                cancelled=output["validation_status"]=="cancelled"
            write_new(folder/(case["case_id"]+".json"),output);outputs.append(output)
            print(case["case_id"]+" "+output["validation_status"],flush=True)
    finally:
        successes=sum(o.get("final_success",False) for o in outputs)
        status="cancelled" if cancelled else ("completed" if successes==len(dataset["cases"]) else "partial" if successes else "failed")
        write_new(folder/"completion.json",{"status":status,"finished_at":now(),"n_cases":len(dataset["cases"]),
            "outputs_saved":len(outputs),"successful":successes,"failures":len(dataset["cases"])-successes})
    print("RUN_PATH "+str(folder),flush=True)
    return folder

