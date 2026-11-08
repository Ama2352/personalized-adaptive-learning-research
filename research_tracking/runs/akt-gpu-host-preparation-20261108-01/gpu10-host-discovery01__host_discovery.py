"""Offline producer/receiver for generic GPU-host no-site discovery; never dispatch."""
from __future__ import annotations
import argparse,ast,base64,hashlib,importlib.util,inspect,json,math,re,zlib
from pathlib import Path

W=Path(__file__).resolve().parent
OLD=W.parent/'t4-discovery01'
SOURCE_SHA='51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f'
PROFILE_SHA='0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228'
BASELINE_SHA='b0032f9d556d0ca3655d4bafa6d010d30feca05e1d4d6c02ac8148757d8c4ec9'
PHASE='GPU_HOST_READONLY_DISCOVERY'
PROJECT_TEXT='/content/KLTN_GPU08_20261108_01'
STAGING_TEXT='/content/KLTN_GPU10_DISCOVERY_20261108_01'

def digest(b):return hashlib.sha256(b).hexdigest()
def valid_attempt(s):return isinstance(s,str) and re.fullmatch('gpu-host-[A-Za-z0-9_-]{1,36}',s) is not None
def expected_map(profile):
    return {**profile['source_files'],**{'artifacts/akt/dependencies/upstream/'+k:v for k,v in profile['upstream_files'].items()},profile['lock_relative']:profile['lock_sha256']}
def project_snapshot(root,expected):
    root=Path(root)
    if root.is_symlink():return {'state':'INCOMPLETE_OR_MISMATCH','file_count':0,'digest':None,'reason':'root symlink'}
    if not root.exists():return {'state':'ABSENT','file_count':0,'digest':None}
    actual={};total=0
    try:
        if not root.is_dir():raise ValueError('not a directory')
        for name,h in expected.items():
            p=root/name
            if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('source escape/symlink')
            with p.open('rb') as f:b=f.read(64*1024**2-total+1)
            total+=len(b)
            if total>64*1024**2 or digest(b)!=h:raise ValueError('source/lock mismatch: '+name)
            actual[name]=h
        return {'state':'EXACT','file_count':len(actual),'digest':digest(json.dumps(actual,sort_keys=True).encode())}
    except (OSError,ValueError) as e:
        return {'state':'INCOMPLETE_OR_MISMATCH','file_count':len(actual),'digest':None,'reason':str(e)}
def gpu_indication(actual):
    s=actual.get('host_signals',{});names=s.get('nvidia_device_entry_names');flag=s.get('COLAB_GPU')
    return (s.get('TPU_present') is False and isinstance(names,list)
            and (flag is None or isinstance(flag,str))
            and all(isinstance(n,str) and re.fullmatch('nvidia[0-9]+',n) for n in names)
            and bool(isinstance(flag,str) and flag not in ('','0') or names))
def classify_result(launch,actual,profile):
    """Shared runtime/receiver predicate; candidate metadata, never execution authority."""
    try:
        if launch.get('phase')!=PHASE or launch.get('source_sha256')!=SOURCE_SHA or launch.get('profile_sha256')!=PROFILE_SHA:
            return 'STOP_RETAIN_PARTIAL_NO_RERUN','phase/source/profile mismatch'
        attempt=launch.get('attempt_id');command=launch.get('command')
        if not valid_attempt(attempt) or not isinstance(command,list) or command[:4]!=['/usr/bin/python3','-I','-S','-B']:
            return 'STOP_RETAIN_PARTIAL_NO_RERUN','generic attempt/isolated argv required'
        def flag(name):
            if command.count(name)!=1 or command.index(name)+1>=len(command):raise ValueError('required flag '+name)
            return command[command.index(name)+1]
        prefix=STAGING_TEXT+'/'+attempt+'-inputs'
        if (command[4]!=prefix+'/discovery02.py' or flag('--attempt-id')!=attempt or flag('--profile')!=prefix+'/profile.json'
                or flag('--profile-sha256')!=PROFILE_SHA or flag('--expected-source-sha256')!=SOURCE_SHA
                or flag('--approval-reference')!=actual.get('approval_reference') or 'GPU_HOST' not in flag('--approval-reference')
                or launch.get('result_path')!=STAGING_TEXT+'/'+attempt+'/result.json'):
            return 'STOP_RETAIN_PARTIAL_NO_RERUN','fresh GPU_HOST command/result identity required'
        if (launch.get('cleanup_accepted') is not True or type(launch.get('child_returncode')) is not int or launch['child_returncode']!=0
                or launch.get('error') is not None):return 'STOP_RETAIN_PARTIAL_NO_RERUN','launcher failure/cleanup'
        for value in (launch.get('launcher_seconds'),actual.get('elapsed_seconds')):
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=30:return 'STOP_RETAIN_PARTIAL_NO_RERUN','elapsed budget'
        if (actual.get('controller_source_sha256_before')!=SOURCE_SHA or actual.get('controller_source_sha256_after')!=SOURCE_SHA
                or actual.get('profile_file_sha256_before')!=PROFILE_SHA or actual.get('profile_file_sha256_after')!=PROFILE_SHA
                or actual.get('host_abi')!=profile['expected_host']):return 'STOP_RETAIN_PARTIAL_NO_RERUN','source/profile/ABI changed'
        if any(type(actual.get(k)) is not int or actual[k]!=0 for k in ('gpu_queries','model_imports','installs')):
            return 'STOP_RETAIN_PARTIAL_NO_RERUN','unexpected discovery scope'
        before,after=launch['root_snapshot_before'],launch['root_snapshot_after']
        child=actual.get('child');status=actual.get('status')
        if status=='COLD_ROOT_ABSENT':
            good=(before==after=={'state':'ABSENT','file_count':0,'digest':None} and child is None and actual.get('source_sha256')=={})
            return ('COLD_GPU_HOST_DISCOVERY_NOT_READY','ROOT absent; zero target child and no ROOT writes') if good else ('STOP_RETAIN_PARTIAL_NO_RERUN','cold ROOT proof mismatch')
        expected=expected_map(profile);expected_digest=digest(json.dumps(expected,sort_keys=True).encode())
        if (len(expected)!=165 or before.get('state')!='EXACT' or after!=before or before.get('file_count')!=165
                or before.get('digest')!=expected_digest or actual.get('source_sha256')!=expected):return 'STOP_RETAIN_PARTIAL_NO_RERUN','source165 snapshot mismatch'
        if status=='COLD_VENV_ABSENT' and child is None:return 'COLD_GPU_HOST_DISCOVERY_NOT_READY','venv absent; no install authority'
        if child is None or type(child.get('returncode')) is not int or child['returncode']!=0 or child.get('cleanup_accepted') is not True:
            return 'STOP_RETAIN_PARTIAL_NO_RERUN','inner target failure/unknown cleanup'
        if status=='COLD_VENV_EMPTY_REQUIRES_INSTALL_APPROVAL':return 'COLD_GPU_HOST_DISCOVERY_NOT_READY','empty existing venv, separate install approval required'
        if status!='WARM_CANDIDATE_REQUIRES_AUDIT':return 'STOP_RETAIN_PARTIAL_NO_RERUN','discovery STOP/unknown status'
        if not gpu_indication(actual):return 'STOP_RETAIN_PARTIAL_NO_RERUN','current GPU-host indication absent; never relabel CPU metadata'
        q=actual['target_probe']
        if (q['abi']!=profile['expected_host'] or type(q['no_site']) is not int or q['no_site']!=1
                or type(q['abi']['gil_disabled']) is not int or type(actual['host_abi']['gil_disabled']) is not int
                or type(q['isolated']) is not int or q['isolated']!=1 or q['prefix']!=q['base_prefix'] or q['prefix']!='/usr'
                or q['cuda_visible_devices']!='' or q['nvidia_visible_devices']!='' or q['heavy_modules_imported']!=[]):
            return 'STOP_RETAIN_PARTIAL_NO_RERUN','no-site target scope mismatch'
        versions={re.sub('[-_.]+','-',x['name']).lower():x['version'] for x in q['distributions']}
        if len(q['distributions'])!=44 or len(versions)!=44 or versions!=profile['package_versions']:
            return 'STOP_RETAIN_PARTIAL_NO_RERUN','selected44 mismatch'
        return 'COMPLETED_GPU_HOST_READONLY_DISCOVERY_NOT_GPU_READY','warm candidate only; not normal startup/CUDA/install authority'
    except (KeyError,TypeError,ValueError,IndexError):return 'STOP_RETAIN_PARTIAL_NO_RERUN','malformed discovery metadata'

RUNTIME=r'''
PROJECT=Path(PROJECT_TEXT);STAGING=Path(STAGING_TEXT);INPUT=STAGING/(ATTEMPT+'-inputs');OUTPUT=STAGING/ATTEMPT
def unpack(text,expected,cap):
    d=zlib.decompressobj();b=d.decompress(base64.b64decode(text,validate=True),cap+1)
    if len(b)>cap or not d.eof or d.unused_data or d.unconsumed_tail or digest(b)!=expected:raise ValueError('bounded payload/SHA')
    return b
source=unpack(SOURCE_COMPRESSED,SOURCE_SHA,128*1024);profile_bytes=unpack(PROFILE_COMPRESSED,PROFILE_SHA,1024**2);profile=json.loads(profile_bytes)
assert os.name=='posix' and not STAGING.is_symlink()
STAGING.mkdir(exist_ok=True);assert STAGING.stat().st_uid==os.getuid()
assert not OUTPUT.exists() and not OUTPUT.is_symlink()
INPUT.mkdir(exist_ok=False)
for name,b in [('discovery02.py',source),('profile.json',profile_bytes)]:
    with (INPUT/name).open('xb') as f:f.write(b)
    assert digest((INPUT/name).read_bytes())==digest(b)
before=project_snapshot(PROJECT,expected_map(profile))
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(INPUT),'CUDA_VISIBLE_DEVICES':'','NVIDIA_VISIBLE_DEVICES':'','PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','PIP_CONFIG_FILE':os.devnull}
if os.environ.get('COLAB_GPU') is not None:env['COLAB_GPU']=os.environ['COLAB_GPU']
if os.environ.get('COLAB_TPU_ADDR'):env['COLAB_TPU_ADDR']='present'
start=time.monotonic();process=None;cleanup=False;cleanup_log=[];error=None
try:
    with (INPUT/'controller.stdout').open('xb') as out,(INPUT/'controller.stderr').open('xb') as err:
        process=subprocess.Popen(COMMAND,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,start_new_session=True)
        try:process.wait(timeout=30)
        finally:
            try:os.killpg(process.pid,signal.SIGKILL);cleanup_log.append('launcher group signalled once')
            except ProcessLookupError:cleanup_log.append('launcher group already absent')
            process.wait(timeout=2);cleanup=True
except Exception as exc:error=type(exc).__name__+': '+str(exc)
launch={'phase':PHASE,'attempt_id':ATTEMPT,'status':'STOP_RETAIN_PARTIAL_NO_RERUN','source_sha256':SOURCE_SHA,'profile_sha256':PROFILE_SHA,'command':COMMAND,'child_returncode':None if process is None else process.returncode,'cleanup_accepted':cleanup,'cleanup':cleanup_log,'error':error,'launcher_seconds':time.monotonic()-start,'root_snapshot_before':before,'root_snapshot_after':project_snapshot(PROJECT,expected_map(profile)),'result_path':str(OUTPUT/'result.json'),'model_gpu_install_calls':0,'install_authority':False}
after=launch['root_snapshot_after'];launch.update(project_source_file_count=after['file_count'],project_source_snapshot_sha256_before=before['digest'],project_source_snapshot_sha256_after=after['digest'])
try:
    assert digest((INPUT/'discovery02.py').read_bytes())==SOURCE_SHA and digest((INPUT/'profile.json').read_bytes())==PROFILE_SHA
    with (OUTPUT/'result.json').open('rb') as f:raw=f.read(128*1024+1)
    assert len(raw)<=128*1024
    actual=json.loads(raw);launch.update(result_sha256=digest(raw),result_bytes=len(raw),inline_result_text=raw.decode('utf-8'),discovery_status=actual.get('status'))
    launch['launcher_seconds']=time.monotonic()-start
    launch['status'],launch['reason']=classify_result(launch,actual,profile)
except Exception as exc:launch['postcheck_error']=type(exc).__name__+': '+str(exc)
for directory,names in [(INPUT,('controller.stdout','controller.stderr')),(OUTPUT,('target.stdout','target.stderr'))]:
    for name in names:
        p=directory/name
        if p.is_file():
            with p.open('rb') as f:b=f.read(512*1024+1)
            row={'captured_bytes':len(b),'captured_sha256':digest(b),'cap_exceeded':len(b)>512*1024}
            if len(b)<=4096:row['text']=b.decode('utf-8',errors='replace')
            launch[name]=row
launch['launcher_seconds']=time.monotonic()-start
if launch['launcher_seconds']>30:launch['status']='STOP_RETAIN_PARTIAL_NO_RERUN';launch['reason']='post-capture budget exceeded'
launch['inline_result_included']='inline_result_text' in launch
if len(json.dumps(launch,ensure_ascii=False).encode())>48000:
    launch.pop('inline_result_text',None);launch['inline_result_included']=False;launch['requires_bounded_text_retrieval']=True
with (INPUT/'launcher-result.json').open('x',encoding='utf-8') as f:json.dump(launch,f,ensure_ascii=False,indent=2)
reply=json.dumps(launch,ensure_ascii=False);assert len(reply.encode())<=48000
print(reply)
'''

def discovery_argv(attempt,approval):
    if not valid_attempt(attempt) or not isinstance(approval,str) or 'GPU_HOST' not in approval:raise ValueError('explicit generic GPU_HOST attempt/approval required')
    prefix=STAGING_TEXT+'/'+attempt+'-inputs'
    return ['/usr/bin/python3','-I','-S','-B',prefix+'/discovery02.py','--profile',prefix+'/profile.json',
            '--profile-sha256',PROFILE_SHA,'--expected-source-sha256',SOURCE_SHA,'--attempt-id',attempt,'--approval-reference',approval]

def render_cell(source,profile_bytes,attempt,approval):
    if digest(source)!=SOURCE_SHA or digest(profile_bytes)!=PROFILE_SHA:raise ValueError('immutable source02/profile exact bytes required')
    command=discovery_argv(attempt,approval)
    header='import base64,hashlib,json,math,os,re,signal,subprocess,time,zlib\nfrom pathlib import Path\n'
    for name,value in [('SOURCE_SHA',SOURCE_SHA),('PROFILE_SHA',PROFILE_SHA),('PHASE',PHASE),('PROJECT_TEXT',PROJECT_TEXT),('STAGING_TEXT',STAGING_TEXT),('ATTEMPT',attempt),('COMMAND',command),('SOURCE_COMPRESSED',base64.b64encode(zlib.compress(source,9)).decode()),('PROFILE_COMPRESSED',base64.b64encode(zlib.compress(profile_bytes,9)).decode())]:header+=name+'='+repr(value)+'\n'
    helpers='\n'.join(inspect.getsource(f) for f in (digest,valid_attempt,expected_map,project_snapshot,gpu_indication,classify_result))
    code=header+helpers+RUNTIME;ast.parse(code)
    if len(json.dumps({'cellIndex':0,'language':'python','code':code},ensure_ascii=False).encode())>48000:raise ValueError('request48k cap')
    return code,command

def decode_rpc(raw):
    if len(raw)>256*1024:raise ValueError('raw RPC byte cap')
    obj=json.loads(raw)
    if obj.get('is_error') is not False:raise ValueError('actual RPC error')
    data=obj.get('structured_content') or obj.get('data');outputs=data['outputs']
    if any(x.get('output_type')=='error' for x in outputs):raise ValueError('remote output error')
    text=''.join(''.join(x['text']) if isinstance(x['text'],list) else x['text'] for x in outputs if x.get('output_type')=='stream' and x.get('name')=='stdout')
    if len(text.encode())>48000:raise ValueError('stdout48k cap')
    return text.encode(),json.loads(text)

def derive_receipt(raw_rpc,profile,reference,external_result=None):
    if not isinstance(reference,str) or not reference.strip():raise ValueError('parent review reference required')
    launcher_raw,launch=decode_rpc(raw_rpc)
    common={'phase':PHASE,'raw_rpc_sha256':digest(raw_rpc),'launcher_sha256':digest(launcher_raw),'parent_review_reference':reference,
            'origin_kind':'LOCAL_DERIVED_RECEIPT_FROM_VERIFIED_RPC','launcher_cleanup':launch.get('cleanup_accepted'),
            'source_files':launch.get('project_source_file_count'),'launcher_seconds':launch.get('launcher_seconds'),
            'model_gpu_install_calls':0,'install_authority':False,'scope':'Generic GPU-host indication metadata; not T4/CUDA/normal startup/install authority.'}
    raw=external_result
    if 'inline_result_text' in launch:
        if not isinstance(launch['inline_result_text'],str):raise ValueError('inline result text type')
        inline=launch['inline_result_text'].encode()
        if raw is not None and raw!=inline:raise ValueError('external and inline result bytes differ')
        raw=inline
    if raw is None:return launcher_raw,None,{**common,'status':'RETRIEVAL_REQUIRED_NOT_ACCEPTED','result_path':launch.get('result_path'),'result_sha256':launch.get('result_sha256')}
    if len(raw)>128*1024 or type(launch.get('result_bytes')) is not int or len(raw)!=launch['result_bytes'] or digest(raw)!=launch.get('result_sha256'):raise ValueError('exact actual result SHA/size mismatch')
    actual=json.loads(raw);status,reason=classify_result(launch,actual,profile)
    if launch.get('status')!=status:status='STOP_RETAIN_PARTIAL_NO_RERUN';reason='launcher predicate/verdict mismatch'
    warm=status=='COMPLETED_GPU_HOST_READONLY_DISCOVERY_NOT_GPU_READY'
    cold=status=='COLD_GPU_HOST_DISCOVERY_NOT_READY'
    receipt={**common,'status':'VERIFIED_ACTUAL_WARM_GPU_HOST_DISCOVERY_NOT_GPU_READY' if warm else ('COLD_DISCOVERY_NOT_GPU_READY_NO_INSTALL_AUTHORITY' if cold else 'STOP_RETAIN_EVIDENCE_NOT_ACCEPTED'),
             'actual_status':actual.get('status'),'result_sha256':digest(raw),'native_target_cleanup':None if actual.get('child') is None else actual['child'].get('cleanup_accepted'),
             'reason':reason,'current_host_indication':gpu_indication(actual)}
    return launcher_raw,raw,receipt

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--operation',choices=('prepare','receive'),required=True);p.add_argument('--mode',choices=(PHASE,),required=True)
    p.add_argument('--attempt-id',required=True);p.add_argument('--approval-reference')
    p.add_argument('--rpc-json',type=Path);p.add_argument('--result-file',type=Path)
    p.add_argument('--receipt-id');p.add_argument('--parent-review-reference')
    return p

def validate_options(a):
    if not valid_attempt(a.attempt_id):raise ValueError('generic gpu-host-* attempt required')
    if a.operation=='prepare':
        discovery_argv(a.attempt_id,a.approval_reference)
        if any(x is not None for x in (a.rpc_json,a.result_file,a.receipt_id,a.parent_review_reference)):raise ValueError('prepare cannot receive/auto-transition')
    elif a.rpc_json is None or not a.parent_review_reference or not valid_attempt(a.receipt_id):
        raise ValueError('explicit actual RPC/parent review/new receipt id required')
    return a

def main(argv=None):
    a=validate_options(parser().parse_args(argv))
    source=(OLD/'discovery02.py').read_bytes();profile_bytes=(OLD/'discovery_profile01.json').read_bytes()
    if digest(source)!=SOURCE_SHA or digest(profile_bytes)!=PROFILE_SHA:raise ValueError('immutable source02/profile drift')
    profile=json.loads(profile_bytes)
    if a.operation=='prepare':
        code,command=render_cell(source,profile_bytes,a.attempt_id,a.approval_reference)
        # Parse exact rendered CLI using reviewed source02 definitions only; never main/probe.
        s=importlib.util.spec_from_file_location('source02_parser_only',OLD/'discovery02.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m._parser().parse_args(command[5:])
        out=W/'requests'/a.attempt_id;out.mkdir(parents=True,exist_ok=False)
        request=json.dumps({'cellIndex':0,'language':'python','code':code},ensure_ascii=False)
        (out/'add-cell.json').open('x',encoding='utf-8',newline='\n').write(request)
        contract={'status':'OFFLINE_GENERIC_REQUEST_PREPARED_NOT_DISPATCHED','phase':PHASE,'source_sha256':SOURCE_SHA,'profile_sha256':PROFILE_SHA,'command':command,'cell_code_sha256':digest(code.encode()),'request_sha256':digest(request.encode()),'request_bytes':len(request.encode()),'reply_max_bytes':48000,'exact_source02_cli_parsed':True,'root_absent_handled_without_ROOT_writes':True,'local_target_model_GPU_remote_calls':0}
        (out/'contract.json').open('x',encoding='utf-8').write(json.dumps(contract,indent=2)+'\n');print(json.dumps(contract));return
    if a.rpc_json is None or not a.parent_review_reference or not valid_attempt(a.receipt_id):raise ValueError('explicit actual RPC/parent review/new receipt id required')
    out=W/'received'/a.receipt_id;out.mkdir(parents=True,exist_ok=False)
    with a.rpc_json.open('rb') as f:rpc=f.read(256*1024+1)
    extra=None
    if a.result_file is not None:
        with a.result_file.open('rb') as f:extra=f.read(128*1024+1)
    try:
        launcher_raw,result_raw,receipt=derive_receipt(rpc,profile,a.parent_review_reference,extra)
        launch=json.loads(launcher_raw)
        if launch.get('attempt_id')!=a.attempt_id:raise ValueError('actual attempt differs from selected operation')
        (out/'launcher.json').open('xb').write(launcher_raw)
        if result_raw is not None:(out/'result.json').open('xb').write(result_raw)
        (out/'acceptance.json').open('x',encoding='utf-8').write(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
    except Exception as e:
        complete=len(rpc)<=256*1024
        failure={'status':'RECEIVE_FAILED_RETAIN_NO_REMOTE_RETRY','raw_rpc_sha256':digest(rpc) if complete else None,
                 'captured_rpc_prefix_sha256':None if complete else digest(rpc),'captured_rpc_bytes':len(rpc),
                 'error_type':type(e).__name__,'error':str(e),'parent_review_reference':a.parent_review_reference}
        (out/'failure.json').open('x',encoding='utf-8').write(json.dumps(failure,indent=2)+'\n');raise

if __name__=='__main__':main()
