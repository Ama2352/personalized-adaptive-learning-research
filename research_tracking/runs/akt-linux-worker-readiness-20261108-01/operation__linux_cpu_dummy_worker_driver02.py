"""OFFLINE v02 CPU dummy lifecycle; Gate24 required, preparation grants no execution.

Chỉ dispatch từng phase sau parent review. Không sửa native source/protocol,
không dùng default data paths, realdata, GPU, cloud hoặc research fullCV.
"""
import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import runpy
import shutil
import signal
import stat
import subprocess
import sys
import time
import traceback

ROOT=Path('/content/KLTN_GPU08_20261108_01')
TARGET=ROOT/'.venv/bin/python'
VALIDATOR=ROOT/'linux_cpu_validation_driver02.py'
VALIDATOR_SHA='105a2388288fc608ac5b8c0b1eb48ee1e877d352ed352189e08fc4c4c86ebba1'
DATASET='ctx-linux-20261108-01'
DATA=ROOT/'artifacts/akt/synthetic'/DATASET
OUTPUT=ROOT/'experiments/akt/results'/DATASET
PREP=ROOT/'linux-cpu-dummy-preparation-20261108-01'
EXEC=ROOT/'linux-cpu-dummy-execution-20261108-01'
RUNTIME=ROOT/'artifacts/akt/runtime/linux-cpu-20261108-02.json'
RUNTIME_SHA='31974cac738a28ae6db6b609f75d596b43e993f2e51a2d5c946ed8ed65675cd6'
ALIAS=ROOT/'artifacts/akt/preflight/runtime-linux-cpu-20261108-02.json'
GATE_STAGE=ROOT/'linux-cpu-validation-gate-20261108-03'
GATE_HELPER=ROOT/'linux_cpu_gate24_driver01.py'
GATE_HELPER_SHA='3c4cb7c17fcbe6618d4c51a870e9ade03b2461e1d9e429f2837e9dfb2c717e25'
MATERIAL=ROOT/'gpu09-worker-kit-materialization-02.json'
LOADER_PATH='upstream-loader-transfer03/result.json'
LOADER_RESULT_SHA='f500a58833c4b3b7f330a565d48eb606de02786a268a14ae488972525016ff24'
TMP_RUN=ROOT/'artifacts/akt/tmp'/DATASET
POINTER=ROOT/'artifacts/akt/preflight/gate2-current.json'
CAPS={'max_train_users':8,'max_val_users':4,'max_targets_per_side':64,'max_steps':2,
      'max_seconds':120,'max_wall_seconds':300,'max_rss_bytes':2*1024**3,'min_available_ram_bytes':1024**3}
PINS={
    'gpu09-worker-kit-materialization-01.json':'debb7590e8fd1247bcbdf7a479c2ea204b7d8625414c989b0a4bab5c1e831c3b',
    'post-install-audit01/result.json':'dd3b18c2ef7fd2f109077395e77a7f7243fd35a0cdc68dd7045f8233de71f966',
    'post-checkout-audit01/result.json':'1f116d3db2c88d2815bee73cb4471e56f6f442b744c4cd29cede7ce2a43cf952',
    'linux-cpu-validation-runtime-20261108-02/result.json':'874336b8923c67edb44f638adc740b7928c152683006bb62c0300c3e56a1fc81',
    'linux-cpu-validation-runtime-20261108-02/output-manifest.json':'05630c55c7821c77d95b47911c26317450a481642b450657c6cb325dcd6a88af',
    'upstream-loader-transfer03/result.json':LOADER_RESULT_SHA,
}
def sha(data):return hashlib.sha256(data).hexdigest()
def validate_sha(value):
    if not isinstance(value,str) or re.fullmatch('[a-f0-9]{64}',value) is None:raise ValueError('exact64hex SHA required')
    return value
def write(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def execution_config(prepared):
    """Pure guard: chỉ flip execution flag trên exact native dummy recipe."""
    expected={**CAPS,'phase':'smoke','device':'cpu','graph':False,'n_pid':0,'d_model':32,'heads':4,
              'blocks':1,'d_ff':64,'final_fc':32,'dropout':0.0,'batch_size':4,'max_epochs':1,
              'context':100,'target_block':100,'max_length':200,'run_id':DATASET,'partition':'development',
              'project_root':'.','output_dir':'experiments/akt/results/'+DATASET,
              'source_root':'artifacts/akt/dependencies/upstream','execution_enabled':False,'recovery':None,'max_total_targets':128}
    if not isinstance(prepared,dict):raise ValueError('native prepared config required')
    for key,value in expected.items():
        if prepared.get(key)!=value or type(prepared.get(key)) is not type(value):raise ValueError('dummy config mismatch: '+key)
    result=json.loads(json.dumps(prepared));result['execution_enabled']=True
    return result

def exclusive_alias_copy(source,destination,expected_sha,reader):
    """Hash actual copied payload; không sửa nguồn hoặc overwrite alias."""
    if destination.exists() or destination.is_symlink():raise FileExistsError('runtime alias exists; STOP')
    for parent in destination.parents:
        if parent.is_symlink():raise ValueError('runtime alias ancestor symlink')
    validate_sha(expected_sha)
    raw=reader(source)
    if sha(raw)!=expected_sha:raise ValueError('runtime original SHA mismatch')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as stream:stream.write(raw)
    after=reader(destination)
    if sha(after)!=expected_sha or reader(source)!=raw:raise ValueError('runtime source/destination drift')
    return {'source':str(source),'destination':str(destination),'bytes':len(raw),
            'source_sha256_before':expected_sha,'source_sha256_after':sha(reader(source)),
            'destination_sha256_after':sha(after),'content_changed':False}

def context_command(phase,config,authorization,context,context_sha):
    if phase not in ('preflight','smoke') or context is None or config is None:
        raise ValueError('explicit supported phase/context SHA required')
    validate_sha(context_sha)
    command=[str(TARGET),'-B','-m','knowledge_tracing.akt.cli',phase,'--config',str(config),
             '--context-file',str(context),'--context-sha256',context_sha]
    if phase=='smoke':
        if authorization is None:raise ValueError('explicit authorization required')
        command+=['--authorization',str(authorization)]
    return command

def validate_completion(manifest,resources,binding,context_sha,public_pid):
    summary=manifest.get('summary',{});training=summary.get('training',{});coverage=summary.get('coverage',{})
    # Native smoke replaces approval identity with loaded data/context identity.
    # Gate hashes are retained under gate_records, while source inventory and the
    # native Gate reader independently bind build_hashes before/after execution.
    gate_keys={'gate2_report_sha256':'report_sha256','gate2_test_log_sha256':'test_log_sha256','gate2_pointer_sha256':'pointer_sha256'}
    authorization_only={'build_hashes',*gate_keys}
    native_identity={k:v for k,v in binding['identity'].items() if k not in authorization_only}
    gate=manifest.get('gate_records',{}).get('gate2',{})
    if gate.get('status')!='PASS':raise ValueError('native Gate record required')
    for key,field in gate_keys.items():
        validate_sha(binding['identity'].get(key))
        if gate.get(field)!=binding['identity'][key]:raise ValueError('native Gate record digest mismatch')
    if (manifest.get('status')!='completed' or manifest.get('phase')!='smoke' or manifest.get('run_id')!=DATASET
            or manifest.get('approved_caps')!=CAPS or manifest.get('authorized_config_sha256')!=binding['config_sha256']
            or any(manifest.get('identity',{}).get(k)!=v for k,v in native_identity.items())
            or manifest.get('identity',{}).get('worker_context_sha256')!=context_sha
            or training.get('optimizer_steps')!=2 or training.get('valid_targets')!=48
            or training.get('nonzero_gradient_steps')!=2 or training.get('parameter_update_steps')!=2
            or coverage.get('prediction_rows')!=8 or coverage.get('expected_rows')!=8
            or summary.get('checkpoint_reload_state_exact') is not True
            or summary.get('outer_users_requested') is not False or summary.get('holdout_requested') is not False):
        raise ValueError('completed genuine2update/48train/8validation/context identity required')
    pid=resources.get('worker_pid');events=resources.get('parent_events',[])
    if (resources.get('status')!='completed' or resources.get('worker_returncode')!=0
            or resources.get('phase')!='smoke' or resources.get('run_id')!=DATASET
            or type(pid) is not int or pid<=1 or pid==public_pid
            or not any(e.get('event')=='watchdog-after-worker-spawn' and e.get('pid')==public_pid and e.get('worker_pid')==pid for e in events)
            or not all(type(resources.get(k)) in (int,float) and math.isfinite(resources[k]) and 0<=resources[k]<=300 for k in ('elapsed_seconds',))):
        raise ValueError('public watchdog ancestry/completion/wall bound required')

BIND_CHILD=r'''
import hashlib,json,sys
from pathlib import Path
root=Path('/content/KLTN_GPU08_20261108_01');sys.path.insert(0,str(root/'src'))
from knowledge_tracing.akt.config import load_config
from knowledge_tracing.akt.context import load_worker_context,context_authorization_identity
from knowledge_tracing.akt.authorization import config_hash,require_authorization
prep=root/'linux-cpu-dummy-preparation-20261108-01';execution=root/'linux-cpu-dummy-execution-20261108-01'
data=root/'artifacts/akt/synthetic/ctx-linux-20261108-01'
def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def w(path,value):
 with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write(chr(10))
config_path=prep/'execution-config.json';context_path=data/'worker-context.json'
config=load_config(config_path);context=load_worker_context(context_path,expected_sha256=CONTEXT_SHA)
context.validate_for(config);identity=context_authorization_identity(config,context)
caps={name:getattr(config,name) for name in CAPS_NAMES}
if MODE=='prepare':
 authorization={'approved':False,'scope':'development-inner-only','phase':'smoke','run_id':config.run_id,
  'source_commit':config.source_commit,'config_sha256':config_hash(config),'identity':identity,'caps':caps,
  'approval_reference':'PENDING_PARENT_REVIEW; preparation does not authorize execution'}
 w(prep/'proposed-authorization.json',authorization)
else:
 proposal=json.loads((prep/'proposed-authorization.json').read_text())
 assert proposal['approved'] is False and proposal['identity']==identity and proposal['config_sha256']==config_hash(config)
 authorization={**proposal,'approved':True,'approval_reference':EXECUTION_REFERENCE}
 require_authorization(config,authorization,identity_fn=lambda cfg:context_authorization_identity(cfg,context))
 w(execution/'authorization.json',authorization)
print(json.dumps({'identity':identity,'context_sha256':h(context_path),'config_sha256':config_hash(config),
 'execution_config_file_sha256':h(config_path),'caps':caps,'model_execution':False,'mode':MODE}))
'''

def binding_child_code(phase,context_sha,execution_reference):
    if phase not in ('prepare','execute'):raise ValueError('explicit binding phase required')
    validate_sha(context_sha)
    # Inject the free-form reference LAST; MODE replacement must not touch MODEL
    # or MODE words inside a legitimate human approval reference.
    code=(BIND_CHILD.replace('CAPS_NAMES',repr(tuple(CAPS))).replace('CONTEXT_SHA',repr(context_sha))
          .replace('MODE',repr(phase)).replace('EXECUTION_REFERENCE',repr(execution_reference)))
    ast.parse(code)
    return code

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('prepare','execute'),required=True)
    parser.add_argument('--expected-source-sha256',required=True)
    parser.add_argument('--gate-result-sha256',required=True)
    parser.add_argument('--gate-manifest-sha256',required=True)
    parser.add_argument('--materialization-sha256',required=True)
    parser.add_argument('--delta-result-sha256',required=True)
    parser.add_argument('--preparation-result-sha256',default='')
    parser.add_argument('--approval-reference',required=True)
    parser.add_argument('--execution-approval-reference',default='')
    args=parser.parse_args(argv)
    for value in (*PINS.values(),VALIDATOR_SHA,GATE_HELPER_SHA,RUNTIME_SHA,LOADER_RESULT_SHA):validate_sha(value)
    for value in (args.expected_source_sha256,args.gate_result_sha256,args.gate_manifest_sha256,args.materialization_sha256,args.delta_result_sha256):validate_sha(value)
    if args.phase=='execute':validate_sha(args.preparation_result_sha256)
    directory=PREP if args.phase=='prepare' else EXEC
    if not (os.name=='posix' and platform.system()=='Linux' and ROOT.is_dir() and ROOT.resolve()==ROOT
            and ROOT.stat().st_uid==os.getuid() and not directory.exists() and not directory.is_symlink()):
        raise ValueError('owned Linux root/new attempt required')
    start=time.monotonic();wall=time.time();cap=90 if args.phase=='prepare' else 330
    directory.mkdir(exist_ok=False)
    result={'status':'FAILED','phase':args.phase,'timeout_seconds':cap,'children':[],
            'role':'CPU dummy engineering only; no research fitted/realdata/GPU/fullCV/paid approval'}
    peak=0;source=Path(__file__).absolute()
    def read(path,limit=4*1024**2):
        if not path.is_absolute() or not path.is_relative_to(ROOT):raise ValueError('outside owned root')
        for part in (path,*path.parents):
            if part.is_symlink():raise ValueError('symlink forbidden')
            if part==ROOT:break
        if not stat.S_ISREG(path.stat().st_mode):raise ValueError('regular file required')
        with path.open('rb') as stream:raw=stream.read(limit+1)
        if len(raw)>limit:raise ValueError('bounded file read')
        return raw
    def pin(path,digest):
        raw=read(path)
        if sha(raw)!=digest:raise ValueError('pin mismatch: '+str(path))
        return json.loads(raw)
    def check():
        nonlocal peak
        if not all(math.isfinite(v) and 0<=v<=cap for v in (time.monotonic()-start,time.time()-wall)):raise TimeoutError('outer phase cap')
        if (directory/'CANCEL').exists():raise RuntimeError('cancelled')
        logical=allocated=0
        for parent,_,names in os.walk(ROOT,followlinks=False):
            for name in names:
                try:st=os.lstat(Path(parent)/name)
                except FileNotFoundError:continue
                logical+=st.st_size;allocated+=getattr(st,'st_blocks',0)*512
        peak=max(peak,logical,allocated)
        if peak>20*1024**3 or shutil.disk_usage(ROOT).free<30*1024**3:raise OSError('cooperative storage bound')
        if sum(p.stat().st_size for p in directory.iterdir() if p.suffix in ('.stdout','.stderr'))>32*1024**2:raise OSError('log cap')
    def run(name,command,env):
        check();entry={'name':name,'command':command};result['children'].append(entry)
        process=None;cleanup=[];cleanup_ok=True
        with (directory/(name+'.stdout')).open('xb') as stdout,(directory/(name+'.stderr')).open('xb') as stderr:
            try:
                process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
                entry['pid']=process.pid
                while process.poll() is None:
                    check()
                    if time.monotonic()-start>cap-5:raise TimeoutError('reserve owned cleanup within outer cap')
                    try:process.wait(timeout=.25)
                    except subprocess.TimeoutExpired:pass
            finally:
                if process is not None:
                    if process.pid<=1 or process.pid==os.getpgrp():cleanup_ok=False;cleanup.append({'error':'refuse global/controller group'})
                    else:
                        for sig in (signal.SIGTERM,signal.SIGKILL):
                            try:os.killpg(process.pid,sig);cleanup.append({'signal':sig.name,'sent':True})
                            except ProcessLookupError:cleanup.append({'signal':sig.name,'already_absent':True})
                            except OSError as exc:cleanup_ok=False;cleanup.append({'signal':sig.name,'error':str(exc)})
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:cleanup_ok=False
                    entry.update(returncode=process.poll(),owned_group_cleanup=cleanup,cleanup_accepted=cleanup_ok)
        if process is None or process.returncode!=0 or not cleanup_ok:raise RuntimeError(name+' failed/cleanup unverified')
        check();return read(directory/(name+'.stdout'))
    try:
        if source!=ROOT/'linux_cpu_dummy_worker_driver02.py' or sha(read(source))!=args.expected_source_sha256:raise ValueError('reviewed helper source required')
        if not args.approval_reference.strip():raise ValueError('preparation/engineering reference required')
        if args.phase=='execute' and not args.execution_approval_reference.strip():raise PermissionError('separate parent-reviewed execution reference required')
        if os.environ.get('COLAB_GPU') not in (None,'','0') or os.environ.get('COLAB_TPU_ADDR') or list(Path('/dev').glob('nvidia[0-9]*')):
            raise ValueError('CPU host only')
        proofs={name:pin(ROOT/name,digest) for name,digest in PINS.items()}
        base=proofs['gpu09-worker-kit-materialization-01.json']
        if sha(read(GATE_HELPER))!=GATE_HELPER_SHA:raise ValueError('reviewed Gate24 helper source required')
        gate_helper=runpy.run_path(str(GATE_HELPER)) # Definitions only; no main/Gate run.
        material=pin(MATERIAL,args.materialization_sha256)
        loader=proofs[LOADER_PATH];gate_helper['validate_loader_remediation'](loader)
        gate_helper['validate_materialization_lineage'](material,base,LOADER_RESULT_SHA,LOADER_PATH)
        gate_helper['validate_delta_result'](pin(ROOT/'source-delta01/result.json',args.delta_result_sha256),material,args.materialization_sha256)
        gate_helper['validate_reused_runtime'](proofs['linux-cpu-validation-runtime-20261108-02/result.json'],json.loads(read(RUNTIME)),base,PINS['post-checkout-audit01/result.json'])
        expected=material['manifest']['files']
        if len(expected)!=161:raise ValueError('full161 materialized delta inventory required')
        def sources():
            rows={}
            for name,entry in expected.items():
                raw=read(ROOT/name)
                if len(raw)!=entry['bytes'] or sha(raw)!=entry['sha256']:raise ValueError('kit drift: '+name)
                rows[name]=sha(raw)
            return rows
        before=sources()
        if sha(read(VALIDATOR))!=VALIDATOR_SHA:raise ValueError('actual helper02 source pin')
        helper=runpy.run_path(str(VALIDATOR))  # Verified stdlib definitions; no main/operation execution.
        for name,digest in helper['LF_SOURCE_FILES'].items():
            if sha(read(helper['UPSTREAM']/name))!=digest:raise ValueError('actual Git LF profile mismatch')
        gate=pin(GATE_STAGE/'result.json',args.gate_result_sha256)
        gate_manifest=pin(GATE_STAGE/'output-manifest.json',args.gate_manifest_sha256)
        if (gate['status']!='ACCEPTED_NATIVE_LINUX_CPU_SOFTWARE_GATE' or gate_manifest['status']!=gate['status']
                or gate['cleanup_accepted'] is not True or gate['child_returncode']!=0
                or gate['test_result']!={'passed':771,'failed':0,'errors':0,'skipped':0}
                or gate['driver_source_sha256']!=GATE_HELPER_SHA or gate['materialization_sha256']!=args.materialization_sha256
                or gate['delta_result_sha256']!=args.delta_result_sha256 or gate['loader_remediation_sha256']!=LOADER_RESULT_SHA):raise ValueError('actual Gate23 prerequisite')
        for name,row in gate_manifest['native_outputs'].items():
            if name not in {str(p.relative_to(ROOT)) for p in (gate_helper['RUNTIME'],gate_helper['REPORT'],gate_helper['LOG'],gate_helper['XML'],gate_helper['POINTER'],gate_helper['POINTER_BACKUP'])}:
                raise ValueError('unexpected native Gate output path')
            raw=read(ROOT/name,32*1024**2)
            if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise ValueError('Gate native output drift')
        if sha(read(RUNTIME))!=RUNTIME_SHA:raise ValueError('actual runtime02 bytes required')
        result.update(source_sha256=args.expected_source_sha256,source_sha256_before=before,gate_result_sha256=args.gate_result_sha256,
                      gate_manifest_sha256=args.gate_manifest_sha256,helper02_sha256=VALIDATOR_SHA,proof_sha256=PINS,
                      runtime_original_sha256=RUNTIME_SHA,approval_reference=args.approval_reference,materialization_sha256=args.materialization_sha256,delta_result_sha256=args.delta_result_sha256,gate_helper_sha256=GATE_HELPER_SHA)
        env={k:v for k,v in os.environ.items() if not k.startswith(('PYTHON','PIP_','UV_','CONDA_')) and k not in ('HOME','VIRTUAL_ENV')}
        for name in ('home','tmp','cache'):(directory/name).mkdir()
        env.update(HOME=str(directory/'home'),TMPDIR=str(directory/'tmp'),XDG_CACHE_HOME=str(directory/'cache'),
                   TORCH_HOME=str(directory/'cache'),TRITON_CACHE_DIR=str(directory/'cache'),CUDA_CACHE_PATH=str(directory/'cache'),
                   CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
                   OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PIP_CONFIG_FILE=os.devnull,
                   PYTHONPATH=str(ROOT/'src'))
        env=helper['isolated_git_environment'](env);env['XDG_CONFIG_HOME']=str(directory/'home')
        if args.phase=='prepare':
            if DATA.exists() or OUTPUT.exists() or TMP_RUN.exists() or any(p.is_symlink() for p in (DATA,OUTPUT,TMP_RUN)):raise FileExistsError('new dummy dataset/output/temp required')
            copy=exclusive_alias_copy(RUNTIME,ALIAS,RUNTIME_SHA,read);write(PREP/'runtime-alias-copy.json',copy)
            command=[str(TARGET),'-B','scripts/akt/prepare_synthetic_context.py','--dataset-id',DATASET,'--mode','smoke',
                     '--runtime-report',ALIAS.relative_to(ROOT).as_posix(),'--lock-file',helper['LOCK'].relative_to(ROOT).as_posix(),
                     '--gate2-report',POINTER.relative_to(ROOT).as_posix()]
            run('native-builder',command,env)
            inventory=json.loads(read(DATA/'preparation-inventory.json'))
            for name,digest in inventory['outputs_sha256'].items():
                if sha(read(ROOT/name))!=digest:raise ValueError('builder output SHA mismatch')
            config=execution_config(json.loads(read(DATA/'config.json')));write(PREP/'execution-config.json',config)
        else:
            preparation=pin(PREP/'result.json',args.preparation_result_sha256)
            if (preparation['status']!='PREPARED_CPU_DUMMY_NOT_EXECUTION_AUTHORIZED'
                    or preparation['source_sha256']!=args.expected_source_sha256 or preparation['gate_result_sha256']!=args.gate_result_sha256
                    or preparation['gate_manifest_sha256']!=args.gate_manifest_sha256 or preparation['materialization_sha256']!=args.materialization_sha256
                    or preparation['delta_result_sha256']!=args.delta_result_sha256):
                raise ValueError('matching reviewed preparation receipt required')
            if OUTPUT.exists() or TMP_RUN.exists() or OUTPUT.is_symlink() or TMP_RUN.is_symlink():raise FileExistsError('dummy output/temp exists; no rerun')
            for name,digest in preparation['prepared_files_sha256'].items():
                if sha(read(ROOT/name))!=digest:raise ValueError('reviewed preparation changed')
            result['preparation_result_sha256']=args.preparation_result_sha256
        context_path=DATA/'worker-context.json';context_sha=sha(read(context_path))
        child=binding_child_code(args.phase,context_sha,args.execution_approval_reference)
        child_path=directory/'bind-child.py'
        with child_path.open('x',encoding='utf-8') as stream:stream.write(child)
        binding=json.loads(run('native-bindings',[str(TARGET),'-B',str(child_path)],env))
        result['bindings']=binding
        if args.phase=='prepare':
            run('native-preflight',context_command('preflight',PREP/'execution-config.json',None,context_path,context_sha),env)
            inventory=json.loads(read(DATA/'preparation-inventory.json'))
            paths=[ROOT/name for name in inventory['outputs_sha256']]+[DATA/'preparation-inventory.json',PREP/'execution-config.json',PREP/'proposed-authorization.json',PREP/'runtime-alias-copy.json',ALIAS]
            result['prepared_files_sha256']={p.relative_to(ROOT).as_posix():sha(read(p)) for p in paths}
            result.update(status='PREPARED_CPU_DUMMY_NOT_EXECUTION_AUTHORIZED',optimizer_steps=0,execution_authorization_approved=False)
        else:
            run('native-smoke',context_command('smoke',PREP/'execution-config.json',EXEC/'authorization.json',context_path,context_sha),env)
            manifest=json.loads(read(OUTPUT/'manifest.json'));summary=manifest['summary']
            resources=json.loads(read(OUTPUT/'watchdog-resources.json'))
            validate_completion(manifest,resources,binding,context_sha,result['children'][-1]['pid'])
            checkpoint=summary['selection_checkpoint']
            if Path(checkpoint).name!=checkpoint or sha(read(OUTPUT/checkpoint,8*1024**2))!=summary['checkpoint_sha256']:
                raise ValueError('actual dummy checkpoint SHA mismatch')
            native_files=sorted(p for p in OUTPUT.rglob('*') if p.is_file())
            if len(native_files)>64 or sum(p.stat().st_size for p in native_files)>16*1024**2:raise ValueError('dummy output inventory cap')
            result['native_output_hashes']={p.relative_to(ROOT).as_posix():sha(read(p,8*1024**2)) for p in native_files}
            for name,digest in preparation['prepared_files_sha256'].items():
                if sha(read(ROOT/name))!=digest:raise ValueError('reviewed preparation/input drift after worker')
            result.update(status='ACCEPTED_NATIVE_CPU_DUMMY_ENGINEERING_ONLY',summary=summary,
                          native_manifest_sha256=sha(read(OUTPUT/'manifest.json')),watchdog_resources_sha256=sha(read(OUTPUT/'watchdog-resources.json')),execution_approval_reference=args.execution_approval_reference)
        if sources()!=before or sha(read(source))!=args.expected_source_sha256 or sha(read(VALIDATOR))!=VALIDATOR_SHA:raise ValueError('source drift during phase')
        for name,digest in PINS.items():pin(ROOT/name,digest)
        pin(GATE_STAGE/'result.json',args.gate_result_sha256);pin(GATE_STAGE/'output-manifest.json',args.gate_manifest_sha256)
        if sha(read(ALIAS))!=RUNTIME_SHA or sha(read(RUNTIME))!=RUNTIME_SHA:raise ValueError('runtime original/alias changed')
        pin(MATERIAL,args.materialization_sha256);pin(ROOT/'source-delta01/result.json',args.delta_result_sha256)
        if sha(read(GATE_HELPER))!=GATE_HELPER_SHA or sha(read(gate_helper['UPSTREAM']/'load_data.py'))!=gate_helper['LOADER_SHA']:raise ValueError('Gatehelper/loader drift')
        check()
    except Exception as exc:
        result.update(status='FAILED_RETAIN_PARTIAL_NO_RETRY',error_type=type(exc).__name__,error=str(exc))
        with (directory/'failure.log').open('x',encoding='utf-8') as stream:stream.write(traceback.format_exc())
    finally:
        inventory={}
        for path in directory.iterdir():
            if path.is_file():
                try:inventory[path.name]={'sha256':sha(read(path,32*1024**2)),'bytes':path.stat().st_size}
                except Exception as exc:inventory[path.name]={'inventory_error':str(exc)}
        result.update(elapsed_seconds=time.monotonic()-start,elapsed_wall_seconds=time.time()-wall,peak_observed_workspace_bytes=peak,
                      storage_monitor_is_cooperative=True,child_cleanup_accepted=all(row.get('cleanup_accepted') is True for row in result['children']))
        if not all(math.isfinite(v) and 0<=v<=cap for v in (result['elapsed_seconds'],result['elapsed_wall_seconds'])):
            result['status']='REJECTED_OUTER_RESOURCE_BOUND'
        write(directory/'result.json',result)
        inventory['result.json']={'sha256':sha(read(directory/'result.json')),'bytes':(directory/'result.json').stat().st_size}
        write(directory/'output-manifest.json',{'status':result['status'],'outputs':inventory,'excluded':'checkpoints/Parquet/pytest temp; no binary export'})
        print(json.dumps({'status':result['status'],'phase':args.phase,'elapsed_seconds':result['elapsed_seconds'],
                          'result_sha256':sha(read(directory/'result.json')),'output_manifest_sha256':sha(read(directory/'output-manifest.json'))}))
    return 0 if result['status'].startswith(('PREPARED_CPU_','ACCEPTED_NATIVE_CPU_')) else 1

if __name__=='__main__':raise SystemExit(main())
