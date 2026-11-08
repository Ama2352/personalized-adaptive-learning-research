"""Audit riêng chỉ đọc checkout đã có; không clone/fetch/install hoặc sửa FAILED01.

LF hashes suy từ Git object local đúng PIN trước khi chấp nhận remote. Chặn Git
transport; đây không là whole-host network attestation hoặc Linux Gate acceptance.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import runpy
import subprocess
import sys
import time
import traceback

ROOT=Path('/content/KLTN_GPU08_20261108_01')
STAGE=ROOT/'post-checkout-audit01'
HELPER=ROOT/'upstream_checkout01.py'
HELPER_SHA='f33c9d50dbde6a354c03c0f9d702f239a70a9d298f3ee0214718d0daadd9db90'
FAILED_SHA='b82828207f763f53ca76d52827bbf1315a4cda7e403e8d1848b8cf9723732ca1'
LOCAL_PROFILE_SHA='c16d3e13ccd84ac2218aae3c53d61a7ad335cab84bca66a2bffca4b9c01f2bda'
PIN='01b7e8d7d7c862cabc9467108e3e7f2555653a88'
EXPECTED={'commit':PIN,'tree':'904863502337ef2eefd1769d14836b62e3c3804a','remote':'https://github.com/arghosh/AKT.git','files':{
 'akt.py':'ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67',
 'README.md':'bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b',
 'LICENSE':'50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf'}}
BLOBS={'akt.py':'06e1bdef6b2ebb8981dd21f486eaab303b823192','README.md':'5552548deab80123686f4ffc0a51c7ef36a7aa72','LICENSE':'2e31516a7158ef8ca84eca4909f4d742196dbed8'}
sha=lambda b:hashlib.sha256(b).hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def bootstrap():
    require(not HELPER.is_symlink() and sha(HELPER.read_bytes())==HELPER_SHA,'preserved helper SHA mismatch')
    helper=runpy.run_path(str(HELPER))  # Verified stdlib definitions; main is not invoked.
    helper['verify_kit']()
    raw=helper['read_regular'](ROOT/'upstream-checkout01/result.json')
    require(sha(raw)==FAILED_SHA,'failed01 result binding')
    require(json.loads(raw)['status']=='FAILED_UPSTREAM_CHECKOUT_RETAIN_NO_RETRY','failed01 status changed')
    return helper


CHILD=r'''
helper=bootstrap();kit_sha=helper['verify_kit']()
require(sys.prefix==str(ROOT/'.venv') and sys.executable==str(ROOT/'.venv/bin/python'),'target venv')
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.provenance import verify_upstream
upstream=ROOT/'artifacts/akt/dependencies/upstream'
started=time.monotonic();identity=verify_upstream(upstream,PIN)
require(identity==EXPECTED,'exact local-derived LF identity mismatch')
rows={}
for name,blob_id in BLOBS.items():
    command=['git','-C',str(upstream),'cat-file','blob',PIN+':'+name]
    raw=subprocess.check_output(command,timeout=10)
    actual_blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    require(actual_blob==blob_id and sha(raw)==EXPECTED['files'][name],'cached Git object mismatch')
    require(helper['read_regular'](upstream/name)==raw,'worktree bytes differ from cached blob')
    rows[name]={'git_blob_id':actual_blob,'sha256':sha(raw),'bytes':len(raw),'command':command}
require(helper['verify_kit']()==kit_sha,'kit drift')
bootstrap()  # Recheck original FAILED01 bytes and preserved controller source.
print(json.dumps({'source':identity,'cached_blobs':rows,'kit_receipt_sha256':kit_sha,
 'local_derivation_profile_sha256':LOCAL_PROFILE_SHA,'prior_failed01_result_sha256':FAILED_SHA,
 'git_transport_allowed':False,'git_optional_locks':'0','elapsed_seconds':time.monotonic()-started,
 'clone_calls':0,'fetch_calls':0,'pip_calls':0,'gpu_model_steps':0,'optimizer_steps':0}))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-source-sha256',required=True);parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args();start=time.monotonic();wall=time.time()
    require(os.name=='posix' and platform.system()=='Linux' and sys.prefix=='/usr' and sys.executable=='/usr/bin/python3','base Linux interpreter')
    require(ROOT.is_dir() and ROOT.resolve()==ROOT and not ROOT.is_symlink() and ROOT.stat().st_uid==os.getuid(),'physical owned ROOT')
    require(not STAGE.exists() and not STAGE.is_symlink(),'existing audit attempt; STOP')
    STAGE.mkdir(exist_ok=False)
    result={'status':'FAILED_READONLY_POST_CHECKOUT_AUDIT','prior_checkout01_status':'FAILED_UPSTREAM_CHECKOUT_RETAIN_NO_RETRY',
            'approval_reference':args.approval_reference,'clone_calls':0,'fetch_calls':0,'pip_calls':0,'gpu_model_steps':0,'optimizer_steps':0,'modal_calls':0}
    process=None;helper=None;state={'attempted':False,'accepted':False,'events':[]};candidate=False
    def check():
        require(all(math.isfinite(v) and 0<=v<=30 for v in (time.monotonic()-start,time.time()-wall)),'overall30s cap')
        require(not (STAGE/'CANCEL').exists(),'cancelled')
        size=0
        for p in STAGE.iterdir():
            if p.is_file():size+=p.stat().st_size
        require(size<=4*1024**2,'audit4MiB cooperative cap')
    try:
        require(re.fullmatch('[a-f0-9]{64}',args.expected_source_sha256) and args.approval_reference.strip(),'source/approval required')
        source=Path(__file__).absolute();require(source==ROOT/'post_checkout_audit01.py' and not source.is_symlink(),'source path')
        require(sha(source.read_bytes())==args.expected_source_sha256,'audit source mismatch')
        require(os.environ.get('COLAB_GPU') in (None,'','0') and not os.environ.get('COLAB_TPU_ADDR') and not list(Path('/dev').glob('nvidia[0-9]*')),'CPU runtime only')
        helper=bootstrap();kit_sha=helper['verify_kit']()
        env={k:v for k,v in os.environ.items() if not k.upper().startswith(('GIT_','GH_','GITHUB_','SSH_','PYTHON','PIP_','UV_','CONDA_'))
             and not any(s in k.upper() for s in ('TOKEN','SECRET','PASSWORD','CREDENTIAL','COOKIE','AUTH','API_KEY','PROXY'))
             and k not in {'HOME','XDG_CONFIG_HOME','LD_PRELOAD','LD_LIBRARY_PATH','CURL_HOME','NETRC'}}
        (STAGE/'home').mkdir();env.update(HOME=str(STAGE/'home'),XDG_CONFIG_HOME=str(STAGE/'home'),PATH='/usr/bin:/bin',
            GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',
            GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',GIT_CONFIG_COUNT='4',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=os.devnull,
            GIT_CONFIG_KEY_1='core.autocrlf',GIT_CONFIG_VALUE_1='false',GIT_CONFIG_KEY_2='credential.helper',GIT_CONFIG_VALUE_2='',
            GIT_CONFIG_KEY_3='credential.interactive',GIT_CONFIG_VALUE_3='false',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
        script=STAGE/'audit-child.py';prelude=source.read_text().split('CHILD=r')[0]
        with script.open('x',encoding='utf-8') as f:f.write(prelude+'\n'+CHILD)
        check()
        with (STAGE/'child.stdout').open('xb') as stdout,(STAGE/'child.stderr').open('xb') as stderr:
            process=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-I','-B',str(script)],cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            try:
                while process.poll() is None:
                    check()
                    try:process.wait(timeout=.1)
                    except subprocess.TimeoutExpired:pass
            finally:helper['cleanup_once'](process,state)
        require(state['accepted'] and state['returncode']==0,'child/cleanup failure')
        payload=json.loads(helper['read_regular'](STAGE/'child.stdout'));require(payload['source']==EXPECTED,'audit identity')
        require(payload['kit_receipt_sha256']==helper['verify_kit']()==kit_sha,'kit changed')
        bootstrap();require(sha(source.read_bytes())==args.expected_source_sha256,'audit source changed')
        result.update(audit=payload,source_sha256=args.expected_source_sha256);check();candidate=True
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error))
        with (STAGE/'failure.log').open('x',encoding='utf-8') as f:f.write(traceback.format_exc())
    finally:
        if helper is not None:helper['cleanup_once'](process,state)
        try:check();resource_ok=True
        except Exception as error:resource_ok=False;result['resource_error']=str(error)
        if candidate and state['accepted'] and resource_ok:result['status']='VERIFIED_LOCAL_DERIVED_LF_UPSTREAM_READONLY_NOT_LINUX_GATE'
        result.update(elapsed_seconds=time.monotonic()-start,elapsed_wall_seconds=time.time()-wall,timeout_seconds=30,
                      cleanup=state,resource_accepted=resource_ok,child_count=int(process is not None),git_transport_allowed=False)
        if not all(math.isfinite(v) and 0<=v<=30 for v in (result['elapsed_seconds'],result['elapsed_wall_seconds'])):
            result['status']='FAILED_READONLY_POST_CHECKOUT_AUDIT';result['resource_accepted']=False
        with (STAGE/'result.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
        inventory={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in STAGE.iterdir() if p.is_file()}
        with (STAGE/'output-manifest.json').open('x',encoding='utf-8') as f:json.dump({'status':result['status'],'outputs':inventory},f,indent=2);f.write('\n')
        print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'result_sha256':sha((STAGE/'result.json').read_bytes()),'output_manifest_sha256':sha((STAGE/'output-manifest.json').read_bytes())}))
    return 0 if result['status']=='VERIFIED_LOCAL_DERIVED_LF_UPSTREAM_READONLY_NOT_LINUX_GATE' else 1


if __name__=='__main__':raise SystemExit(main())
