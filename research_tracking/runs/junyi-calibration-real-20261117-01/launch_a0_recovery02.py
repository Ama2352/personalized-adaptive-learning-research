"""Phục hồi audit A0 trên CPU, dùng nguyên Parquet và snapshot GPU đã có."""
import hashlib
import json
import os
from pathlib import Path
import sys
import warnings

ROOT = Path.cwd()
B = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE'] = 'kltn2016'
warnings.filterwarnings('ignore', message=r'Your Modal token .*')
sys.path[:0] = [str(ROOT/'scripts/akt'), str(ROOT/'src')]
import modal
from modal_junyi_calibration import create_app, operation_tranche


def read(name):
    return json.loads((B/name).read_text())


def save(name, value):
    with (B/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


gate = json.loads((ROOT/'research_tracking/runs/cloud-calibration-fit-20261117-01/LINUX_CPU_GATE06.json').read_text())
assert gate['exit_code'] == 0 and gate['receipt']['status'] == 'DRIVE_SHA256_VERIFIED'
preflight = read('PREFLIGHT06.json')
for name, pin in preflight['worker_sources'].items():
    assert hashlib.sha256((ROOT/'scripts/akt'/name).read_bytes()).hexdigest() == pin, name
entry = read('A0_GPU_REQUEST_ENTRY01.json')
gpu = read('A0_GPU_RESULT01.json')
assert gpu['status'] == 'STAGE_COMMITTED'
writer_stop = read('A0_WRITER_STOP_RECEIPT01.json')
assert writer_stop['tasks'] == 0 and writer_stop['status'] == 'APP_STOPPED'
admission = read('RAW_RECOVERY_ADMISSION01.json')['variants']['a0']
raw_pin = dict(path='/__modal/volumes/vo-dv1975utRQbmagCjA0brSe/'
    'junyi-calibration-real-20261117-01/a0-raw-calibration-a0-join-20261117-01/payloads/raw/manifest.json',
    sha256=admission['raw']['manifest_sha256'])
allocation_id = 'calibration-a0-recover-20261117-01'
ledger = json.loads((ROOT/'research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json').read_text())
assert ledger['historical_usage_reserved_upper_usd'] + sum(
    item.get('reserved_upper_usd', 0) for item in ledger['new_allocations']) + 5 <= 30
assert next(item for item in ledger['new_allocations'] if item['id'] == allocation_id)['reserved_upper_usd'] == .75
authorization = dict(workspace='honguyenminhsang2016', stage='cpu-join', allocation_id=allocation_id,
                     reserved_usd=.75, request_sha256=entry['sha256'])
save('A0_CPU_RECOVERY_AUTHORIZATION02.json', authorization)
operation = operation_tranche('A0', 'cpu-join', allocation_id)
app, functions = create_app()
with modal.enable_output(), app.run(environment_name='main'):
    try:
        print('A0_CPU_RECOVERY_SAME_PARQUET_NO_GPU_START', flush=True)
        result = functions['recover_fit'].remote(entry,
            preflight['worker_sources']['calibration_cloud_worker.py'], authorization,
            dict(path=gpu['result_path'], sha256=gpu['result_sha256']), raw_pin, writer_stop)
        save('A0_CPU_RECOVERY_RESULT02.json', result)
        assert result['status'] == 'STAGE_COMMITTED'
        assert result['result']['status'] == 'CPU_CALIBRATION_RECOVERY_PUBLISHED'
        print('A0_CPU_RECOVERY_V1_FIT_DRIVE_VERIFIED', flush=True)
    except BaseException as error:
        save('A0_CPU_RECOVERY_FAILURE02.json', dict(error_type=type(error).__name__, operation=operation))
        raise
    finally:
        publication = functions['publish_metadata'].remote('junyi-calibration-real-20261117-01', [operation])
        save('A0_CPU_RECOVERY_METADATA_DRIVE02.json', publication)
print('A0_RECOVERY_APP_STOPPED_NO_GPU', flush=True)
