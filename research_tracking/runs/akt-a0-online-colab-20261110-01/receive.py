"""Kiểm archive và JUnit của cả lượt lỗi lẫn lượt sửa trên Colab."""
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SESSION = ROOT/'artifacts/akt/private/colab-bridge/session-7b319172d1ee4b068afd33de8b74beab'
parts = {}
for path in SESSION.glob('result*.json'):
    value = json.loads(path.read_bytes())
    for output in (value.get('data') or {}).get('outputs', []):
        if output.get('output_type') != 'stream': continue
        try:
            decoded = json.loads(''.join(output.get('text', [])).strip())
        except ValueError:
            continue
        if type(decoded) is dict and set(decoded) == {'a0_part', 'data'}:
            part = base64.b64decode(decoded['data'], validate=True)
            index = decoded['a0_part']
            assert index not in parts or parts[index] == part
            parts[index] = part
assert set(parts) == {0, 1, 2}, sorted(parts)
raw = b''.join(parts[i] for i in range(3))
sha = hashlib.sha256(raw).hexdigest()
assert len(raw) == 41989 and sha == '336705f845d0a82f0a353cbb06db2eabf2aad08e1d6e8ca1339c0035a80f629b'
archive = zipfile.ZipFile(io.BytesIO(raw))
assert archive.testzip() is None
inventory = json.loads(archive.read('SHA256.json'))
assert len(archive.namelist()) == len(set(archive.namelist())) == len(inventory)+1
assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
for name, digest in inventory.items():
    path = PurePosixPath(name)
    assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
    assert hashlib.sha256(archive.read(name)).hexdigest() == digest
remote = HERE/'remote'
remote.mkdir(exist_ok=False)
for name in archive.namelist():
    path = remote/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(archive.read(name))
summary = {}
for prefix in ('attempt01', 'attempt02'):
    cases = list(ET.parse(remote/prefix/'a0-online-tests.xml').getroot().iter('testcase'))
    counts = {tag:sum(c.find(tag) is not None for c in cases) for tag in ('failure', 'error', 'skipped')}
    status = json.loads((remote/prefix/'a0-online-status.json').read_bytes())
    assert len(cases) == status['tests'] == 22 and counts == status['counts']
    assert status['source_unchanged'] is True
    summary[prefix] = status
assert summary['attempt01']['status'] == 'FAILED' and summary['attempt01']['counts']['error'] == 12
assert summary['attempt02']['status'] == 'PASS' and not any(summary['attempt02']['counts'].values())
manifest = json.loads((remote/'attempt02/bundle-manifest.json').read_bytes())
for name in ('src/knowledge_tracing/akt/research_a0_online.py', 'tests/akt/test_research_a0_online.py',
             'tests/akt/test_research_graph_model.py'):
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == manifest['files'][name]
(HERE/'verification.json').write_text(json.dumps(dict(archive_sha256=sha, archive_bytes=len(raw),
    remote_files=len(inventory), suites=summary, source_matches_local=True), indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
