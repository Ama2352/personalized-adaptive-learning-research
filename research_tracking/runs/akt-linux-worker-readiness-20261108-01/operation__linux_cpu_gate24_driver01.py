"""OFFLINE Gate24-only: test delta lineage + accepted loader + prior runtime02; review before dispatch.

Không installer/network/GPU training/realdata/fullCV. Gate là software synthetic
suite có các optimizer fixtures sẵn có; KHÔNG tuyên bố zero optimizer của suite.
Không thay validator, source, lock, test selection hoặc timeout native.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path,PurePosixPath
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
MATERIALIZATION=ROOT/'gpu09-worker-kit-materialization-02.json'
BASE_MATERIALIZATION=ROOT/'gpu09-worker-kit-materialization-01.json'
BASE_MATERIALIZATION_SHA='debb7590e8fd1247bcbdf7a479c2ea204b7d8625414c989b0a4bab5c1e831c3b'
PROFILE=ROOT/'post-install-audit01/result.json'
PROFILE_SHA='dd3b18c2ef7fd2f109077395e77a7f7243fd35a0cdc68dd7045f8233de71f966'
LF_SOURCE_FILES={
    'akt.py':'ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67',
    'README.md':'bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b',
    'LICENSE':'50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf',
}
RUNTIME=ROOT/'artifacts/akt/runtime/linux-cpu-20261108-02.json'
RUN_ID='20261108-linux-native-24'
PREFLIGHT=ROOT/'artifacts/akt/preflight'
REPORT=PREFLIGHT/f'gate2-evidence-{RUN_ID}.json'
LOG=PREFLIGHT/f'gate2-tests-{RUN_ID}.log'
XML=PREFLIGHT/f'gate2-tests-{RUN_ID}.xml'
POINTER=PREFLIGHT/'gate2-current.json'
POINTER_BACKUP=PREFLIGHT/f'gate2-pointer-before-{RUN_ID}.json'
MAX_BYTES=20*1024**3
MIN_FREE=30*1024**3

RUNTIME_SHA='31974cac738a28ae6db6b609f75d596b43e993f2e51a2d5c946ed8ed65675cd6'
PRIOR_RUNTIME_RESULT=ROOT/'linux-cpu-validation-runtime-20261108-02/result.json'
PRIOR_RUNTIME_RESULT_SHA='874336b8923c67edb44f638adc740b7928c152683006bb62c0300c3e56a1fc81'
PRIOR_RUNTIME_DRIVER_SHA='105a2388288fc608ac5b8c0b1eb48ee1e877d352ed352189e08fc4c4c86ebba1'
LOADER_SOURCE_SHA='6aff88a7abc9620d6372ee934391d2079bccd253330e7a1e4f0ddcaa436b41b2'
LOADER_SHA='27550ccd07c1131971c4381f024c0f3795dba3d32b7f9fb4eea4ababd8bfe9e8'
LOADER_BLOB='9fafe965e0b442242125250f37dc8c3f8a145edf'
DELTA_SOURCE_SHA='04392264e8b23d9e00b2c4f68f1a4260f0e972cf3a12388f71601292f8d8fafd'
TEST_PATH='tests/akt/test_graph_prototype.py'
OLD_TEST_SHA='5e2aae220d1b862c337951182efab417a3ed81dd5eb6899f84af710a3cfd76ae'
NEW_TEST_SHA='7a198d79b11b0c2e18af8532f26658e7119a2e352299d4bba66f859c16082f04'
PRESERVED={
 'gpu09-worker-kit-materialization-01.json':BASE_MATERIALIZATION_SHA,
 'source-kit-transfer01/exact-linux-cpu-source-kit.zip':'b6707cfd0139898a22dd04db9095d01622c1df9b7061f05f8579ecb4ab30d233',
 'linux-cpu-validation-gate-20261108-02/result.json':'c7cf0a96ca75c32728fcb7d566d0f1fcac22b95ae940d6e37e916645081c6583',
 'linux-cpu-validation-gate-20261108-02/output-manifest.json':'4edfac1ec01d910d92862c527d215400211d0e4f0729cb35904148514afe1224'}

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


def validate_materialization_lineage(material,base,loader_sha,loader_path):
    original=base['manifest']['files']
    if (base.get('status')!='MATERIALIZED_SOURCE_ONLY_NO_EXECUTION' or len(original)!=161
            or original.get(TEST_PATH)!={'bytes':16086,'sha256':OLD_TEST_SHA}):raise ValueError('exact base161 required')
    expected={**original,TEST_PATH:{'bytes':17214,'sha256':NEW_TEST_SHA}}
    delta=material.get('delta',{})
    if (material.get('status')!='MATERIALIZED_SOURCE_DELTA_ONLY_NO_EXECUTION'
            or material.get('base_materialization_receipt_sha256')!=BASE_MATERIALIZATION_SHA
            or material.get('base_archive_sha256')!=base['archive_sha256']
            or material.get('base_archive_contains_delta') is not False or material.get('new_archive_created') is not False
            or material.get('manifest',{}).get('files')!=expected
            or material.get('source_sha256_after')!={n:e['sha256'] for n,e in expected.items()}
            or delta.get('target')!=TEST_PATH or delta.get('old_sha256')!=OLD_TEST_SHA or delta.get('new_sha256')!=NEW_TEST_SHA
            or delta.get('controller_source_sha256')!=DELTA_SOURCE_SHA or delta.get('loader_remediation_sha256')!=loader_sha
            or delta.get('loader_remediation_path')!=loader_path):
        raise ValueError('test-only delta lineage/all161 inventory required')

def validate_delta_result(result,material,material_sha):
    if (result.get('status')!='ACCEPTED_TEST_ONLY_SOURCE_DELTA_NO_EXECUTION'
            or result.get('source_sha256')!=DELTA_SOURCE_SHA or result.get('new_materialization_sha256')!=material_sha
            or result.get('changed_paths')!=[TEST_PATH] or result.get('other160files_unchanged') is not True
            or result.get('inventory_file_count')!=161 or result.get('old_backup_sha256')!=OLD_TEST_SHA
            or result.get('new_target_sha256')!=NEW_TEST_SHA
            or not all(type(result.get(k)) in (int,float) and math.isfinite(result[k]) and 0<=result[k]<=30 for k in ('elapsed_seconds','elapsed_wall_seconds'))):
        raise ValueError('accepted bounded source-delta result required')

def validate_loader_remediation(receipt):
    audit=receipt.get('audit',{})
    if (receipt.get('status')!='MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY'
            or receipt.get('source_sha256')!=LOADER_SOURCE_SHA or receipt.get('source_origin')!='LOCAL_PINNED_GIT_BLOB_TRANSFER'
            or receipt.get('cleanup',{}).get('accepted') is not True or audit.get('source_origin')!='LOCAL_PINNED_GIT_BLOB_TRANSFER'
            or audit.get('loader')!={'path':'load_data.py','sha256':LOADER_SHA,'git_blob_id':LOADER_BLOB,'bytes':6428}
            or audit.get('source_before_after',{}).get('files')!=LF_SOURCE_FILES):
        raise ValueError('actual accepted loader remediation prerequisite required')

def loader_relative_path(value):
    path=PurePosixPath(value)
    if (path.is_absolute() or '..' in path.parts or '\\' in value or ':' in value or path.as_posix()!=value
            or len(path.parts)!=2 or not path.parts[0].startswith('upstream-loader-transfer') or path.name!='result.json'):
        raise ValueError('explicit ROOT-relative loader remediation result path required')
    return path.as_posix()

def validate_reused_runtime(prior,runtime,base,audit_sha):
    if (prior.get('status')!='ACCEPTED_NATIVE_RUNTIME_CPU' or prior.get('runtime_sha256')!=RUNTIME_SHA
            or prior.get('driver_source_sha256')!=PRIOR_RUNTIME_DRIVER_SHA
            or prior.get('upstream_audit_sha256')!=audit_sha or prior.get('cleanup_accepted') is not True
            or prior.get('materialization_sha256')!=BASE_MATERIALIZATION_SHA
            or prior.get('source_sha256_before')!={n:e['sha256'] for n,e in base['manifest']['files'].items()}
            or runtime.get('device')!='cpu' or runtime.get('platform_id')!='linux' or runtime.get('lock_sha256')!=LOCK_SHA
            or runtime.get('source',{}).get('files')!=LF_SOURCE_FILES):raise ValueError('exact accepted prior105a runtime02 binding required')

def preserved_inputs():
    for name,h in PRESERVED.items():
        if sha(read(ROOT/name))!=h:raise ValueError('historical failure/base input drift')
    if sha(read(UPSTREAM/'load_data.py'))!=LOADER_SHA:raise ValueError('actual upstream loader drift')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('gate',),required=True)
    parser.add_argument('--expected-source-sha256',required=True)
    parser.add_argument('--upstream-audit-path',required=True)
    parser.add_argument('--upstream-audit-sha256',required=True)
    parser.add_argument('--upstream-audit-status',required=True)
    parser.add_argument('--materialization-sha256',required=True)
    parser.add_argument('--loader-remediation-sha256',required=True)
    parser.add_argument('--loader-remediation-path',required=True)
    parser.add_argument('--delta-result-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args(argv)
    start=time.monotonic();wall=time.time();cap=630
    directory=ROOT/'linux-cpu-validation-gate-20261108-03'
    result={'status':'FAILED','phase':args.phase,'timeout_seconds':cap,'native_gate_timeout_seconds':600,
            'no_fullCV_or_realdata':True,'no_gpu_model_phase':True,'no_installs_or_network_phase':True,
            'scope':'native full Linux CPU software suite with accepted prior runtime02 reused; not efficacy/CUDA/worker training acceptance'}
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
        if source!=ROOT/'linux_cpu_gate24_driver01.py' or sha(read(source))!=args.expected_source_sha256:
            raise ValueError('reviewed driver source SHA/path required')
        if not args.approval_reference.strip():raise ValueError('dispatch approval reference required')
        if os.environ.get('COLAB_GPU') not in (None,'','0') or os.environ.get('COLAB_TPU_ADDR') or list(Path('/dev').glob('nvidia[0-9]*')):
            raise ValueError('CPU host only')
        material=pinned(MATERIALIZATION,args.materialization_sha256)
        base=pinned(BASE_MATERIALIZATION,BASE_MATERIALIZATION_SHA)
        loader_name=loader_relative_path(args.loader_remediation_path);loader_path=ROOT/loader_name
        validate_materialization_lineage(material,base,args.loader_remediation_sha256,loader_name)
        loader=pinned(loader_path,args.loader_remediation_sha256)
        validate_loader_remediation(loader)
        delta_result=pinned(ROOT/'source-delta01/result.json',args.delta_result_sha256)
        validate_delta_result(delta_result,material,args.materialization_sha256)
        preserved_inputs()
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
                      materialization_sha256=args.materialization_sha256,base_materialization_sha256=BASE_MATERIALIZATION_SHA,profile_sha256=PROFILE_SHA,
                      loader_remediation_sha256=args.loader_remediation_sha256,loader_remediation_path=loader_name,
                      delta_result_sha256=args.delta_result_sha256,
                      source_sha256_before=before,upstream_git_lf_sha256=LF_SOURCE_FILES,lock_file=str(LOCK),lock_sha256=LOCK_SHA)
        runtime_accept=pinned(PRIOR_RUNTIME_RESULT,PRIOR_RUNTIME_RESULT_SHA)
        runtime=pinned(RUNTIME,RUNTIME_SHA)
        validate_reused_runtime(runtime_accept,runtime,base,args.upstream_audit_sha256)
        result.update(runtime_phase_result_sha256=PRIOR_RUNTIME_RESULT_SHA,runtime_sha256=RUNTIME_SHA,
                      accepted_prior_runtime_driver_sha256=PRIOR_RUNTIME_DRIVER_SHA,
                      runtime_reuse_reason='Only one test fixture changed; native3LF/runtime producer/other160 kit files unchanged; no runtime rerun')
        if any(p.exists() or p.is_symlink() for p in (REPORT,LOG,XML,POINTER_BACKUP)):raise FileExistsError('Gate24 outputs exist; STOP')
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
        pinned(MATERIALIZATION,args.materialization_sha256);pinned(BASE_MATERIALIZATION,BASE_MATERIALIZATION_SHA)
        pinned(PROFILE,PROFILE_SHA);pinned(audit_path,args.upstream_audit_sha256)
        validate_loader_remediation(pinned(loader_path,args.loader_remediation_sha256))
        validate_delta_result(pinned(ROOT/'source-delta01/result.json',args.delta_result_sha256),material,args.materialization_sha256)
        validate_reused_runtime(pinned(PRIOR_RUNTIME_RESULT,PRIOR_RUNTIME_RESULT_SHA),pinned(RUNTIME,RUNTIME_SHA),base,args.upstream_audit_sha256)
        preserved_inputs()
        if any(sha(read(UPSTREAM/name))!=digest for name,digest in LF_SOURCE_FILES.items()):
            raise ValueError('actual Git LF source changed during native phase')
        report=json.loads(read(REPORT));pointer=json.loads(read(POINTER))
        counts=report.get('test_result',{})
        if (report.get('status')!='PASS' or report.get('timeout_seconds')!=600 or report.get('lock_sha256')!=LOCK_SHA
                or counts!={'passed':771,'failed':0,'errors':0,'skipped':0}
                or report.get('source',{}).get('files')!=LF_SOURCE_FILES
                or report.get('junit_sha256')!=sha(read(XML,32*1024**2))
                or pointer.get('evidence_sha256')!=sha(read(REPORT)) or pointer.get('test_log_sha256')!=sha(read(LOG,32*1024**2))):
            raise ValueError('native Gate expected771/no-skip result/pointer mismatch; no substitutions')
        # Native publisher already called require_gate2_evidence; retain XML actual counts, not a new validator.
        suites=list(ET.fromstring(read(XML,32*1024**2)).iter('testsuite'))
        if sum(int(row.attrib.get('tests',0)) for row in suites)!=771 or any(sum(int(row.attrib.get(k,0)) for row in suites) for k in ('failures','errors','skipped')):
            raise ValueError('actual JUnit771/no-failure required')
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
