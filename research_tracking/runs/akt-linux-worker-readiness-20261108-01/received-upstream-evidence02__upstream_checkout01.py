"""Stage riêng: public AKT sparse checkout; không chạy model/dataset/Gate.

Chỉ chuẩn bị để parent review. Một child process-group, 90s tổng kể cleanup;
128MiB upstream+stage và 4MiB logs là monitor hợp tác, không hard quota.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import stat
import subprocess
import sys
import time
import traceback

ROOT=Path('/content/KLTN_GPU08_20261108_01')
UPSTREAM=ROOT/'artifacts/akt/dependencies/upstream'
STAGE=ROOT/'upstream-checkout01'
URL='https://github.com/arghosh/AKT.git'
PIN='01b7e8d7d7c862cabc9467108e3e7f2555653a88'
EXPECTED={'commit':PIN,'tree':'904863502337ef2eefd1769d14836b62e3c3804a','remote':URL,'files':{
 'akt.py':'be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d',
 'README.md':'df8eea9919dcdb343f3a841540af18e2039b8b0c33af449ca9c752d11f56ee8b',
 'LICENSE':'891133edce0d8693f5b916d4257ce70b71a02aa110cb02cc5d47326544ea4522'}}
KIT_CANONICAL_SHA='0c3414991a2879033272526822bcec371af78f034cd2716795e33695697acb43'
CAP_SECONDS=90
CAP_BYTES=128*1024**2
LOG_BYTES=4*1024**2
sha=lambda b:hashlib.sha256(b).hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def read_regular(path,cap=1024**2):
    require(path.is_absolute() and path.is_relative_to(ROOT),'input escaped ROOT')
    for p in (path,*path.parents):
        require(not p.is_symlink(),'input symlink')
        if p==ROOT:break
    require(stat.S_ISREG(path.stat().st_mode),'input not regular')
    with path.open('rb') as stream:data=stream.read(cap+1)
    require(len(data)<=cap,'input byte cap')
    return data


def verify_kit():
    raw=read_regular(ROOT/'gpu09-worker-kit-materialization-01.json');receipt=json.loads(raw)
    require(receipt['status']=='MATERIALIZED_SOURCE_ONLY_NO_EXECUTION','kit not materialized')
    manifest=receipt['manifest'];files=manifest['files'];rows=receipt['copy_inventory']
    require(sha(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode())==KIT_CANONICAL_SHA,'kit manifest mismatch')
    require(len(files)==len(rows)==161 and len(manifest['gate2_build_hashes'])==120,'kit inventory count')
    require(len({r['member'] for r in rows})==161 and {r['member'] for r in rows}==set(files),'kit copy inventory')
    for name,entry in files.items():
        p=PurePosixPath(name)
        require(not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name,'kit path')
        data=read_regular(ROOT/name);require(len(data)==entry['bytes'] and sha(data)==entry['sha256'],'kit source drift')
    require(all(files[n]['sha256']==h for n,h in manifest['gate2_build_hashes'].items()),'Gate22 source binding')
    require(all(r['sha256_before_from_archive']==r['sha256_after']==files[r['member']]['sha256'] for r in rows),'copy hash mismatch')
    return sha(raw)


def cleanup_once(process,state):
    if process is None or state['attempted']:return
    state['attempted']=True;ok=True;pgid=process.pid
    if pgid<=1 or pgid==os.getpgrp():ok=False;state['events'].append({'error':'refuse controller/global PGID'})
    else:
        for sig in (signal.SIGTERM,signal.SIGKILL):
            try:os.killpg(pgid,sig);state['events'].append({'signal':sig.name,'sent':True})
            except ProcessLookupError:state['events'].append({'signal':sig.name,'already_absent':True})
            except OSError as error:ok=False;state['events'].append({'signal':sig.name,'error':str(error)})
    try:process.wait(timeout=5)
    except (subprocess.TimeoutExpired,OSError) as error:ok=False;state['events'].append({'error':'reap_failed','type':type(error).__name__})
    state['returncode']=process.poll();state['accepted']=ok and state['returncode'] is not None


CHILD=r'''
import json,os,subprocess,sys,time
from pathlib import Path
require(sys.prefix==str(ROOT/'.venv') and sys.executable==str(ROOT/'.venv/bin/python'),'target venv entry')
require(not any(n in sys.modules for n in ('torch','numpy')),'unexpected heavy import')
kit_sha=verify_kit()  # All161files and120Gate paths BEFORE provenance/config import.
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.provenance import verify_upstream
deadline=time.monotonic()+CHILD_BUDGET
rows=[]
def run(args):
    command=['git','-c','core.hooksPath=/dev/null','-c','core.autocrlf=false',
             '-c','credential.helper=','-c','credential.interactive=false',*args]
    started=time.monotonic();remaining=deadline-started
    require(remaining>0,'child deadline')
    row={'command':command};rows.append(row)
    try:
        result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=remaining,check=False)
        row.update(returncode=result.returncode,stdout_sha256=sha(result.stdout),stderr_sha256=sha(result.stderr))
        require(len(result.stdout)+len(result.stderr)<=1024**2,'git output cap')
        row.update(stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace'))
        require(result.returncode==0,'git command failed')
        return row['stdout'].strip()
    except subprocess.TimeoutExpired:
        row.update(returncode=None,timed_out=True)
        raise
    finally:
        row['elapsed_seconds']=time.monotonic()-started
        (STAGE/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
version=run(['--version'])
run(['clone','--filter=blob:none','--depth','1','--no-checkout','--no-tags',URL,str(UPSTREAM)])
run(['-C',str(UPSTREAM),'sparse-checkout','init','--no-cone'])
run(['-C',str(UPSTREAM),'sparse-checkout','set','--no-cone','/akt.py','/README.md','/LICENSE'])
run(['-C',str(UPSTREAM),'fetch','--depth','1','--no-tags','--filter=blob:none','origin',PIN])
run(['-C',str(UPSTREAM),'checkout','--detach',PIN])
clean=run(['-C',str(UPSTREAM),'status','--porcelain','--untracked-files=all'])
require(not clean,'dirty source checkout')
started=time.monotonic();identity=verify_upstream(UPSTREAM,PIN)
require(identity==EXPECTED,'upstream source identity mismatch')
require({p.name for p in UPSTREAM.iterdir() if p.name!='.git'}==set(EXPECTED['files']),'sparse worktree extra files')
require(verify_kit()==kit_sha,'kit drift during checkout')
require(time.monotonic()<=deadline,'post-child deadline')
print(json.dumps({'git_version':version,'commands':rows,'source':identity,'clean_status':clean,
 'library_verifier':'source-verified knowledge_tracing.akt.provenance.verify_upstream; actual Git check_output calls',
 'library_verify_elapsed_seconds':time.monotonic()-started,'kit_receipt_sha256':kit_sha,
 'gpu_model_steps':0,'optimizer_steps':0,'upstream_git_transport_exported':False}))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-source-sha256',required=True);parser.add_argument('--approval-reference',required=True)
    args=parser.parse_args();start=time.monotonic();wall=time.time()
    require(os.name=='posix' and platform.system()=='Linux' and sys.prefix=='/usr' and sys.executable=='/usr/bin/python3','base Linux interpreter')
    require(ROOT.is_dir() and ROOT.resolve()==ROOT and not ROOT.is_symlink() and ROOT.stat().st_uid==os.getuid(),'physical owned ROOT')
    require(not STAGE.exists() and not STAGE.is_symlink(),'existing checkout stage; no retry')
    STAGE.mkdir(exist_ok=False)
    result={'status':'FAILED_UPSTREAM_CHECKOUT_RETAIN_NO_RETRY','scope':'public source checkout only; no dataset/model/Gate/GPU acceptance',
            'approval_reference':args.approval_reference,'gpu_model_steps':0,'optimizer_steps':0,'pip_calls':0,'modal_calls':0}
    process=None;state={'attempted':False,'accepted':False,'events':[]};peak=0;candidate=False
    def check():
        nonlocal peak
        require(all(math.isfinite(v) and 0<=v<=CAP_SECONDS for v in (time.monotonic()-start,time.time()-wall)),'overall90s cap')
        require(not (STAGE/'CANCEL').exists(),'cancelled')
        logical=allocated=logs=0
        for base in (UPSTREAM,STAGE):
            for directory,_,names in os.walk(base,followlinks=False):
                for name in names:
                    try:st=os.lstat(Path(directory)/name)
                    except FileNotFoundError:continue
                    logical+=st.st_size;allocated+=getattr(st,'st_blocks',0)*512
                    if Path(directory).is_relative_to(STAGE):logs+=st.st_size
        peak=max(peak,logical,allocated);require(peak<=CAP_BYTES and logs<=LOG_BYTES,'cooperative storage/log cap')
    try:
        require(re.fullmatch('[a-f0-9]{64}',args.expected_source_sha256) and args.approval_reference.strip(),'source SHA/approval required')
        source=Path(__file__).absolute();require(source==ROOT/'upstream_checkout01.py','stage source path')
        require(sha(read_regular(source))==args.expected_source_sha256,'stage source mismatch')
        require(os.environ.get('COLAB_GPU') in (None,'','0') and not os.environ.get('COLAB_TPU_ADDR') and not list(Path('/dev').glob('nvidia[0-9]*')),'CPU runtime required')
        kit_sha=verify_kit();require(not UPSTREAM.exists() and not UPSTREAM.is_symlink(),'fresh upstream destination required')
        for p in (UPSTREAM.parent,*UPSTREAM.parent.parents):
            require(not p.is_symlink(),'destination ancestor symlink')
            if p==ROOT:break
        UPSTREAM.parent.mkdir(parents=True,exist_ok=True)
        env={k:v for k,v in os.environ.items() if not k.upper().startswith(('GIT_','GH_','GITHUB_','SSH_','PYTHON','PIP_','UV_','CONDA_'))
             and not any(s in k.upper() for s in ('TOKEN','SECRET','PASSWORD','CREDENTIAL','COOKIE','AUTH','API_KEY','PROXY'))
             and k not in {'HOME','XDG_CONFIG_HOME','LD_PRELOAD','LD_LIBRARY_PATH','CURL_HOME','NETRC'}}
        (STAGE/'home').mkdir();env.update(HOME=str(STAGE/'home'),XDG_CONFIG_HOME=str(STAGE/'home'),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
            GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='4',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=os.devnull,
            GIT_CONFIG_KEY_1='core.autocrlf',GIT_CONFIG_VALUE_1='false',GIT_CONFIG_KEY_2='credential.helper',GIT_CONFIG_VALUE_2='',
            GIT_CONFIG_KEY_3='credential.interactive',GIT_CONFIG_VALUE_3='false',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',
            PATH='/usr/bin:/bin',PYTHONDONTWRITEBYTECODE='1')
        prelude='\n'.join(Path(__file__).read_text().split('CHILD=r')[0].splitlines())
        script=STAGE/'checkout-child.py'
        with script.open('x',encoding='utf-8') as f:f.write(prelude+'\nCHILD_BUDGET='+repr(max(.01,CAP_SECONDS-(time.monotonic()-start)))+'\n'+CHILD)
        check()
        with (STAGE/'child.stdout').open('xb') as stdout,(STAGE/'child.stderr').open('xb') as stderr:
            process=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-I','-B',str(script)],cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            try:
                while process.poll() is None:
                    check()
                    try:process.wait(timeout=.25)
                    except subprocess.TimeoutExpired:pass
            finally:cleanup_once(process,state)
        require(state['accepted'] and state['returncode']==0,'child/cleanup failure; retain logs')
        payload=json.loads(read_regular(STAGE/'child.stdout'));require(payload['source']==EXPECTED,'child source identity')
        require(verify_kit()==kit_sha==payload['kit_receipt_sha256'],'kit changed')
        require(sha(read_regular(source))==args.expected_source_sha256,'stage changed')
        require(all(sha(read_regular(UPSTREAM/n))==h for n,h in EXPECTED['files'].items()),'source file drift')
        result.update(audit=payload,source_sha256=args.expected_source_sha256);check();candidate=True
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error))
        with (STAGE/'failure.log').open('x',encoding='utf-8') as f:f.write(traceback.format_exc())
    finally:
        cleanup_once(process,state)
        try:check();resource_ok=True
        except Exception as error:resource_ok=False;result['resource_error']=str(error)
        elapsed=time.monotonic()-start;elapsed_wall=time.time()-wall
        resource_ok=resource_ok and all(math.isfinite(v) and 0<=v<=CAP_SECONDS for v in (elapsed,elapsed_wall))
        if candidate and state['accepted'] and resource_ok:result['status']='VERIFIED_PUBLIC_PINNED_UPSTREAM_SOURCE_ONLY'
        result.update(elapsed_seconds=elapsed,elapsed_wall_seconds=elapsed_wall,timeout_seconds=90,peak_observed_bytes=peak,
                      storage_monitor_cooperative=True,resource_accepted=resource_ok,cleanup=state,child_count=int(process is not None))
        with (STAGE/'result.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
        inventory={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in STAGE.iterdir() if p.is_file()}
        with (STAGE/'output-manifest.json').open('x',encoding='utf-8') as f:json.dump({'status':result['status'],'outputs':inventory},f,indent=2);f.write('\n')
        print(json.dumps({'status':result['status'],'elapsed_seconds':elapsed,'result_sha256':sha((STAGE/'result.json').read_bytes()),
                          'output_manifest_sha256':sha((STAGE/'output-manifest.json').read_bytes()),'child_count':result['child_count']}))
    return 0 if result['status']=='VERIFIED_PUBLIC_PINNED_UPSTREAM_SOURCE_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
