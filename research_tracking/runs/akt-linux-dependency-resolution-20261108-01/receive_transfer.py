"""Nhận bằng chứng đã chọn, kiểm SHA và đường dẫn trước khi trích xuất."""
import base64, hashlib, io, json, zipfile
from pathlib import Path, PurePosixPath

w=Path(__file__).resolve().parent
d=Path('artifacts/akt/private/colab-bridge/session-fd8fa3f60adf408285b7fc231a9e4cf0')
p=max(d.glob('result-*.json'),key=lambda p:p.stat().st_mtime_ns)
r=json.loads(p.read_text()); assert r['is_error'] is False
v=r.get('structured_content') or r['data']
assert not any(o.get('output_type')=='error' for o in v['outputs'])
s=''.join(''.join(o.get('text',[])) if isinstance(o.get('text'),list) else o.get('text','') for o in v['outputs'] if o.get('name')=='stdout')
payload=json.loads(s)
sha=lambda b:hashlib.sha256(b).hexdigest()
for c in payload['chunks']:
    assert c['index'] in (1,2)
    b=base64.b64decode(c['b64'],validate=True); assert sha(b)==c['sha256']
    with (w/'transfer'/f"chunk-{c['index']:04d}.bin").open('xb') as f:f.write(b)
plan=json.loads((w/'transfer/plan.json').read_text())
raw=b''.join((w/'transfer'/f'chunk-{i:04d}.bin').read_bytes() for i in range(3))
assert len(raw)==plan['bytes'] and sha(raw)==plan['sha256']
with (w/'transfer'/plan['archive']).open('xb') as f:f.write(raw)
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    names=z.namelist(); assert len(names)==len(set(names))==15 and z.testzip() is None
    for n in names:
        pp=PurePosixPath(n); assert not pp.is_absolute() and '..' not in pp.parts and '\\' not in n
        assert z.getinfo(n).file_size<=8*1024**2
    m=json.loads(z.read('manifest.json'));assert sha(z.read('manifest.json'))==plan['manifest_sha256']
    assert set(names)==set(m['files'])|{'manifest.json'}
    for n,a in m['files'].items():
        b=z.read(n);assert len(b)==a['bytes'] and sha(b)==a['sha256']
    target=w/'received';target.mkdir(exist_ok=False)
    for n in names:
        dst=target/n;dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open('xb') as f:f.write(z.read(n))
    for n,a in m['files'].items():assert sha((target/n).read_bytes())==a['sha256']
receipt={'status':'VERIFIED_LOCAL_COPY','files':14,'archive_sha256':sha(raw),'manifest_sha256':plan['manifest_sha256'],'remote_receipt_sha256':sha(p.read_bytes()),'scope':'Phân giải dependency CPU; chưa cài đặt, chưa kiểm CUDA, không dùng Modal.'}
with (w/'transfer/acceptance.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
