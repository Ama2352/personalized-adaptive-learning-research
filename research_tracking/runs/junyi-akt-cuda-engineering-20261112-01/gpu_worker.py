"""Worker cô lập cho một epoch Junyi được duyệt, không mở calibration/Holdout."""
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import traceback
import zipfile

ROOT = Path('/opt/kltn')
RUN = 'modal-junyi-a0-epoch-20261112-02'
OPERATION = ROOT/'experiments/akt/results'/(RUN+'-operation')
OPERATION.mkdir(parents=True, exist_ok=False)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


result = dict(status='FAILED', full_junyi_benchmark=False)
try:
    for archive in ('/opt/kltn-input.zip', '/opt/junyi-cohort.zip'):
        with zipfile.ZipFile(archive) as saved:
            pins = json.loads(saved.read('MANIFEST.json'))['files']
            for name, digest in pins.items():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
                raw = saved.read(name)
                assert hashlib.sha256(raw).hexdigest() == digest
                path = ROOT/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
    preflight = ROOT/'artifacts/akt/preflight'
    preflight.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile('/opt/cpu-gate.zip') as saved:
        for name, entry in json.loads(saved.read('SHA256.json')).items():
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest() == entry['sha256']
            if name.startswith('gate2-'):
                assert Path(name).name == name
                (preflight/name).write_bytes(raw)
    lock = ROOT/'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
    lock.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile('/opt/locked-cu126.txt', lock)
    upstream = ROOT/'artifacts/akt/dependencies/upstream'
    os.environ.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=str(upstream),
        GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='false',
        GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',
        CUDA_VISIBLE_DEVICES='0', CUBLAS_WORKSPACE_CONFIG=':4096:8',
        OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    runtime = preflight/(RUN+'-runtime.json')
    subprocess.run([sys.executable, '-I', '-B', str(ROOT/'scripts/akt/check_runtime.py'),
        '--upstream', str(upstream), '--device', 'cuda', '--lock-file', str(lock),
        '--output', str(runtime)], check=True, timeout=35)
    sys.path.insert(0, str(ROOT/'src'))
    import numpy as np
    import torch
    from knowledge_tracing.akt.config import ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.authorization import preflight as check_preflight, require_gate2_evidence
    from knowledge_tracing.akt.research_junyi_engineering import engineering_config, run_one_epoch, write_json
    config = engineering_config(RUN)
    profile = ResearchCUDAExecutionProfile(2*1024**3)
    gate = require_gate2_evidence(config, lock_file=lock)
    runtime_proof = check_preflight(config, runtime_report_path=runtime, lock_file=lock, cuda_profile=profile)
    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory, 0)
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    write_json(OPERATION/'preflight.json', dict(gate=gate, runtime=runtime_proof,
        gpu_name=torch.cuda.get_device_name(0), all_rng_seeded=42))
    cohort = ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
    roles = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    inventory = json.loads(Path('/opt/junyi-request.json').read_text())
    assert inventory['status'] == 'USER_APPROVED' and inventory['authorized_usd'] == 0.5
    terminal = run_one_epoch(config, profile, cohort_root=cohort, roles_path=roles,
        cohort_sha256=inventory['cohort_sha256'], roles_sha256=inventory['roles_sha256'])
    result.update(status=terminal['status'], terminal=terminal)
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    (OPERATION/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
raise SystemExit(0 if result['status']=='ACTUAL_JUNYI_A0_CUDA_ONE_EPOCH_COMPLETE' else 1)
