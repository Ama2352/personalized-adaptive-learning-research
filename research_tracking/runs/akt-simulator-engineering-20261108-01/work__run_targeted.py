"""Targeted handmade-observable CPU suite, <=90s and <=16 optimizer steps."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
paths=[ROOT/"src/knowledge_tracing/akt/simulator_engineering.py",ROOT/"tests/akt/test_simulator_engineering.py"]
protected=[ROOT/"src/knowledge_tracing/akt"/name for name in ("config.py","training.py","model.py","checkpoint.py","simulator_data.py","online.py","runner.py","authorization.py","context.py")]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(ROOT).as_posix():sha(p) for p in paths+protected}
for p in paths:
    with (OUT/(p.name+".before-trial01")).open("xb") as target:target.write(p.read_bytes())
_existing=set((ROOT/"artifacts/akt/synthetic").glob("simeng-20261108-*"))
env=os.environ.copy()
env.update(PYTHONPATH=str(ROOT/"src"),PYTHONDONTWRITEBYTECODE="1",CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="2")
n=int(env.get("GIT_CONFIG_COUNT","0"))
env.update({"GIT_CONFIG_COUNT":str(n+1),f"GIT_CONFIG_KEY_{n}":"safe.directory",f"GIT_CONFIG_VALUE_{n}":(ROOT/"artifacts/akt/dependencies/upstream").as_posix()})
command=[sys.executable,"-B","-m","pytest","tests/akt/test_simulator_engineering.py","-q","-p","no:cacheprovider","--basetemp="+str(OUT/"tmp01"),"--junitxml="+str(OUT/"pytest-trial01.xml")]
started=time.perf_counter()
with (OUT/"pytest-trial01.log").open("xb") as stream:
    result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=90)
after={p.relative_to(ROOT).as_posix():sha(p) for p in paths+protected}
runs=sorted(set((ROOT/"artifacts/akt/synthetic").glob("simeng-20261108-*"))-_existing)
step_count=sum(json.loads((p/"training.json").read_text())["optimizer_steps"] for p in runs if (p/"training.json").exists())
outputs={p.relative_to(ROOT).as_posix():sha(p) for run in runs for p in run.iterdir() if p.is_file()}
receipt={"command":command,"exit_code":result.returncode,"elapsed_seconds":time.perf_counter()-started,
         "source_before_sha256":before,"source_after_sha256":after,"source_identity":before==after,
         "actual_optimizer_steps":step_count,"optimizer_step_cap":16,"new_outputs_sha256":outputs,
         "runtime_source":"real native pinned upstream validation and real CPU/RAM; injected negative guards only in declared tests",
         "git_safe_directory":"process-only exact pinned upstream; no Git writes","research_simulation_or_realdata":False}
(OUT/"trial01-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf8")
print((OUT/"pytest-trial01.log").read_text(encoding="utf8")[-12000:])
assert before==after
assert step_count<=16
raise SystemExit(result.returncode)
