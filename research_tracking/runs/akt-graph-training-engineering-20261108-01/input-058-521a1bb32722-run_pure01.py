"""ONE local pure-contract attempt, cap30s; không native/optimizer constructors."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PREP=Path(__file__).resolve().parent
ROOT=PREP.parents[3]
RUN=PREP/'pure01'
FILES=('src/knowledge_tracing/akt/graph_training.py','tests/akt/test_graph_training.py')
CAP=30.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert Path(sys.prefix).resolve()==ROOT/'.venv'
    RUN.mkdir(exist_ok=False)
    before={f:sha(ROOT/f) for f in FILES}
    assert before==dict(zip(FILES,('1465d03e3bd9a35d9e0d861e6d03ea614f5f33e54a89ee02052836fe1632e5a6',
                                 '9293d3f0e9db56b53c6cdcfafb00006e93118d32a8e53d7b8b089c6faeec966a')))
    for f in FILES:(RUN/(Path(f).name+'.before')).write_bytes((ROOT/f).read_bytes())
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',
             NVIDIA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-c',
        'import torch,pytest;torch.set_num_threads(2);raise SystemExit(pytest.main())','-q',FILES[1],'-k','TestPureContracts',
        '-o','cache_dir='+str(RUN/'cache'),'--basetemp='+str(RUN/'tmp'),'--junitxml='+str(RUN/'pytest.xml')]
    start=time.monotonic();wall=time.time();process=None;code=None;counts={};error=None
    try:
        with (RUN/'stdout.log').open('xb') as out,(RUN/'stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=err)
            try:process.wait(timeout=CAP-3)
            except subprocess.TimeoutExpired:
                process.kill();process.wait(timeout=2);raise
        code=process.returncode
        suites=list(ET.parse(RUN/'pytest.xml').getroot().iter('testsuite'))
        counts={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    except BaseException as e:error=dict(type=type(e).__name__,message=str(e))
    finally:
        if process is not None and process.poll() is None:process.kill();process.wait(timeout=2)
        elapsed=time.monotonic()-start;wall_elapsed=time.time()-wall
        after={f:sha(ROOT/f) for f in FILES}
        for f in FILES:(RUN/(Path(f).name+'.after')).write_bytes((ROOT/f).read_bytes())
        status='PASS_PURE_ONLY' if code==0 and counts.get('tests',0)>0 and not any(counts.get(k,1) for k in ('failures','errors','skipped')) and before==after and elapsed<=CAP and wall_elapsed<=CAP else 'FAILED_RETAIN_NO_AUTORETRY'
        receipt=dict(status=status,command=command,counts=counts,returncode=code,error=error,
            source_before=before,source_after=after,controller_seconds=elapsed,wall_seconds=wall_elapsed,
            cumulative_seconds=elapsed,cumulative_cap_seconds=CAP,ledger='GRAPH04-pure independent of rootcallback17.699122s and actual-stage60s',
            child_reaped=process is None or process.poll() is not None,actual_neural_constructors=0,
            actual_optimizer_constructors=0,actual_optimizer_steps=0,actual_checkpoint_loads=0,
            spies='Autouse raises for GraphAKTPrototype.__init__, nn.Linear.__init__, Adam.__init__, torch.load; CUDA guards mocked false',
            scope='Pure role/recipe/window/ticket/parameter metadata only; no model fit/GPU/cloud/data run')
        (RUN/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        print(json.dumps(receipt))
    return 0 if status=='PASS_PURE_ONLY' else 1

if __name__=='__main__':raise SystemExit(main())
