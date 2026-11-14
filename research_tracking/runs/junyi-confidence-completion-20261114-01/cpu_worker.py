"""CPU Gate nguồn A1 hiện hành, tạo đủ parent scratch trước pytest."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import time
import traceback
import zipfile

ROOT = Path('/opt/kltn')
RUN = 'modal-junyi-a2-a3-final-cpu-20261114-01'
OUTPUT = Path('/cpu-evidence')/RUN
OUTPUT.mkdir(parents=True,exist_ok=False)
started = time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


result = dict(status='FAILED_PRESERVED',run_id=RUN,gpu_requested=False,main_training=False,
              numerical_diagnostic_repeated=False,max_vm_seconds=600)
try:
    request = json.loads(Path('/opt/junyi-selection-cpu-request.json').read_text())
    if request['run_id']!=RUN or request['reserved_usd']!=.15:
        raise ValueError('CPU selection cache scope mismatch')
    if sha(Path(__file__))!=request['worker_sha256'] or sha(Path('/opt/junyi-a1-source.zip'))!=request['source_sha256']:
        raise ValueError('Pinned CPU selection cache input changed')
    with zipfile.ZipFile('/opt/junyi-a1-source.zip') as saved:
        pins = json.loads(saved.read('MANIFEST.json'))['files']
        if set(saved.namelist())!=set(pins)|{'MANIFEST.json'}:
            raise ValueError('Source inventory mismatch')
        for name,digest in pins.items():
            relative = PurePosixPath(name)
            if (relative.is_absolute() or '..' in relative.parts or '\\' in name
                    or relative.parts[0] in ('dataset','venv','.wsl','.git')
                    or relative.parts[:2]==('artifacts','bkt_baseline')):
                raise ValueError('Unsafe source member')
            raw = saved.read(name)
            if hashlib.sha256(raw).hexdigest()!=digest:
                raise ValueError('Source member changed')
            path = ROOT.joinpath(*relative.parts)
            if not path.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('Source escapes project')
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)
    # pytest tạo basetemp leaf với parents=False; parent phải tồn tại trước.
    for relative in ('artifacts/akt/local-tests','artifacts/akt/tmp',
                     'artifacts/akt/runtime','artifacts/akt/preflight'):
        (ROOT/relative).mkdir(parents=True,exist_ok=True)
    lock = ROOT/'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
    shutil.copyfile('/opt/locked-cu126.txt',lock)
    environment = dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
        OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    command = [str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/akt/refresh_gate2.py'),
        '--run-id',RUN,'--publish-current','--timeout-seconds','480','--lock-file',str(lock)]
    with (OUTPUT/'gate-controller.log').open('xb') as stream:
        completed = subprocess.run(command,cwd=ROOT,env=environment,stdout=stream,
            stderr=subprocess.STDOUT,timeout=510)
    result['returncode'] = completed.returncode
    report = ROOT/'artifacts/akt/preflight'/('gate2-evidence-'+RUN+'.json')
    if report.is_file():
        evidence = json.loads(report.read_text())
        build_sha = hashlib.sha256(json.dumps(evidence['build_hashes'],sort_keys=True,
            separators=(',', ':')).encode()).hexdigest()
        if build_sha != request['expected_source_build_sha256']:
            raise ValueError('Gate build differs from packaged virtual inventory')
        result.update(gate_status=evidence['status'],test_result=evidence.get('test_result'),
                      source_build_sha256=build_sha)
    result['source_files_unchanged'] = all(sha(ROOT/name)==digest for name,digest in pins.items())
    if completed.returncode==0 and result.get('gate_status')=='PASS' and result['source_files_unchanged']:
        result['status'] = 'MODAL_CPU_GATE_VERIFIED'
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OUTPUT/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (OUTPUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    files = list(OUTPUT.glob('*.json'))+list(OUTPUT.glob('*.log'))
    preflight = ROOT/'artifacts/akt/preflight'
    files += list(preflight.glob('*'+RUN+'*'))
    if (preflight/'gate2-current.json').is_file():
        files.append(preflight/'gate2-current.json')
    inventory = {}
    with zipfile.ZipFile(OUTPUT/'artifacts.zip','x',zipfile.ZIP_DEFLATED) as saved:
        for path in sorted(files):
            if path.is_file():
                if path.name in inventory:
                    raise ValueError('Duplicate artifact basename')
                inventory[path.name] = dict(bytes=path.stat().st_size,sha256=sha(path))
                saved.write(path,path.name)
        saved.writestr('SHA256.json',json.dumps(inventory,indent=2)+'\n')
    result.update(archive_sha256=sha(OUTPUT/'artifacts.zip'),archive_bytes=(OUTPUT/'artifacts.zip').stat().st_size)
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='MODAL_CPU_GATE_VERIFIED' else 1)
