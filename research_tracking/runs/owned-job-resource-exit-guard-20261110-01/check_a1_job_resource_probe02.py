"""Probe ownedJob/Git exit, không mô hình hoặc import thư viện khoa học."""
import time
START = time.perf_counter()
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import threading
import traceback

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP/'a1_job_resource_probe02_packet.json'
OUT = PREP/'a1-job-resource-probe02'
OWNED = PREP/'a1-job-resource-probe02-owned'


def need(ok, message):
    if not ok: raise ValueError(message)


def check():
    need(time.perf_counter()-START < 23., 'probe worker23 deadline')


def sha(path):
    need(path.stat().st_size <= 2**20, 'bounded probe source')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    need(len(raw) <= 2**20, 'small probe receipt')
    with (OUT/name).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def canaries(helper):
    counts = dict(passed=0)
    ticks = 134387324892686944
    def times(handle, creation, *unused):
        creation._obj.dwLowDateTime = ticks & 0xffffffff
        creation._obj.dwHighDateTime = ticks >> 32
        return 1
    def check_result(value):
        if not value: raise PermissionError('synthetic native failure')
        return value
    api = SimpleNamespace(check=check_result, k=SimpleNamespace(GetProcessId=lambda handle:123, GetProcessTimes=times))
    result = helper(api, 1, 123)
    need(result['pid'] == 123 and result['created_filetime_100ns'] == str(ticks), 'creation-only helper without image API')
    counts['passed'] += 1
    for name, candidate, expected, kind in (
        ('wrong_pid', api, 124, ValueError),
        ('bool_pid', api, True, ValueError),
        ('GetProcessId_access_denied', SimpleNamespace(check=check_result,k=SimpleNamespace(GetProcessId=lambda h:0)),123,PermissionError),
        ('GetProcessTimes_access_denied', SimpleNamespace(check=check_result,k=SimpleNamespace(GetProcessId=lambda h:123,GetProcessTimes=lambda *a:0)),123,PermissionError)):
        try: helper(candidate, 1, expected)
        except kind: counts['passed'] += 1
        else: raise ValueError('rejection canary failed '+name)
    need(counts['passed'] == 5, 'five exact source-helper canaries')
    return counts


def main():
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate, Kernel, MAX_PROCESSES
    owner = worker_gate()
    parser = argparse.ArgumentParser(); parser.add_argument('--packet-sha256', required=True); args=parser.parse_args()
    need(sha(PACKET) == args.packet_sha256 and not OUT.exists(), 'reviewed new probe')
    packet = json.loads(PACKET.read_bytes())
    before = {n:sha(ROOT/n) for n in packet['source_pins']}
    need(before == packet['source_pins'], 'actual source pins')
    need(sha(Path(packet['git_executable'])) == packet['git_sha256'], 'actual pinned Git executable')
    OUT.mkdir()
    timer = threading.Timer(max(.001,23.-(time.perf_counter()-START)),lambda:os._exit(124));timer.daemon=True;timer.start()
    blocked={'torch','numpy','pandas','scipy','sklearn','joblib','modal','boto3','knowledge_tracing'}
    calls=[];denied=[];job_handle=None;api=None;handle_closed=False;children=[];error=None;proof=None
    resources=dict(samples=0,peak_family_rss_bytes=0,minimum_available_ram_bytes=None,maximum_job_processes=0)
    command=[packet['git_executable'],'-C',str(ROOT/'artifacts/akt/dependencies/upstream'),'hash-object','--stdin']
    expected_command=subprocess.list2cmdline(command)
    def audit(event, values):
        if event=='import' and str(values[0]).split('.')[0] in blocked:
            denied.append(str(values[0]));raise RuntimeError('no scientific module in probe')
        if event=='subprocess.Popen':
            need(len(calls)<4 and values[0]==packet['git_executable'] and values[1]==expected_command,'only four exact read-only Git commands')
            calls.append(expected_command)
        if event.startswith('socket.') or event=='os.system' or event.startswith('os.spawn'):
            denied.append(event);raise RuntimeError('no network/system')
        if event=='open' and values and isinstance(values[0],(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(values[0])).absolute().resolve()
            if any(path==ROOT/n or path.is_relative_to(ROOT/n) for n in ('dataset','artifacts/bkt_baseline','venv','.wsl','experiments','artifacts/simulator/corpora')):
                denied.append(str(path));raise RuntimeError('no dataset/corpus/native model artifact')
            flags=values[2] if type(values[2])is int else 0;mode=values[1]or''
            if any(c in mode for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR):
                need(path.is_relative_to(OUT) or path.is_relative_to(OWNED/'runtime-temp'),'only own probe writes')
    sys.addaudithook(audit)
    try:
        import psutil
        spec=importlib.util.spec_from_file_location('a1_probe_resource_definitions',ROOT/packet['worker02'])
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        helper=module.resource_identity_from_handle
        pure=canaries(helper)
        api=Kernel();job_handle=api.check(api.k.OpenJobObjectW(0x0004,False,owner['job_name']))
        api.k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];api.k.WaitForSingleObject.restype=wintypes.DWORD
        api.k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];api.k.GetExitCodeProcess.restype=wintypes.BOOL
        class ProcessList(ctypes.Structure):
            _fields_=[('assigned',wintypes.DWORD),('listed',wintypes.DWORD),('pids',ctypes.c_size_t*MAX_PROCESSES)]
        def sample():
            check();row=ProcessList();api.check(api.k.QueryInformationJobObject(job_handle,3,ctypes.byref(row),ctypes.sizeof(row),None))
            need(0<row.assigned==row.listed<=MAX_PROCESSES,'complete Job members')
            total=0
            for i in range(row.listed):
                pid=int(row.pids[i]);handle=api.k.OpenProcess(0x1000,False,pid)
                if not handle:
                    need(not psutil.pid_exists(pid),'live process denied');continue
                try:
                    need(api.contains(handle,job_handle),'same Job')
                    token=helper(api,handle,pid);process=psutil.Process(pid)
                    need(abs(token['create_time']-process.create_time())<=1e-5,'same creation identity')
                    total+=int(process.memory_info().rss)
                except psutil.NoSuchProcess:pass
                finally:api.close(handle)
            free=int(psutil.virtual_memory().available)
            resources['samples']+=1;resources['peak_family_rss_bytes']=max(total,resources['peak_family_rss_bytes'])
            previous=resources['minimum_available_ram_bytes'];resources['minimum_available_ram_bytes']=free if previous is None else min(free,previous)
            resources['maximum_job_processes']=max(int(row.listed),resources['maximum_job_processes'])
            need(total<=512*2**20 and free>=1536*2**20,'probe Job512MiB/free1536MiB')
        sample();records=[]
        environment=dict(os.environ)
        profile=dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_CONFIG_COUNT='3',GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
            GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=(ROOT/'artifacts/akt/dependencies/upstream').as_posix(),
            GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='true',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
        inherited={k:v for k,v in environment.items() if k.startswith(('GIT_','GH_'))}
        need(all(k in ('GIT_PAGER','GH_PAGER') or k in profile and v==profile[k] for k,v in inherited.items()),'no undeclared Git profile')
        for key in ('GIT_PAGER','GH_PAGER'):environment.pop(key,None)
        environment.update(profile)
        for i in range(4):
            check();child=subprocess.Popen(command,executable=packet['git_executable'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment)
            children.append(child);handle=None
            try:
                # Git waits for this exact stdin, so the read-only query handle opens while live.
                handle=api.check(api.k.OpenProcess(0x1000|0x100000,False,child.pid))
                need(api.contains(handle,job_handle),'Git belongs to actual owned Job')
                before_token=helper(api,handle,child.pid);sample()
                old_before=api.token(handle)
                payload=b'owned-job-resource-exit-probe\n'
                stdout,stderr=child.communicate(input=payload,timeout=3.)
                need(child.returncode==0 and stderr==b'' and len(stdout)<=128,'exact Git command returned')
                expected=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
                need(stdout.decode().strip()==expected,'read-only Git fixed input digest')
                wait=int(api.k.WaitForSingleObject(handle,0));need(wait==0,'opened exact Git handle signaled exit')
                exit_code=wintypes.DWORD();api.check(api.k.GetExitCodeProcess(handle,ctypes.byref(exit_code)))
                need(exit_code.value==0,'actual Git exit0')
                after_token=helper(api,handle,child.pid)
                need(after_token==before_token and old_before['created_filetime_100ns']==before_token['created_filetime_100ns'],'creation identity survives known exit')
                old_error=None
                try:api.token(handle)
                except BaseException as caught:
                    old_error=dict(type=type(caught).__name__,message=str(caught),winerror=getattr(caught,'winerror',None),
                        traceback=traceback.format_exc(limit=8),exit_already_proven=wait==0)
                records.append(dict(pid=child.pid,creation=before_token,old_after_exit_error=old_error,
                    resource_identity_after_exit_exact=True,WaitForSingleObject=wait,GetExitCodeProcess=int(exit_code.value)))
            finally:
                if handle is not None:api.close(handle)
            sample()
        need(len(calls)==len(records)==4 and pure['passed']==5,'four actual Git children/five canaries')
        errors=[row['old_after_exit_error'] for row in records if row['old_after_exit_error'] is not None]
        proof=dict(pure_canaries=pure,git_children=records,git_calls=len(calls),new_resource_identity_post_exit_matches=4,
            old_token_after_exit_errors=len(errors),old_WinError5_reproduced=any(e['winerror']==5 for e in errors),
            old_failure_cause_scope='actual held-handle observations; no attribution of the original missing traceback beyond this evidence')
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught),traceback=traceback.format_exc(limit=12))
    finally:
        cleanup_errors=[];popen_handles_closed=0
        timer.cancel();timer.join(timeout=.1)
        if timer.is_alive():cleanup_errors.append(dict(scope='timer',type='TimerStillAlive'))
        for child in children:
            try:
                if child.poll()is None:child.kill();child.communicate(timeout=.5)
            except BaseException as caught:
                cleanup_errors.append(dict(scope='child_reap',pid=child.pid,type=type(caught).__name__,message=str(caught)))
            finally:
                try:child._handle.Close();popen_handles_closed+=1
                except BaseException as caught:
                    cleanup_errors.append(dict(scope='popen_handle',pid=child.pid,type=type(caught).__name__,message=str(caught)))
        try:
            if job_handle is not None:api.close(job_handle);handle_closed=True
        except BaseException as caught:
            cleanup_errors.append(dict(scope='job_query_handle',type=type(caught).__name__,message=str(caught)))
        finally:
            after={n:sha(ROOT/n) for n in packet['source_pins']}
            accepted=error is None and not cleanup_errors and not denied and before==after and handle_closed and not blocked.intersection(sys.modules)
            accepted=accepted and time.perf_counter()-START<23.
            write('result.json',dict(status='RESOURCE_IDENTITY_PROBE_PENDING_OUTER' if accepted else 'REJECTED_PROBE_KEEP_PARTIAL',
                error=error,cleanup_errors=cleanup_errors,proof=proof,source_before=before,source_after=after,denied=denied,resources=resources,
                query_handle_closed=handle_closed,scientific_modules_absent=not blocked.intersection(sys.modules),
                popen_handles_closed=popen_handles_closed,model_calls=0,packet_sha256=args.packet_sha256,elapsed_seconds=time.perf_counter()-START))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    main()
