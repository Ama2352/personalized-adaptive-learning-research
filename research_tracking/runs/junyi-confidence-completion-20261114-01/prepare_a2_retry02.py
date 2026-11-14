"""Đóng lượt lỗi mount đã dừng, giữ input và chuẩn bị retry A2."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
attempt = int(sys.argv[1]) if len(sys.argv)>1 else 2
assert 2<=attempt<=99
previous = f'{attempt-1:02d}'
current = f'{attempt:02d}'
old = json.loads((HERE / f'a2-training-request{previous}.json').read_text())
failed = ROOT / 'experiments/akt/results' / old['execution_id']
guard = json.loads((failed / 'app-budget-guard.json').read_text())
assert guard['stop_acknowledged'] is True
dispatched = (failed / 'dispatch.json').exists()
assert json.loads((failed / 'local-failure.json').read_text())['error_type'] in ('InvalidError','RemoteError','ImageBuildError','FileNotFoundError','FunctionTimeoutError')
test_log={2:'05',3:'06',8:'08'}.get(attempt,'07')
tests = (HERE / f'staged-mount-regression{test_log}.log').read_text()
assert 'failed' not in tests and 'passed' in tests
ledger_path = ROOT / 'research_tracking/COMPUTE_BUDGET.json'
ledger = json.loads(ledger_path.read_text())
assert len(ledger['new_allocations']) == 1
assert ledger['new_allocations'][0]['id'] == old['allocation_id']
margin=.1 if dispatched else .03
settlement = dict(id=old['allocation_id'], status='PROVIDER_STARTUP_FAILED_APP_STOPPED',
    stop_acknowledged=True, app_id=guard['app']['app_id'],
    compute_actual_usd=None, reserved_upper_closed_usd=margin,
    function_dispatched=dispatched,
    note_vi='Lỗi cấu hình khởi tạo trước numerical worker. Giữ cận chi bảo thủ, tái dùng input Volume đã upload.')
ledger['closed_reservations'].append(settlement)
ledger['historical_usage_reserved_upper_usd'] += margin
request = dict(old, execution_id='modal-junyi-a2-staged-h100-20261114-'+current,
               allocation_id='junyi-a2-staged-h100-20261114-'+current)
ledger['new_allocations'] = [dict(id=request['allocation_id'], cap_usd=2.6,
    purpose_vi='Retry A2 sau sửa mount Volume, giữ snapshot và toàn cấu hình học.')]
for filename, value in [(f'a2-mount-failure-settlement{previous}.json', settlement), (f'a2-training-request{current}.json', request)]:
    with (HERE / filename).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
state_path = HERE / 'STATE.json'
state = json.loads(state_path.read_text())
state.update(status='A2_RETRY_AFTER_VOLUME_MOUNT_CORRECTION', training_request=f'a2-training-request{current}.json',
    training_log=f'a2-training{current}.log', gpu_start_confirmed=False,
    first_attempt_stop_acknowledged=True, first_attempt_dispatched=False)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
pins = {}
for name in ('experiments/akt/modal_junyi_staged.py', 'tests/akt/test_junyi_staged_local.py'):
    pins[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
with (HERE / f'staged-controller-mount-fix{current}.json').open('x', encoding='utf-8') as stream:
    json.dump(dict(status='LOCAL_REGRESSION_PASS', files=pins,
        source_snapshot_unchanged=True,
        note_vi='Sửa controller local và mock kiểm mount. Source numerical worker và Gate trong snapshot giữ nguyên byte.'),
        stream, ensure_ascii=False, indent=2)
print(json.dumps(dict(status='RETRY_READY', reserved_usd=2.6, prior_margin_usd=margin)))
