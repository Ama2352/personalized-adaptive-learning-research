"""Bộ điều khiển pytest riêng:30s cộng dồn,0teacher/model/remote."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
FILES=['src/knowledge_tracing/simulator_corpus_publisher.py',
       'tests/shared_kt/test_simulator_corpus_publisher.py',
       'src/knowledge_tracing/simulator_research_collection.py',
       'src/knowledge_tracing/simulator_research_data.py','src/knowledge_tracing/simulator_data.py',
       'src/knowledge_tracing/simulator_bridge.py','src/knowledge_tracing/simulator_collection.py',
       'src/knowledge_tracing/paper2_reference.py','src/knowledge_tracing/akt/resources.py',
       'src/knowledge_tracing/akt/research_execution.py',
       'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
       'artifacts/akt/local-tests/akt-research-execution-20261108-01/CORPUS_SCHEMA_V1.json',
       'artifacts/akt/local-tests/simulator-corpus-publisher-20261108-01/run_pure.py']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')
def inventory():return {name:dict(sha256=sha(ROOT/name),bytes=(ROOT/name).stat().st_size) for name in FILES}

if __name__=='__main__':
    started=time.perf_counter()
    assert Path(sys.executable).absolute()==ROOT/'.venv/Scripts/python.exe'
    budget=PREP/'budget.json'
    prior=json.loads(budget.read_bytes()) if budget.exists() else []
    spent=sum(row['controller_seconds'] for row in prior)
    remaining=30-spent
    assert remaining>.5
    trial=PREP/sys.argv[1];trial.mkdir()
    before=inventory()
    snapshots=trial/'source-before';snapshots.mkdir()
    for name,row in before.items():
        copy=snapshots/name.replace('/','__');copy.write_bytes((ROOT/name).read_bytes())
        assert sha(copy)==row['sha256']
    dump(snapshots/'inventory.json',before)
    command=[sys.executable,'-B','-m','pytest','tests/shared_kt/test_simulator_corpus_publisher.py',
             '-q','-p','no:cacheprovider','-o','addopts=',
             '--basetemp='+str(trial/'tmp'),'--junitxml='+str(trial/'pytest.xml')]
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTEST_ADDOPTS='',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='none',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    timeout=False
    with (trial/'pytest.log').open('wb') as log:
        try:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=remaining-.5)
            rc=result.returncode
        except subprocess.TimeoutExpired:
            rc=None;timeout=True
    after=inventory();elapsed=time.perf_counter()-started
    receipt=dict(command=command,returncode=rc,timed_out=timeout,controller_seconds=elapsed,
        cumulative_seconds=spent+elapsed,budget_seconds=30,before=before,after=after,
        sources_unchanged=before==after,teacher_calls=0,collector_calls=0,model_calls=0,optimizer_steps=0,remote_calls=0)
    dump(trial/'run.json',receipt)
    prior.append(dict(trial=sys.argv[1],controller_seconds=elapsed,returncode=rc))
    budget.write_text(json.dumps(prior,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('before','after','command')}))
    assert elapsed+spent<=30 and before==after
