"""Nhận đủ log bốn lượt Colab, nghiệm thu JUnit và byte nguồn độc lập."""
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import runpy
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
        if type(decoded) is dict and set(decoded) == {'integration_part', 'data'}:
            part = base64.b64decode(decoded['data'], validate=True)
            index = decoded['integration_part']
            assert index not in parts or parts[index] == part
            parts[index] = part
assert set(parts) == set(range(12)), sorted(parts)
raw = b''.join(parts[index] for index in range(12))
sha = hashlib.sha256(raw).hexdigest()
assert len(raw) == 279901 and sha == 'b5229857ddf499028a4f9a7f675839b54606d9552d30ecbae6194bdc14902704'
archive = zipfile.ZipFile(io.BytesIO(raw))
assert archive.testzip() is None
inventory = json.loads(archive.read('SHA256.json'))
assert len(archive.namelist()) == len(set(archive.namelist())) == len(inventory)+1
assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
for name, digest in inventory.items():
    p = PurePosixPath(name)
    assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
    assert hashlib.sha256(archive.read(name)).hexdigest() == digest

native = ROOT/'experiments/akt/results/colab-integration-20261110-01'
native.mkdir(exist_ok=False)
(native/'logs.zip').write_bytes(raw)
remote = HERE/'remote'
remote.mkdir(exist_ok=False)
summaries = {}
for number in range(1, 5):
    prefix = f'attempt{number:02d}'
    status = json.loads(archive.read(prefix+'/status.json'))
    totals = dict(tests=0, failure=0, error=0, skipped=0)
    identifiers = []
    for group in status['groups']:
        xml = archive.read(prefix+'/'+group['name']+'.xml')
        cases = list(ET.fromstring(xml).iter('testcase'))
        counts = {tag:sum(c.find(tag) is not None for c in cases) for tag in ('failure', 'error', 'skipped')}
        assert len(cases) == group['tests'] and counts == group['counts']
        totals['tests'] += len(cases)
        for key, count in counts.items(): totals[key] += count
        identifiers.extend((c.get('classname'), c.get('name')) for c in cases)
        if number == 4: (remote/('04-'+group['name']+'.xml')).write_bytes(xml)
    assert len(identifiers) == len(set(identifiers))
    assert status['source_unchanged'] is True and status['elapsed_seconds'] <= 600
    summaries[prefix] = dict(status=status['status'], totals=totals, elapsed_seconds=status['elapsed_seconds'])
    (remote/(f'{number:02d}-status.json')).write_bytes(archive.read(prefix+'/status.json'))
    if number == 4:
        assert status['status'] == 'PASS_SCOPED_PORTABILITY_ONLY'
        assert totals == dict(tests=1992, failure=0, error=0, skipped=0)
        assert sum(g['module_count'] for g in status['groups']) == 92
        assert status['excluded_node'] == 'tests/akt/test_runtime.py::test_native_akt_import_cpu'
        assert b'1 deselected' in archive.read(prefix+'/remaining.log')
        current = json.loads(archive.read(prefix+'/sources.json'))
        contents, _ = runpy.run_path(str(ROOT/'scripts/akt/build_colab_bundle.py'))['bundle_contents']()
        assert {name:hashlib.sha256(data).hexdigest() for name, data in contents.items()} == current['files']
        (remote/'04-sources.json').write_bytes(archive.read(prefix+'/sources.json'))
(remote/'runtime.json').write_bytes(archive.read('runtime.json'))
(remote/'archive-inventory.json').write_bytes(archive.read('SHA256.json'))
proof = dict(archive_sha256=sha, archive_bytes=len(raw), archive_members=len(inventory),
    archive_relative=(native/'logs.zip').relative_to(ROOT).as_posix(), attempts=summaries,
    explicit_deselections=1, source_files_in_bundle=len(current['files']), local_source_matches=True,
    fresh_gate=False, isolated_runtime_verified=False, cuda_verified=False, modal_spend_usd=0)
(HERE/'verification.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
(native/'receipt.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
print(json.dumps(summaries, indent=2))
