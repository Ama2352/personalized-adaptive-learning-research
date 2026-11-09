"""SOURCE-ONLY F041. Một policy native, evaluator từ transitions đã ghi.

Không world constructor/interact, không response/RNG/NN mới. Native panel
và endpoint parity phải đóng trước khi đọc oracle transitions cho evaluator.
"""
import time
START, WALL = time.perf_counter(), time.time()
import argparse
import ast
from collections import Counter, deque
import ctypes
from ctypes import wintypes
from dataclasses import asdict, is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import struct
import sys
import threading
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONTRACT = PREP/"rq1_f041_native_panel_contract01.json"
OUTPUT_REL = "experiments/gam_kt/results/rq1-f041-native-panel-20261110-01"
DIRECT = {"policy_builder": 1, "select": 120, "predict": 120, "update": 120, "theta_at": 3360}
NAMES = {"reservation.json", "native_metadata.json", "resources.jsonl", "native_panel.jsonl",
         "parity.json", "joined_panel.jsonl", "lineage.json", "summary.json", "result.json", "failure.json"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def check():
    need(elapsed() < 50, "Worker50s hard-stop allocation")


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is float:
        return struct.pack(">d", a) == struct.pack(">d", b)
    if type(a) is dict:
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if type(a) in (list, tuple):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def decode(raw):
    def pairs(items):
        value = {}
        for name, item in items:
            need(name not in value, "Duplicate JSON key")
            value[name] = item
        return value
    def invalid(value):
        raise ValueError("Nonfinite JSON token")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def selected_definitions(path, names, namespace):
    tree = ast.parse(path.read_bytes())
    selected = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in names]
    need(len(selected) == len(names) and {node.name for node in selected} == set(names), "Exact helper definitions only")
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def main():
    sys.path.insert(0, str(ROOT/"scripts/research"))
    from windows_owned_worker import worker_gate, Kernel, MAX_PROCESSES, safe
    owner = worker_gate()  # Trước NumPy/Pandas/knowledge_tracing.
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--contract-sha256", required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT/".venv"
         and Path.cwd().resolve() == ROOT and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
         and sys.getprofile() is None, "Owned CPU .venv -B without profiler")

    def sha(path, cap=4*1024**2):
        check()
        safe(path)
        need(path.is_file() and path.stat().st_size <= cap, "Bounded regular physical file")
        digest, size = hashlib.sha256(), 0
        with path.open("rb") as stream:
            while chunk := stream.read(65536):
                check()
                size += len(chunk)
                need(size <= cap, "SHA byte cap")
                digest.update(chunk)
        need(size == path.stat().st_size, "Stable file size")
        return digest.hexdigest()

    need(sha(Path(__file__).resolve()) == args.source_sha256 and sha(CONTRACT) == args.contract_sha256, "External source/contract pins")
    contract = decode(CONTRACT.read_bytes())
    need(contract["worker_sha256"] == args.source_sha256 and contract["output_relative"] == OUTPUT_REL
         and contract["direct_caps"] == DIRECT and contract["cell"] == {"cell_id":"F041", "block":21010,
             "ability":1000, "graph":"full", "mechanism_strength":0.0, "phase":"main"}, "Fixed F041 scope")
    need(contract["resources"] == dict(whole_seconds=60,worker_seconds=50,owned_seconds=55,cleanup_seconds=3,
         max_job_family_rss_bytes=512*1024**2,min_available_bytes=1536*1024**2,admission_available_bytes=2*1024**3),
         "Exact reviewed resource allocation")
    out = safe(ROOT/OUTPUT_REL)
    need(out.parent.is_dir() and not out.exists(), "New scientific output only")
    before = {}
    for name, record in contract["bindings"].items():
        path = ROOT/name
        need(path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], "Source/input preflight")
        before[name] = record["sha256"]
    out.mkdir()
    timer = threading.Timer(max(.001, 50-elapsed()), lambda: os._exit(124))
    timer.daemon = True
    timer.start()
    phase, error = "admission", None
    attempted, returned = Counter({name:0 for name in DIRECT}), Counter({name:0 for name in DIRECT})
    files, after, guards, restoration_errors, denied = {}, {}, [], [], []
    metadata, memory_errors = {}, []
    recorder = None
    pretruth_frozen = evaluator_complete = rng_unchanged = False
    stop, lock = threading.Event(), threading.Lock()
    thread = api = job = resource_stream = None
    handle_closed = False
    resources = {"samples":0, "family_peak_bytes":0, "worker_peak_bytes":0, "minimum_available_bytes":None}

    def write(name, value):
        check()
        raw = encoded(value)+b"\n"
        need(name in NAMES and len(raw) <= 256*1024, "Fixed metadata256KiB")
        with (out/name).open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        files[name] = {"sha256":sha(out/name), "bytes":len(raw)}

    def write_rows(name, rows):
        size, count, digest = 0, 0, hashlib.sha256()
        with (out/name).open("xb") as stream:
            for row in rows:
                check()
                raw = encoded(row)+b"\n"
                size += len(raw)
                count += 1
                need(len(raw) <= 16384 and size <= 4*1024**2 and count <= 3360, "Panel byte/row cap")
                stream.write(raw)
                digest.update(raw)
            stream.flush()
            os.fsync(stream.fileno())
        need(count == 3360 and sha(out/name) == digest.hexdigest(), "Complete panel readback")
        files[name] = {"sha256":digest.hexdigest(), "bytes":size, "rows":count}

    def invoke(name, function, *values, **kwargs):
        attempted[name] += 1
        need(attempted[name] <= DIRECT[name], "Reservation before native/evaluator body")
        value = function(*values, **kwargs)
        returned[name] += 1
        return value

    def verify():
        result = {}
        for name, record in contract["bindings"].items():
            path = ROOT/name
            need(path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], "Source/input postflight")
            result[name] = record["sha256"]
        need(result == before and sha(CONTRACT) == args.contract_sha256, "All pre/post bindings")
        return result

    def replace(obj, name, replacement):
        local = vars(obj)
        guards.append((obj, name, name in local, local.get(name)))
        setattr(obj, name, replacement)

    def deny_scientific(*values, **kwargs):
        denied.append("world/persona/RNG route attempted")
        raise RuntimeError(denied[-1])

    def rows(path, cap):
        seen, size = 0, 0
        with path.open("rb") as stream:
            while line := stream.readline(16385):
                check()
                seen += 1
                size += len(line)
                need(len(line) <= 16384 and line.endswith(b"\n") and size <= cap and seen <= 7350, "Complete bounded parent JSONL")
                yield decode(line)

    try:
        import psutil
        api = Kernel()
        job = api.check(api.k.OpenJobObjectW(0x0004 | 0x0008, False, owner["job_name"]))
        need(api.contains(api.k.GetCurrentProcess(), job), "Actual worker in exact Job")
        process = psutil.Process()
        class ProcessList(ctypes.Structure):
            _fields_ = [("assigned",wintypes.DWORD),("listed",wintypes.DWORD),("pids",ctypes.c_size_t*MAX_PROCESSES)]
        resource_stream = (out/"resources.jsonl").open("xb")
        def guard(stage="check"):
            with lock:
                check()
                need(not memory_errors, "Resource monitor already rejected")
                record = ProcessList()
                api.check(api.k.QueryInformationJobObject(job,3,ctypes.byref(record),ctypes.sizeof(record),None))
                need(0 < record.listed == record.assigned <= MAX_PROCESSES, "Complete Job membership")
                pids = [int(record.pids[i]) for i in range(record.listed)]
                need(len(set(pids)) == len(pids) and process.pid in pids, "Unique owned Job PIDs")
                family = 0
                for pid in pids:
                    handle = api.k.OpenProcess(0x1000,False,pid)
                    if not handle:
                        need(not psutil.pid_exists(pid), "Live Job member query failed")
                        continue
                    try:
                        need(api.contains(handle,job), "Exact Job member handle")
                        token = api.token(handle)
                        child = psutil.Process(pid)
                        need(abs(child.create_time()-token["create_time"]) <= 1e-5, "PID creation identity")
                        family += int(child.memory_info().rss)
                    except psutil.NoSuchProcess:
                        pass
                    finally:
                        api.close(handle)
                info = process.memory_info()
                peak, available = max(int(info.rss),int(info.peak_wset)), int(psutil.virtual_memory().available)
                resources["samples"] += 1
                resources["family_peak_bytes"] = max(resources["family_peak_bytes"],family)
                resources["worker_peak_bytes"] = max(resources["worker_peak_bytes"],peak)
                resources["minimum_available_bytes"] = min(resources["minimum_available_bytes"] or available,available)
                raw = encoded(dict(stage=stage,seconds=elapsed(),family_bytes=family,worker_peak_bytes=peak,available_bytes=available))+b"\n"
                need(resources["samples"] <= 1000 and resource_stream.tell()+len(raw) <= 256*1024, "Resource journal cap")
                resource_stream.write(raw)
                resource_stream.flush()
                if max(family,peak) > 512*1024**2 or available < 1536*1024**2:
                    os.fsync(resource_stream.fileno())
                    raise MemoryError("Family512MiB/free1536MiB")
        guard("before_metadata")
        def watch():
            while not stop.wait(.1):
                try:
                    guard("monitor")
                except BaseException as caught:
                    memory_errors.append({"type":type(caught).__name__,"message":str(caught)})
                    api.k.TerminateJobObject(job,1)  # Chỉ exact owned Job đã kiểm membership.
                    return
        thread = threading.Thread(target=watch,daemon=True)
        thread.start()
        meta = selected_definitions(ROOT/contract["metadata_helper"],
            ("windows_metadata_command","metadata_audit","require_metadata_closed","native_windows_metadata"),
            dict(need=need,os=os,sys=sys,Path=Path,time=time,platform=platform,hashlib=hashlib))
        meta["native_windows_metadata"](lambda:guard("metadata"),metadata)
        write("native_metadata.json",metadata)
        allowed = {os.path.normcase(str((ROOT/name).resolve())) for name in contract["bindings"]}
        allowed.add(os.path.normcase(str(CONTRACT.resolve())))  # Đã external-pin trước read entitlement.
        runtime_roots = (Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve())
        def audit(event, values):
            def deny(message):
                denied.append(dict(event=event,phase=phase,message=message,
                    path=str(values[0])[:1024] if event == "open" and values else None))
                raise RuntimeError(message)
            if event in ("subprocess.Popen","os.system","os.posix_spawn") or event.startswith("socket."):
                deny("No process/network after genuine metadata")
            if event == "import" and str(values[0]).split(".")[0] in ("torch","scipy","sklearn","tensorflow","modal","boto3"):
                deny("No NN/solver/cloud import")
            if event == "open" and values and not isinstance(values[0],int):
                path = Path(os.path.abspath(os.fsdecode(values[0])))
                mode, flags = values[1] or "", values[2] if type(values[2]) is int else 0
                writing = any(c in mode for c in "wax+") or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
                own_output = path.parent == out and path.name in NAMES
                runtime = path.suffix.lower() in (".py",".pyc",".pyd",".dll") and any(path.resolve().is_relative_to(root) for root in runtime_roots)
                if writing and not own_output or not writing and not (own_output or runtime or os.path.normcase(str(path.resolve())) in allowed):
                    deny("Read/write outside exact bound input/runtime/output")
            if event in ("os.remove","os.rename","os.rmdir","os.link","os.symlink","os.mkdir"):
                deny("No filesystem mutation outside exclusive writes")
        sys.addaudithook(audit)
        phase = "native_import"
        need(not any(name in sys.modules for name in ("numpy","pandas","torch")), "Cold native imports")
        import numpy as np
        import pandas as pd
        # Compile nguyên byte canonical dưới đúng module name, không đọc project
        # pyc không được ghim hoặc đổi class identity bằng proxy/alias.
        project_modules = {}
        for name,relative,package in (
            ("knowledge_tracing","src/knowledge_tracing/__init__.py",True),
            ("knowledge_tracing.gam_kt","src/knowledge_tracing/gam_kt/__init__.py",True),
            ("knowledge_tracing.paper2_reference","src/knowledge_tracing/paper2_reference.py",False),
            ("knowledge_tracing.gam_kt.simulator_pathways","src/knowledge_tracing/gam_kt/simulator_pathways.py",False),
            ("knowledge_tracing.gam_kt.native_panel_observer","src/knowledge_tracing/gam_kt/native_panel_observer.py",False)):
            need(name not in sys.modules and relative in before, "Cold source-bound canonical module")
            path = ROOT/relative
            module = ModuleType(name)
            module.__file__ = str(path)
            module.__package__ = name if package else name.rpartition(".")[0]
            if package:
                module.__path__ = [str(path.parent)]
            sys.modules[name] = module
            exec(compile(path.read_bytes(),str(path),"exec"),module.__dict__)
            if "." in name:
                setattr(sys.modules[name.rpartition(".")[0]],name.rpartition(".")[2],module)
            project_modules[name] = module
        load_reference = project_modules["knowledge_tracing.paper2_reference"].load_reference
        build_pathway_policy = project_modules["knowledge_tracing.gam_kt.simulator_pathways"].build_pathway_policy
        NativePanelRecorder = project_modules["knowledge_tracing.gam_kt.native_panel_observer"].NativePanelRecorder
        need([sys.version,np.__version__,pd.__version__] == contract["runtime"], "Exact historical runtime versions")
        need(all(Path(module.__file__).resolve().is_relative_to(ROOT/".venv") for module in (np,pd,psutil)), "Genuine runtime origins")
        reference = load_reference()
        scope, nodes = reference["environment"], tuple(reference["estimator"]["nodes"])
        need(list(nodes) == contract["node_order"] and len(nodes) == 28 and scope["MASTERY_ELO"] == 1250., "Source nodes/native threshold")
        for name in ("environment","controller","estimator"):
            source = reference[name]
            graph = source["graph"]
            graph_sha = identity(dict(nodes=list(source["nodes"]),edges=sorted((p,c) for p in graph.nodes for c in graph.successors(p))))
            need(graph_sha == contract["treatment_binding"][name+"_graph_sha256"], "Actual full graph namespaces")
        accepted = decode((ROOT/contract["recovery_acceptance"]).read_bytes())
        proof = decode((ROOT/contract["parent_proof"]).read_bytes())
        need(accepted["source_input_stable"] is True and accepted["summary"]["primary_worlds"] == 120
             and accepted["summary"]["primary_responses"] == 14400 and accepted["summary"]["parent_complete_components"] == 61
             and "F041" in proof["committed_cell_ids"], "Accepted recovery contains complete parent F041")
        core_manifest = decode((ROOT/contract["canonical_bundle"]).read_bytes())
        core_result = decode((ROOT/contract["canonical_result"]).read_bytes())
        need(core_manifest["status"] == "completed" and core_manifest["tests"] == 6
             and core_result["accepted"] is True and core_result["returncode"] == 0
             and core_result["source_before"] == core_result["source_after"], "Canonical six manufactured fixtures only, not native authority")
        helpers = selected_definitions(ROOT/contract["state_helper_source"],("state_data","fingerprint"),
            dict(np=np,pd=pd,deque=deque,is_dataclass=is_dataclass,identity=identity,hashlib=hashlib))
        state_data, fingerprint = helpers["state_data"], helpers["fingerprint"]
        for name in ("environment","controller","estimator"):
            source = reference[name]
            for method in ("__init__","interact"):
                replace(source["LatentStudentEnvironment"],method,deny_scientific)
        # Persona functions nằm trong dict namespace, lưu và phục hồi riêng.
        for source in (reference[name] for name in ("environment","controller","estimator")):
            guards.append((source,"persona_base_abilities",True,source["persona_base_abilities"]))
            source["persona_base_abilities"] = deny_scientific
        for module,names in ((random,("random","seed","randrange","randint","choice","choices","shuffle","sample","uniform","gauss","getrandbits")),
            (np.random,("default_rng","seed","random","random_sample","rand","randn","randint","choice","shuffle","permutation","uniform","normal"))):
            for name in names:
                replace(module,name,deny_scientific)
        rng_before = fingerprint(dict(python=random.getstate(),numpy=np.random.get_state()))
        guard("before_policy")
        write("reservation.json",dict(cell=contract["cell"],caps=DIRECT,owner=owner,
            hardkill_actual="UNKNOWN<=RESERVED_UNTIL_TERMINAL",world_constructor_interact_permitted=0))
        parent = ROOT/contract["parent_directory"]
        initial = decode((parent/"initial-F041.json").read_bytes())
        need(initial["cell"] == contract["cell"] and initial["nonedge_policy_sha256"] == contract["policy_initial_sha256"]
             and initial["treatment_binding_sha256"] == identity(initial["treatment_binding"]), "Actual initial cell/model seal")
        expected_initial = initial["nonedge_policy_sha256"]
        need(initial["treatment_binding"] == contract["treatment_binding"], "Full S1P1L0 treatment binding")
        del initial  # Không truyền env initial/base vào constructor hoặc policy.
        history = []
        for row in rows(parent/"observables.jsonl",2*1024**2):
            if row["cell_id"] == "F041":
                need(row["step"] == len(history) and set(row) == {"cell_id","step","query","probability","correct"}, "Public F041 ordered schema")
                history.append(row)
        need(len(history) == 120, "Whole120 historical questions")
        policy = invoke("policy_builder",build_pathway_policy,reference,signal=True,parent_adaptation=True,local_adaptation=False)
        need(fingerprint(vars(policy)) == expected_initial, "Actual model initial fingerprint")
        recorder = NativePanelRecorder(policy,nodes)
        native, selector_calls = [], []
        phase = "native_pretruth"
        clock = pd.Timestamp("2026-01-01",tz="UTC")
        for step,row in enumerate(history):
            guard("native_step")
            query = row["query"]
            clock += pd.Timedelta(hours=72 if step > 0 and step%28 == 0 else 6)
            need(query["timestamp_iso"] == clock.isoformat() and query["timestamp_ns"] == int(clock.value), "Exact historical clock")
            with recorder.capture(step=step,timestamp=query["timestamp_iso"]):
                selected = invoke("select",policy.select)
            need(recorder.restored and not recorder.cleanup_errors and recorder.latest is not None, "Recorder descriptors restored")
            need(exact(selected,(query["concept"],query["question"],query["difficulty"])), "Actual native selected tuple exact")
            need(len(recorder.latest.rows) == 28 and recorder.ready_calls == 1, "Existing complete first28")
            for state in recorder.latest.rows:
                native.append(dict(step=step,timestamp=query["timestamp_iso"],**asdict(state),queried=state.concept == query["concept"]))
            selector_calls.append(recorder.mastery_calls)
            probability = invoke("predict",policy.predict,*selected,clock)
            need(type(probability) is float and math.isfinite(probability) and 0 <= probability <= 1
                 and exact(probability,row["probability"]), "Historical P binary64 parity")
            need(type(row["correct"]) is int and row["correct"] in (0,1), "Current public binary answer")
            invoke("update",policy.update,*selected,clock,row["correct"],probability)
        need(len(native) == 3360 and sum(state.attempts for state in policy.states.values()) == 120, "All120updates/3360native states")
        endpoint_model = [row["final_policy_state_sha256"] for row in rows(parent/"oracle_endpoints.jsonl",1024**2) if row["cell_id"] == "F041"]
        final_policy = fingerprint(vars(policy))
        need(endpoint_model == [final_policy], "Native model endpoint parity before latent join")
        need(attempted == returned and all(returned[name] == DIRECT[name] for name in ("policy_builder","select","predict","update")), "All actual native bodies returned")
        after = verify()
        write_rows("native_panel.jsonl",native)
        write("parity.json",dict(status="ALL120_NATIVE_ACTION_P_UPDATE_ENDPOINT_ADMITTED_BEFORE_LATENT",cell="F041",
            initial_policy_sha256=expected_initial,final_policy_sha256=final_policy,direct_returned=dict(returned),
            first_pass_rows=3360,selector_existing_M_calls=selector_calls,selector_existing_M_calls_total=sum(selector_calls),
            update_M_getters_observed=False,extra_M_score_predict_calls=0,source_checked_before_truth=True,
            native_panel=files["native_panel.jsonl"],all_descriptors_restored=recorder.restored))
        pretruth_frozen = True
        phase = "readonly_evaluator_after_native_freeze"
        initial = decode((parent/"initial-F041.json").read_bytes())
        raw_env = initial["environment_state"]
        need(set(raw_env) == {"base","theta","last_seen"} and all(set(raw_env[name]) == set(nodes) for name in raw_env), "Actual full initial28")
        def floats(mapping):
            need(all(type(value) is dict and set(value) == {"float_hex"} for value in mapping.values()), "Literal float_hex state")
            result = {cid:float.fromhex(value["float_hex"]) for cid,value in mapping.items()}
            need(all(math.isfinite(value) for value in result.values()), "Finite actual initial state")
            return result
        container = SimpleNamespace(base=floats(raw_env["base"]),theta=floats(raw_env["theta"]),
            last_seen={cid:None if value is None else pd.Timestamp(value["ns"],tz="UTC") for cid,value in raw_env["last_seen"].items()})
        need(fingerprint(vars(container)) == initial["environment_sha256"] == contract["environment_initial_sha256"], "Exact source-decoded actual initial")
        oracle = [row for row in rows(parent/"oracle.jsonl",4*1024**2) if row["cell_id"] == "F041"]
        need(len(oracle) == 120 and [row["step"] for row in oracle] == list(range(120)), "Exact evaluator transition120")
        theta_at = scope["LatentStudentEnvironment"].theta_at  # Hàm nguồn thật, không gọi constructor/interact.
        groups = {name:Counter(dict(rows=0,latent_true=0,native_true=0,theta_gate_true=0,uncertainty_suppression=0,TP=0,FP=0,FN=0,TN=0)) for name in ("all28","queried","not_queried")}
        joined, lineage = [], []
        for step,(public,truth) in enumerate(zip(history,oracle,strict=True)):
            guard("evaluator_step")
            timestamp = pd.Timestamp(public["query"]["timestamp_ns"],tz="UTC")
            before_hash = fingerprint(vars(container))
            need(before_hash == truth["environment_readonly_probe_sha256"], "Fullvars SHA at EVERY pre-step")
            current = truth["result"]
            selected_theta = None
            for index,cid in enumerate(nodes):
                native_row = native[step*28+index]
                need(native_row["step"] == step and native_row["concept"] == cid, "Native/evaluator strict grid")
                theta = invoke("theta_at",theta_at,container,cid,timestamp)
                need(type(theta) is float and math.isfinite(theta), "Finite source theta_at")
                latent = theta >= 1250.
                if native_row["queried"]:
                    selected_theta = theta
                result = dict(**native_row,simulator_theta_at=theta,simulator_latent_criterion=latent)
                joined.append(result)
                for group in (groups["all28"],groups["queried" if result["queried"] else "not_queried"]):
                    group.update(rows=1,latent_true=int(latent),native_true=int(result["native_M"]),
                        theta_gate_true=int(result["theta_gate"]),uncertainty_suppression=int(result["theta_gate"] and not result["stored_pi_gate"]))
                    cell = "TP" if result["native_M"] and latent else "FP" if result["native_M"] else "FN" if latent else "TN"
                    group[cell] += 1
            need(exact(selected_theta,truth["oracle_theta_before"]) and exact(selected_theta,current["theta_before"]), "Recorded queried latent exact")
            need(type(current["learning_gain"]) is float and math.isfinite(current["learning_gain"]), "Logged finite transition only")
            cid = public["query"]["concept"]
            container.theta[cid] = min(1600.,current["theta_before"]+current["learning_gain"])
            container.last_seen[cid] = timestamp
            lineage.append(dict(step=step,timestamp=timestamp.isoformat(),source_prestate_sha256=before_hash,
                literal_logged_transition=True,source_poststate_sha256=fingerprint(vars(container))))
        endpoint = [row for row in rows(parent/"oracle_endpoints.jsonl",1024**2) if row["cell_id"] == "F041"]
        need(len(endpoint) == 1 and endpoint[0]["timestamp_ns"] == int(clock.value)
             and endpoint[0]["timestamp_iso"] == clock.isoformat()
             and exact(state_data(vars(container)),endpoint[0]["final_environment_state"]), "Full final environment/time exact")
        # Chỉ lấy snapshot cuối từ28 getter đã gọi ở cuối step119, không thêm calls.
        final_snapshot = {row["concept"]:row["simulator_theta_at"] for row in joined[-28:]}
        cid = history[-1]["query"]["concept"]
        need(container.last_seen[cid] == clock, "Selected endpoint has zero time gap")
        base, stored = container.base[cid], container.theta[cid]
        final_snapshot[cid] = base + max(0.,stored-base)*math.exp(-scope["TRUE_FORGET_RATE"]*0.)
        need(exact(final_snapshot,endpoint[0]["final_snapshot"]), "All28 endpoint theta exact")
        rng_unchanged = fingerprint(dict(python=random.getstate(),numpy=np.random.get_state())) == rng_before
        need(rng_unchanged, "No replay/evaluator RNG changes")
        need(attempted == returned == Counter(DIRECT) and len(joined) == 3360, "Exact whole native/evaluator ledger")
        write_rows("joined_panel.jsonl",joined)
        write("lineage.json",dict(initial_environment_sha256=initial["environment_sha256"],presteps=lineage,
            full_prestate_sha_matches=120,final_environment_exact=True,all28_endpoint_exact=True,
            endpoint_method="UNCHANGED_NODES_REUSE_LAST_PRESTEP;LAST_UPDATED_NODE_LITERAL_ZERO_GAP_SOURCE_EXPRESSION_NO_EXTRA_GETTER",
            scope="SOURCE_EQUATION_RECONSTRUCTION_FROM_ACTUAL_SAVED_INITIAL_AND_TRANSITIONS"))
        write("summary.json",dict(status="FINITE_ONE_HISTORY_NATIVE_CRITERION_DIAGNOSTIC_ONLY",cell=contract["cell"],
            independent_histories=1,concepts=28,steps=120,repeated_rows=3360,groups={name:dict(value) for name,value in groups.items()},
            source_latent_threshold=1250.,native_stored_pi_threshold=.55,extra_world_responses=0,
            no_AUC_calibration_or_selection_causality_claim=True,old_PG120_population=False))
        evaluator_complete = True
        after = verify()
        meta["require_metadata_closed"](metadata)
        need(sys.getprofile() is None and "torch" not in sys.modules, "No profiler/neural import")
        guard("final")
    except BaseException as caught:
        error = dict(type=type(caught).__name__,message=str(caught),phase=phase)
    finally:
        if recorder is not None and not recorder.restored:
            restoration_errors.extend(recorder.restore())
            if not recorder.restored:
                restoration_errors.append(("recorder","RestorationError","attributes still pending"))
        for obj,name,present,original in reversed(guards):
            try:
                if isinstance(obj,dict):
                    obj[name] = original
                elif present:
                    setattr(obj,name,original)
                elif name in vars(obj):
                    delattr(obj,name)
                need((obj.get(name) is original) if isinstance(obj,dict) else
                     ((name in vars(obj)) == present and (not present or vars(obj)[name] is original)), "Original guard attribute restored")
            except BaseException as caught:
                restoration_errors.append((name,type(caught).__name__,str(caught)))
        stop.set()
        if thread is not None:
            thread.join(timeout=.5)
        if resource_stream is not None:
            resource_stream.flush()
            os.fsync(resource_stream.fileno())
            resource_stream.close()
        if api is not None and job is not None:
            api.close(job)
            handle_closed = True
    clean = (error is None and not restoration_errors and not denied and not memory_errors and handle_closed
             and thread is not None and not thread.is_alive() and pretruth_frozen and evaluator_complete
             and attempted == returned == Counter(DIRECT) and after == before and elapsed() < 50)
    if (out/"resources.jsonl").exists():
        files["resources.jsonl"] = dict(sha256=sha(out/"resources.jsonl"),bytes=(out/"resources.jsonl").stat().st_size)
    if error is not None:
        write("failure.json",dict(error=error,attempted=dict(attempted),returned=dict(returned),
            pretruth_frozen=pretruth_frozen,evaluator_complete=evaluator_complete))
    write("result.json",dict(status="ACCEPTED_F041_NATIVE_PANEL_AND_SOURCE_RECONSTRUCTED_LATENT" if clean else "REJECTED_KEEP_ALL_NO_RETRY",
        error=error,source_before=before,source_after=after,attempted=dict(attempted),returned=dict(returned),
        resources=resources,memory_errors=memory_errors,monitor_stopped=thread is not None and not thread.is_alive(),
        job_query_handle_closed=handle_closed,restoration_errors=restoration_errors,denied=denied,
        metadata_final=metadata,pretruth_frozen=pretruth_frozen,evaluator_complete=evaluator_complete,outputs=files,
        output_relative=OUTPUT_REL,elapsed_seconds_before_final=elapsed(),worker_cap_seconds=50,
        hardkill_counts="UNKNOWN<=RESERVATION_NOT_ZERO",native_GAM_updates=returned["update"],
        NN_optimizer_calls=0,world_constructor_calls=0,world_interact_calls=0,legacy_rng_state_unchanged=rng_unchanged))
    need(sum(path.stat().st_size for path in out.iterdir()) <= 12*1024**2, "Total12MiB output")
    if elapsed() >= 50:
        clean = False
    timer.cancel()
    print(json.dumps(dict(accepted=clean,error=error,elapsed_seconds=elapsed())))
    raise SystemExit(0 if clean else 1)


if __name__ == "__main__":
    main()
