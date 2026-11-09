"""ROOT-only owned outer F041, source-only tới exact review/dispatch."""
import time
START, WALL = time.perf_counter(), time.time()
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/"worker_rq1_f041_native_panel01.py"
CONTRACT = PREP/"rq1_f041_native_panel_contract01.json"
OUT = PREP/"rq1-f041-native-panel01-outer"
OWNED = PREP/"rq1-f041-native-panel01-owned"
INNER = ROOT/"experiments/gam_kt/results/rq1-f041-native-panel-20261110-01"
DIRECT = {"policy_builder":1,"select":120,"predict":120,"update":120,"theta_at":3360}


def need(ok,message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START,time.time()-WALL)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, "Physical workspace path")
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor,"is_junction",lambda:False)(), "No path aliases")
    return path


def sha(path,cap=4*1024**2):
    physical(path)
    need(path.is_file() and path.stat().st_size <= cap,"Bounded regular file")
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while data := stream.read(65536):
            need(elapsed() < 60,"Whole60 while hashing")
            size += len(data)
            need(size <= cap,"Hash cap")
            digest.update(data)
    need(size == path.stat().st_size,"Stable file size")
    return digest.hexdigest()


def read(path):
    sha(path,256*1024)
    return json.loads(path.read_bytes())


def write(path,value):
    raw = (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()
    need(len(raw) <= 256*1024,"Outer metadata256KiB")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def validate_panels(contract):
    nodes = contract["node_order"]
    need(len(nodes) == len(set(nodes)) == 28,"28exact nodes")
    groups = {name:Counter(dict(rows=0,latent_true=0,native_true=0,theta_gate_true=0,
        uncertainty_suppression=0,TP=0,FP=0,FN=0,TN=0)) for name in ("all28","queried","not_queried")}
    def rows(name):
        count = 0
        with (INNER/name).open("rb") as stream:
            while line := stream.readline(16385):
                need(elapsed() < 60 and len(line) <= 16384 and line.endswith(b"\n"),"Whole60 complete JSONL")
                count += 1
                need(count <= 3360,"Panel cap3360")
                yield json.loads(line)
        need(count == 3360,"Panel exactly3360atEOF")
    timestamp = datetime(2026,1,1,tzinfo=timezone.utc)
    queried_in_step, count = 0, 0
    for index,(native,joined) in enumerate(zip(rows("native_panel.jsonl"),rows("joined_panel.jsonl"),strict=True)):
        step, ordinal = divmod(index,28)
        if ordinal == 0:
            if step:
                need(queried_in_step == 1,"Exactly1queried perstep")
            queried_in_step = 0
            timestamp += timedelta(hours=72 if step > 0 and step%28 == 0 else 6)
        need(type(native["step"]) is int and native["step"] == step and native["concept"] == nodes[ordinal]
             and native["timestamp"] == timestamp.isoformat(),"Native grid/order/clock")
        need(set(joined) == set(native)|{"simulator_theta_at","simulator_latent_criterion"}
             and all(type(joined[name]) is type(value) and
                 (struct.pack(">d",joined[name]) == struct.pack(">d",value) if type(value) is float else joined[name] == value)
                 for name,value in native.items()),"Strict untouched binary64 pretruth join")
        for field in ("theta","pi_task_stored","pi_time_stored","simulator_theta_at"):
            value = joined[field]
            need(type(value) is float and math.isfinite(value),"Binary64 finite state")
        need(0 <= joined["pi_task_stored"] <= 1 and 0 <= joined["pi_time_stored"] <= 1,"Pi range")
        for field in ("theta_gate","stored_pi_gate","native_M","queried","simulator_latent_criterion"):
            need(type(joined[field]) is bool,"Literal boolean fields")
        need(joined["theta_gate"] == (joined["theta"] >= 1250.)
             and joined["stored_pi_gate"] == (joined["pi_task_stored"] <= .55)
             and joined["native_M"] == (joined["theta_gate"] and joined["stored_pi_gate"])
             and joined["simulator_latent_criterion"] == (joined["simulator_theta_at"] >= 1250.),"Source predicates")
        queried_in_step += joined["queried"]
        for group in (groups["all28"],groups["queried" if joined["queried"] else "not_queried"]):
            predicted, latent = joined["native_M"], joined["simulator_latent_criterion"]
            group.update(rows=1,latent_true=int(latent),native_true=int(predicted),
                theta_gate_true=int(joined["theta_gate"]),uncertainty_suppression=int(joined["theta_gate"] and not joined["stored_pi_gate"]))
            group["TP" if predicted and latent else "FP" if predicted else "FN" if latent else "TN"] += 1
        count += 1
    need(count == 3360 and queried_in_step == 1 and groups["queried"]["rows"] == 120
         and groups["not_queried"]["rows"] == 3240,"Complete denominators")
    summary = read(INNER/"summary.json")
    need(summary["status"] == "FINITE_ONE_HISTORY_NATIVE_CRITERION_DIAGNOSTIC_ONLY"
         and summary["independent_histories"] == 1 and summary["repeated_rows"] == 3360
         and summary["old_PG120_population"] is False
         and summary["groups"] == {name:dict(value) for name,value in groups.items()},"All summary counts recomputed")
    lineage = read(INNER/"lineage.json")
    need(lineage["full_prestate_sha_matches"] == 120 and lineage["final_environment_exact"] is True
         and lineage["all28_endpoint_exact"] is True and len(lineage["presteps"]) == 120
         and lineage["initial_environment_sha256"] == contract["environment_initial_sha256"],"Whole source-reconstructed evaluator admission")
    previous = None
    lineage_clock = datetime(2026,1,1,tzinfo=timezone.utc)
    for step,row in enumerate(lineage["presteps"]):
        lineage_clock += timedelta(hours=72 if step > 0 and step%28 == 0 else 6)
        need(row["step"] == step and row["literal_logged_transition"] is True
             and row["timestamp"] == lineage_clock.isoformat(),"120step source-clock lineage")
        for field in ("source_prestate_sha256","source_poststate_sha256"):
            pin = row[field]
            need(type(pin) is str and len(pin) == 64 and all(c in "0123456789abcdef" for c in pin),"Lineage SHA format")
        need(previous is None or previous == row["source_prestate_sha256"],"Consecutive actual stored state chain")
        if step == 0:
            need(row["source_prestate_sha256"] == contract["environment_initial_sha256"],"Actual initial prestate")
        previous = row["source_poststate_sha256"]
    parity = read(INNER/"parity.json")
    need(parity["status"] == "ALL120_NATIVE_ACTION_P_UPDATE_ENDPOINT_ADMITTED_BEFORE_LATENT"
         and parity["first_pass_rows"] == 3360 and parity["source_checked_before_truth"] is True
         and parity["all_descriptors_restored"] is True and parity["extra_M_score_predict_calls"] == 0
         and parity["update_M_getters_observed"] is False
         and parity["initial_policy_sha256"] == contract["policy_initial_sha256"],"Genuine native pretruth scope")
    need(parity["native_panel"] == dict(sha256=sha(INNER/"native_panel.jsonl"),
         bytes=(INNER/"native_panel.jsonl").stat().st_size,rows=3360),"Frozen actual pretruth bytes")
    calls = parity["selector_existing_M_calls"]
    need(len(calls) == 120 and all(type(n) is int and 28 <= n <= 121 for n in calls)
         and sum(calls) == parity["selector_existing_M_calls_total"],"Existing source getter calls vs3360recorded rows")
    return dict(rows=count,queried=120,not_queried=3240,history_units=1,
        all_zero_cells_retained=True,groups={name:dict(value) for name,value in groups.items()},lineage_steps=120)


def main():
    parser = argparse.ArgumentParser()
    for name in ("source-sha256","contract-sha256","controller-sha256","approval-reference"):
        parser.add_argument("--"+name,required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT/".venv","Root .venv -B")
    need(sha(WORKER) == args.source_sha256 and sha(CONTRACT) == args.contract_sha256
         and sha(Path(__file__).resolve()) == args.controller_sha256 and args.approval_reference.strip(),"Reviewed exact source bindings")
    contract = read(CONTRACT)
    need(contract["worker_sha256"] == args.source_sha256 and contract["controller_sha256"] == args.controller_sha256
         and contract["output_relative"] == INNER.relative_to(ROOT).as_posix(),"Fixed source/output agreement")
    before = {}
    for name,record in contract["bindings"].items():
        need((ROOT/name).stat().st_size == record["bytes"] and sha(ROOT/name) == record["sha256"],"Bound source/input bytes")
        before[name] = record["sha256"]
    for path in (OUT,OWNED,INNER):
        physical(path)
        need(not path.exists() and path.parent.is_dir(),"Exclusive output namespaces")
    need(sha(ROOT/"scripts/research/windows_owned_worker.py") == "0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1","Genuine owner helper unchanged")
    sys.path.insert(0,str(ROOT/"scripts/research"))
    import windows_owned_worker as helper
    import psutil
    helper.entry()
    available = int(psutil.virtual_memory().available)
    OUT.mkdir()
    if available < 2*1024**3:
        write(OUT/"final.json",dict(status="NO_GO_PRELAUNCH_RAM_NO_WORKER",available_bytes=available,
            required_available_bytes=2*1024**3,worker_launched=False,source_before=before,
            automatic_retry=False,elapsed_seconds_before_final=elapsed()))
        print(json.dumps(dict(status="NO_GO_PRELAUNCH_RAM_NO_WORKER",available_bytes=available)))
        raise SystemExit(1)
    write(OUT/"admission.json",dict(approval_reference=args.approval_reference,source_before=before,
        available_bytes=available,whole_seconds=60,worker_seconds=50,owned_seconds=55,cleanup_seconds=3,
        scientific_scope="ONE_F041_NATIVE_HISTORY_ONLY_NO_WORLD_OR_MAIN_METHOD_AUTHORITY",automatic_retry=False))
    receipt, error, after, files, validation = None, None, {}, {}, None
    postcheck_error = None
    environment = {name:os.environ.get(name) for name in ("CUDA_VISIBLE_DEVICES","OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")}
    try:
        os.environ.update(CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="2",MKL_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2")
        need(elapsed() < 5,"Prelaunch within whole allocation")
        receipt = helper.run_owned(WORKER,["--source-sha256",args.source_sha256,"--contract-sha256",args.contract_sha256],OWNED,
            expected_worker_sha256=args.source_sha256,approval_reference=args.approval_reference,
            max_seconds=min(55.,60.-elapsed()-2.),cleanup_reserve_seconds=3,max_output_bytes=65536)
        write((OWNED if OWNED.is_dir() else OUT)/"receipt.json",receipt)
        need(receipt["accepted"] is True and receipt["returncode"] == receipt["worker_returncode_before_cleanup"] == 0
             and receipt["cleanup_accepted"] is True and receipt["job_active_after_cleanup"] == 0
             and receipt["popen_handle_closed"] is True and receipt["errors"] == receipt["cleanup_errors"] == [],"Owned exact clean terminal")
        expected = {"reservation.json","native_metadata.json","resources.jsonl","native_panel.jsonl","parity.json",
                    "joined_panel.jsonl","lineage.json","summary.json","result.json"}
        need({path.name for path in INNER.iterdir()} == expected,"No failure/partial/extra file acceptance")
        files = {name:dict(sha256=sha(INNER/name,4*1024**2 if name.endswith("panel.jsonl") else 256*1024),
                          bytes=(INNER/name).stat().st_size) for name in expected}
        need(sum(row["bytes"] for row in files.values()) <= 12*1024**2,"Global12MiB output")
        child = read(INNER/"result.json")
        need(child["status"] == "ACCEPTED_F041_NATIVE_PANEL_AND_SOURCE_RECONSTRUCTED_LATENT"
             and child["error"] is None and child["attempted"] == child["returned"] == DIRECT
             and child["source_before"] == child["source_after"] == before
             and child["pretruth_frozen"] is True and child["evaluator_complete"] is True
             and child["monitor_stopped"] is True and child["job_query_handle_closed"] is True
             and child["memory_errors"] == child["restoration_errors"] == child["denied"] == []
             and child["legacy_rng_state_unchanged"] is True,"All worker acceptance conditions")
        need(child["native_GAM_updates"] == 120 and child["NN_optimizer_calls"] == child["world_constructor_calls"] == child["world_interact_calls"] == 0,"Actual GAM vsNN/world roles")
        resource = child["resources"]
        need(0 < resource["samples"] <= 1000 and max(resource["family_peak_bytes"],resource["worker_peak_bytes"]) <= 512*1024**2
             and resource["minimum_available_bytes"] >= 1536*1024**2,"Actual sampled Job family resource verdict")
        metadata = child["metadata_final"]
        need(metadata["phase_closed"] is True and 0 <= metadata["helper_calls"] <= 3
             and metadata["outside_phase_popen_attempts"] == metadata["outside_phase_socket_attempts"] == metadata["blocked_bootstrap_attempts"] == 0,"Metadata closed and no late forbidden attempts")
        for name,record in child["outputs"].items():
            need(files[name]["sha256"] == record["sha256"] and files[name]["bytes"] == record["bytes"],"Actual output readback receipt")
        validation = validate_panels(contract)
        after = {name:sha(ROOT/name) for name in before}
        need(after == before and sha(CONTRACT) == args.contract_sha256 and sha(Path(__file__).resolve()) == args.controller_sha256,"Final source/input bytes unchanged")
        need(all(sha(OWNED/name) == pin for name,pin in receipt["output_sha256"].items()),"Original owned stdout/stderr")
    except BaseException as caught:
        error = dict(type=type(caught).__name__,message=str(caught))
    finally:
        for name,value in environment.items():
            if value is None:
                os.environ.pop(name,None)
            else:
                os.environ[name] = value
        try:
            after = {name:sha(ROOT/name) for name in before}
            need(after == before and sha(CONTRACT) == args.contract_sha256,"Terminal source/input postcheck")
        except BaseException as caught:
            postcheck_error = dict(type=type(caught).__name__,message=str(caught))
    restored = all(os.environ.get(name) == value for name,value in environment.items())
    accepted = error is None and postcheck_error is None and restored and validation is not None and elapsed() < 60
    result = dict(status="ACCEPTED_F041_NATIVE_FIRSTPASS_AND_RECONSTRUCTED28_PANEL" if accepted else "REJECTED_KEEP_ALL_NO_RETRY",
        error=error,postcheck_error=postcheck_error,owned_receipt=receipt,source_before=before,source_after=after,outputs=files,
        worker_output_relative=INNER.relative_to(ROOT).as_posix(),validation=validation,environment_restored=restored,
        declared_history_units=1,accepted_complete_histories=1 if accepted else 0,
        new_world_response_calls=0,elapsed_seconds_before_final=elapsed(),whole_cap_seconds=60,
        automatic_retry=False,missing_hardkill_actual_counts="UNKNOWN_NOT_ZERO")
    write(OUT/"final.json",result)
    if elapsed() >= 60:
        accepted = False
        write(OUT/"postwrite-rejection.json",dict(status="REJECTED_AFTER_FINALWRITE",elapsed_seconds=elapsed()))
    print(json.dumps(dict(status=result["status"] if accepted else "REJECTED_KEEP_ALL_NO_RETRY",error=error,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == "__main__":
    main()
