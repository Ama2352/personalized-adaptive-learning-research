
import ast,hashlib,json,os,runpy,subprocess,sys,time
from pathlib import Path
profile={'pin': '01b7e8d7d7c862cabc9467108e3e7f2555653a88', 'tree': '904863502337ef2eefd1769d14836b62e3c3804a', 'url': 'https://github.com/arghosh/AKT.git', 'lf': {'akt.py': 'ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67', 'README.md': 'bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b', 'LICENSE': '50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf'}, 'loader_sha': '27550ccd07c1131971c4381f024c0f3795dba3d32b7f9fb4eea4ababd8bfe9e8', 'loader_blob': '9fafe965e0b442242125250f37dc8c3f8a145edf', 'local_profile_sha': 'fe92be5208b9b2b1ba041945c7a5c190c0eef13a34679203c5f76acc93a8088e'}
root=Path('/content/KLTN_GPU08_20261108_01');upstream=root/'artifacts/akt/dependencies/upstream';stage=root/'upstream-loader-transfer03'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
helper=runpy.run_path(str(root/'upstream_checkout01.py'))
if (upstream/'.git').is_symlink() or not (upstream/'.git').is_dir():raise ValueError('existing physical legitimate clone metadata required')
before={name:helper['read_regular'](upstream/name) for name in profile['lf']}
kit_sha=helper['verify_kit']();started=time.monotonic();rows=[]
def git(*args,input_bytes=None):
 command=['/usr/bin/git','-C',str(upstream),*args]
 result=subprocess.run(command,capture_output=True,input=input_bytes,timeout=max(.01,min(10,24-(time.monotonic()-started))))
 row={'command':command,'returncode':result.returncode,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr),
      'stdout_bytes':len(result.stdout),'stderr_bytes':len(result.stderr)}
 if input_bytes is not None:row.update(stdin_sha256=sha(input_bytes),stdin_bytes=len(input_bytes))
 rows.append(row)
 (stage/'commands.json').write_text(json.dumps(rows,indent=2)+chr(10))
 if len(result.stdout)+len(result.stderr)>1024**2:raise ValueError('Git output byte cap')
 return result
def required(*args):
 result=git(*args)
 if result.returncode:raise RuntimeError('Git command failed; cached-only, no network fallback')
 return result.stdout
# Inspect local/worktree config names without following includes before source/status operations.
for scope in ('--local','--worktree'):
 keys=required('config',scope,'--no-includes','--name-only','--list').decode().lower().splitlines()
 if any(k.startswith(('include','filter.','url.','credential.','http.','https.','diff.','merge.','core.sshcommand','core.gitproxy')) for k in keys):
  raise ValueError('unreviewed repository config routing/filter/auth')
sys.path.insert(0,str(root/'src'))
from knowledge_tracing.akt.provenance import verify_upstream
identity=verify_upstream(upstream,profile['pin'])
expected={'commit':profile['pin'],'tree':profile['tree'],'remote':profile['url'],'files':profile['lf']}
if identity!=expected:raise ValueError('actual Git identity/3LF mismatch')
if required('status','--porcelain','--untracked-files=all').strip():raise ValueError('dirty checkout')
if {p.name for p in upstream.iterdir() if p.name!='.git'}!=set(profile['lf']):raise ValueError('worktree must contain original3only')
if set(required('sparse-checkout','list').decode().splitlines())!={'/akt.py','/README.md','/LICENSE'}:
 raise ValueError('unexpected original sparse patterns; no rewrite')
raw=helper['read_regular'](stage/'input/load_data.py')
local_profile=helper['read_regular'](stage/'input/upstream-loader-profile01.json')
if sha(local_profile)!=profile['local_profile_sha']:raise ValueError('local-derived profile bytes mismatch')
meta=json.loads(local_profile)
if meta['commit']!=profile['pin'] or meta['path']!='load_data.py' or meta['git_blob_id']!=profile['loader_blob'] or meta['sha256']!=profile['loader_sha'] or meta['bytes']!=6428:
 raise ValueError('local-derived profile identity mismatch')
oid=required('rev-parse',profile['pin']+':load_data.py').decode().strip()
actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
if len(raw)!=6428 or sha(raw)!=profile['loader_sha'] or oid!=profile['loader_blob'] or actual!=oid:
 raise ValueError('transferred loader size/SHA/blob mismatch BEFORE Git object write')
ast.parse(raw) # Syntax only, not source/model execution.
written=git('hash-object','-w','--stdin',input_bytes=raw)
if written.returncode or written.stdout.decode().strip()!=profile['loader_blob']:raise ValueError('actual Git object cache write mismatch')
if required('cat-file','blob','HEAD:load_data.py')!=raw:raise ValueError('actual HEAD loader blob differs from transferred bytes')
required('sparse-checkout','set','--no-cone','/akt.py','/README.md','/LICENSE','/load_data.py')
after=helper['read_regular'](upstream/'load_data.py')
if after!=raw or sha(after)!=profile['loader_sha']:raise ValueError('materialized loader mismatch')
if any(helper['read_regular'](upstream/n)!=data for n,data in before.items()):raise ValueError('original3source bytes changed')
if verify_upstream(upstream,profile['pin'])!=identity or required('status','--porcelain','--untracked-files=all').strip():raise ValueError('source Git identity/cleanliness drift')
if {p.name for p in upstream.iterdir() if p.name!='.git'}!=set(profile['lf'])|{'load_data.py'}:raise ValueError('unexpected sparse worktree output')
if helper['verify_kit']()!=kit_sha:raise ValueError('kit source drift')
print(json.dumps({'status':'MATERIALIZED_TRANSFERRED_PINNED_LOADER_SOURCE_ONLY','mutation_attempted':True,'commands':rows,
 'source_origin':'LOCAL_PINNED_GIT_BLOB_TRANSFER','local_loader_profile_sha256':profile['local_profile_sha'],
 'source_before_after':identity,'loader':{'path':'load_data.py','sha256':sha(after),'git_blob_id':oid,'bytes':len(after)},
 'kit_receipt_sha256':kit_sha,'git_transport_allowed':False,'model_or_optimizer_steps':0,'gate_reruns':0}))
