"""Root focused Windows-host metadata regressions, không native Linux/training."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
WORK=Path(__file__).resolve().parent
OUT=WORK/'linux-main-metadata-tests02'
PINS={'src/knowledge_tracing/akt/research_main_execution.py':'73bbacc8c8bd196cc9d3eeb7e3ac65f27a51f3a52fa8d3fe83d14dd87ac8c7aa',
      'tests/akt/test_research_main_execution.py':'f7ed9b4dc7d28c54e3899089c5db8876d2f0fd4bf9532a901fa5eaef46431e55',
      'scripts/akt/refresh_gate2.py':'ed87ee74589087b66b434137f67388b64efb4160c41c33ff423ffc41bcc9e157',
      'tests/akt/test_gate2_refresh.py':'9c3456146634187bd9758b89b38d48c38b1364fe8d0b31a0910384f442c0cb21'}
def pins():
    return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in PINS}
if __name__=='__main__':
    if Path(sys.prefix).resolve()!=ROOT/'.venv':raise ValueError('Repository .venv')
    if pins()!=PINS:raise ValueError('Reviewed sources required')
    OUT.mkdir(exist_ok=False)
    base=OUT/'pytest-temp'
    if not base.resolve().is_relative_to(ROOT) or base.exists():raise ValueError('Owned temporary path')
    command=[sys.executable,'-B','-m','pytest','tests/akt/test_research_main_execution.py',
             'tests/akt/test_gate2_refresh.py','-q','-o','addopts=','-p','no:cacheprovider',
             '--basetemp',str(base),'--junitxml',str(OUT/'junit.xml')]
    environment=dict(os.environ,PYTHONPATH=str(ROOT/'src')+os.pathsep+str(ROOT/'third_party'),
        PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',
        CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    start=time.perf_counter();timeout=False
    try:
        with (OUT/'stdout.log').open('xb') as stdout,(OUT/'stderr.log').open('xb') as stderr:
            done=subprocess.run(command,cwd=ROOT,env=environment,stdout=stdout,stderr=stderr,timeout=30)
        returncode=done.returncode
    except subprocess.TimeoutExpired:
        returncode=None;timeout=True
    elapsed=time.perf_counter()-start
    counts=dict(tests=0,failures=0,errors=0,skipped=0);caseids=[]
    if (OUT/'junit.xml').is_file() and (OUT/'junit.xml').stat().st_size<=4*1024**2:
        tree=ET.parse(OUT/'junit.xml')
        for case in tree.iter('testcase'):
            counts['tests']+=1;caseids.append((case.get('classname'),case.get('name')))
            for key,tag in [('failures','failure'),('errors','error'),('skipped','skipped')]:counts[key]+=len(case.findall(tag))
    after=pins()
    accepted=returncode==0 and not timeout and counts==dict(tests=154,failures=0,errors=0,skipped=0)
    accepted=accepted and after==PINS and len(caseids)==len(set(caseids)) and elapsed<30
    result=dict(status='ACCEPTED_154_METADATA_REGRESSIONS' if accepted else 'REJECTED',command=command,
        returncode=returncode,timeout=timeout,elapsed_seconds=elapsed,cap_seconds=30,counts=counts,
        unique_case_ids=len(set(caseids)),source_before=PINS,source_after=after,
        scope_vi='Windows-host manufactured metadata/tmpFS tests. Chưa actual Linux Gate/runtime, CUDA hoặc training.')
    with (OUT/'result.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)
