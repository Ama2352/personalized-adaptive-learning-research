"""OFFLINE: hai phase native Linux CPU; chỉ chạy sau parent review source/pins.

Không installer/network/GPU training/realdata/fullCV. Gate là software synthetic
suite có các optimizer fixtures sẵn có; KHÔNG tuyên bố zero optimizer của suite.
Không thay validator, source, lock, test selection hoặc timeout native.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import stat
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

ROOT=Path('/content/KLTN_GPU08_20261108_01')
TARGET=ROOT/'.venv/bin/python'
UPSTREAM=ROOT/'artifacts/akt/dependencies/upstream'
LOCK=ROOT/'artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt'
LOCK_SHA='60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a'
MATERIALIZATION=ROOT/'gpu09-worker-kit-materialization-01.json'
MATERIALIZATION_SHA='debb7590e8fd1247bcbdf7a479c2ea204b7d8625414c989b0a4bab5c1e831c3b'
PROFILE=ROOT/'post-install-audit01/result.json'
PROFILE_SHA='dd3b18c2ef7fd2f109077395e77a7f7243fd35a0cdc68dd7045f8233de71f966'
LF_SOURCE_FILES={
    'akt.py':'ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67',
    'README.md':'bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b',
    'LICENSE':'50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf',
}
RUNTIME=ROOT/'artifacts/akt/runtime/linux-cpu-20261108-02.json'
RUN_ID='20261108-linux-native-23'
PREFLIGHT=ROOT/'artifacts/akt/preflight'
REPORT=PREFLIGHT/f'gate2-evidence-{RUN_ID}.json'
LOG=PREFLIGHT/f'gate2-tests-{RUN_ID}.log'
XML=PREFLIGHT/f'gate2-tests-{RUN_ID}.xml'
POINTER=PREFLIGHT/'gate2-current.json'
POINTER_BACKUP=PREFLIGHT/f'gate2-pointer-before-{RUN_ID}.json'
MAX_BYTES=20*1024**3
MIN_FREE=30*1024**3

def sha(data):return hashlib.sha256(data).hexdigest()

def read(path,cap=4*1024**2):
    if not path.is_absolute() or not path.is_relative_to(ROOT):raise ValueError('outside owned root')
    for part in (path,*path.parents):
        if part.is_symlink():raise ValueError('symlink source/output path forbidden')
        if part==ROOT:break
    if not stat.S_ISREG(path.stat().st_mode):raise ValueError('regular file required')
    with path.open('rb') as stream:data=stream.read(cap+1)
    if len(data)>cap:raise ValueError('read byte cap')
    return data

def pinned(path,digest):
    data=read(path)
    if sha(data)!=digest:raise ValueError('input SHA mismatch: '+str(path))
    return json.loads(data)

def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def isolated_git_environment(environment):
    # Reject inherited Git routing/config/auth state; all Git transports disabled.
    cleaned={k:v for k,v in environment.items()
             if not k.upper().startswith(('GIT_','GH_','GITHUB_','SSH_'))
             and not any(word in k.upper() for word in ('TOKEN','SECRET','PASSWORD','CREDENTIAL','COOKIE','AUTH','API_KEY','PROXY'))
             and k not in {'LD_PRELOAD','LD_LIBRARY_PATH','CURL_HOME','NETRC','XDG_CONFIG_HOME'}}
    cleaned.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',
                   GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',
                   GIT_CONFIG_COUNT='5',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=UPSTREAM.as_posix(),
                   GIT_CONFIG_KEY_1='core.hooksPath',GIT_CONFIG_VALUE_1=os.devnull,
                   GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false',
                   GIT_CONFIG_KEY_3='credential.helper',GIT_CONFIG_VALUE_3='',
                   GIT_CONFIG_KEY_4='credential.interactive',GIT_CONFIG_VALUE_4='false',PATH='/usr/bin:/bin')
    return cleaned


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('runtime','gate'),required=True)
    parser.add_argument('--expected-source-sha256',required=True)
    parser.add_argument('--upstream-audit-path',required=True)
    parser.add_argument('--upstream-audit-sha256',required=True)
    parser.add_argument('--upstream-audit-status',required=True)
    parser.add_argument('--runtime-result-sha256',default='')
    parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args(argv)
    start=time.monotonic();wall=time.time();cap=60 if args.phase=='runtime' else 630
    directory=ROOT/f'linux-cpu-validation-{args.phase}-20261108-02'
    result={'status':'FAILED','phase':args.phase,'timeout_seconds':cap,'native_gate_timeout_seconds':600,
            'no_fullCV_or_realdata':True,'no_gpu_model_phase':True,'no_installs_or_network_phase':True,
            'scope':'native runtime CLI or full CPU software suite; not efficacy/CUDA/worker training acceptance'}
    process=None;cleaned=False;cleanup_ok=False;peak=0;samples=0
    def check():
        nonlocal peak,samples
        values=(time.monotonic()-start,time.time()-wall)
        if not all(math.isfinite(v) and 0<=v<=cap for v in values):raise TimeoutError('outer elapsed cap')
        if (directory/'CANCEL').exists():raise RuntimeError('owned cancellation')
        logical=allocated=0
        for parent,_,names in os.walk(ROOT,followlinks=False):
            for name in names:
                try:st=os.lstat(Path(parent)/name)
                except FileNotFoundError:continue
                logical+=st.st_size;allocated+=getattr(st,'st_blocks',0)*512
        total=max(logical,allocated);peak=max(peak,total);samples+=1
        if total>MAX_BYTES or shutil.disk_usage(ROOT).free<MIN_FREE:raise OSError('cooperative storage bound')
        monitored=[p for p in directory.iterdir() if p.suffix in ('.stdout','.stderr')]
        monitored += [p for p in (LOG,XML) if p.is_file()]
        if sum(p.stat().st_size for p in monitored)>32*1024**2:
            raise OSError('controller log byte bound')
    def cleanup():
        nonlocal cleaned,cleanup_ok
        if process is None or cleaned:return
        cleaned=True;cleanup_ok=True;pgid=process.pid;rows=[]
        if pgid<=1 or pgid==os.getpgrp():cleanup_ok=False;rows.append({'error':'refuse controller/global group'})
        else:
            for sig in (signal.SIGTERM,signal.SIGKILL):
                try:os.killpg(pgid,sig);rows.append({'signal':sig.name,'sent':True})
                except ProcessLookupError:rows.append({'signal':sig.name,'already_absent':True})
                except OSError as exc:cleanup_ok=False;rows.append({'signal':sig.name,'error':str(exc)})
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:cleanup_ok=False;rows.append({'error':'leader reap timeout'})
        result['owned_group_cleanup']=rows
    # Fail before output mutation for wrong host/root/existing attempt.
    if not (os.name=='posix' and platform.system()=='Linux' and ROOT.is_dir() and ROOT.resolve()==ROOT
            and ROOT.stat().st_uid==os.getuid() and not directory.exists() and not directory.is_symlink()):
        raise ValueError('Linux owned root/new attempt required')
    directory.mkdir(exist_ok=False)
    try:
        source=Path(__file__).absolute()
        if source!=ROOT/'linux_cpu_validation_driver02.py' or sha(read(source))!=args.expected_source_sha256:
            raise ValueError('reviewed driver source SHA/path required')
        if not args.approval_reference.strip():raise ValueError('dispatch approval reference required')
        if os.environ.get('COLAB_GPU') not in (None,'','0') or os.environ.get('COLAB_TPU_ADDR') or list(Path('/dev').glob('nvidia[0-9]*')):
            raise ValueError('CPU host only')
        material=pinned(MATERIALIZATION,MATERIALIZATION_SHA)
        if material['status']!='MATERIALIZED_SOURCE_ONLY_NO_EXECUTION':raise ValueError('source materialization status')
        expected=material['manifest']['files']
        if len(expected)!=161:raise ValueError('full161 payload required')
        def source_inventory():
            current={}
            for name,entry in expected.items():
                data=read(ROOT/name)
                if len(data)!=entry['bytes'] or sha(data)!=entry['sha256']:raise ValueError('exact kit source drift: '+name)
                current[name]=sha(data)
            return current
        before=source_inventory()
        if sha(read(LOCK))!=LOCK_SHA:raise ValueError('canonical Linux lock SHA required')
        profile=pinned(PROFILE,PROFILE_SHA)
        if (profile['status']!='EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY'
                or profile['audit']['package_count']!=44 or profile['cleanup_accepted'] is not True or profile['resource_accepted'] is not True):
            raise ValueError('actual44 CPU profile prerequisite')
        audit_path=ROOT/args.upstream_audit_path
        audit=pinned(audit_path,args.upstream_audit_sha256)
        if audit.get('status')!=args.upstream_audit_status:raise ValueError('accepted LF audit status mismatch')
        if any(sha(read(UPSTREAM/name))!=digest for name,digest in LF_SOURCE_FILES.items()):
            raise ValueError('actual Git LF source profile mismatch')
        result.update(driver_source_sha256=args.expected_source_sha256,approval_reference=args.approval_reference,
                      upstream_audit_path=str(audit_path),upstream_audit_sha256=args.upstream_audit_sha256,
                      materialization_sha256=MATERIALIZATION_SHA,profile_sha256=PROFILE_SHA,
                      source_sha256_before=before,upstream_git_lf_sha256=LF_SOURCE_FILES,lock_file=str(LOCK),lock_sha256=LOCK_SHA)
        if args.phase=='runtime':
            if RUNTIME.exists() or RUNTIME.is_symlink():raise FileExistsError('runtime output exists; STOP')
            command=[str(TARGET),'-B','scripts/akt/check_runtime.py','--upstream',str(UPSTREAM),'--device','cpu',
                     '--lock-file',str(LOCK),'--output',str(RUNTIME)]
        else:
            prior=ROOT/'linux-cpu-validation-runtime-20261108-02/result.json'
            runtime_accept=pinned(prior,args.runtime_result_sha256)
            if (runtime_accept.get('status')!='ACCEPTED_NATIVE_RUNTIME_CPU' or runtime_accept.get('runtime_sha256')!=sha(read(RUNTIME))
                    or runtime_accept.get('upstream_audit_sha256')!=args.upstream_audit_sha256
                    or runtime_accept.get('driver_source_sha256')!=args.expected_source_sha256
                    or runtime_accept.get('cleanup_accepted') is not True):raise ValueError('runtime phase prerequisite')
            result['runtime_phase_result_sha256']=args.runtime_result_sha256
            if any(p.exists() or p.is_symlink() for p in (REPORT,LOG,XML,POINTER_BACKUP)):raise FileExistsError('Gate23 outputs exist; STOP')
            command=[str(TARGET),'-B','scripts/akt/refresh_gate2.py','--run-id',RUN_ID,'--publish-current',
                     '--timeout-seconds','600','--lock-file',str(LOCK)]
        env=os.environ.copy()
        for key in tuple(env):
            if key.startswith(('PIP_','UV_','PYTHON','CONDA_','GIT_CONFIG_')) or key in ('HOME','VIRTUAL_ENV'):env.pop(key,None)
        for name in ('home','tmp','cache'):(directory/name).mkdir()
        env.update(HOME=str(directory/'home'),TMPDIR=str(directory/'tmp'),XDG_CACHE_HOME=str(directory/'cache'),
                   TORCH_HOME=str(directory/'cache'),TRITON_CACHE_DIR=str(directory/'cache'),CUDA_CACHE_PATH=str(directory/'cache'),
                   CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
                   OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PIP_CONFIG_FILE=os.devnull,
                   XDG_CONFIG_HOME=str(directory/'home'))
        env=isolated_git_environment(env)
        env['XDG_CONFIG_HOME']=str(directory/'home')
        result['command']=command
        if POINTER.exists():
            data=read(POINTER);result['pointer_before_sha256']=sha(data)
            with (directory/'pointer-before.json').open('xb') as stream:stream.write(data)
        check()
        with (directory/'native.stdout').open('xb') as stdout,(directory/'native.stderr').open('xb') as stderr:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            result['child_pid']=process.pid
            try:
                while process.poll() is None:
                    check()
                    if time.monotonic()-start>cap-5:raise TimeoutError('reserve owned cleanup within outer cap')
                    try:process.wait(timeout=.25)
                    except subprocess.TimeoutExpired:pass
            finally:cleanup()
        if process.returncode!=0 or not cleanup_ok:raise RuntimeError('native child/owned cleanup failed; retain partial outputs')
        check()
        if before!=source_inventory() or sha(read(source))!=args.expected_source_sha256:raise ValueError('source changed during native phase')
        pinned(MATERIALIZATION,MATERIALIZATION_SHA);pinned(PROFILE,PROFILE_SHA);pinned(audit_path,args.upstream_audit_sha256)
        if any(sha(read(UPSTREAM/name))!=digest for name,digest in LF_SOURCE_FILES.items()):
            raise ValueError('actual Git LF source changed during native phase')
        if args.phase=='runtime':
            runtime=json.loads(read(RUNTIME))
            if (runtime.get('device')!='cpu' or runtime.get('platform_id')!='linux' or runtime.get('lock_sha256')!=LOCK_SHA
                    or runtime.get('source',{}).get('files')!=LF_SOURCE_FILES):
                raise ValueError('native runtime report scope mismatch')
            result.update(status='ACCEPTED_NATIVE_RUNTIME_CPU',runtime_sha256=sha(read(RUNTIME)),runtime=runtime)
        else:
            report=json.loads(read(REPORT));pointer=json.loads(read(POINTER))
            counts=report.get('test_result',{})
            if (report.get('status')!='PASS' or report.get('timeout_seconds')!=600 or report.get('lock_sha256')!=LOCK_SHA
                    or counts!={'passed':768,'failed':0,'errors':0,'skipped':0}
                    or pointer.get('evidence_sha256')!=sha(read(REPORT)) or pointer.get('test_log_sha256')!=sha(read(LOG,32*1024**2))):
                raise ValueError('native Gate expected768/no-skip result/pointer mismatch; no substitutions')
            # Native publisher already called require_gate2_evidence; retain XML actual counts, not a new validator.
            suites=list(ET.fromstring(read(XML,32*1024**2)).iter('testsuite'))
            result.update(status='ACCEPTED_NATIVE_LINUX_CPU_SOFTWARE_GATE',test_result=counts,
                          native_gate_elapsed_seconds=report['elapsed_seconds'],junit_suites=[s.attrib for s in suites])
        check()
    except Exception as exc:
        result.update(status='FAILED_RETAIN_PARTIAL_NO_RETRY',error_type=type(exc).__name__,error=str(exc))
        with (directory/'failure.log').open('x',encoding='utf-8') as stream:stream.write(traceback.format_exc())
    finally:
        cleanup()
        result.update(child_returncode=None if process is None else process.poll(),cleanup_attempted=cleaned,cleanup_accepted=cleanup_ok,
                      peak_observed_workspace_bytes=peak,resource_samples=samples,storage_monitor_is_cooperative=True)
        outputs={}
        for path in (RUNTIME,REPORT,LOG,XML,POINTER,POINTER_BACKUP):
            if path.is_file():
                try:outputs[str(path.relative_to(ROOT))]={'sha256':sha(read(path,32*1024**2)),'bytes':path.stat().st_size}
                except Exception as exc:outputs[str(path.relative_to(ROOT))]={'inventory_error':str(exc)}
        result['native_outputs']=outputs
        inventory={}
        for path in directory.iterdir():
            if path.is_file():
                try:inventory[path.name]={'sha256':sha(read(path,32*1024**2)),'bytes':path.stat().st_size}
                except Exception as exc:inventory[path.name]={'inventory_error':str(exc)}
        result.update(elapsed_seconds=time.monotonic()-start,elapsed_wall_seconds=time.time()-wall)
        if not all(math.isfinite(v) and 0<=v<=cap for v in (result['elapsed_seconds'],result['elapsed_wall_seconds'])):
            result['status']='REJECTED_OUTER_ELAPSED_BOUND'
        write(directory/'result.json',result)
        inventory['result.json']={'sha256':sha(read(directory/'result.json')),'bytes':(directory/'result.json').stat().st_size}
        write(directory/'output-manifest.json',{'status':result['status'],'outputs':inventory,'native_outputs':outputs,
                                               'excludes':'pytest temp/checkpoints/parquet; no binary export'})
        print(json.dumps({'status':result['status'],'phase':args.phase,'elapsed_seconds':result['elapsed_seconds'],
                          'result_sha256':sha(read(directory/'result.json')),'output_manifest_sha256':sha(read(directory/'output-manifest.json'))}))
    return 0 if result['status'].startswith('ACCEPTED_NATIVE_') else 1

if __name__=='__main__':raise SystemExit(main())
