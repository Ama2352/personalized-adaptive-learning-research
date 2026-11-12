"""Profile batch shape trên cùng packet Junyi, tách khỏi selected training."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path('/opt/kltn')
REQUEST = json.loads(Path('/opt/probe-request.json').read_text())
RUN = REQUEST['run_id']
OUTPUT = ROOT/'experiments/akt/results'/RUN
OPERATION = ROOT/'experiments/akt/results'/(RUN+'-operation')
OUTPUT.mkdir(parents=True,exist_ok=False)
OPERATION.mkdir(parents=True,exist_ok=False)
started = time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def extract(archive):
    with zipfile.ZipFile(archive) as saved:
        pins = json.loads(saved.read('MANIFEST.json'))['files']
        assert set(saved.namelist())==set(pins)|{'MANIFEST.json'}
        for name,pin in pins.items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert ':' not in name and '\\' not in name
            raw = saved.read(name)
            expected = pin if isinstance(pin,str) else pin['sha256']
            assert hashlib.sha256(raw).hexdigest()==expected
            path = ROOT/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)


result = dict(status='FAILED',scope='engineering_concurrent_gpu_only',full_junyi_epoch=False)
try:
    assert REQUEST['status']=='USER_APPROVED' and REQUEST['gpu']=='T4'
    assert REQUEST['max_optimizer_steps']==1160 and REQUEST['expected_targets']==56332
    extract('/opt/kltn-input.zip')
    extract('/opt/junyi-data.zip')
    preflight = ROOT/'artifacts/akt/preflight'
    preflight.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile('/opt/cpu-gate.zip') as saved:
        for name,pin in json.loads(saved.read('SHA256.json')).items():
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest()==pin['sha256']
            if name.startswith('gate2-'):
                assert Path(name).name==name
                (preflight/name).write_bytes(raw)
    lock = ROOT/'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
    lock.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile('/opt/locked-cu126.txt',lock)
    upstream = ROOT/'artifacts/akt/dependencies/upstream'
    os.environ.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=str(upstream),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false',
        GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',
        CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
        OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    runtime = preflight/(RUN+'-runtime.json')
    subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/akt/check_runtime.py'),
        '--upstream',str(upstream),'--device','cuda','--lock-file',str(lock),'--output',str(runtime)],
        check=True,timeout=120)
    import csv
    import threading
    control_root = Path('/opt/concurrent-control')
    control_root.mkdir(exist_ok=False)
    processes = []
    streams = []
    cases = []
    phase = dict(name='setup')
    telemetry_errors = []
    stop = threading.Event()

    def sample_gpu():
        try:
            with (OPERATION/'gpu-telemetry.jsonl').open('x') as stream:
                while not stop.is_set():
                    observed_phase = dict(phase)
                    query = subprocess.run(['nvidia-smi',
                        '--query-gpu=utilization.gpu,memory.used,memory.total,power.draw',
                        '--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=4)
                    values = next(csv.reader(query.stdout.splitlines()))
                    stream.write(json.dumps(dict(at_monotonic=time.monotonic(),phase=observed_phase,
                        gpu_utilization=float(values[0]),vram_used_mib=float(values[1]),
                        vram_total_mib=float(values[2]),power_w=float(values[3])))+'\n')
                    stream.flush()
                    stop.wait(.5)
        except Exception as error:
            telemetry_errors.append(str(error))

    def guard():
        assert time.monotonic()-started < 330, 'Parent worker deadline'
        for label, process in processes:
            assert process.poll() in (None,0), f'Child failed {label}: {process.returncode}'

    def run_group(name, specifications):
        phase.update(name=name+'-warmup')
        current = []
        for label, seed in specifications:
            environment = dict(os.environ,KLTN_CHILD_RUN=RUN+'-'+label,
                KLTN_CHILD_LABEL=label,KLTN_CHILD_SEED=str(seed))
            log = (OPERATION/(label+'.log')).open('xb')
            streams.append(log)
            process = subprocess.Popen([sys.executable,'-B','/opt/concurrent_child.py'],
                cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT)
            processes.append((label,process))
            current.append((label,process,control_root/(RUN+'-'+label)))
        while not all((control/'READY').is_file() for _,_,control in current):
            guard()
            time.sleep(.05)
        phase.update(name=name)
        begin = time.monotonic()
        for _,_,control in current:
            (control/'GO').write_text('go')
        while not all((control/'DONE.json').is_file() for _,_,control in current):
            guard()
            time.sleep(.02)
        finish = time.monotonic()
        phase.update(name=name+'-checkpoint')
        for _,_,control in current:
            (control/'CHECKPOINT_GO').write_text('go')
        bounds = [json.loads((control/'DONE.json').read_text()) for _,_,control in current]
        measured_seconds = max(row['finished_monotonic'] for row in bounds)-min(
            row['started_monotonic'] for row in bounds)
        for label,process,_ in current:
            while process.poll() is None:
                guard()
                time.sleep(.05)
            child = json.loads((OUTPUT/'children'/(RUN+'-'+label)/'operation/result.json').read_text())
            assert child['status']=='JUNYI_BATCH_UTILIZATION_COMPLETE', child
            assert child['checkpoint_reload_and_next_update_exact'] is True
        scored = sum(row['measured_targets'] for row in bounds)
        case = dict(name=name,labels=[label for label,_,_ in current],
            concurrent_processes=len(current),measurement_started_monotonic=begin,
            measurement_finished_monotonic=finish,seconds=measured_seconds,
            targets=scored,targets_per_second=scored/measured_seconds)
        cases.append(case)
        write_json(OPERATION/'progress.json',dict(cases=cases))

    sampler = threading.Thread(target=sample_gpu,daemon=True)
    sampler.start()
    try:
        run_group('solo-a',[('solo-a',42)])
        run_group('solo-b',[('solo-b',43)])
        run_group('parallel',[('parallel-a',42),('parallel-b',43)])
        equivalence = {}
        for suffix in ('a','b'):
            solo = json.loads((OUTPUT/'children'/(RUN+'-solo-'+suffix)/'operation/result.json').read_text())
            parallel = json.loads((OUTPUT/'children'/(RUN+'-parallel-'+suffix)/'operation/result.json').read_text())
            assert solo['seed']==parallel['seed']
            assert solo['final_fingerprints']==parallel['final_fingerprints']
            assert [p['mean_training_loss'] for p in solo['passes']]==[
                p['mean_training_loss'] for p in parallel['passes']]
            equivalence[suffix] = dict(seed=solo['seed'],fingerprints=solo['final_fingerprints'],
                serial_parallel_exact=True,checkpoint_resume_exact=True)
        serial_seconds = sum(row['seconds'] for row in cases[:2])
        parallel_seconds = cases[2]['seconds']
        result.update(status='JUNYI_CONCURRENT_GPU_COMPLETE',cases=cases,equivalence=equivalence,
            aggregate_speedup=serial_seconds/parallel_seconds,
            measured_total_optimizer_steps=4*9*32+8,
            max_total_target_exposures=2039032,training_protocol_changed=False,
            h100_tested=False,independent_quality_evaluation=False)
    finally:
        stop.set()
        sampler.join(timeout=5)
        for _,process in processes:
            if process.poll() is None:
                process.terminate()
        for _,process in processes:
            if process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        for stream in streams:
            stream.close()
    assert not telemetry_errors,telemetry_errors
except BaseException as error:
    result.update(status='FAILED',error_type=type(error).__name__,error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds']=time.monotonic()-started
    write_json(OPERATION/'result.json',result)
print(json.dumps(result,allow_nan=False),flush=True)
raise SystemExit(0 if result['status']=='JUNYI_CONCURRENT_GPU_COMPLETE' else 1)
