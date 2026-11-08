"""ONE bounded reader test run; publisher fixtures only, no teacher/NN."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
INPUTS=['src/knowledge_tracing/'+name for name in ('simulator_corpus_reader.py','simulator_corpus_publisher.py',
    'simulator_research_collection.py','simulator_research_data.py','simulator_data.py','simulator_bridge.py',
    'simulator_collection.py','paper2_reference.py','akt/resources.py')]
INPUTS+=['tests/shared_kt/test_simulator_corpus_reader.py','tests/shared_kt/test_simulator_corpus_publisher.py',
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    trial=PREP/'trial01';trial.mkdir()
    before={n:sha(ROOT/n) for n in INPUTS}
    for i,n in enumerate(INPUTS):(trial/f'{i:02}-{Path(n).name}.before').write_bytes((ROOT/n).read_bytes())
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-I','-B','-c',
        "import sys;sys.path.insert(0,'src');import pytest;raise SystemExit(pytest.main(sys.argv[1:]))",
        'tests/shared_kt/test_simulator_corpus_reader.py','-q','-p','no:cacheprovider',
        '--basetemp='+str(trial/'tmp'),'--junitxml='+str(trial/'junit.xml')]
    env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
             OPENBLAS_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='')
    start=time.monotonic();wall=time.time();code=None;error=None
    with (trial/'stdout.log').open('xb') as out,(trial/'stderr.log').open('xb') as err:
        try:code=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=28).returncode
        except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    elapsed=max(time.monotonic()-start,time.time()-wall)
    after={n:sha(ROOT/n) for n in INPUTS}
    for i,n in enumerate(INPUTS):(trial/f'{i:02}-{Path(n).name}.after').write_bytes((ROOT/n).read_bytes())
    counts=ET.parse(trial/'junit.xml').getroot().find('testsuite').attrib if (trial/'junit.xml').exists() else None
    value=dict(status='PASS' if code==0 and error is None and elapsed<=30 and before==after else 'FAILED_OR_RESOURCE_REJECTED',
        exit_code=code,error=error,command=command,controller_elapsed_seconds=elapsed,cumulative_seconds=elapsed,cap_seconds=30,
        counts=counts,source_sha256_before=before,source_sha256_after=after,model_calls=0,optimizer_updates=0,
        teacher_collection_calls=0,torch_imports=0,fixture_origin='publisher-produced temporary corpus of hand-built observations; mockedsource/memory only',
        research_corpus_generated=False,actual_runtime_gate=False,production_reader_imports='stdlib+publicobservablevalidators only')
    (trial/'receipt.json').open('x',encoding='utf-8').write(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))
    return 0 if value['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
