"""Chốt đầu vào A2 đã kiểm và dự phòng một tranche H100 trong trần 30 USD."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from modal_junyi_staged import validate_execution
from modal_junyi_main_selected import validate_project_budget


def main():
    verified = json.loads((HERE / 'a2-snapshot-dependency-verification02.json').read_text())
    assert verified['status'] == 'PASS_SNAPSHOT_DEPENDENCY_AND_INVENTORY'
    snapshot = ROOT / verified['snapshot']
    worker = json.loads((snapshot / 'project/gpu-stage-request.json').read_text())
    request = dict(status='USER_APPROVED',
        approval_reference='Người dùng 14/11 yêu cầu kiểm snapshot A2 và chạy training khi đạt, tự phân bổ chi nhỏ trong trần toàn KLTN 30 USD.',
        execution_id='modal-junyi-a2-staged-h100-20261114-01',
        allocation_id='junyi-a2-staged-h100-20261114-01', gpu='H100',
        image_id='im-ldjZsYO21pzaupmQXGLhnS',
        child_timeout_seconds=1740, function_timeout_seconds=1800, watchdog_seconds=1860,
        authorized_batch_usd=2.6, reserved_usd_per_run=2.6)
    resource = validate_execution(request, worker)
    ledger_path = ROOT / 'research_tracking/COMPUTE_BUDGET.json'
    ledger = json.loads(ledger_path.read_text())
    assert not ledger['new_allocations']
    ledger['new_allocations'] = [dict(id=request['allocation_id'], cap_usd=2.6,
        purpose_vi='A2 Junyi TRAIN80 selected-fit, một H100, tiếp tục bằng checkpoint nếu hết tranche.')]
    envelope = validate_project_budget(ledger, request, 0.)
    # Runner sẽ đọc billing thật và kiểm lại trước upload/cấp GPU.
    for path, value in ((HERE / 'a2-training-request01.json', request),
                        (HERE / 'a2-allocation-local-check01.json', dict(resource=resource, envelope=envelope))):
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status='LOCAL_ALLOCATION_PREPARED', resource=resource, envelope=envelope)), flush=True)


if __name__ == '__main__':
    main()
