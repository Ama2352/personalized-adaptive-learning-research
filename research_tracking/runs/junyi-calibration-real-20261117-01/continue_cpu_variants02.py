"""Nối và fit temperature A1–A3 bằng CPU, tái sử dụng snapshot GPU đã đóng."""
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


gate = json.loads((ROOT / 'research_tracking/runs/cloud-calibration-fit-20261117-01/LINUX_CPU_GATE06.json').read_text())
assert gate['exit_code'] == 0 and gate['receipt']['status'] == 'DRIVE_SHA256_VERIFIED'
ledger = json.loads((ROOT / 'research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json').read_text())
assert ledger['workspace_name'] == 'honguyenminhsang2016'
assert ledger['historical_usage_reserved_upper_usd'] + sum(
    item.get('reserved_upper_usd', 0) for item in ledger['new_allocations']) + 5 <= 30
preflight = json.loads((BUNDLE / 'PREFLIGHT06.json').read_text())
for name, pin in preflight['worker_sources'].items():
    assert hashlib.sha256((ROOT / 'scripts/akt' / name).read_bytes()).hexdigest() == pin, name
for variant in ('A2', 'A3'):
    result = json.loads((BUNDLE / f'{variant}_GPU_RESULT01.json').read_text())
    assert result['status'] == 'STAGE_COMMITTED'
    assert (BUNDLE / f'{variant}_GPU_METADATA_DRIVE01.json').is_file()
app, functions = create_app()
with modal.enable_output(), app.run(environment_name='main'):
    for variant in ('A2', 'A3'):
        entry = json.loads((BUNDLE / f'{variant}_GPU_REQUEST_ENTRY01.json').read_text())
        gpu = json.loads((BUNDLE / f'{variant}_GPU_RESULT01.json').read_text())
        allocation_id = f'calibration-{variant.lower()}-join-20261117-01'
        allocation = next(item for item in ledger['new_allocations'] if item['id'] == allocation_id)
        assert allocation['reserved_upper_usd'] == .75
        authorization = dict(workspace='honguyenminhsang2016', stage='cpu-join',
                             allocation_id=allocation_id, reserved_usd=.75,
                             request_sha256=entry['sha256'])
        save(f'{variant}_CPU_JOIN_AUTHORIZATION01.json', authorization)
        operation = operation_tranche(variant, 'cpu-join', allocation_id)
        try:
            print(f'{variant}_CPU_JOIN_V1_FIT_START_NO_GPU', flush=True)
            result = functions['join_fit'].remote(entry,
                preflight['worker_sources']['calibration_cloud_worker.py'], authorization,
                dict(path=gpu['result_path'], sha256=gpu['result_sha256']))
            save(f'{variant}_CPU_JOIN_RESULT01.json', result)
            assert result['status'] == 'STAGE_COMMITTED'
            print(f'{variant}_CPU_JOIN_FIT_COMMITTED', flush=True)
        finally:
            publication = functions['publish_metadata'].remote('junyi-calibration-real-20261117-01', [operation])
            save(f'{variant}_CPU_JOIN_METADATA_DRIVE01.json', publication)
            assert publication['status'] == 'OPERATION_METADATA_PUBLISHED'
print('ALL_CPU_JOINS_COMPLETE_APP_STOPPED', flush=True)
