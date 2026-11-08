"""Local ENGINEERING test controller only; cumulative30s, no installer/target calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PYTHON = ROOT / '.venv/Scripts/python.exe'
WATCH = [HERE / 'packet_validator01.py', HERE / 'test_packet_validator01.py', HERE / 'PURE_API01.md',
         HERE / 'input-packet-schema01.json', HERE / 'IMPLEMENTATION_PLAN01.md',
         HERE.parent / 'fresh_install_verified_profile_v3.py',
         HERE.parent / 'gpu10-cold-bootstrap01/gpu10_cold_bootstrap02.py',
         HERE.parents[1] / 'gpu08-linux-20261108-01/received/resolution-attempt01/pip-report.json',
         HERE.parents[1] / 'gpu08-linux-20261108-01/received/resolution-attempt01/candidate-linux-cuda.lock.txt']


def hashes(): return {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in WATCH}


def main():
    ledger_path = HERE / 'pure-test-ledger01.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else dict(attempts=[], cumulative_seconds=0)
    remaining = 30 - ledger['cumulative_seconds']
    if remaining <= 0: raise RuntimeError('same cumulative30s exhausted; no reset')
    attempt = HERE / ('pure-trial%02d' % (len(ledger['attempts']) + 1)); attempt.mkdir(exist_ok=False)
    started = time.monotonic(); before = hashes()
    for name in ('packet_validator01.py', 'test_packet_validator01.py'):
        (attempt / (name + '.snapshot')).write_bytes((HERE / name).read_bytes())
    command = [str(PYTHON), '-I', '-B', '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_packet_validator01.py', '-v']
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    rc = None; timeout = False
    try:
        with (attempt / 'unittest.log').open('xb') as log:
            try:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=max(.001, remaining - (time.monotonic() - started) - .5))
                rc = result.returncode
            except subprocess.TimeoutExpired:
                timeout = True
    finally:
        after = hashes(); elapsed = time.monotonic() - started
        ledger['cumulative_seconds'] += elapsed
        receipt = dict(command=command, returncode=rc, timeout=timeout, controller_posthash_seconds=elapsed,
            cumulative_seconds=ledger['cumulative_seconds'], cumulative_cap_seconds=30,
            before=before, after=after, source_inputs_unchanged=before == after,
            scope='LOCAL_PURE_ENGINEERING_FIXTURES_NOT_ACTUAL_TARGET', actual_target_processes=0,
            pip_network_GPU_model_calls=0)
        (attempt / 'run.json').write_text(json.dumps(receipt, indent=2) + '\n')
        ledger['attempts'].append(dict(path=attempt.name, **{k: receipt[k] for k in ('returncode', 'timeout', 'controller_posthash_seconds')}))
        ledger_path.write_text(json.dumps(ledger, indent=2) + '\n')
    print(json.dumps(receipt))
    return 0 if rc == 0 and before == after and ledger['cumulative_seconds'] <= 30 else 1


if __name__ == '__main__': raise SystemExit(main())
