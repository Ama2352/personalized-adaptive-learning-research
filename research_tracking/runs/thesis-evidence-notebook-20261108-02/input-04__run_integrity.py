"""Giữ nguồn/lượt thất bại; ngân sách cộng dồn30s, không kernel/model."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
FILES=['scripts/research/build_thesis_evidence_notebook.py','notebooks/thesis_evidence_report.ipynb',
       'research_tracking/reports/thesis_evidence_notebook_20261108.md',
       'research_tracking/reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json',
       'research_tracking/runs/thesis-evidence-notebook-20261108-01/manifest.json']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')
def inventory(): return {p:dict(sha256=sha(ROOT/p),bytes=(ROOT/p).stat().st_size) for p in FILES}
def snapshot(folder):
    folder.mkdir()
    rows=inventory()
    for name,row in rows.items():
        destination=folder/name.replace('/','__')
        destination.write_bytes((ROOT/name).read_bytes())
        assert sha(destination)==row['sha256']
    dump(folder/'inventory.json',rows)
    return rows

if __name__=='__main__':
    assert Path(sys.executable).absolute()==ROOT/'.venv/Scripts/python.exe'
    if sys.argv[1]=='prepare':
        snapshot(PREP/'before')
    else:
        start=time.perf_counter()
        budget=PREP/'budget.json'
        previous=json.loads(budget.read_text()) if budget.exists() else []
        spent=sum(r['controller_seconds'] for r in previous)
        remaining=30-spent
        assert remaining>.5
        trial=PREP/sys.argv[1];trial.mkdir()
        before=snapshot(trial/'source-before')
        command=[sys.executable,*sys.argv[2:]]
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='none')
        timeout=False
        with (trial/'execution.log').open('wb') as log:
            try:
                result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=remaining-.5)
                rc=result.returncode
            except subprocess.TimeoutExpired:
                rc=None;timeout=True
        after=inventory()
        elapsed=time.perf_counter()-start
        record=dict(command=command,returncode=rc,timed_out=timeout,controller_seconds=elapsed,
                    cumulative_seconds=spent+elapsed,budget_seconds=30,before=before,after=after,
                    changed_paths=[p for p in FILES if before[p]!=after[p]],
                    kernels=0,model_or_simulator_runs=0,remote_calls=0)
        dump(trial/'run.json',record)
        previous.append(dict(trial=sys.argv[1],controller_seconds=elapsed,returncode=rc))
        budget.write_text(json.dumps(previous,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in record.items() if k not in ('before','after','command')}))
        assert elapsed+spent<=30
