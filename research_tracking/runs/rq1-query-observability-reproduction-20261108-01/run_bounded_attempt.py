"""Một authorized attempt: spy tests trước, rồi exact replay; <=120s tổng, no retry."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=Path(__file__).resolve().parent;ATTEMPT=PREP/'attempt01';ATTEMPT.mkdir(exist_ok=False)
START=time.perf_counter();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['observer.py','test_observer.py','run_reproduction.py','run_bounded_attempt.py','INSPECTION_NOTE.md','inspection_sources.json']
before={name:sha(PREP/name) for name in names};copies=[]
for name in names:
    path=PREP/name
    if path.suffix=='.py':ast.parse(path.read_bytes())
    shutil.copyfile(path,ATTEMPT/('source__'+name));assert sha(ATTEMPT/('source__'+name))==before[name]
    copies.append({'source':str(path.relative_to(ROOT)),'copy':'source__'+name,'sha256_before_copy':before[name],'sha256_after_copy':sha(ATTEMPT/('source__'+name))})
env={**os.environ,'PYTHONPATH':str(PREP)+os.pathsep+str(ROOT/'src'),'CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1',
     'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'}
commands=[];failure=None;unit_counts=None
try:
    command=[sys.executable,'-B','-m','pytest',str(PREP/'test_observer.py'),'-q','-p','no:cacheprovider',
             '--basetemp',str(ATTEMPT/'tmp'),'--junitxml',str(ATTEMPT/'pytest.xml')]
    with (ATTEMPT/'pytest.log').open('xb') as stream:rc=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120-(time.perf_counter()-START)).returncode
    commands.append({'phase':'dummy_unit_checks','command':command,'returncode':rc})
    assert rc==0, 'observer unit checks failed; STOP'
    suites=list(ET.parse(ATTEMPT/'pytest.xml').getroot().iter('testsuite'))
    unit_counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    assert unit_counts['tests']>0 and not any(unit_counts[key] for key in ('failures','errors','skipped'))
    remaining=120-(time.perf_counter()-START);assert remaining>0
    env['RQ1_REMAINING_SECONDS']=str(remaining)
    command=[sys.executable,'-B',str(PREP/'run_reproduction.py'),str(ATTEMPT/'replay')]
    with (ATTEMPT/'reproduction.log').open('xb') as stream:rc=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=remaining).returncode
    commands.append({'phase':'control_then_observed_reproduction','command':command,'returncode':rc})
    assert rc==0,'exact reproduction failed; STOP/no tolerance fallback'
except Exception as error:
    failure={'error_type':type(error).__name__,'error':str(error)}
elapsed=time.perf_counter()-START;after={name:sha(PREP/name) for name in names}
result={'status':'PASS' if failure is None and elapsed<=120 and before==after else 'FAILED_STOP_RETAIN_ATTEMPT',
        'commands':commands,'unit_counts':unit_counts,'failure':failure,'controller_elapsed_seconds':elapsed,'cumulative_cap_seconds':120,
        'source_sha256_before':before,'source_sha256_after':after,'source_unchanged':before==after,'copies':copies,
        'optimizer_steps':0,'new_independent_N':0,'historical_metadata_backfilled':False,
        'environment':{key:env[key] for key in ('CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')}}
with (ATTEMPT/'run.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('copies','source_sha256_before','source_sha256_after','commands')},ensure_ascii=False))
raise SystemExit(0 if result['status']=='PASS' else 1)
