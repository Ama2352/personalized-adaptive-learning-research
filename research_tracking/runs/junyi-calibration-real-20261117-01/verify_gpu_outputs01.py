"""Nghiệm thu metadata bốn snapshot inference, không đọc dataset hoặc model."""
import hashlib
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
baseline = json.loads((BUNDLE / 'REQUEST_A0_GPU01.json').read_text())
rows = []
pins = {}
for variant in ('A0', 'A1', 'A2', 'A3'):
    names = [f'REQUEST_{variant}_GPU01.json', f'{variant}_GPU_RESULT01.json',
             f'{variant}_GPU_METADATA_DRIVE01.json']
    request, outer, publication = [json.loads((BUNDLE / name).read_text()) for name in names]
    assert request['variant'] == variant
    assert request['gpu_output'] == f"{baseline['run_id']}/{variant.lower()}-numeric/payloads"
    assert {key: value for key, value in request.items() if key not in ('variant', 'gpu_output')} == {
        key: value for key, value in baseline.items() if key not in ('variant', 'gpu_output')}
    result = outer['result']
    assert outer['status'] == 'STAGE_COMMITTED'
    assert result['status'] == 'GPU_NUMERIC_COMMITTED_RELEASE_GPU'
    assert result['counts'] == dict(fitted_targets=1621484, oov_targets=0,
                                    records=28653, targets=1621484, windows=28653)
    assert publication['status'] == 'OPERATION_METADATA_PUBLISHED'
    assert publication['publications']
    assert all(item['account'] == 'honguyenminhsang2005@gmail.com'
               and item['status'] == 'DRIVE_SHA256_VERIFIED'
               for item in publication['publications'])
    rows.append(dict(variant=variant, targets=result['counts']['targets'],
                     gpu_worker_seconds=outer['worker_seconds'],
                     receipt_path=result['receipt_path'], receipt_sha256=result['receipt_sha256']))
    pins.update({name: hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest() for name in names})
acceptance = dict(status='FOUR_GPU_SNAPSHOTS_METADATA_ACCEPTED', variants=rows,
    source_pins=pins, limits_vi='Chưa nghiệm thu raw CPU/temperature hoặc so sánh độc lập. '
    'SHA numeric được kiểm khi CPU join, đây là nghiệm thu receipt metadata và coverage.')
with (BUNDLE / 'GPU_OUTPUT_ACCEPTANCE01.json').open('x', encoding='utf-8') as stream:
    json.dump(acceptance, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(acceptance, ensure_ascii=False))
