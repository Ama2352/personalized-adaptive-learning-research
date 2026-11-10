import base64,hashlib,io,json,os,shutil,subprocess,sys,traceback,zipfile
from pathlib import Path
try:
    assert sys.platform=='linux' and not list(Path('/dev').glob('nvidia[0-9]*'))
    assert os.environ.get('COLAB_GPU') in (None,'','0') and not os.environ.get('COLAB_TPU_ADDR')
    assert shutil.disk_usage('/content').free>=30*1024**3
    fresh=Path('/content/kltn-isolated-cpu-20261110-01')
    assert not fresh.exists()
    current={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in manifest['files']}
    assert current==manifest['files']
    payload=base64.b64decode(ISOLATED_INPUT_B64,validate=True)
    assert hashlib.sha256(payload).hexdigest()=='a1200bb5dace708435ba4c9ff0bfa7ddba29d7a121f5634faa933db63d9306d0'
    z=zipfile.ZipFile(io.BytesIO(payload));assert z.testzip() is None
    pins=json.loads(z.read('input-manifest.json'))
    assert len(z.namelist())==len(set(z.namelist()))==len(pins['files'])+1
    assert set(z.namelist())==set(pins['files'])|{'input-manifest.json'}
    for name,digest in pins['files'].items():
        assert Path(name).name==name and hashlib.sha256(z.read(name)).hexdigest()==digest
    fresh.mkdir()
    for name in manifest['files']:
        source=ROOT/name;target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    upstream=ROOT/'artifacts/akt/dependencies/upstream'
    assert sum(p.stat().st_size for p in upstream.rglob('*') if p.is_file())<=64*1024**2
    shutil.copytree(upstream,fresh/'artifacts/akt/dependencies/upstream')
    inputs=fresh/'artifacts/akt/runtime/isolated-input01';inputs.mkdir(parents=True)
    for name in z.namelist():(inputs/name).write_bytes(z.read(name))
    lock=fresh/'artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt'
    lock.parent.mkdir(parents=True);lock.write_bytes(z.read('candidate-linux-cuda.lock.txt'))
    result=subprocess.run([sys.executable,'-B','-m','venv','--without-pip',str(fresh/'.venv')],capture_output=True,text=True,timeout=30)
    (inputs/'venv-create.stdout').write_text(result.stdout);(inputs/'venv-create.stderr').write_text(result.stderr)
    assert result.returncode==0
    assert 'include-system-site-packages = false' in (fresh/'.venv/pyvenv.cfg').read_text().lower()
    proof=dict(status='ISOLATED_VENV_PREPARED_NOT_INSTALLED',source_manifest=manifest,root=str(fresh),input_zip_sha256='a1200bb5dace708435ba4c9ff0bfa7ddba29d7a121f5634faa933db63d9306d0',free_disk_bytes=shutil.disk_usage(fresh).free)
    (inputs/'preparation.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps({k:v for k,v in proof.items() if k!='source_manifest'}),flush=True)
except BaseException:
    print(traceback.format_exc(),flush=True)
