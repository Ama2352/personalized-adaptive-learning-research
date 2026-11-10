"""Chỉ đóng gói log và receipt nhỏ, không model, dataset hoặc credentials."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
code = '''import base64, hashlib, io, json, subprocess, sys, zipfile
runtime_code = "import json,sys,torch,numpy,pandas,duckdb,pytest; print(json.dumps(dict(python=sys.version,executable=sys.executable,prefix=sys.prefix,torch=torch.__version__,cuda_build=torch.version.cuda,numpy=numpy.__version__,pandas=pandas.__version__,duckdb=duckdb.__version__,pytest=pytest.__version__)))"
runtime = subprocess.check_output([AKT_PY,'-B','-c',runtime_code],env=dict(ENV,CUDA_VISIBLE_DEVICES=''),text=True,timeout=60)
(OUTPUT/'runtime.json').write_text(runtime)
names = ['bundle-manifest.json','transfer.json','setup-started.json','setup-status.json',
         'setup-venv.log','setup-venv-target.log','setup-packages.log','setup-clone.log',
         'setup-pin.log','setup-freeze.log','missing-packages.json','install-report.json','runtime.json',
         'baseline-command.json','baseline-tests.log','baseline-tests.xml','baseline-status.json',
         'research-core-command.json','research-core-tests.log','research-core-tests.xml','research-core-status.json']
names = [name for name in names if (OUTPUT/name).is_file()]
assert all((OUTPUT/name).stat().st_size <= 1024*1024 for name in names)
assert sum((OUTPUT/name).stat().st_size for name in names) <= 4*1024*1024
inventory = {name:hashlib.sha256((OUTPUT/name).read_bytes()).hexdigest() for name in names}
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for name in names: archive.writestr(name,(OUTPUT/name).read_bytes())
    archive.writestr('SHA256.json',json.dumps(inventory,indent=2))
KLTN_EXPORT = buffer.getvalue()
KLTN_EXPORT_PARTS = [base64.b64encode(KLTN_EXPORT[i:i+20000]).decode('ascii') for i in range(0,len(KLTN_EXPORT),20000)]
print(json.dumps({'bytes':len(KLTN_EXPORT),'sha256':hashlib.sha256(KLTN_EXPORT).hexdigest(),'parts':len(KLTN_EXPORT_PARTS),'files':len(names),'runtime':json.loads(runtime)}))
'''
compile(code, '<colab-export>', 'exec')
(ROOT/'artifacts/akt/colab/requests/current-cpu-export-add.json').write_text(
    json.dumps(dict(cellIndex=5, language='python', code=code)), encoding='utf-8')
