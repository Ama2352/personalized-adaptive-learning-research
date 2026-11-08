"""Tạo source02 độc quyền từ source01 đã freeze, chỉ sửa scheme purelib."""
import ast,difflib,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent
old=W/'discovery.py';new=W/'discovery02.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=old.read_bytes();assert sha(raw)=='c176c85ad5e93c6daf229f9f7f884b277aa11c1ae99a259389059292784d0b75'
before="v=Path(sys.argv[1]);pure=Path(sysconfig.get_path('purelib',vars={'base':str(v),'platbase':str(v)}))"
after="v=Path(sys.argv[1])\nif 'venv' not in sysconfig.get_scheme_names():raise ValueError('explicit venv scheme unavailable')\npure=Path(sysconfig.get_path('purelib',scheme='venv',vars={'base':str(v),'platbase':str(v)}))"
assert raw.count(before.encode())==1
payload=raw.replace(before.encode(),after.encode());ast.parse(payload)
with new.open('xb') as f:f.write(payload)
assert old.read_bytes()==raw and new.read_bytes()==payload
profile=W/'discovery_profile01.json';assert sha(profile.read_bytes())=='0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228'
record={'status':'EXCLUSIVE_SOURCE02_NARROW_DERIVED_COPY_NO_EXECUTION','source01_sha256_before':sha(raw),'source01_sha256_after':sha(old.read_bytes()),'source02_sha256_before_write':sha(payload),'source02_sha256_after_write':sha(new.read_bytes()),'source01_bytes':len(raw),'source02_bytes':len(payload),'profile_unchanged_sha256':sha(profile.read_bytes()),'diff':''.join(difflib.unified_diff(raw.decode().splitlines(True),payload.decode().splitlines(True),fromfile='discovery.py',tofile='discovery02.py')),'reason':'Actual Debian defaultscheme posix_local pointed at nonexistent .venv/local/lib/python3.13/dist-packages. No package/venv repair or install.'}
(W/'source02-copy-inventory.json').open('x',encoding='utf-8').write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='diff'}))
