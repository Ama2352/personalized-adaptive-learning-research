import base64,hashlib,io,json,shutil,subprocess,sys,traceback,zipfile
from pathlib import Path
try:
    fresh=Path('/content/kltn-isolated-cpu-20261110-01')
    assert fresh.is_dir() and not (fresh/'.venv').exists()
    assert all(hashlib.sha256((fresh/name).read_bytes()).hexdigest()==sha for name,sha in manifest['files'].items())
    upstream=ROOT/'artifacts/akt/dependencies/upstream'
    size=sum(p.stat().st_size for p in upstream.rglob('*') if p.is_file())
    assert size==93951280 and size<=128*1024**2 and shutil.disk_usage(fresh).free>=30*1024**3
    shutil.copytree(upstream,fresh/'artifacts/akt/dependencies/upstream')
    payload=base64.b64decode(''.join(ISOLATED_INPUT_CHUNKS[i] for i in range(12)),validate=True)
    assert hashlib.sha256(payload).hexdigest()=='a1200bb5dace708435ba4c9ff0bfa7ddba29d7a121f5634faa933db63d9306d0'
    z=zipfile.ZipFile(io.BytesIO(payload));assert z.testzip() is None
    inputs=fresh/'artifacts/akt/runtime/isolated-input01';inputs.mkdir(parents=True)
    for name in z.namelist():(inputs/name).write_bytes(z.read(name))
    lock=fresh/'artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt'
    lock.parent.mkdir(parents=True);lock.write_bytes(z.read('candidate-linux-cuda.lock.txt'))
    result=subprocess.run([sys.executable,'-B','-m','venv','--without-pip',str(fresh/'.venv')],capture_output=True,text=True,timeout=30)
    (inputs/'venv-create.stdout').write_text(result.stdout);(inputs/'venv-create.stderr').write_text(result.stderr)
    assert result.returncode==0
    assert 'include-system-site-packages = false' in (fresh/'.venv/pyvenv.cfg').read_text().lower()
    proof=dict(status='ISOLATED_VENV_PREPARED_NOT_INSTALLED',source_manifest=manifest,root=str(fresh),upstream_bytes=size,upstream_copy_cap_bytes=128*1024**2,input_zip_sha256=hashlib.sha256(payload).hexdigest(),free_disk_bytes=shutil.disk_usage(fresh).free)
    (inputs/'preparation.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps({k:v for k,v in proof.items() if k!='source_manifest'}),flush=True)
except BaseException:
    print(traceback.format_exc(),flush=True)
