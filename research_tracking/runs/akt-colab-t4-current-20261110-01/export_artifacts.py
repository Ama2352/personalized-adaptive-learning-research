import base64,hashlib,io,json,time,zipfile
from pathlib import Path
r=Path('/content/kltn-current-t4-20261110-01');files={}
for area in ['artifacts/akt/runtime/t4-setup01','artifacts/akt/runtime/isolated-install01','artifacts/akt/runtime/isolated-install02','artifacts/akt/runtime/t4-smoke01','experiments/akt/results/current-t4-four-variant-smoke-20261110-01']:
    for p in (r/area).iterdir():
        if p.is_file() and p.suffix in ('.json','.log','.stdout','.stderr','.py'):
            assert p.stat().st_size<=16*1024**2
            files[p.relative_to(r).as_posix()]=p.read_bytes()
assert sum(map(len,files.values()))<=128*1024**2
files['BUNDLE_MANIFEST.json']=(r/'BUNDLE_MANIFEST.json').read_bytes()
inventory={k:hashlib.sha256(v).hexdigest() for k,v in files.items()}
b=io.BytesIO()
with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items():z.writestr(name,data)
    z.writestr('SHA256.json',json.dumps(inventory,indent=2)+'\n')
T4_EXPORT=b.getvalue()
print(json.dumps(dict(export='CURRENT_T4',bytes=len(T4_EXPORT),sha256=hashlib.sha256(T4_EXPORT).hexdigest(),parts=(len(T4_EXPORT)+23999)//24000,members=len(files),observed_at_epoch=time.time())),flush=True)
