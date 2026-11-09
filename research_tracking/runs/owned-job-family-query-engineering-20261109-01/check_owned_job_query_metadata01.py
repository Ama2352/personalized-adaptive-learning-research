"""Probe metadata6samples của named owned Job, không model/data/network."""
import time
START = time.monotonic()
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'owned-job-query-metadata01'
sys.path.insert(0, str(ROOT / 'scripts/research'))
from windows_owned_worker import worker_gate, Kernel, MAX_PROCESSES, safe
owner = worker_gate()
assert len(sys.argv) == 2
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == sys.argv[1]
assert not safe(OUT).exists()
OUT.mkdir()
timer = threading.Timer(max(.001, 5 - (time.monotonic() - START)), lambda: os._exit(124))
timer.daemon = True
timer.start()
samples, error = [], None
api = handle = None
closed = False

def audit(kind, args):
    if kind == 'import' and str(args[0]).split('.')[0] in ('torch', 'numpy', 'pandas', 'knowledge_tracing', 'modal'):
        raise RuntimeError('metadata probe forbids scientific imports')
    if kind == 'subprocess.Popen' or kind == 'os.system' or kind.startswith('socket.') and kind != 'socket.gethostname':
        raise RuntimeError('metadata probe has no process/network action')

sys.addaudithook(audit)
try:
    import psutil
    process = psutil.Process()
    api = Kernel()
    handle = api.check(api.k.OpenJobObjectW(0x0004, False, owner['job_name']))
    assert api.contains(api.k.GetCurrentProcess(), handle)
    class ProcessList(ctypes.Structure):
        _fields_ = [('assigned', wintypes.DWORD), ('listed', wintypes.DWORD),
                    ('pids', ctypes.c_size_t * MAX_PROCESSES)]
    for index in range(6):
        assert time.monotonic() - START < 5
        begin = time.perf_counter()
        row = ProcessList()
        api.check(api.k.QueryInformationJobObject(handle, 3, ctypes.byref(row), ctypes.sizeof(row), None))
        assert 0 < row.listed == row.assigned <= MAX_PROCESSES
        pids = [int(row.pids[i]) for i in range(row.listed)]
        assert len(pids) == len(set(pids)) and process.pid in pids
        members, exited = [], []
        for pid in pids:
            child_handle = api.k.OpenProcess(0x1000, False, pid)
            if not child_handle:
                assert not psutil.pid_exists(pid)
                exited.append(pid)
                continue
            try:
                assert api.contains(child_handle, handle)
                token = api.token(child_handle)
                child = psutil.Process(pid)
                assert abs(child.create_time() - token['create_time']) <= 1e-5
                members.append(dict(pid=pid, create_time=token['create_time'], rss_bytes=int(child.memory_info().rss)))
            except psutil.NoSuchProcess:
                exited.append(pid)
            finally:
                api.close(child_handle)
        descendants = {p.pid for p in process.children(recursive=True)} | {process.pid}
        info = process.memory_info()
        sample = dict(index=index, members=members, exited_during_sample=exited,
            family_rss_bytes=sum(p['rss_bytes'] for p in members),
            worker_highwater_bytes=max(int(info.rss), int(info.peak_wset)),
            available_bytes=int(psutil.virtual_memory().available),
            owned_job_members_outside_worker_descendants=sorted(set(pids) - descendants),
            query_seconds=time.perf_counter() - begin)
        assert sample['family_rss_bytes'] <= 128 * 1024**2
        assert sample['worker_highwater_bytes'] <= 128 * 1024**2
        assert sample['available_bytes'] >= 1024**3
        samples.append(sample)
        if index != 5:
            time.sleep(.03)
except BaseException as caught:
    error = dict(type=type(caught).__name__, message=str(caught))
finally:
    if handle is not None:
        api.close(handle)
        closed = True
    elapsed = time.monotonic() - START
    absent = not any(n.split('.')[0] in ('torch', 'numpy', 'pandas', 'knowledge_tracing', 'modal') for n in sys.modules)
    accepted = error is None and len(samples) == 6 and closed and absent and elapsed < 5
    result = dict(status='ACCEPTED_JOB_QUERY_METADATA_CHILD' if accepted else 'REJECTED_KEEP_ALL',
        error=error, samples=samples, handle_closed=closed, scientific_modules_absent=absent,
        elapsed_seconds=elapsed, cap_seconds=5, new_model_world_calls=0)
    with (OUT / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    timer.cancel()
raise SystemExit(0 if accepted and time.monotonic() - START < 5 else 1)
