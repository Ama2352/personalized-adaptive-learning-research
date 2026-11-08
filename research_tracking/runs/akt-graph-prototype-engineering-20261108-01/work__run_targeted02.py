"""One authorized rerun after elapsed-budget fix:0optimizer, postcheck<=30s."""
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

started_perf=time.perf_counter()
started_wall=time.time()
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((OUT/"trial01-receipt.json").read_text(encoding="utf8"))
report=ROOT/"research_tracking/reports/akt_graph_prototype_readiness_20261108.md"
assert sha(report)=="a7ae0826617821383a9aeae5d499b9dd15bef73ef20d9a94e347d60fda98780f"
with (OUT/"readiness_report_before_dependency_update_a7.md").open("xb") as target:target.write(report.read_bytes())
owned=[ROOT/"src/knowledge_tracing/akt/graph_prototype.py",ROOT/"tests/akt/test_graph_prototype.py"]
assert [sha(p) for p in owned]==["c7e9ce13a6225d60c550640b48c173275a6d5b353959eec133cd20b8c08afc84","5e2aae220d1b862c337951182efab417a3ed81dd5eb6899f84af710a3cfd76ae"]
dependencies=[p for p in (ROOT/"src/knowledge_tracing/akt").glob("*.py") if p not in owned]
dependencies += [ROOT/"src/knowledge_tracing"/name for name in ("simulator_data.py","simulator_bridge.py","shared_kt.py","graph_augmentation.py","graph_context.py")]
before={p.relative_to(ROOT).as_posix():sha(p) for p in owned+dependencies}
assert len(before)==36
materialization={}
for relative,digest in old["source_before_sha256"].items():
    current=ROOT/relative
    if sha(current)==digest:
        source=current
        basis="post-run current bytes equal historical recorded pre/post SHA; not a pre-run physical copy"
    else:
        assert relative=="src/knowledge_tracing/akt/authorization.py"
        source=ROOT/"research_tracking/runs/akt-simulator-engineering-20261108-01/source__src__knowledge_tracing__akt__authorization.py"
        archived=json.loads((source.parent/"manifest.json").read_text(encoding="utf8"))
        assert archived["outputs_sha256"][source.name]==sha(source)==digest
        basis="existing immutable historical source snapshot; no reconstruction/edit from new bytes"
    destination=OUT/"source36-trial01-materialized"/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("xb") as target:target.write(source.read_bytes())
    assert sha(destination)==digest
    materialization[relative]={"sha256":digest,"copied_from":source.relative_to(ROOT).as_posix(),"basis":basis}
for relative,digest in before.items():
    destination=OUT/"source36-trial02-before"/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("xb") as target:target.write((ROOT/relative).read_bytes())
    assert sha(destination)==digest
(OUT/"old_new_dependency_snapshot_provenance.json").write_text(json.dumps({"trial01_materialized":materialization,"trial02_actual_before":before,
    "changed_dependencies":{p:{"old_sha256":s,"new_sha256":before[p]} for p,s in old["source_before_sha256"].items() if before[p]!=s}},indent=2)+"\n",encoding="utf8")
env=os.environ.copy()
env.update(PYTHONPATH=str(ROOT/"src"),PYTHONDONTWRITEBYTECODE="1",CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="2",MKL_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2")
n=int(env.get("GIT_CONFIG_COUNT","0"))
env.update({"GIT_CONFIG_COUNT":str(n+1),f"GIT_CONFIG_KEY_{n}":"safe.directory",f"GIT_CONFIG_VALUE_{n}":(ROOT/"artifacts/akt/dependencies/upstream").as_posix()})
command=[sys.executable,"-B","-m","pytest","tests/akt/test_graph_prototype.py","-q","-p","no:cacheprovider","--basetemp="+str(OUT/"tmp02"),"--junitxml="+str(OUT/"pytest-trial02.xml")]
timed_out=False
with (OUT/"pytest-trial02.log").open("xb") as stream:
    try:
        process=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=30)
        exit_code=process.returncode
    except subprocess.TimeoutExpired:
        timed_out=True
        exit_code=124
after={p.relative_to(ROOT).as_posix():sha(p) for p in owned+dependencies}
for relative,digest in after.items():
    destination=OUT/"source36-trial02-after"/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("xb") as target:target.write((ROOT/relative).read_bytes())
elapsed_perf=time.perf_counter()-started_perf
elapsed_wall=time.time()-started_wall
cumulative=old["elapsed_seconds"]+max(elapsed_perf,elapsed_wall)
resource_ok=all(math.isfinite(v) and 0<=v<=30 for v in (elapsed_perf,elapsed_wall)) and cumulative<=90 and not timed_out
functional=False
counts=None
if (OUT/"pytest-trial02.xml").is_file():
    suite=ET.parse(OUT/"pytest-trial02.xml").getroot().find("testsuite")
    counts={key:int(suite.attrib[key]) for key in ("tests","failures","errors","skipped")}
    functional=exit_code==0 and counts=={"tests":23,"failures":0,"errors":0,"skipped":0}
receipt={"command":command,"exit_code":exit_code,"elapsed_seconds":elapsed_perf,"elapsed_wall_seconds":elapsed_wall,
    "post_elapsed_cap_seconds":30,"resource_verdict":"ACCEPTED" if resource_ok else "REJECTED",
    "functional_pass":functional,"counts":counts,"timeout_occurred":timed_out,"cumulative_controller_seconds":cumulative,
    "cumulative_cap_seconds":90,"source_before_sha256":before,"source_after_sha256":after,"source_identity":before==after,
    "optimizer_steps":0,"fit_or_simulator_events":0,"scope":"Only targeted23 graph prototype rerun; no accepted Gate20 claim",
    "old_new_source_snapshot_provenance":"old_new_dependency_snapshot_provenance.json",
    "trial_outputs_sha256":{name:sha(OUT/name) for name in ("pytest-trial02.log","pytest-trial02.xml") if (OUT/name).is_file()}}
with (OUT/"trial02-receipt.json").open("x",encoding="utf8") as stream:json.dump(receipt,stream,indent=2)
print((OUT/"pytest-trial02.log").read_text(encoding="utf8")[-12000:])
print(json.dumps({k:receipt[k] for k in ("functional_pass","resource_verdict","elapsed_seconds","elapsed_wall_seconds","cumulative_controller_seconds","source_identity")},indent=2))
raise SystemExit(0 if functional and resource_ok and before==after else 2)
