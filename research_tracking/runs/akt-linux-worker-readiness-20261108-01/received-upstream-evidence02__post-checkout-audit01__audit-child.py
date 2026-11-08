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
