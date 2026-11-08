"""Một .venv launch probe≤10s; chỉ PID/exe/ctime, không replay/model."""
import time
START=time.perf_counter()
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[5]
PREP=Path(__file__).resolve().parent
SCIENCE=PREP.parent
CAP=16384

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')
def norm(path):return os.path.normcase(os.path.abspath(path))

if __name__=='__main__':
    assert norm(sys.executable)==norm(ROOT/'.venv/Scripts/python.exe')
    assert Path(sys.prefix).resolve()==ROOT/'.venv' and sys.platform=='win32'
    import psutil
    assert not any(name in sys.modules for name in ('torch','numpy','pandas','knowledge_tracing'))
    out=PREP/'probe-attempt01';out.mkdir(exist_ok=False)
    prior_path=SCIENCE/'availability-replay-attempt01/run.json'
    prior=json.loads(prior_path.read_bytes())
    assert prior['status']=='REJECTED_RETAIN_NO_RETRY_NO_PARTIAL_CLAIM' and prior['returncode']==1
    spent=prior['elapsed_seconds']
    sources=[Path(__file__).resolve(),PREP/'child_probe.py',SCIENCE/'history_availability_worker.py',
             SCIENCE/'run_history_availability.py',prior_path]
    before={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    assert before[(SCIENCE/'history_availability_worker.py').relative_to(ROOT).as_posix()]=='28b2b60f958064b88d126aeb76e40f30e4d33d4ec10cd5f6010b7dff12039718'
    assert before[(SCIENCE/'run_history_availability.py').relative_to(ROOT).as_posix()]=='65fca33aa1074e7d17e9b53a6ebd07142b308507930e51d6907e3cc196c5b6ce'
    own=psutil.Process(os.getpid())
    outer=dict(pid=os.getpid(),ppid=os.getppid(),exe=own.exe(),create_time=own.create_time(),
               executable=sys.executable,prefix=sys.prefix,base_executable=getattr(sys,'_base_executable',None))
    release=out/'release.txt'
    command=[sys.executable,'-B',str(PREP/'child_probe.py'),'--outer-pid',str(outer['pid']),
             '--outer-create-time',repr(outer['create_time']),'--release-file',str(release)]
    env=os.environ.copy()
    for name in ('PYTHONPATH','PYTHONSTARTUP','PYTHONINSPECT'):
        env.pop(name,None)
    env.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    child=None;observed=None;error=None;popen=None;owned={};cleanup=[];rc=None
    def remember(process):
        row=dict(pid=process.pid,ppid=process.ppid(),exe=process.exe(),create_time=process.create_time())
        owned[row['pid']]=row
        return row
    def original_alive(row):
        try:
            process=psutil.Process(row['pid'])
            return process.create_time()==row['create_time'] and process.is_running()
        except psutil.NoSuchProcess:
            return False
    with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
        try:
            assert time.perf_counter()-START<7
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
                stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
            popen=remember(psutil.Process(child.pid))
            while time.perf_counter()-START<7:
                for process in psutil.Process(child.pid).children(recursive=True):
                    remember(process)
                assert (out/'stdout.log').stat().st_size<=CAP and (out/'stderr.log').stat().st_size<=CAP
                with (out/'stdout.log').open('rb') as stream:raw=stream.read(CAP+1)
                if raw.endswith(b'\n'):
                    observed=json.loads(raw)
                    break
                if child.poll() is not None:
                    raise RuntimeError('pure child exited without metadata')
                time.sleep(.005)
            assert observed is not None,'pure probe7s active deadline'
            chain=observed['ancestors']
            assert observed['pid'] in owned and chain[0]['pid']==observed['pid']
            assert norm(observed['executable'])==norm(sys.executable) and norm(observed['prefix'])==norm(sys.prefix)
            assert not observed['forbidden_modules_loaded']
            for row in chain:
                live=psutil.Process(row['pid'])
                assert live.create_time()==row['create_time'] and live.ppid()==row['ppid'] and norm(live.exe())==norm(row['exe'])
            assert chain[-1]['pid']==outer['pid'] and chain[-1]['create_time']==outer['create_time']
            assert any(row['pid']==popen['pid'] and row['create_time']==popen['create_time'] for row in chain)
            assert all(left['ppid']==right['pid'] for left,right in zip(chain,chain[1:]))
            if observed['ppid']!=outer['pid']:
                assert len(chain)==3 and chain[1]['pid']==popen['pid']
                assert norm(chain[1]['exe'])==norm(sys.executable)
                assert norm(chain[0]['exe'])==norm(outer['exe'])
            with release.open('xb') as stream:stream.write(b'RELEASE\n')
            rc=child.wait(timeout=max(.001,min(2,9-(time.perf_counter()-START))))
            assert rc==0
        except Exception as exc:
            error=dict(type=type(exc).__name__,message=str(exc))
        finally:
            if child is not None:
                # Exact observed PID/create-time tokens only; no process-name/global kill.
                if not release.exists():
                    try:
                        with release.open('xb') as stream:stream.write(b'RELEASE\n')
                    except Exception:
                        pass
                try:
                    if child.poll() is None:
                        child.wait(timeout=max(.001,min(.5,9-(time.perf_counter()-START))))
                except subprocess.TimeoutExpired:
                    for row in reversed(list(owned.values())):
                        if original_alive(row):
                            psutil.Process(row['pid']).kill()
                            cleanup.append(dict(action='killed_exact_observed_owned_pid',pid=row['pid'],create_time=row['create_time']))
                    child.wait(timeout=max(.001,10-(time.perf_counter()-START)))
                rc=child.returncode
    alive=[]
    for row in owned.values():
        if original_alive(row):alive.append(row)
    after={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    assert before==after
    elapsed=time.perf_counter()-START
    cleanup_accepted=not alive and child is not None and child.returncode is not None
    accepted=error is None and cleanup_accepted and elapsed<=10
    status=('OBSERVED_VERIFIED_VENV_REDIRECTOR_CHAIN_NOT_NATIVE_REPLAY' if accepted and observed['ppid']!=outer['pid']
            else 'OBSERVED_VERIFIED_DIRECT_CHILD_NOT_NATIVE_REPLAY' if accepted else 'UNKNOWN_OR_REJECTED_RETAIN_PURE_PROBE')
    record=dict(status=status,outer=outer,popen=popen,child=observed,command=command,
        error=error,returncode=rc,owned_processes=list(owned.values()),cleanup_actions=cleanup,
        surviving_owned_processes=alive,cleanup_accepted=cleanup_accepted,
        elapsed_seconds=elapsed,max_probe_seconds=10,source_before_sha256=before,source_after_sha256=after,
        prior_replay_receipt_sha256=sha(prior_path),availability_cumulative_seconds_before=spent,
        availability_cumulative_seconds_after=spent+elapsed,availability_cumulative_cap_seconds=60,
        explicit_torch_native_collector_model_gpu_remote_calls=0,automatic_retry=False,
        limitations='One observed Windows chain only; no native timeout/orphan simulation, no worker guard bypass, no independent process-security attestation.')
    assert spent+elapsed<=60
    dump(out/'probe.json',record)
    print(json.dumps(dict(status=status,elapsed_seconds=elapsed,cumulative_seconds_after=spent+elapsed,
        outer_pid=outer['pid'],popen_pid=popen['pid'] if popen else None,
        child_pid=observed['pid'] if observed else None,child_ppid=observed['ppid'] if observed else None,
        cleanup_accepted=cleanup_accepted,receipt_sha256=sha(out/'probe.json'))))
