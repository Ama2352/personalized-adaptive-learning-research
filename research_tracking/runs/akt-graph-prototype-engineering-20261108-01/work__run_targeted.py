"""Đợi parent review rồi chạy toy forward/backward:0optimizer,<=90sCPU."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
owned=[ROOT/"src/knowledge_tracing/akt/graph_prototype.py",ROOT/"tests/akt/test_graph_prototype.py"]
dependencies=[p for p in (ROOT/"src/knowledge_tracing/akt").glob("*.py") if p not in owned]
dependencies += [ROOT/"src/knowledge_tracing"/name for name in ("simulator_data.py","simulator_bridge.py","shared_kt.py","graph_augmentation.py","graph_context.py")]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(ROOT).as_posix():sha(p) for p in owned+dependencies}
for p in owned:
    with (OUT/(p.name+".before-trial01")).open("xb") as target:target.write(p.read_bytes())
env=os.environ.copy()
env.update(PYTHONPATH=str(ROOT/"src"),PYTHONDONTWRITEBYTECODE="1",CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="2")
n=int(env.get("GIT_CONFIG_COUNT","0"))
env.update({"GIT_CONFIG_COUNT":str(n+1),f"GIT_CONFIG_KEY_{n}":"safe.directory",f"GIT_CONFIG_VALUE_{n}":(ROOT/"artifacts/akt/dependencies/upstream").as_posix()})
command=[sys.executable,"-B","-m","pytest","tests/akt/test_graph_prototype.py","-q","-p","no:cacheprovider","--basetemp="+str(OUT/"tmp01"),"--junitxml="+str(OUT/"pytest-trial01.xml")]
started=time.perf_counter()
with (OUT/"pytest-trial01.log").open("xb") as stream:
    result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=90)
after={p.relative_to(ROOT).as_posix():sha(p) for p in owned+dependencies}
receipt={"command":command,"exit_code":result.returncode,"elapsed_seconds":time.perf_counter()-started,
         "source_before_sha256":before,"source_after_sha256":after,"source_identity":before==after,
         "optimizer_steps":0,"fit_or_simulator_events":0,"scope":"CPU handmade-observable A0/A1 forward/backward only; not train_epoch/fitted research",
         "git_safe_directory":"process-only exact pinned upstream; no Git writes",
         "trial_outputs_sha256":{name:sha(OUT/name) for name in ("pytest-trial01.log","pytest-trial01.xml")}}
(OUT/"trial01-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf8")
print((OUT/"pytest-trial01.log").read_text(encoding="utf8")[-14000:])
assert before==after
raise SystemExit(result.returncode)
