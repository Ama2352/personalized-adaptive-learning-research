"""Điều phối sáu process fixture CUDA, dừng lỗi đầu, giữ checkpoint và log."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
import traceback

ROOT = Path('/content/kltn-current-t4-20261110-01')
BASE = ROOT/'experiments/akt/results/t4-checkpoint-recovery-20261110-01'
BASE.mkdir(parents=True, exist_ok=False)
started = time.monotonic()
env = dict(os.environ, CUBLAS_WORKSPACE_CONFIG=':4096:8', PYTHONDONTWRITEBYTECODE='1',
    CUDA_VISIBLE_DEVICES='0', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
worker = ROOT/'artifacts/akt/runtime/t4_checkpoint_worker.py'
result = dict(status='FAILED', scope='Fixture CUDA complete-epoch checkpoint and fresh-process restore',
    main_training=False, modal_spend_usd=0, processes=[], timeout_seconds=360,
    max_physical_optimizer_updates=16, max_physical_targets=384,
    worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest())
try:
    installed = json.loads((ROOT/'artifacts/akt/runtime/isolated-install02/result.json').read_text())
    assert installed['status'] == 'ISOLATED_ENV_READY_GPU_UNTESTED'
    smoke = json.loads((ROOT/'experiments/akt/results/current-t4-four-variant-smoke-20261110-01/result.json').read_text())
    assert smoke['status'] == 'CUDA_FOUR_VARIANT_SMOKE_PASS'
    for variant in ('A0', 'A3'):
        for phase in ('continuous', 'interrupted', 'resumed'):
            remaining = 360-(time.monotonic()-started)
            assert remaining > 0 and shutil.disk_usage(ROOT).free >= 30*1024**3
            assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()) <= 256*1024**2
            command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(worker),
                '--variant', variant, '--phase', phase]
            entry = dict(variant=variant, phase=phase, command=command)
            result['processes'].append(entry)
            with (BASE/(variant+'-'+phase+'.log')).open('xb') as log:
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
                entry['pid'] = process.pid
                try:
                    entry['returncode'] = process.wait(timeout=min(90, remaining))
                except subprocess.TimeoutExpired:
                    assert process.pid > 1 and process.pid != os.getpgrp()
                    for sig in (signal.SIGTERM, signal.SIGKILL):
                        try:
                            os.killpg(process.pid, sig)
                        except ProcessLookupError:
                            pass
                    process.wait(timeout=10)
                    raise
            assert entry['returncode'] == 0, entry
            actual = json.loads((BASE/variant/phase/'result.json').read_text())
            expected = 'CHECKPOINT_SAVED_AT_EPOCH1' if phase == 'interrupted' else 'COMPLETE'
            assert actual['status'] == expected and actual['source_unchanged'] is True
            if phase == 'resumed':
                assert actual['continuous_resumed_exact'] is True
    assert len({entry['pid'] for entry in result['processes']}) == 6
    result.update(status='CUDA_CHECKPOINT_FRESH_PROCESS_RESTORE_VERIFIED',
        physical_optimizer_updates=16, physical_optimized_targets=384,
        checkpoint_download_verified=False, full_lifecycle_recovery=False,
        unexpected_fault_recovery=False, variants=['A0', 'A3'])
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    (BASE/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (BASE/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    inventory = {path.relative_to(BASE).as_posix(): dict(bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted(BASE.rglob('*')) if path.is_file()}
    (BASE/'SHA256.json').write_text(json.dumps(inventory, indent=2)+'\n')
    print(json.dumps(result), flush=True)
