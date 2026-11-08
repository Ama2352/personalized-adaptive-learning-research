"""CPU synthetic controller, cumulative120s; giữ snapshots/log/XML cả failure."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=ROOT/'artifacts/akt/local-tests/parallel-gkt-recurrent-20261108-preparation'
BUDGET=PREP/'budget.json'
trial=sys.argv[1];assert trial in ('01','02','03')
directory=ROOT/f'artifacts/akt/local-tests/parallel-gkt-recurrent-20261108-{trial}'
directory.mkdir(exist_ok=False)
sources=['src/knowledge_tracing/gkt/recurrent.py','tests/gkt/test_recurrent.py',
    'src/knowledge_tracing/gkt/core.py','src/knowledge_tracing/gkt/config.py','src/knowledge_tracing/gkt/__init__.py',
    'tests/gkt/test_core.py','research_tracking/reports/gkt_recurrence_specification_20261108.md',
    'research_tracking/reports/gkt_recurrence_specification_20261108.sources.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={name:sha(ROOT/name) for name in sources}
copies=[]
for index,name in enumerate(sources):
    target=directory/f'source{index:02d}__{Path(name).name}';shutil.copyfile(ROOT/name,target)
    assert sha(target)==before[name]
    copies.append({'source':name,'copy':target.name,'sha256_before_copy':before[name],'sha256_after_copy':sha(target)})
budget=json.loads(BUDGET.read_text()) if BUDGET.exists() else {'elapsed_seconds':0.,'attempts':[],'cap_seconds':120,'optimizer_steps':0}
remaining=120-budget['elapsed_seconds'];assert remaining>=1
timeout=math.floor(remaining)
env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1',
     'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'}
command=[sys.executable,'-B','-m','pytest','tests/gkt','-q','-p','no:cacheprovider',
         '--basetemp',str(directory/'tmp'),'--junitxml',str(directory/'pytest.xml')]
start=time.perf_counter();error=None;returncode=None
with (directory/'pytest.log').open('xb') as stream:
    try:returncode=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout).returncode
    except subprocess.TimeoutExpired as exc:error=type(exc).__name__
elapsed=time.perf_counter()-start
budget['elapsed_seconds']+=elapsed;budget['attempts'].append({'trial':trial,'elapsed_seconds':elapsed,'returncode':returncode,'error':error})
BUDGET.write_text(json.dumps(budget,indent=2)+'\n')
after={name:sha(ROOT/name) for name in sources}
counts=None
if (directory/'pytest.xml').is_file():
    suites=list(ET.parse(directory/'pytest.xml').getroot().iter('testsuite'))
    counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
run={'command':command,'timeout_seconds':timeout,'returncode':returncode,'error':error,'controller_elapsed_seconds':elapsed,
     'cumulative_controller_seconds':budget['elapsed_seconds'],'cumulative_cap_seconds':120,'optimizer_steps':0,
     'source_sha256_before':before,'source_sha256_after':after,'sources_unchanged':before==after,'copies':copies,
     'counts':counts,'environment':{key:env[key] for key in ('CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')}}
(directory/'run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert before==after and budget['elapsed_seconds']<=120
print(json.dumps({k:v for k,v in run.items() if k not in ('copies','source_sha256_before','source_sha256_after','command')},ensure_ascii=False))
raise SystemExit(returncode if returncode is not None else 124)
