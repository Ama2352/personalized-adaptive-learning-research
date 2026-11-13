"""Ghép phần tải MCP vào D, kiểm SHA/CRC/inventory trước nghiệm thu."""
import base64
import hashlib
import json
from pathlib import Path
import zipfile

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
SESSION = ROOT/'artifacts/akt/private/colab-bridge/session-1b6a9d7307c24e4ab1ff1117f7f21dcb'
OUTPUT = ROOT/'experiments/akt/results/colab-junyi-comparison-20261113-01'
OUTPUT.mkdir(parents=True,exist_ok=True)
receipt = json.loads((BUNDLE/'colab-archive-receipt.json').read_text())
partial = OUTPUT/'artifacts.zip.partial'
archive = OUTPUT/'artifacts.zip'
if archive.exists():
    raise FileExistsError('Archive đã nghiệm thu, không ghi đè.')
seen = {}
with partial.open('w+b') as output:
    for path in SESSION.glob('result-*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        outputs = (data.get('structured_content') or data.get('data') or {}).get('outputs', [])
        for item in outputs:
            text = ''.join(item.get('text',[])).strip()
            if not text.startswith('{'):
                continue
            try:
                record = json.loads(text)
            except ValueError:
                continue
            if record.get('event') != 'COMPARISON_CHUNK':
                continue
            payload = base64.b64decode(record['data'],validate=True)
            digest = hashlib.sha256(payload).hexdigest()
            assert digest == record['sha256'] and len(payload) == record['bytes']
            index = record['index']
            if index in seen:
                assert seen[index]['sha256'] == digest
            output.seek(index*262144)
            output.write(payload)
            seen[index] = dict(index=index,bytes=len(payload),sha256=digest)
expected_parts = (receipt['bytes']+262143)//262144
if set(seen) != set(range(expected_parts)):
    print(json.dumps(dict(status='INCOMPLETE_DOWNLOAD',parts=len(seen),expected=expected_parts)))
    raise SystemExit(2)
assert partial.stat().st_size == receipt['bytes']
assert hashlib.sha256(partial.read_bytes()).hexdigest() == receipt['sha256']
with zipfile.ZipFile(partial) as stream:
    assert stream.testzip() is None
    inventory = json.loads(stream.read('INVENTORY.json'))
    assert set(stream.namelist()) == {*inventory,'INVENTORY.json'}
    for name, expected in inventory.items():
        payload = stream.read(name)
        assert len(payload) == expected['bytes']
        assert hashlib.sha256(payload).hexdigest() == expected['sha256']
        if name.endswith(('.log','.xml','.json')):
            target = BUNDLE/('colab-'+Path(name).name)
            if target.exists():
                assert target.read_bytes() == payload
            else:
                target.write_bytes(payload)
    result = json.loads(stream.read(next(name for name in inventory if name.endswith('/result.json'))))
    assert result['status'] == 'PASS_SYNTHETIC_A0_A1_T4_BATCH128'
    reference_initial = 'a29f65ae4c668b55c1ff30a19f41f232a6761848ba2304c9cde5ba594db9fa9c'
    assert result['initial_backbone_sha256'] == reference_initial
    assert all(result[key] is True for key in ('model_and_adam_resume_exact',
        'causal_current_future_test','graph_off_matches_a0'))
    checkpoint = next(name for name in inventory if name.endswith('/step1.pt'))
    assert inventory[checkpoint]['sha256'] == result['checkpoint_sha256']
    overlay = json.loads(stream.read(next(name for name in inventory if name.endswith('/source-overlay.json'))))
    assert hashlib.sha256((ROOT/overlay['path']).read_bytes()).hexdigest() == overlay['after']
partial.rename(archive)
report = dict(status='PASS_ARCHIVE_SHA_CRC_INVENTORY_T4_RESULT',archive=str(archive.relative_to(ROOT)),
    bytes=receipt['bytes'],sha256=receipt['sha256'],members=len(inventory),parts=len(seen),
    checkpoint_member=checkpoint,checkpoint_sha256=result['checkpoint_sha256'],
    initial_backbone_matches_a0_h100=True,source_overlay_matches_local=True,
    t4_seconds=result['seconds'],max_vram_allocated=result['max_vram_allocated'],
    a2_a3_junyi_ready=False,paid_training_ready=False)
(BUNDLE/'artifact-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BUNDLE/'colab-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
