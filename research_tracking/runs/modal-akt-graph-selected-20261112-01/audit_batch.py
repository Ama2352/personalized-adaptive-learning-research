"""Tổng hợp sáu nghiệm thu, kiểm bộ đếm tham số đồ thị và chi phí quan sát."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
allocation = json.loads((BUNDLE / 'allocation.json').read_text())
rows, audits = [], []
for candidate, name in allocation['candidate_requests'].items():
    request = json.loads((BUNDLE / name).read_text())
    native = ROOT / 'experiments/akt/results' / request['run_id']
    receipt = json.loads((native / 'receipt.json').read_text())
    terminal = receipt['terminal']
    verified = json.loads((BUNDLE / (candidate.lower() + '-verification.json')).read_text())
    assert verified['status'] == 'VERIFIED_MAIN60_GRAPH_CUDA_SELECTED'
    rows.append(verified)
    required = ['alpha'] + (['gate.weight', 'gate.bias'] if candidate.startswith('A3') else [])
    for epoch in terminal['complete_epoch_receipts']:
        participation = dict(epoch['parameter_participation'])
        for parameter in required:
            assert participation[parameter] == epoch['optimizer_body_returns']
    audits.append(dict(candidate_id=candidate, required_graph_parameters=required,
        epochs_checked=len(terminal['complete_epoch_receipts']),
        cumulative_optimizer_participation_counters_match=True,
        limit='Participation xác nhận gradTensor và optimizer ownership. Chưa chứng minh grad khác0 hoặc graph cải thiện outcome.'))
shutil.copyfile(ROOT / 'research_tracking/runs/modal-akt-recovery-20261112-01/billing-after-six-graph-fits.json',
                BUNDLE / 'billing-after.json')
billing = json.loads((BUNDLE / 'billing-after.json').read_text())
total = float(billing['billing']['metered_cost'])
summary = dict(status='SIX_GRAPH_SELECTED_FITS_VERIFIED', condition_count=6, all_models_including_A0=7,
    graph_optimizer_updates=sum(row['optimizer_updates'] for row in rows),
    graph_physical_train_target_exposures=sum(row['physical_train_target_exposures'] for row in rows),
    graph_checkpoints=sum(row['checkpoint_count'] for row in rows),
    selection_target_count_per_model=1260, unique_selection_learners=6, neural_seed=42,
    total_workspace_metered_usd=total,
    observed_batch_increment_usd=total-allocation['baseline_metered_usd'],
    authorized_batch_usd=2.5, billing_may_lag=True,
    final_refit_calibration_complete=False, junyi_training_complete=False, closed_loop_complete=False,
    conditions=rows)
(BUNDLE / 'batch-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(BUNDLE / 'graph-parameter-audit.json').write_text(json.dumps(dict(
    note='Lượt đọc đầu đã nhầm bộ đếm cumulative thành per-epoch và assertion dừng. Source/receipt xác nhận cumulative, phép kiểm cuối so với optimizer_body_returns.',
    conditions=audits), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key != 'conditions'}, ensure_ascii=False))
