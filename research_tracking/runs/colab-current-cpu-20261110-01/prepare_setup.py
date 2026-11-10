"""Tạo cell giải nén và chuẩn bị venv từ notebook hiện có."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
notebook = json.loads((ROOT/'notebooks/akt_colab_synthetic.ipynb').read_bytes())
code = '''import base64, hashlib, io, json, os, pathlib, subprocess, sys, uuid, zipfile
from pathlib import Path, PurePosixPath
assert sys.platform == 'linux' and Path('/content').is_dir()
assert len(KLTN_TRANSFER) == 30
raw = base64.b64decode(''.join(KLTN_TRANSFER), validate=True)
assert hashlib.sha256(raw).hexdigest() == 'c7c0fbb160e2ef5f62c6a5f002242bdb36528c4994e3edf17d4c314bf65d2707'
archive = zipfile.ZipFile(io.BytesIO(raw))
names = archive.namelist()
assert len(names) == len(set(names)) and archive.testzip() is None
assert sum(i.file_size for i in archive.infolist()) <= 50*1024*1024
manifest = json.loads(archive.read('BUNDLE_MANIFEST.json'))
assert manifest['schema_version'] == 2
assert set(names) == set(manifest['files']) | {'BUNDLE_MANIFEST.json'}
for name, sha in manifest['files'].items():
    p = PurePosixPath(name)
    assert not p.is_absolute() and '..' not in p.parts and '\\\\' not in name
    assert hashlib.sha256(archive.read(name)).hexdigest() == sha
ROOT = Path('/content') / ('kltn-current-cpu-' + uuid.uuid4().hex)
ROOT.mkdir()
archive.extractall(ROOT)
OUTPUT = ROOT/'colab-evidence'
OUTPUT.mkdir()
(OUTPUT/'bundle-manifest.json').write_bytes(archive.read('BUNDLE_MANIFEST.json'))
(OUTPUT/'transfer.json').write_text(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(), 'files':len(manifest['files']), 'root':str(ROOT)}))
COLAB_CONNECTION_OK = SOURCE_READY = True
'''
extraction = dict(cellId='L7Vz6DBtqB1V', content=code+'\nprint("SOURCE_VERIFIED", str(ROOT), len(manifest["files"]), flush=True)\n')
(ROOT/'artifacts/akt/colab/requests/current-cpu-extract.json').write_text(json.dumps(extraction), encoding='utf-8')
code += ''.join(notebook['cells'][3]['source'])
path = ROOT/'artifacts/akt/colab/requests/current-cpu-setup.json'
path.write_text(json.dumps(dict(cellId='D6wvrfzyoyjR', content=code)), encoding='utf-8')
compile(code, '<colab-setup>', 'exec')
print(path)
