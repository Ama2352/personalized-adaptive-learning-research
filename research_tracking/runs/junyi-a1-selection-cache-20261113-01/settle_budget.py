"""Đối soát tranche đã dừng bằng cận tài nguyên và snapshot billing, giữ ledger lịch sử."""
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    assert json.loads((HERE / 'archive-extraction09.json').read_text())['status'] == 'PASS_ALL_ARTIFACTS_VERIFIED_ON_D'
    runs = ['modal-junyi-a1-b128-h100-20261113-' + suffix for suffix in ('06', '07', '08', '09')]
    # Dùng toàn elapsed App thay vì chỉ thời gian tính toán GPU, bao cả startup và packaging.
    rate_upper = .001097 + 4 * .00003942 + 12 * .00000667
    records = []
    for run in runs:
        folder = ROOT / 'experiments/akt/results' / run
        guard = json.loads((folder / 'app-budget-guard.json').read_text())
        assert guard['stop_acknowledged'] is True
        elapsed = max(row['elapsed_seconds'] for row in guard['events'])
        records.append({'run_id': run, 'app_id': guard['app']['app_id'], 'stop_acknowledged': True,
                        'elapsed_upper_seconds': math.ceil(elapsed), 'rate_upper_usd_per_second': rate_upper,
                        'compute_upper_usd': math.ceil(elapsed) * rate_upper})
    assert sum(row['compute_upper_usd'] for row in records[:2]) <= 3
    assert sum(row['compute_upper_usd'] for row in records[2:]) <= 3
    cpu_guard = ROOT / 'experiments/akt/results/modal-junyi-a1-selection-cpu-20261113-01/app-budget-guard.json'
    assert json.loads(cpu_guard.read_text())['stop_acknowledged'] is True
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
    sys.path.insert(0, str(ROOT / 'experiments/akt'))
    from modal_graph_selected import read_billing
    billing = asyncio.run(read_billing())
    ledger_path = ROOT / 'research_tracking/COMPUTE_BUDGET.json'
    raw = ledger_path.read_bytes()
    ledger = json.loads(raw)
    ids = {'junyi-a1-selection-cpu-20261113-01', 'junyi-a1-compact-resume-h100-20261113-01',
           'junyi-a1-same-source-resume-h100-20261113-01'}
    allocations = [row for row in ledger['new_allocations'] if row['id'] in ids]
    assert len(allocations) == 3
    increment = .15 + sum(row['compute_upper_usd'] for row in records)
    historical = max(ledger['historical_usage_reserved_upper_usd'] + increment,
                     float(billing['billing']['metered_cost']))
    for allocation in allocations:
        ledger['closed_reservations'].append(dict(allocation,
            financial_record_status='CLOSED_ALL_APPS_STOPPED_ARTIFACTS_VERIFIED',
            evidence='research_tracking/runs/' + HERE.name + '/budget-settlement.json'))
    ledger['new_allocations'] = [row for row in ledger['new_allocations'] if row['id'] not in ids]
    ledger['historical_usage_reserved_upper_usd'] = historical
    result = {'status': 'CLOSED_BOUNDED_TRANCHES', 'prior_ledger_sha256': hashlib.sha256(raw).hexdigest(),
              'gpu_runs': records, 'cpu_reserved_upper_usd': .15,
              'new_compute_upper_usd': increment, 'provider_snapshot': billing,
              'historical_upper_usd': historical,
              'available_after_safety_reserve_upper_policy_usd': 30 - historical - ledger['safety_and_final_inference_reserve_usd'],
              'note_vi': 'Cận tài nguyên là dự phòng bảo thủ. Billing có thể trễ, hai số có ý nghĩa khác nhau.'}
    (HERE / 'budget-settlement.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    ledger['last_a1_compact_accounting_snapshot'] = result
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'new_compute_upper_usd', 'historical_upper_usd',
                                                   'available_after_safety_reserve_upper_policy_usd')}))


if __name__ == '__main__':
    main()
