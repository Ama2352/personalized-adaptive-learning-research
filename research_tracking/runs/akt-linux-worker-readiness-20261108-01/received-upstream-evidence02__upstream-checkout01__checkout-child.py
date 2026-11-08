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


CHILD_BUDGET=89.98222016099862

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
