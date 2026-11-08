"""Đọc metadata/RECORD local, không import hoặc thực thi các scripts pywin32."""
from pathlib import Path
import base64
import hashlib
from importlib import metadata
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT/'.venv'
dist = metadata.distribution('pywin32')
assert dist.version == '312'
site = ROOT/'.venv/Lib/site-packages'
namespace = site/'win32/scripts'
expected = {}
for entry in dist.files or ():
    name = entry.as_posix()
    if not ((name.startswith('win32/scripts/') and name.endswith('.py')) or name == 'pywin32.pth'):
        continue
    path = Path(dist.locate_file(entry))
    assert path.resolve() == path.absolute() and path.is_relative_to(site)
    assert path.is_file() and not path.is_symlink()
    assert entry.hash is not None and entry.hash.mode == 'sha256'
    raw = path.read_bytes()
    assert len(raw) == entry.size
    digest = hashlib.sha256(raw).digest()
    assert base64.urlsafe_b64encode(digest).decode().rstrip('=') == entry.hash.value
    expected[path.relative_to(ROOT).as_posix()] = digest.hex()
actual = {p.relative_to(ROOT).as_posix() for p in namespace.rglob('*.py')}
assert actual == {name for name in expected if '/win32/scripts/' in name}
assert not (namespace/'__init__.py').exists()
assert not (namespace/'akt').exists() and not (namespace/'research').exists()
for name in ('METADATA','RECORD'):
    path = site/'pywin32-312.dist-info'/name
    expected[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
proof = dict(status='INSTALLED_PYWIN32_RECORD_MATCHED_NOT_WHEEL_ATTESTATION',
             package='pywin32',version=dist.version,
             namespace_relative=namespace.relative_to(ROOT).as_posix(),
             file_sha256=expected,script_count=len(actual),
             project_children_absent=True,no_scripts_executed=True,
             scope_vi='Đối chiếu bytes local với RECORD đã cài; không xác thực wheel từ mạng hoặc attestation môi trường toàn bộ.')
with (PREP/'pywin32_namespace_record01.json').open('x',encoding='utf-8') as stream:
    json.dump(proof,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(status=proof['status'],script_count=len(actual),files=len(expected),proof_sha256=hashlib.sha256((PREP/'pywin32_namespace_record01.json').read_bytes()).hexdigest())))
