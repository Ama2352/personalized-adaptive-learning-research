"""Nhận gói kết quả Colab, lưu D và kiểm SHA/CRC/nguồn/phạm vi phép đo."""
import base64
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

BUNDLE=Path(__file__).resolve().parent
ROOT=BUNDLE.parents[2]
SESSION=ROOT/'artifacts/akt/private/colab-bridge/session-eb39ce9d2e55497e99f6a906e61cbaba'
record=None
for path in sorted(SESSION.glob('result-*.json'),key=lambda p:p.stat().st_mtime,reverse=True):
    document=json.loads(path.read_text(encoding='utf-8'))
    outputs=(document.get('structured_content') or document.get('data') or {}).get('outputs',[])
    for item in outputs:
        text=''.join(item.get('text',[])).strip()
        if not text.startswith('{'):
            continue
        try:
            candidate=json.loads(text)
        except ValueError:
            continue
        if candidate.get('event')=='VALIDATION_ARCHIVE':
            record=candidate
            break
    if record:
        break
assert record is not None,'Chưa có artifact từ Colab'
payload=base64.b64decode(record['data'],validate=True)
assert len(payload)==record['bytes'] and hashlib.sha256(payload).hexdigest()==record['sha256']
output=ROOT/'experiments/akt/results/colab-validation-batch-20261113-01'
output.mkdir(parents=True,exist_ok=True)
archive_path=output/'artifacts.zip'
if archive_path.exists():
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest()==record['sha256']
else:
    with archive_path.open('xb') as stream:
        stream.write(payload)
assert hashlib.sha256(archive_path.read_bytes()).hexdigest()==record['sha256']
reports={}
with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    assert archive.testzip() is None
    inventory=json.loads(archive.read('INVENTORY.json'))
    assert len(inventory)==record['files'] and set(archive.namelist())=={*inventory,'INVENTORY.json'}
    for name,entry in inventory.items():
        data=archive.read(name)
        assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
        if name.endswith('/result.json'):
            case='positive' if 'positive-' in name else 'balanced'
            report=json.loads(data)
            assert report['status']=='PASS_SYNTHETIC_VALIDATION_BATCH128_PARITY'
            assert report['model_training'] is False and report['a0_checkpoint_epoch_selection_replayed'] is False
            for result in report['results']:
                assert result['targets_metadata_exact'] is True and result['targets']==12800
                assert result['max_abs_probability_delta']<=1e-6
                assert abs(result['log_loss_delta'])<=1e-6
                assert result['metrics']['1']['population_sha256']==result['metrics']['128']['population_sha256']
            if case=='positive':
                assert report['fixture_signal']=='positive'
                assert report['results'][1]['graph_residual_vs_a0_max_abs']>=.01
            reports[case]=report
            destination=BUNDLE/(case+'-result.json')
        else:
            destination=BUNDLE/('colab-'+Path(name).name)
        if destination.exists():
            assert destination.read_bytes()==data
        else:
            destination.write_bytes(data)
assert set(reports)=={'balanced','positive'}
suite=ET.parse(BUNDLE/'colab-test-attempt-01.xml').getroot().find('testsuite')
assert suite.attrib['tests']=='126' and all(suite.attrib[key]=='0' for key in ('failures','errors','skipped'))
overlay=json.loads((BUNDLE/'colab-probe-source-overlay.json').read_text())
assert hashlib.sha256((ROOT/overlay['path']).read_bytes()).hexdigest()==overlay['after']
receipt={key:value for key,value in record.items() if key!='data'}
receipt.update(status='PASS_SHA_CRC_INVENTORY_PARITY_AND_NONZERO_GRAPH',
    local_archive=archive_path.relative_to(ROOT).as_posix(),linux_tests=126,
    actual_t4=True,model_training=False,a0_full_selection_replay=False,modal_spent_usd=0)
(BUNDLE/'artifact-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BUNDLE/'colab-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=receipt['status'],bytes=len(payload),files=len(inventory),
    positive_results=[dict(variant=row['variant'],legacy=row['legacy_mean_seconds'],
        batched=row['batch128_mean_seconds'],speedup=row['speedup'],
        vram_gib=row['batch128_peak_vram_bytes']/1024**3) for row in reports['positive']['results']]),ensure_ascii=False))
