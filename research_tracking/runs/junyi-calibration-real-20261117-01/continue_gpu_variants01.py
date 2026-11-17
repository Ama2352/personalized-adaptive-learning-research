"""Tiếp tục A1–A3 cùng cache và protocol A0, mỗi GPU có trần riêng."""
import hashlib
import json
import os
from pathlib import Path
import sys
import warnings

ROOT = Path.cwd()
BUNDLE = ROOT / 'research_tracking/runs/junyi-calibration-real-20261117-01'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE'] = 'kltn2016'
warnings.filterwarnings('ignore', message=r'Your Modal token .*')
sys.path[:0] = [str(ROOT / 'scripts/akt'), str(ROOT / 'src')]
import modal
from modal_junyi_calibration import create_app, operation_tranche


def save(name, value):
    with (BUNDLE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


ledger = json.loads((ROOT / 'research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json').read_text())
assert ledger['workspace_name'] == 'honguyenminhsang2016'
assert (ledger['historical_usage_reserved_upper_usd']
        + sum(item.get('reserved_upper_usd', 0) for item in ledger['new_allocations'])
        + ledger['safety_and_final_inference_reserve_usd']) <= 30
baseline = json.loads((BUNDLE / 'REQUEST_A0_GPU01.json').read_text())
app, functions = create_app()
with modal.enable_output(), app.run(environment_name='main'):
    preflight = functions['preflight'].remote()
    save('PREFLIGHT05.json', preflight)
    assert preflight['source_identity'] == baseline['source_identity']
    for name, pin in preflight['worker_sources'].items():
        assert hashlib.sha256((ROOT / 'scripts/akt' / name).read_bytes()).hexdigest() == pin, name
    print('ACTUAL_RUNTIME_SOURCE_GATE_PASS', flush=True)
    for variant in ('A1', 'A2', 'A3'):
        allocation_id = f'calibration-{variant.lower()}-gpu-20261117-01'
        allocation = next(item for item in ledger['new_allocations'] if item['id'] == allocation_id)
        assert allocation['reserved_upper_usd'] == .75
        request = dict(baseline, variant=variant,
                       gpu_output=f"{baseline['run_id']}/{variant.lower()}-numeric/payloads")
        assert {key: value for key, value in request.items() if key not in ('variant', 'gpu_output')} == {
            key: value for key, value in baseline.items() if key not in ('variant', 'gpu_output')}
        save(f'REQUEST_{variant}_GPU01.json', request)
        published = functions['put_request'].remote(
            request, f"requests/{request['run_id']}-{variant.lower()}-gpu01.json")
        entry = {key: published[key] for key in ('path', 'sha256')}
        save(f'{variant}_GPU_REQUEST_ENTRY01.json', entry)
        authorization = dict(workspace='honguyenminhsang2016', stage='gpu',
                             allocation_id=allocation_id, reserved_usd=.75,
                             request_sha256=entry['sha256'])
        save(f'{variant}_GPU_AUTHORIZATION01.json', authorization)
        operation = operation_tranche(variant, 'gpu', allocation_id)
        try:
            print(f'{variant}_GPU_START_ONE_CONTAINER_MAX300_SECONDS', flush=True)
            result = functions['predict'].remote(
                entry, preflight['worker_sources']['calibration_cloud_worker.py'], authorization)
            save(f'{variant}_GPU_RESULT01.json', result)
            assert result['status'] == 'STAGE_COMMITTED'
            print(f'{variant}_GPU_COMMITTED_RELEASED', flush=True)
        finally:
            publication = functions['publish_metadata'].remote(request['run_id'], [operation])
            save(f'{variant}_GPU_METADATA_DRIVE01.json', publication)
            assert publication['status'] == 'OPERATION_METADATA_PUBLISHED'
            assert all(item['account'] == 'honguyenminhsang2005@gmail.com'
                       and item['status'] == 'DRIVE_SHA256_VERIFIED'
                       for item in publication['publications'])
    print('A1_A2_A3_GPU_COMPLETE_NO_MORE_INPUTS_APP_STOPPING', flush=True)
