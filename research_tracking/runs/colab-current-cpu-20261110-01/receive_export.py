"""Nhận log từ MCP, kiểm archive và từng SHA trước lưu bằng chứng."""
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SESSION = ROOT/'artifacts/akt/private/colab-bridge/session-7b319172d1ee4b068afd33de8b74beab'
parts = {}
for path in SESSION.glob('result*.json'):
    value = json.loads(path.read_bytes())
    for output in (value.get('data') or {}).get('outputs', []):
        if output.get('output_type') != 'stream':
            continue
        text = ''.join(output.get('text', [])).strip()
        try:
            decoded = json.loads(text)
        except ValueError:
            continue
        if type(decoded) is dict and set(decoded) == {'index', 'data'}:
            index = decoded['index']
            raw = base64.b64decode(decoded['data'], validate=True)
            assert index not in parts or parts[index] == raw
            parts[index] = raw
assert set(parts) == {0, 1}, sorted(parts)
raw = b''.join(parts[index] for index in range(2))
assert len(raw) == 31922
assert hashlib.sha256(raw).hexdigest() == 'bfe3be32e853ba2456d43915811b9f8f6a8d9a194bff5220e8007246d37d4ab1'
archive = zipfile.ZipFile(io.BytesIO(raw))
assert archive.testzip() is None
inventory = json.loads(archive.read('SHA256.json'))
assert len(archive.namelist()) == len(set(archive.namelist())) == len(inventory)+1
assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
for name, sha in inventory.items():
    assert Path(name).name == name and hashlib.sha256(archive.read(name)).hexdigest() == sha
out = HERE/'remote'
out.mkdir(exist_ok=False)
for name in archive.namelist():
    (out/name).write_bytes(archive.read(name))
summary = {}
for prefix in ('baseline', 'research-core'):
    cases = list(ET.parse(out/f'{prefix}-tests.xml').getroot().iter('testcase'))
    assert cases and all(c.find(tag) is None for c in cases for tag in ('failure', 'error', 'skipped'))
    status = json.loads((out/f'{prefix}-status.json').read_bytes())
    assert status['status'] == 'PASS' and status['tests'] == len(cases) and status['source_unchanged'] is True
    summary[prefix] = status
(HERE/'verification.json').write_text(json.dumps(dict(archive_sha256=hashlib.sha256(raw).hexdigest(),
    archive_bytes=len(raw), remote_files=len(inventory), suites=summary), indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
