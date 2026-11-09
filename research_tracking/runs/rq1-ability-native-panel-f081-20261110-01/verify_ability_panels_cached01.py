"""Kiểm cache hai ô ability độc lập, stdlib, không import model/getter/RNG hoặc world."""
import time
START = time.perf_counter()
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
NATIVE = PARENT = OUT = None


def need(ok,message):
    if not ok:
        raise ValueError(message)


def raw(path,cap=4*1024**2):
    need(path.is_relative_to(ROOT) and path.stat().st_size <= cap,"Bounded input")
    return path.read_bytes()


def sha(path):
    return hashlib.sha256(raw(path)).hexdigest()


def exact(a,b):
    if type(a) is not type(b):
        return False
    if type(a) is float:
        return struct.pack(">d",a) == struct.pack(">d",b)
    if type(a) is dict:
        return a.keys() == b.keys() and all(exact(a[k],b[k]) for k in a)
    if type(a) in (tuple,list):
        return len(a) == len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a == b


def records(path,cell=None):
    result = []
    with path.open("rb") as stream:
        for index,line in enumerate(stream):
            need(index < 7350 and len(line) <= 16384 and line.endswith(b"\n"),"Bounded complete JSONL")
            row = json.loads(line)
            if cell is None or row["cell_id"] == cell:
                result.append(row)
    return result


def packed_env(base,theta,seen):
    origin = datetime(1970,1,1,tzinfo=timezone.utc)
    def stamp(value):
        if value is None:
            return None
        gap = value-origin
        return {"iso":value.isoformat(),"ns":(gap.days*86400+gap.seconds)*10**9+gap.microseconds*1000}
    return {"base":{c:{"float_hex":v.hex()} for c,v in base.items()},
            "theta":{c:{"float_hex":v.hex()} for c,v in theta.items()},
            "last_seen":{c:stamp(v) for c,v in seen.items()}}


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def main():
    global NATIVE, PARENT, OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell-id", required=True, choices=("F001","F081"))
    cell = parser.parse_args().cell_id
    NATIVE = ROOT/("experiments/gam_kt/results/rq1-ability-panel-"+cell.lower()+"-20261110-01")
    PARENT = ROOT/("experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-"+("02" if cell == "F001" else "03"))
    OUT = PREP/("ability_"+cell.lower()+"_independent_cached_review01.json")
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT/".venv" and not OUT.exists(),".venv-B/exclusive proof")
    timer = threading.Timer(max(.1,4.8-(time.perf_counter()-START)),lambda:os._exit(124))
    timer.daemon = True
    timer.start()
    def audit(event,args):
        if event == "import" and str(args[0]).split(".")[0] in {"numpy","pandas","torch","knowledge_tracing","random"}:
            raise RuntimeError("Cache-only verification forbids model/scientific/RNG imports")
        if event.startswith("socket.") or event in {"subprocess.Popen","os.system"}:
            raise RuntimeError("No process/network")
    sys.addaudithook(audit)
    result = {"status":"REJECTED_PRESERVE","new_model_world_getter_calls":0,"new_random_calls":0}
    try:
        outer_path = PREP/("rq1-ability-native-panel02-"+cell.lower()+"-outer/final.json")
        need(sha(outer_path) == {"F001":"3d271f0adaaee74b0c4d61d168e5739ef937a120ddb06b9f1679ca1004412868","F081":"770418e18095a949a7385af951bec4d8e5ef73b5cb0a8ca6df0e4a275ccb67d7"}[cell],"Exact accepted outer")
        outer = json.loads(raw(outer_path))
        need(outer["status"] == "ACCEPTED_PREDECLARED_ABILITY_NATIVE_FIRSTPASS_AND_RECONSTRUCTED28_PANEL"
             and outer["error"] is None and outer["postcheck_error"] is None
             and outer["owned_receipt"]["job_active_after_cleanup"] == 0
             and outer["owned_receipt"]["cleanup_accepted"] is True,"Accepted terminal cleanup")
        contract_path = PREP/"rq1_ability_native_panel_contract02.json"
        need(sha(contract_path) == "50de7ccd6c93d9affde33db08d8dff14e9e140fbb2878370692dfb3d4b3f4db1","Frozen contract")
        root_contract = json.loads(raw(contract_path))
        contract = {**root_contract, **root_contract["cases"][cell]}
        pins = {ROOT/name:record["sha256"] for name,record in contract["bindings"].items()}
        pins.update({NATIVE/name:record["sha256"] for name,record in outer["outputs"].items()})
        pins[outer_path] = sha(outer_path)
        pins[contract_path] = sha(contract_path)
        for path,pin in pins.items():
            need(sha(path) == pin,"Pre hash binding")
        nodes = contract["node_order"]
        native = records(NATIVE/"native_panel.jsonl")
        joined = records(NATIVE/"joined_panel.jsonl")
        public,oracle,endpoints = (records(PARENT/name,cell) for name in ("observables.jsonl","oracle.jsonl","oracle_endpoints.jsonl"))
        need(len(native) == len(joined) == 3360 and len(public) == len(oracle) == 120 and len(endpoints) == 1,"Whole populations")
        initial = json.loads(raw(PARENT/("initial-"+cell+".json")))["environment_state"]
        base = {c:float.fromhex(v["float_hex"]) for c,v in initial["base"].items()}
        theta = {c:float.fromhex(v["float_hex"]) for c,v in initial["theta"].items()}
        need(set(base) == set(theta) == set(nodes) and all(v is None for v in initial["last_seen"].values()),"Actual fresh all28base")
        seen = dict.fromkeys(nodes,None)
        groups = {name:Counter(dict(rows=0,latent_true=0,native_true=0,theta_gate_true=0,
            uncertainty_suppression=0,TP=0,FP=0,FN=0,TN=0)) for name in ("all28","queried","not_queried")}
        for step,(query,truth) in enumerate(zip(public,oracle,strict=True)):
            need(query["step"] == truth["step"] == step,"Ordered source steps")
            timestamp = datetime.fromisoformat(query["query"]["timestamp_iso"])
            need(digest(packed_env(base,theta,seen)) == truth["environment_readonly_probe_sha256"],"Every fullvars prestate")
            queried_count = 0
            for ordinal,cid in enumerate(nodes):
                a,b = native[step*28+ordinal],joined[step*28+ordinal]
                need(a["step"] == step and a["concept"] == cid and a["timestamp"] == timestamp.isoformat()
                     and exact(a,{name:b[name] for name in a}),"Strict source grid/native prefix")
                need(type(a["native_M"]) is bool and a["native_M"] == (a["theta"] >= 1250. and a["pi_task_stored"] <= .55)
                     and a["theta_gate"] == (a["theta"] >= 1250.) and a["stored_pi_gate"] == (a["pi_task_stored"] <= .55),"Native literal gates")
                gap = 0. if seen[cid] is None else max(0.,(timestamp-seen[cid]).total_seconds()/86400.)
                latent_theta = theta[cid] if seen[cid] is None else base[cid]+max(0.,theta[cid]-base[cid])*math.exp(-.06*gap)
                need(exact(latent_theta,b["simulator_theta_at"]) and b["simulator_latent_criterion"] == (latent_theta >= 1250.),"Independent source equation every3360row")
                queried = cid == query["query"]["concept"]
                need(a["queried"] is queried,"Queried-membership exactsource")
                queried_count += queried
                if queried:
                    need(exact(latent_theta,truth["oracle_theta_before"]) and exact(latent_theta,truth["result"]["theta_before"]),"Recorded queried pretheta")
                for group in (groups["all28"],groups["queried" if queried else "not_queried"]):
                    pred,actual = a["native_M"],b["simulator_latent_criterion"]
                    group.update(rows=1,latent_true=int(actual),native_true=int(pred),theta_gate_true=int(a["theta_gate"]),
                                 uncertainty_suppression=int(a["theta_gate"] and not a["stored_pi_gate"]))
                    group["TP" if pred and actual else "FP" if pred else "FN" if actual else "TN"] += 1
            need(queried_count == 1,"One publicquery perstep")
            cid = query["query"]["concept"]
            theta[cid] = min(1600.,truth["result"]["theta_before"]+truth["result"]["learning_gain"])
            seen[cid] = timestamp
        need(exact(packed_env(base,theta,seen),endpoints[0]["final_environment_state"]),"Complete final env cached exact")
        final_snapshot = {c:theta[c] if seen[c] is None else base[c]+max(0.,theta[c]-base[c])*math.exp(-.06*max(0.,(timestamp-seen[c]).total_seconds()/86400.)) for c in nodes}
        need(exact(final_snapshot,endpoints[0]["final_snapshot"]),"All28source-equation endpoint")
        summary = json.loads(raw(NATIVE/"summary.json"))
        actual_groups = {name:dict(value) for name,value in groups.items()}
        need(actual_groups == summary["groups"] == outer["validation"]["groups"],"All summarycells independent recount")
        for path,pin in pins.items():
            need(sha(path) == pin,"Post hash unchanged")
        result.update(status="PASS_CACHED_ABILITY_RECOUNT_AND_LATENT_STATE_RECONSTRUCTION",cell_id=cell,groups=actual_groups,
            source_prestate_fullvars_sha_matches=120,independent_latent_row_equations=3360,
            full_final_environment_exact=True,all28_endpoint_exact=True,input_pins_before_after={p.relative_to(ROOT).as_posix():v for p,v in pins.items()},
            limits_vi=["Một lịch sử của cùng block. Không có ba block độc lập.",
                "So sánh criterion latent của simulator, không truth người học hoặc calibrated S04 mastery.",
                "Chỉ định lượng opportunity quan sát được, không kết luận pi luôn dư thừa.",
                "Native parity dựa receipt nghiệm thu. Checker không chạy GAM/getter/world/RNG."])
    except BaseException as error:
        result["error"] = {"type":type(error).__name__,"message":str(error)}
    result["checker_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["elapsed_seconds_before_final"] = time.perf_counter()-START
    with OUT.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    timer.cancel()
    timer.join(timeout=.1)
    print(json.dumps(dict(status=result["status"],elapsed_seconds=time.perf_counter()-START)))
    return 0 if result["status"].startswith("PASS_") and time.perf_counter()-START < 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
