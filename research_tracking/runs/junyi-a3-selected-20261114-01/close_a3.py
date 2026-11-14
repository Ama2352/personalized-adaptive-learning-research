"""Niêm phong bằng chứng A3 sau model, metric, figure và hai báo cáo."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import sha, write_new


def main():
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    assert not (HERE / 'CLOSEOUT_MANIFEST.json').exists()
    acceptance = read(HERE / 'a3-final-acceptance.json')
    assert acceptance['status'] == 'PASS_A3_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT'
    assert read(HERE / 'a3-gate-selection-audit.json')['status'] == 'PASS_CPU_SELECTED_GATE_CONTEXT_AUDIT'
    assert read(HERE / 'a3-report-verification.json')['status'] == 'PASS_STATIC_A3_REPORT_AND_FIGURE_OUTPUTS'
    assert read(HERE / 'figure-visual-qa.json')['png_viewed'] is True
    assert read(HERE / 'containers-after.json') == []
    ledger = read(ROOT / 'research_tracking/COMPUTE_BUDGET.json')
    assert ledger['new_allocations'] == []
    assert ledger['historical_usage_reserved_upper_usd'] + ledger['safety_and_final_inference_reserve_usd'] <= 30
    state = read(HERE / 'STATE.json')
    assert state['status'] == 'A3_SELECTED_FIT80_COMPLETE_ARTIFACTS_VERIFIED'
    export = ROOT / 'experiments/akt/results/model-export-a3-batch128-20261114-01'
    assert {path.name for path in export.iterdir()} == {'A3_JUNYI_SELECTED.pt', 'MODEL_INDEX.json', 'SUPPORT.zip', 'README.md'}
    billing = read(HERE / 'billing-after.json')
    performance = read(HERE / 'a3-final-performance.json')
    ledger.setdefault('accounting_snapshot_history', []).append(ledger['last_accounting_snapshot'])
    ledger['last_accounting_snapshot'] = dict(observed_at_utc=billing['observed_at_utc'],
        metered_cost_usd=float(billing['billing']['metered_cost']),
        billed_cost_usd=float(billing['billing']['billed_cost']),
        credits_applied_usd=abs(float(billing['billing']['adjustments']['Credits'])),
        evidence=(HERE / 'billing-after.json').relative_to(ROOT).as_posix(), containers_empty=True,
        full_remaining_matrix_cost_status='REESTIMATE_REFIT_CALIBRATION_AND_INDEPENDENT_EVALUATION')
    ledger['historical_upper_note_before_a3_reconciliation'] = ledger['historical_upper_note']
    ledger['historical_upper_note'] = ('Cận sau đối soátA3 dựa trên metering mốcA1, toàn bộ cận tài nguyên '
        'các lượt sau mốc đó và1USD biên trễ. Đây là cận dự phòng, số metering hiện tại được lưu riêng. '
        'Khoản dự phòng cuối hiện2,50USD, trần toàn dự án30USD.')
    (ROOT / 'research_tracking/COMPUTE_BUDGET.json').write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    state.update(closed=True, action='READ_ONLY_CLOSED_EVIDENCE', active_exec_session=None,
        active_processes=[], gpu_started=False, gpu_stopped_acknowledged=True,
        gpu_utilization_goal_50_percent_met=performance['gpu_utilization_goal_50_percent_met'],
        mean_sampled_gpu_utilization=performance['mean_sampled_gpu_utilization'],
        budget_at_closeout=dict(historical_reserved_upper_usd=ledger['historical_usage_reserved_upper_usd'],
            safety_reserve_usd=ledger['safety_and_final_inference_reserve_usd'],
            last_provider_metered_usd=float(billing['billing']['metered_cost']),
            last_provider_billed_usd=float(billing['billing']['billed_cost']), project_ceiling_usd=30),
        next_steps=[
            'Tạo bundle mới cho công việc tiếp theo, không sửa hồ sơ đã niêm phong này',
            'A0–A3 Junyi đã selected-fit, còn refit/calibration/đánh giá độc lập theo protocol',
            'Đối chiếu ranking đầy đủ A0 khi dùng validation batch128',
            'RQ3 còn đối chứng graph-off, ổn định, perturbation và quyết định/vòng kín; thống kê gate CPU là mô tả',
            'Kiểm lại ngân sách và workload có ích trước khoản Modal tiếp theo trong trần toàn KLTN30USD'])
    (HERE / 'STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    files = {path.relative_to(HERE).as_posix(): dict(bytes=path.stat().st_size, sha256=sha(path))
        for path in sorted(HERE.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}
    exports = {path.relative_to(ROOT).as_posix(): dict(bytes=path.stat().st_size, sha256=sha(path))
               for path in sorted(export.iterdir())}
    large = {}
    for name in state['verified_tranches']:
        run = ROOT / 'experiments/akt/results' / name
        receipt = read(run / 'COMPLETE.json')
        assert receipt['status'] == 'LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
        large[run.relative_to(ROOT).as_posix()] = dict(files=receipt['files'],
            archive_sha256=receipt['archive_sha256'], archive_bytes=receipt['archive_bytes'],
            local_control_files={path.name: dict(bytes=path.stat().st_size, sha256=sha(path))
                for path in sorted(run.glob('*.json')) if path.name != 'remote-inventory.json'})
    write_new(HERE / 'CLOSEOUT_MANIFEST.json', dict(status='CLOSED_A3_EVIDENCE_BUNDLE',
        closed_at_utc=datetime.now(timezone.utc).isoformat(), files=files, exports=exports, large_artifacts=large))
    print(json.dumps(dict(status='CLOSED_A3_EVIDENCE_BUNDLE', files=len(files), export_files=len(exports))))


if __name__ == '__main__':
    main()
