"""Kiểm NumPy-only research data; ONE invocation,30s cumulative,0NN."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
INPUTS=['src/knowledge_tracing/'+n for n in ('shared_kt.py','simulator_bridge.py','simulator_data.py',
    'simulator_research_data.py','akt/research_simulator_data.py','akt/simulator_data.py','akt/windows.py',
    'akt/types.py','akt/encoding.py','akt/provenance.py','akt/config.py')]
INPUTS+=['tests/akt/test_research_simulator_data.py','docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md']


def main():
    trial=PREP/'trial02';trial.mkdir()
    before={name:sha(ROOT/name) for name in INPUTS}
    for i,name in enumerate(INPUTS):
        (trial/f'{i:02}-{Path(name).name}.before').write_bytes((ROOT/name).read_bytes())
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-I','-B','-c',
        "import sys;sys.path.insert(0,'src');import pytest;raise SystemExit(pytest.main(sys.argv[1:]))",
        'tests/akt/test_research_simulator_data.py','-q','-p','no:cacheprovider',
        '--basetemp='+str(trial/'tmp'),'--junitxml='+str(trial/'junit.xml')]
    env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
             OPENBLAS_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='')
    start=time.monotonic();wall=time.time();code=None;error=None
    with (trial/'stdout.log').open('xb') as out,(trial/'stderr.log').open('xb') as err:
        try:code=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=29).returncode
        except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    elapsed=max(time.monotonic()-start,time.time()-wall)
    after={name:sha(ROOT/name) for name in INPUTS}
    for i,name in enumerate(INPUTS):
        (trial/f'{i:02}-{Path(name).name}.after').write_bytes((ROOT/name).read_bytes())
    counts=None
    if (trial/'junit.xml').exists():
        counts=ET.parse(trial/'junit.xml').getroot().find('testsuite').attrib
    receipt=dict(status='PASS' if code==0 and error is None and elapsed+1.780566200031899<=30 and before==after else 'FAILED_OR_RESOURCE_REJECTED',
        command=command,exit_code=code,error=error,controller_elapsed_seconds=elapsed,cumulative_seconds=elapsed+1.780566200031899,
        cap_seconds=30,counts=counts,source_sha256_before=before,source_sha256_after=after,
        neural_model_calls=0,optimizer_updates=0,only_handmade_observables=True,generated_corpus=False,
        run_kind='pure_numpy_data_contract_not_training_or_runtime_gate')
    (trial/'receipt.json').open('x',encoding='utf-8').write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    return 0 if receipt['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
