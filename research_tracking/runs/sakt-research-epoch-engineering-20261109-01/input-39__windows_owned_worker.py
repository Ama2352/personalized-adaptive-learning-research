"""Windows .venv worker ownership helper; không là research authorization.

Worker gọi worker_gate trước native/model imports. Chỉ GO sau kiểm membership
của actual worker, kể cả khi .venv redirector đã tạo child trước assign shim.
Job/struct dựa trên wrapper Gate25 đã review; không broad PID/name kill.
"""
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = Path(__file__).resolve()
FORBIDDEN = ('torch', 'numpy', 'pandas', 'knowledge_tracing')
MAX_PROCESSES = 16
META_CAP = 32768


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def norm(value):
    return os.path.normcase(os.path.abspath(str(value)))


def safe(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'absolute path without traversal required')
    need(not ROOT.is_symlink() and not getattr(ROOT, 'is_junction', lambda: False)()
         and ROOT.resolve() == ROOT.absolute(), 'physical ROOT required')
    need(path.is_relative_to(ROOT) and path.resolve().is_relative_to(ROOT.resolve()), 'physical in-project path required')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor = cursor / part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias forbidden')
    return path


def bounded(path, cap):
    path = safe(path)
    need(path.is_file(), 'regular bounded file required')
    with path.open('rb') as handle:
        payload = handle.read(cap + 1)
    need(len(payload) <= cap, 'bounded file exceeded cap')
    return payload


def write(path, value):
    payload = canonical(value) + b'\n'
    need(len(payload) <= META_CAP, 'launch metadata cap')
    with safe(path).open('xb') as handle:
        need(handle.write(payload) == len(payload), 'short metadata write')
        handle.flush()
        os.fsync(handle.fileno())
    return digest(payload)


def entry():
    need(sys.platform == 'win32', 'Windows-only ownership helper')
    expected = safe(ROOT / '.venv/Scripts/python.exe')
    need(norm(sys.executable) == norm(expected) and Path(sys.prefix).resolve() == ROOT / '.venv',
         'exact repository .venv entry and prefix required; base Python launch forbidden')
    need(not (ROOT / '.venv').is_symlink() and not getattr(ROOT / '.venv', 'is_junction', lambda: False)(),
         'physical .venv required')
    return expected


class Kernel:
    def __init__(self):
        need(sys.platform == 'win32', 'Windows kernel API required')
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'GetCurrentProcess': ([], wintypes.HANDLE),
            'GetProcessId': ([wintypes.HANDLE], wintypes.DWORD),
            'OpenProcess': ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            'CloseHandle': ([wintypes.HANDLE], wintypes.BOOL),
            'TerminateProcess': ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            'QueryFullProcessImageNameW': ([wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                           ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            'GetProcessTimes': ([wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)], wintypes.BOOL),
            'IsProcessInJob': ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
            'CreateJobObjectW': ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            'OpenJobObjectW': ([wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            'SetInformationJobObject': ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            'AssignProcessToJobObject': ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            'QueryInformationJobObject': ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                           wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
            'TerminateJobObject': ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.k, name); fn.argtypes = args; fn.restype = result

    def check(self, result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return result

    def token(self, handle):
        creation, exit_time, kernel, user = (wintypes.FILETIME() for _ in range(4))
        self.check(self.k.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                         ctypes.byref(kernel), ctypes.byref(user)))
        ticks = creation.dwLowDateTime | (creation.dwHighDateTime << 32)
        buffer = ctypes.create_unicode_buffer(32768); size = wintypes.DWORD(len(buffer))
        self.check(self.k.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)))
        image = buffer.value
        need(Path(image).is_absolute() and bool(Path(image).drive), 'full image path from owned handle required')
        return dict(pid=int(self.k.GetProcessId(handle)), created_filetime_100ns=str(ticks),
                    create_time=(ticks - 116444736000000000) / 10000000, image=image)

    def open(self, pid):
        # Query, assign-to-job, terminate and synchronize rights on this exact handle.
        return self.check(self.k.OpenProcess(0x1000 | 0x0100 | 0x0001 | 0x100000, False, pid))

    def contains(self, process, job):
        answer = wintypes.BOOL()
        self.check(self.k.IsProcessInJob(process, job, ctypes.byref(answer)))
        return bool(answer.value)

    def close(self, handle):
        self.check(self.k.CloseHandle(handle))


class WindowsJob:
    """Named exclusive kill-on-close Job; only owned handles are assigned."""
    def __init__(self, api, name):
        self.api, self.handle = api, None
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                ('flags', wintypes.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                ('active_limit', wintypes.DWORD), ('affinity', ctypes.c_size_t),
                ('priority', wintypes.DWORD), ('scheduling', wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', IO), ('process_limit', ctypes.c_size_t),
                ('job_limit', ctypes.c_size_t), ('process_peak', ctypes.c_size_t), ('job_peak', ctypes.c_size_t)]
        ctypes.set_last_error(0)
        handle = api.check(api.k.CreateJobObjectW(None, name))
        if ctypes.get_last_error() == 183:
            api.close(handle)
            raise ValueError('job name already exists; no reuse')
        self.handle = handle
        info = Extended(); info.basic.flags = 0x2000 | 0x8
        info.basic.active_limit = MAX_PROCESSES
        try:
            api.check(api.k.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)))
        except BaseException:
            self.close()
            raise

    def assign(self, handle):
        if not self.api.contains(handle, self.handle):
            self.api.check(self.api.k.AssignProcessToJobObject(self.handle, handle))
        need(self.api.contains(handle, self.handle), 'assigned process membership unverified')

    def active(self):
        class Accounting(ctypes.Structure):
            _fields_ = [('user', ctypes.c_longlong), ('kernel', ctypes.c_longlong),
                ('period_user', ctypes.c_longlong), ('period_kernel', ctypes.c_longlong),
                ('faults', wintypes.DWORD), ('total', wintypes.DWORD),
                ('active', wintypes.DWORD), ('terminated', wintypes.DWORD)]
        row = Accounting()
        self.api.check(self.api.k.QueryInformationJobObject(self.handle, 1, ctypes.byref(row), ctypes.sizeof(row), None))
        return int(row.active)

    def terminate(self):
        self.api.check(self.api.k.TerminateJobObject(self.handle, 1))

    def close(self):
        if self.handle is not None:
            handle, self.handle = self.handle, None
            self.api.close(handle)


def validate_ready(value, manifest, token):
    need(type(value) is dict and set(value) == {'schema_version','nonce','worker','parent_pid','entry','prefix',
        'worker_sha256','helper_sha256','argv_sha256','forbidden_imports'}, 'closed ready schema')
    need(type(value['schema_version']) is int and value['schema_version'] == 1
         and value['nonce'] == manifest['nonce'] and value['worker'] == token
         and type(value['parent_pid']) is int and value['parent_pid'] > 0, 'ready nonce/process token mismatch')
    need(norm(value['entry']) == norm(manifest['entry']) and norm(value['prefix']) == norm(ROOT / '.venv')
         and value['worker_sha256'] == manifest['worker_sha256']
         and value['helper_sha256'] == manifest['helper_sha256']
         and value['argv_sha256'] == digest(canonical(manifest['worker_args']))
         and value['forbidden_imports'] == [], 'ready entry/prefix/source/command/preGO imports mismatch')


def provisional_descendant(api, snapshot, parent_lease, allowed, process_lookup):
    """Unknown/recycled handle is closed, never registered or terminated."""
    need(parent_lease is not None and snapshot['parent_pid'] == parent_lease['token']['pid'],
         'provisional descendant has no validated owned parent')
    pid = snapshot['pid']; handle = api.open(pid)
    try:
        token = api.token(handle)
        need(token['pid'] == pid and norm(token['image']) in allowed, 'unexpected descendant handle identity/image')
        need(abs(token['create_time']-snapshot['create_time']) <= .000002,
             'descendant PID creation time changed during handle open')
        live = process_lookup(pid)
        need(live.create_time() == snapshot['create_time'] and live.ppid() == snapshot['parent_pid'],
             'provisional descendant ancestry changed')
        need(api.token(parent_lease['handle']) == parent_lease['token'], 'owned parent handle token changed')
        need(abs(process_lookup(snapshot['parent_pid']).create_time()-parent_lease['token']['create_time']) <= .000002,
             'owned parent PID no longer matches handle')
        return dict(handle=handle,borrowed=False,token=token)
    except BaseException:
        api.close(handle)
        raise


def worker_gate():
    """Worker call BEFORE native imports; no child process is created here."""
    expected = entry()
    manifest_path = safe(os.environ['KLTN_WINDOWS_LAUNCH_MANIFEST'])
    need(manifest_path.name == 'launch.json' and manifest_path.is_relative_to(ROOT / 'artifacts/akt/local-tests'),
         'owned attempt manifest path required')
    manifest = json.loads(bounded(manifest_path, META_CAP))
    nonce = os.environ['KLTN_WINDOWS_LAUNCH_NONCE']
    need(manifest['nonce'] == nonce and len(nonce) == 64, 'launch nonce mismatch')
    need(norm(manifest['entry']) == norm(expected), 'launch interpreter mismatch')
    worker = safe(ROOT / manifest['worker_relative'])
    need(norm(Path(sys.argv[0])) == norm(worker)
         and digest(bounded(worker, 256*1024)) == manifest['worker_sha256']
         and digest(bounded(HELPER_PATH, 256*1024)) == manifest['helper_sha256']
         and sys.argv[1:] == manifest['worker_args'], 'worker/helper/argv binding mismatch')
    forbidden = [n for n in FORBIDDEN if n in sys.modules]
    need(not forbidden, 'native/model imports before owned gate')
    api = Kernel(); current = api.token(api.k.GetCurrentProcess())
    ready = dict(schema_version=1,nonce=nonce,worker=current,parent_pid=os.getppid(),entry=sys.executable,
        prefix=sys.prefix,worker_sha256=manifest['worker_sha256'],helper_sha256=manifest['helper_sha256'],
        argv_sha256=digest(canonical(sys.argv[1:])),forbidden_imports=forbidden)
    ready_sha = write(manifest_path.parent / 'ready.json', ready)
    deadline = manifest['gate_deadline']
    need(type(deadline) in (int,float) and math.isfinite(deadline)
         and 0 < deadline-time.perf_counter() <= 10, 'finite short remaining gate deadline required')
    go_path = manifest_path.parent / 'GO.json'
    while time.perf_counter() < deadline:
        if go_path.exists():
            go = json.loads(bounded(go_path, META_CAP))
            need(go == dict(nonce=nonce,ready_sha256=ready_sha,worker=current,job_name=manifest['job_name']),
                 'GO nonce/source/process binding mismatch')
            handle = api.check(api.k.OpenJobObjectW(0x0004, False, manifest['job_name']))  # JOB_OBJECT_QUERY
            try:
                need(api.contains(api.k.GetCurrentProcess(),handle), 'actual worker not in exact owned Job')
            finally:
                api.close(handle)
            return dict(status='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE',worker=current,
                        parent_owner=manifest['parent'],os_parent_pid=os.getppid(),nonce=nonce,
                        ready_sha256=ready_sha,job_name=manifest['job_name'],preGO_forbidden_imports=[])
        time.sleep(.01)
    raise TimeoutError('worker GO gate deadline; native work never released')


def run_owned(worker_path, worker_args, attempt_dir, *, expected_worker_sha256,
              approval_reference, max_seconds, cleanup_reserve_seconds, max_output_bytes):
    """One launch, no retry; caller still validates scientific outputs/overall budget."""
    start = time.perf_counter(); wall = time.time()
    api = job = process = None
    leases = {}; errors = []; record = dict(status='REJECTED_OWNED_PROCESS_LAUNCH',GO_released=False)
    worker = attempt = None; helper_sha = worker_sha = None
    def remaining_active():
        elapsed = max(time.perf_counter()-start,time.time()-wall)
        need(math.isfinite(elapsed) and elapsed >= 0, 'invalid launch clock')
        left = max_seconds-cleanup_reserve_seconds-elapsed
        if left <= 0:
            raise TimeoutError('active deadline preserves cleanup reserve')
        return left
    try:
        need(type(max_seconds) in (int,float) and math.isfinite(max_seconds) and 0 < max_seconds <= 600
             and type(cleanup_reserve_seconds) in (int,float) and math.isfinite(cleanup_reserve_seconds)
             and 0 < cleanup_reserve_seconds < max_seconds, 'explicit bounded launch/cleanup caps required')
        need(type(max_output_bytes) is int and 0 < max_output_bytes <= 1024**2, 'bounded stdout/stderr cap required')
        need(type(approval_reference) is str and bool(approval_reference.strip()), 'caller review reference required')
        expected = entry()
        worker, attempt = safe(worker_path), safe(attempt_dir)
        need(worker.suffix == '.py' and (worker.is_relative_to(ROOT/'artifacts/akt/local-tests')
             or worker.is_relative_to(ROOT/'scripts/research')), 'local reviewed worker script required')
        need(attempt.is_relative_to(ROOT/'artifacts/akt/local-tests') and not attempt.exists(),
             'exclusive local attempt required')
        need(type(worker_args) is list and all(type(a) is str for a in worker_args), 'exact worker argv strings required')
        worker_sha, helper_sha = digest(bounded(worker,256*1024)), digest(bounded(HELPER_PATH,256*1024))
        need(worker_sha == expected_worker_sha256, 'worker source SHA mismatch')
        import psutil
        remaining_active()
        api = Kernel(); parent = api.token(api.k.GetCurrentProcess())
        nonce = secrets.token_hex(32); job_name = 'KLTN_OWNED_' + nonce
        job = WindowsJob(api,job_name)
        attempt.mkdir(parents=True,exist_ok=False)
        command = [str(expected),'-B',str(worker),*worker_args]
        manifest = dict(schema_version=1,nonce=nonce,parent=parent,entry=str(expected),
            worker_relative=worker.relative_to(ROOT).as_posix(),worker_args=list(worker_args),
            worker_sha256=worker_sha,helper_sha256=helper_sha,job_name=job_name,
            active_deadline=time.perf_counter()+remaining_active(),approval_reference=approval_reference)
        manifest['gate_deadline']=min(manifest['active_deadline'],time.perf_counter()+10)
        write(attempt/'launch.json',manifest)
        env = os.environ.copy()
        for key in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONINSPECT'):
            env.pop(key,None)
        env.update(KLTN_WINDOWS_LAUNCH_MANIFEST=str(attempt/'launch.json'),KLTN_WINDOWS_LAUNCH_NONCE=nonce,
            CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1',
            PYTHONNOUSERSITE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        allowed = {norm(expected),norm(parent['image']),norm(Path(os.environ['SystemRoot'])/'System32/conhost.exe')}
        def lease(pid, borrowed=None, snapshot=None):
            if pid in leases:
                return leases[pid]
            need(len(leases) < MAX_PROCESSES, 'bounded owned process count')
            if borrowed is None:
                need(snapshot is not None and snapshot['pid'] == pid, 'snapshot required before opening descendant')
                value = provisional_descendant(api,snapshot,leases.get(snapshot['parent_pid']),allowed,psutil.Process)
            else:
                token = api.token(borrowed)
                need(token['pid'] == pid and norm(token['image']) in allowed, 'unexpected owned startup process image')
                value = dict(handle=borrowed,borrowed=True,token=token)
            leases[pid] = value
            return value
        def adopt_tree():
            root = psutil.Process(process.pid)
            need(api.token(int(process._handle)) == leases[process.pid]['token'], 'owned root process token changed')
            pending = []
            for child in root.children(recursive=True):
                try:
                    pending.append(dict(pid=child.pid,parent_pid=child.ppid(),create_time=child.create_time()))
                except psutil.NoSuchProcess:
                    continue
            need(len(pending)+1 <= MAX_PROCESSES, 'bounded startup tree')
            for _ in range(MAX_PROCESSES):
                eligible = [row for row in pending if row['parent_pid'] in leases]
                if not eligible: break
                for row in eligible:
                    value = lease(row['pid'],snapshot=row)
                    job.assign(value['handle']);pending.remove(row)
            need(not pending, 'startup tree has unverified ancestry')
        record.update(command=command,parent=parent,approval_reference=approval_reference,job_name=job_name,
                      helper_sha256=helper_sha,worker_sha256=worker_sha)
        with (attempt/'stdout.log').open('xb') as stdout,(attempt/'stderr.log').open('xb') as stderr:
            remaining_active()
            # Detached + redirected stdio; no interactive console is needed for file GO.
            process = subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                                       creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            root_lease = lease(process.pid,int(process._handle))
            job.assign(root_lease['handle'])
            ready_path = attempt/'ready.json'
            while True:
                remaining_active()
                if time.perf_counter() >= manifest['gate_deadline']:
                    raise TimeoutError('short startup gate deadline')
                adopt_tree()
                if ready_path.exists():
                    try:
                        ready_bytes = bounded(ready_path,META_CAP); ready = json.loads(ready_bytes)
                    except json.JSONDecodeError:
                        ready = None
                    if ready is not None:
                        break
                need(process.poll() is None, 'worker exited before owned gate')
                time.sleep(.01)
            actual_pid = ready['worker']['pid']
            need(type(actual_pid) is int and actual_pid in leases, 'ready PID not in validated owned tree')
            actual = leases[actual_pid]
            validate_ready(ready,manifest,actual['token'])
            need(norm(actual['token']['image']) == norm(parent['image']), 'actual worker interpreter image mismatch')
            if actual['token']['pid'] == process.pid:
                need(ready['parent_pid'] == parent['pid'], 'direct worker parent mismatch')
            else:
                need(ready['parent_pid'] == process.pid
                     and psutil.Process(process.pid).ppid() == parent['pid']
                     and norm(root_lease['token']['image']) == norm(expected), 'exact .venv shim chain mismatch')
            job.assign(actual['handle']); adopt_tree()
            need(all(api.contains(row['handle'],job.handle) for row in leases.values()), 'owned membership not verified before GO')
            remaining_active()
            need(time.perf_counter()<manifest['gate_deadline'], 'gate deadline before GO')
            record.update(actual_worker=actual['token'],popen=root_lease['token'],
                preGO_owned_tokens=[row['token'] for row in leases.values()],actual_worker_in_job_before_GO=True)
            write(attempt/'GO.json',dict(nonce=nonce,ready_sha256=digest(ready_bytes),worker=actual['token'],job_name=job_name))
            record['GO_released'] = True
            samples=[]
            while process.poll() is None:
                left=remaining_active()
                need(all((attempt/name).stat().st_size <= max_output_bytes for name in ('stdout.log','stderr.log')),
                     'worker output cap')
                samples.append(job.active());need(len(samples)<=16384,'bounded Job samples')
                try:process.wait(timeout=min(.05,left))
                except subprocess.TimeoutExpired:pass
            record.update(worker_returncode_before_cleanup=process.returncode,active_process_samples=samples,
                          job_active_before_cleanup=job.active())
            remaining_active()
    except Exception as error:
        errors.append(dict(stage='launch_or_run',type=type(error).__name__,message=str(error)))
    finally:
        cleanup_errors=[]
        if job is not None:
            # Discover held startup children even when initial Job assignment failed.
            if process is not None and process.poll() is None and 'adopt_tree' in locals():
                try:adopt_tree()
                except Exception as error:cleanup_errors.append('startup_tree:'+type(error).__name__)
            try:job.terminate()
            except Exception as error:cleanup_errors.append('terminate_job:'+type(error).__name__)
            # Owned opened handles cover pre-existing children even on assignment failure.
            for row in leases.values():
                try:
                    if not api.contains(row['handle'],job.handle):
                        api.check(api.k.TerminateProcess(row['handle'],1))
                except Exception as error:cleanup_errors.append('unassigned_owned_handle:'+type(error).__name__)
            if process is not None:
                try:process.wait(timeout=max(.001,max_seconds-(time.perf_counter()-start)-.05))
                except Exception as error:cleanup_errors.append('reap:'+type(error).__name__)
            try:
                while job.active() and time.perf_counter()-start < max_seconds-.05:
                    time.sleep(.01)
                record['job_active_after_cleanup']=job.active()
                if record['job_active_after_cleanup']!=0:cleanup_errors.append('owned_job_not_empty')
            except Exception as error:cleanup_errors.append('query_job:'+type(error).__name__)
            try:job.close()
            except Exception as error:cleanup_errors.append('close_job:'+type(error).__name__)
        for row in leases.values():
            if not row['borrowed']:
                try:api.close(row['handle'])
                except Exception as error:cleanup_errors.append('close_process_handle:'+type(error).__name__)
        if process is not None:
            try:
                if process.returncode is None:
                    process.terminate()  # Exact created handle only; never an opened unknown PID.
                    process.wait(timeout=max(.001,max_seconds-(time.perf_counter()-start)))
                process._handle.Close()
                record['popen_handle_closed']=True
            except Exception as error:cleanup_errors.append('close_or_reap_popen:'+type(error).__name__)
        record.update(cleanup_errors=cleanup_errors,cleanup_accepted=not cleanup_errors
            and (process is None or process.returncode is not None) and record.get('job_active_after_cleanup',0)==0,
            observed_owned_tokens=[row['token'] for row in leases.values()])
    if worker is not None and helper_sha is not None:
        try:
            need(digest(bounded(worker,256*1024))==worker_sha and digest(bounded(HELPER_PATH,256*1024))==helper_sha,
                 'worker/helper source changed')
            if attempt is not None and attempt.exists():
                record['output_sha256'] = {name:digest(bounded(attempt/name,max_output_bytes))
                    for name in ('stdout.log','stderr.log') if (attempt/name).exists()}
        except Exception as error:errors.append(dict(stage='posthash',type=type(error).__name__,message=str(error)))
    elapsed=max(time.perf_counter()-start,time.time()-wall)
    within=type(max_seconds) in (int,float) and math.isfinite(max_seconds) and 0<=elapsed<=max_seconds
    accepted=not errors and record['cleanup_accepted'] and record.get('worker_returncode_before_cleanup')==0 and within
    record.update(status='ACCEPTED_OWNED_PROCESS_LAUNCH_NOT_SCIENTIFIC_ACCEPTANCE' if accepted else 'REJECTED_OWNED_PROCESS_LAUNCH',
        accepted=accepted,errors=errors,elapsed_seconds=elapsed,max_seconds=max_seconds,
        cleanup_reserve_seconds=cleanup_reserve_seconds,returncode=None if process is None else process.returncode,
        automatic_retry=False,elapsed_scope='call through cleanup/posthash; caller must check final total after persisting/reading its outputs')
    return record
