"""Chuẩn bị A3 bằng confidence/cache thật và source03 đã nghiệm thu."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / 'research_tracking/runs/junyi-confidence-completion-20261114-01'


def write(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    old = json.loads((PRIOR / 'a3-stage-inputs02.json').read_text())
    a2 = json.loads((PRIOR / 'a2-stage-inputs03.json').read_text())
    request = json.loads(json.dumps(old))
    request['archives'] = a2['archives']
    # Checkout portable03 có ref để Git nhận đúng repository trong container.
    for name, pin in a2['local_files'].items():
        if name.startswith('artifacts/akt/dependencies/upstream/'):
            request['local_files'][name] = pin
    assert request['worker'] == old['worker']
    a2worker = a2['worker']
    worker = request['worker']
    differences = {key: [a2worker['config'][key], value]
                   for key, value in worker['config'].items()
                   if value != a2worker['config'][key]}
    assert set(differences) == {'run_id', 'output_dir'}
    assert worker['inputs'] == a2worker['inputs']
    assert worker['profile'] == a2worker['profile']
    for key in ('confidence_sha256', 'graph_sha256', 'runtime_lock_sha256',
                'validation_batch_size', 'purpose', 'workload_epochs'):
        assert worker[key] == a2worker[key]
    write('a3-stage-inputs03.json', request)
    write('a3-a2-preparation-comparison.json', dict(
        status='PASS_SAME_TRAINING_DATA_NUMERICS_CONFIDENCE',
        config_differences=differences, variant_difference='A3 adds learned graph gate',
        selection_population_expected=1600343, train_targets_expected=13347331,
        a0_full_epoch_ranking_batch128_verified=False,
        source_sha256=request['archives']['source']['sha256']))
    execution = json.loads((PRIOR / 'a2-training-request10.json').read_text())
    for key in ('resume_checkpoint', 'resume_sha256', 'resume_inventory'):
        execution.pop(key)
    execution.update(execution_id='modal-junyi-a3-staged-h100-20261114-01',
                     allocation_id='junyi-a3-staged-h100-20261114-01',
                     approval_reference='Người dùng yêu cầu 14/11 tiếp tục chuẩn bị/training A3, '
                     'giữ cấu hình A0–A2 và trần toàn KLTN30USD.')
    write('a3-training-request01.json', execution)
    state = dict(status='PREPARING_A3_SNAPSHOT_AND_BUDGET', closed=False,
                 prior_evidence=str(PRIOR.relative_to(ROOT)).replace('\\', '/'),
                 snapshot='artifacts/akt/staged/junyi-a3-expert-20261114-03',
                 execution_id=execution['execution_id'], gpu_started=False,
                 token_refresh_required=True, next_steps=[
                     'Kiểm snapshot03, runtime/upstream và cache A3 trên CPU local',
                     'Đối soát cận reservation lịch sử, giữ toàn KLTN30USD',
                     'Xác nhận token đủ thời hạn trước GPU',
                     'Training có checkpoint, dừng GPU trước tải artifact'])
    write('STATE.json', state)
    print(json.dumps(dict(status=state['status'], config_differences=differences)))


if __name__ == '__main__':
    main()
