"""Kiểm toy A0–A3, .venv local; budget tích lũy120s, không optimizer."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
FILES = ('src/knowledge_tracing/akt/graph_prototype.py', 'tests/akt/test_graph_prototype.py')
CAP = 120.


def hashes():
    return {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}


def main():
    assert Path(sys.prefix).resolve() == ROOT/'.venv'
    prior = sorted(PREP.glob('attempt*/receipt.json'))
    spent = sum(json.loads(p.read_text(encoding='utf-8'))['controller_seconds'] for p in prior)
    remaining = CAP - spent
    assert remaining > 5, 'budget exhausted; no automatic reset'
    attempt = PREP/f'attempt{len(prior)+1:02d}'
    attempt.mkdir(exist_ok=False)
    before = hashes()
    (attempt/'source_before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    for f in FILES:
        (attempt/Path(f).name).write_bytes((ROOT/f).read_bytes())
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
               PYTHONPATH=str(ROOT/'src'), PYTHONDONTWRITEBYTECODE='1')
    # Chỉ child này tin hai checkout đã kiểm; không ghi Git config global.
    count=int(env.get('GIT_CONFIG_COUNT','0'))
    for path in (ROOT,ROOT/'artifacts/akt/dependencies/upstream'):
        env[f'GIT_CONFIG_KEY_{count}']='safe.directory'
        env[f'GIT_CONFIG_VALUE_{count}']=path.as_posix()
        count+=1
    env['GIT_CONFIG_COUNT']=str(count)
    command=[str(ROOT/'.venv/Scripts/python.exe'), '-c',
        'import torch,pytest;torch.set_num_threads(2);raise SystemExit(pytest.main())',
        '-q', FILES[1], '--basetemp='+str(attempt/'tmp'), '--junitxml='+str(attempt/'pytest.xml')]
    start = time.perf_counter()
    process = None
    status = 'FAILED'
    try:
        with (attempt/'stdout.log').open('xb') as out, (attempt/'stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=err)
            try:
                process.wait(timeout=max(.1,remaining-3))
            except subprocess.TimeoutExpired:
                status='REJECTED_CUMULATIVE_RESOURCE_BOUND'
                process.kill();process.wait(timeout=2)
        after=hashes()
        suites=list(ET.parse(attempt/'pytest.xml').getroot().iter('testsuite')) if (attempt/'pytest.xml').exists() else []
        counts={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
        if process.returncode==0 and before==after and counts['tests'] and not any(counts[k] for k in ('failures','errors','skipped')):
            status='PASS_TARGETED_TOY_FORWARD_BACKWARD_ONLY'
    finally:
        if process is not None and process.poll() is None:
            process.kill();process.wait(timeout=2)
        elapsed=time.perf_counter()-start
        if elapsed+spent>CAP:status='REJECTED_CUMULATIVE_RESOURCE_BOUND'
        receipt=dict(status=status,command=command,source_before=before,source_after=hashes(),
            counts=locals().get('counts'),returncode=None if process is None else process.returncode,
            child_reaped=process is None or process.poll() is not None,
            controller_seconds=elapsed,previous_seconds=spent,cumulative_seconds=elapsed+spent,
            cumulative_cap_seconds=CAP,optimizer_steps=0,realdata_targets=0,cloud_calls=0,
            scope='Toy B<=2,N<=4,T<=12,d32; caller-declared confidence/gate recipe, not fitted or method adoption')
        (attempt/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(receipt,ensure_ascii=False))
    return 0 if status.startswith('PASS_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
