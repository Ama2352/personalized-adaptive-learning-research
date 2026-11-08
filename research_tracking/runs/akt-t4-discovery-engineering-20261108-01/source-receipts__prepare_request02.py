"""Chỉ chuẩn bị một request CPU discovery; không dispatch hoặc chạy target."""
import ast
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import zlib

HERE=Path(__file__).resolve().parent
SOURCE_SHA='51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f'
PROFILE_SHA='0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228'
SOURCE=HERE/'discovery02.py'
PROFILE=HERE/'discovery_profile01.json'
sha=lambda b:hashlib.sha256(b).hexdigest()

TEMPLATE=r'''import base64,hashlib,json,os,signal,subprocess,time,zlib
from pathlib import Path
PROJECT=Path('/content/KLTN_GPU08_20261108_01')
STAGING=Path('/content/KLTN_GPU10_DISCOVERY_20261108_01')
INPUT=STAGING/'cpu-readonly02-inputs'
ATTEMPT=STAGING/'cpu-readonly02'
def sha(b):return hashlib.sha256(b).hexdigest()
def unpack(text,expected,cap):
    compressed=base64.b64decode(text,validate=True);d=zlib.decompressobj()
    b=d.decompress(compressed,cap+1)
    if len(b)>cap or not d.eof or d.unused_data or d.unconsumed_tail or sha(b)!=expected:raise ValueError('bounded payload/hash mismatch')
    return b
source=unpack(SOURCE_COMPRESSED,SOURCE_SHA,128*1024)
profile_bytes=unpack(PROFILE_COMPRESSED,PROFILE_SHA,1024**2)
profile=json.loads(profile_bytes)
assert os.name=='posix' and PROJECT.is_dir() and PROJECT.resolve()==PROJECT
assert not STAGING.is_symlink()
STAGING.mkdir(exist_ok=True);assert STAGING.stat().st_uid==os.getuid()
assert not ATTEMPT.exists() and not ATTEMPT.is_symlink()
INPUT.mkdir(exist_ok=False)
for name,b in [('discovery02.py',source),('profile.json',profile_bytes)]:
    with (INPUT/name).open('xb') as f:f.write(b)
    assert sha((INPUT/name).read_bytes())==sha(b)
expected={**profile['source_files'],**{'artifacts/akt/dependencies/upstream/'+k:v for k,v in profile['upstream_files'].items()},profile['lock_relative']:profile['lock_sha256']}
def project_snapshot():
    actual={};total=0
    for name,h in expected.items():
        p=PROJECT/name
        assert not p.is_symlink() and p.resolve().is_relative_to(PROJECT)
        with p.open('rb') as f:b=f.read(64*1024**2-total+1)
        total+=len(b);assert total<=64*1024**2 and sha(b)==h
        actual[name]=h
    return sha(json.dumps(actual,sort_keys=True).encode()),len(actual)
before,count=project_snapshot()
command=ARGV
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(INPUT),'CUDA_VISIBLE_DEVICES':'','NVIDIA_VISIBLE_DEVICES':'','PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','PIP_CONFIG_FILE':os.devnull}
start=time.monotonic();child=None;cleanup_ok=False;cleanup=[];error=None
try:
    with (INPUT/'controller.stdout').open('xb') as out,(INPUT/'controller.stderr').open('xb') as err:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,start_new_session=True)
        try:child.wait(timeout=30)
        finally:
            try:os.killpg(child.pid,signal.SIGKILL);cleanup.append('owned launcher group signalled once')
            except ProcessLookupError:cleanup.append('owned launcher group already absent')
            child.wait(timeout=2);cleanup_ok=True
except Exception as exc:error=type(exc).__name__+': '+str(exc)
elapsed=time.monotonic()-start
result={'status':'STOP_RETAIN_PARTIAL_NO_RERUN','source_sha256':SOURCE_SHA,'profile_sha256':PROFILE_SHA,'command':command,'child_returncode':None if child is None else child.returncode,'cleanup_accepted':cleanup_ok,'cleanup':cleanup,'error':error,'launcher_seconds':elapsed,'source_cap_seconds':30,'launcher_timeout_seconds':30,'cleanup_reap_grace_seconds':2,'project_source_file_count':count,'project_source_snapshot_sha256_before':before,'model_gpu_install_calls':0,'scope':'Actual CPU read-only discovery only; not GPU/runtime/install authorization'}
try:
    after,aftercount=project_snapshot();result['project_source_snapshot_sha256_after']=after
    assert before==after and count==aftercount
    assert sha((INPUT/'discovery02.py').read_bytes())==SOURCE_SHA and sha((INPUT/'profile.json').read_bytes())==PROFILE_SHA
    path=ATTEMPT/'result.json'
    with path.open('rb') as f:raw=f.read(128*1024+1)
    assert len(raw)<=128*1024
    actual=json.loads(raw)
    result.update(discovery_status=actual['status'],result_path=str(path),result_sha256=sha(raw),result_bytes=len(raw))
    if error is None and child.returncode==0 and cleanup_ok and elapsed<=30 and actual['elapsed_seconds']<=30:
        result['status']='COMPLETED_CPU_DISCOVERY_ONLY_NOT_GPU_READY'
    # Include exact text only if the complete JSON reply (including logs metadata) remains <=48k.
    result['inline_result_text']=raw.decode('utf-8')
except Exception as exc:result['postcheck_error']=type(exc).__name__+': '+str(exc)
for label in ('controller.stdout','controller.stderr'):
    p=INPUT/label
    if p.is_file():
        with p.open('rb') as f:b=f.read(512*1024+1)
        result[label]={'bytes':len(b),'sha256':sha(b),'capture_cap_exceeded':len(b)>512*1024}
for label in ('target.stdout','target.stderr'):
    p=ATTEMPT/label
    if p.is_file():
        with p.open('rb') as f:b=f.read(512*1024+1)
        row={'bytes_captured':len(b),'sha256_captured':sha(b),'capture_cap_exceeded':len(b)>512*1024}
        if len(b)<=4096:row['text']=b.decode('utf-8',errors='replace')
        result[label]=row
result['inline_result_included']='inline_result_text' in result
if len(json.dumps(result,ensure_ascii=False).encode('utf-8'))>48000:
    result.pop('inline_result_text',None);result['inline_result_included']=False;result['requires_bounded_text_retrieval']=True
with (INPUT/'launcher-result.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
reply=json.dumps(result,ensure_ascii=False)
assert len(reply.encode('utf-8'))<=48000
print(reply)
'''


def main():
    source,profile=SOURCE.read_bytes(),PROFILE.read_bytes()
    assert sha(source)==SOURCE_SHA and sha(profile)==PROFILE_SHA
    ast.parse(source);tree=ast.parse(source)
    spec=importlib.util.spec_from_file_location('discovery_definition_only',SOURCE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.validate_profile(json.loads(profile))
    flags=['--profile','/content/KLTN_GPU10_DISCOVERY_20261108_01/cpu-readonly02-inputs/profile.json',
           '--profile-sha256',PROFILE_SHA,'--expected-source-sha256',SOURCE_SHA,
           '--attempt-id','cpu-readonly02','--approval-reference','USER_FREE_COLAB_CPU_READONLY_DISCOVERY_NO_INSTALL_MODEL_GPU']
    module._parser().parse_args(flags)  # Exact generatedargv parsed; never operation main.
    command=['/usr/bin/python3','-I','-S','-B','/content/KLTN_GPU10_DISCOVERY_20261108_01/cpu-readonly02-inputs/discovery02.py',*flags]
    header='\n'.join(['SOURCE_SHA='+repr(SOURCE_SHA),'PROFILE_SHA='+repr(PROFILE_SHA),
        'SOURCE_COMPRESSED='+repr(base64.b64encode(zlib.compress(source,9)).decode()),
        'PROFILE_COMPRESSED='+repr(base64.b64encode(zlib.compress(profile,9)).decode()),'ARGV='+repr(command)])+'\n'
    code=header+TEMPLATE
    ast.parse(code)
    request=json.dumps({'cellIndex':0,'language':'python','code':code},ensure_ascii=False)
    assert len(request.encode())<=48000
    (HERE/'cpu-discovery02-cell.py').open('x',encoding='utf-8',newline='\n').write(code)
    path=HERE/'request-add-cpu-discovery02.json';path.open('x',encoding='utf-8').write(request)
    contract={'status':'OFFLINE_PREPARED_NOT_DISPATCHED','source_sha256':SOURCE_SHA,'profile_sha256':PROFILE_SHA,
              'cell_sha256':sha(code.encode()),'request_sha256':sha(path.read_bytes()),'request_bytes':len(request.encode()),
              'exact_generated_cli_argv_parsed':True,'source_stage_seconds':30,'launcher_timeout_seconds':30,
              'cleanup_reap_grace_seconds':2,'suggested_MCP_timeout_seconds':45,'reply_max_bytes':48000,
              'project_writes':False,'new_exclusive_staging':'/content/KLTN_GPU10_DISCOVERY_20261108_01/cpu-readonly02-inputs',
              'discovery_result':'/content/KLTN_GPU10_DISCOVERY_20261108_01/cpu-readonly02/result.json',
              'model_target_probe_remote_install_GPU_calls_local':0,'limits':'AST/definition-only profile+argv preparation; no operation main/target subprocess dispatched. Source controller and target both -I -S -B.'}
    (HERE/'request-contract02.json').open('x',encoding='utf-8').write(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(contract))


if __name__=='__main__':main()
