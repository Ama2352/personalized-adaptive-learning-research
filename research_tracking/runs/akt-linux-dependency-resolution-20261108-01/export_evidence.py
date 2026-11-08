import base64, hashlib, json, math, zipfile
from pathlib import Path
ROOT=Path('/content/KLTN_GPU08_20261108_01')
ATTEMPT=ROOT/'resolution-attempt01'
result=json.loads((ATTEMPT/'resolution.json').read_text())
assert result['status']=='CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED'
assert result['executed_source_sha256']=='39c68ed7921ccd7660ab1e625ab5df6ca3d2cfd473339b2b9babc7de3665b861'
assert result['packages_installed']==result['gpu_model_steps']==result['modal_calls']==0
assert result['isolated_site_unchanged'] is True and result['elapsed_seconds']<=180
assert result['peak_observed_workspace_bytes']<=256*1024**2 and result['returncode']==0 and result['stop_reason'] is None
names=['connection.json','venv.json','venv-create.stdout','venv-create.stderr','.venv/pyvenv.cfg',
       'connection_probe.py','venv_prepare.py','resolve_dependencies.py',
       *('resolution-attempt01/'+n for n in ['requirements-proposed.txt','pip-report.json',
          'candidate-linux-cuda.lock.txt','resolution.json','pip.stdout.log','pip.stderr.log'])]
sha=lambda data:hashlib.sha256(data).hexdigest()
payloads={}
for name in names:
    path=ROOT/name
    assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT)
    data=path.read_bytes();assert len(data)<=8*1024**2
    payloads[name]=data
assert sum(map(len,payloads.values()))<=16*1024**2
manifest={'kind':'ACTUAL_LINUX_CPU_DEPENDENCY_RESOLUTION_NO_INSTALL','files':{
          name:{'sha256':sha(data),'bytes':len(data)} for name,data in payloads.items()},
          'report_sha256':result['report_sha256'],'candidate_lock_sha256':result['candidate_lock_sha256'],
          'package_count':44,'nvidia_package_count':14,'packages_installed':0,'gpu_model_steps':0,
          'scope':'Candidate closure/index hashes only; no wheel-byte verification/install/image/CUDA acceptance.'}
archive=ROOT/'gpu08-resolution-evidence.zip'
if not archive.exists():
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as output:
        for name,data in payloads.items():output.writestr(name,data)
        output.writestr('manifest.json',json.dumps(manifest,indent=2).encode())
else:
    with zipfile.ZipFile(archive) as existing:
        assert json.loads(existing.read('manifest.json'))==manifest
        assert existing.testzip() is None
raw=archive.read_bytes();assert 0<len(raw)<=4*1024**2
chunk=raw[:48000]
print(json.dumps({'archive':'gpu08-resolution-evidence.zip','bytes':len(raw),'sha256':sha(raw),
    'chunk_bytes':48000,'total_chunks':math.ceil(len(raw)/48000),'chunk_index':0,
    'chunk_length':len(chunk),'chunk_sha256':sha(chunk),'chunk_b64':base64.b64encode(chunk).decode(),
    'selected_files':len(payloads),'manifest_sha256':sha(json.dumps(manifest,indent=2).encode())}))
