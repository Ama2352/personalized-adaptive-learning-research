import base64,hashlib,io,json,time,zipfile
from pathlib import Path
r=Path('/content/kltn-isolated-cpu-20261110-02')
files={}
for area,patterns in [('artifacts/akt/runtime/recovery02',['*.json','*.log']),('artifacts/akt/runtime/isolated-install01',['*.json','*.stdout','*.stderr','*.log']),('artifacts/akt/runtime/isolated-gate198-01',['*.json','*.log']),('artifacts/akt/preflight',['*colab-isolated198-20261110-01*','gate2-current.json'])]:
    for pattern in patterns:
        for p in (r/area).glob(pattern):
            if p.is_file():
                assert p.stat().st_size<=16*1024**2
                files[p.relative_to(r).as_posix()]=p.read_bytes()
assert files and sum(map(len,files.values()))<=128*1024**2
files['BUNDLE_MANIFEST.json']=(r/'BUNDLE_MANIFEST.json').read_bytes()
inventory={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
b=io.BytesIO()
with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items():z.writestr(name,data)
    z.writestr('SHA256.json',json.dumps(inventory,indent=2)+'\n')
ISOLATED02_EXPORT=b.getvalue()
print(json.dumps(dict(export='ISOLATED02',bytes=len(ISOLATED02_EXPORT),sha256=hashlib.sha256(ISOLATED02_EXPORT).hexdigest(),parts=(len(ISOLATED02_EXPORT)+23999)//24000,members=len(files),observed_at_epoch=time.time())),flush=True)
