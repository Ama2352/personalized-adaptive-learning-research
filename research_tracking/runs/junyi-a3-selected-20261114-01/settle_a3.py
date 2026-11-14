"""Nghiệm thu tranche A3 đã dừng, lưu chi phí và chuẩn bị resume có giới hạn."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import sha, write_new
from modal_junyi_main_selected import validate_project_budget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=int)
    parser.add_argument('--prepare-resume', action='store_true')
    args = parser.parse_args()
    attempt = f'{args.attempt:02}'
    request = json.loads((HERE / f'a3-training-request{attempt}.json').read_text())
    output = ROOT / 'experiments/akt/results' / request['execution_id']
    read = lambda name: json.loads((output / name).read_text())
    complete, stage, remote, guard = [read(name) for name in
        ('COMPLETE.json', 'stage-result.json', 'remote-inventory.json', 'app-budget-guard.json')]
    assert complete['status'] == stage['status'] == 'LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    recovered_stop = None
    if guard['stop_acknowledged'] is not True:
        recovered_stop = json.loads((HERE / f'recovery-stop-acknowledged{attempt}.json').read_text())
        assert recovered_stop['status'] == 'SERVER_APP_ALREADY_STOPPED_CONFIRMED'
        assert recovered_stop['original_guard_sha256'] == sha(output / 'app-budget-guard.json')
        assert recovered_stop['containers_empty'] is True
    assert complete['files'] == len(remote['files'])
    assert sha(output / 'artifacts.zip') == complete['archive_sha256']
    for name, pin in remote['files'].items():
        path = output / 'files' / name
        assert path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256']
    terminal = remote['worker_result']['terminal']
    finished = terminal['status'] == 'JUNYI_A3_SELECTED_ONLY_COMPLETE'
    assert finished or terminal['status'] == 'PARTIAL_SELECTED_ONLY_NOT_FINAL'
    assert all(row['validation']['targets'] == 1600343 and row['validation']['oov'] == 0
               and row['validation']['population_sha256'] ==
               'c26bac9fbbdcf488dc1c8d7b953663158b53216d980676de70b67819fc470b64'
               for row in terminal['history'])
    latest = terminal['history'][-1]['epoch']
    key = f'outputs/junyi-a3-expert-selected-20261114-01/checkpoints/epoch-{latest:03}/state.pt'
    partials = []
    for name in remote['files']:
        match = re.search(r'/checkpoints/inner-batch-epoch-(\d+)-step-(\d+)-[^/]+/state.pt$', name)
        if match and int(match[1]) == latest + 1:
            partials.append((int(match[2]), name))
    if partials and not finished:
        key = max(partials)[1]
    assert key in remote['files']
    import torch
    torch.set_num_threads(1)
    payload = torch.load(output / 'files' / key, map_location='cpu', weights_only=True)
    partial = payload.get('checkpoint_kind') == 'training_recovery_v1'
    if partial:
        assert payload['resume_state']['epoch'] == latest + 1
        assert payload['resume_state']['trainer_state']['selection_state']['history'] == terminal['history']
        assert payload['resume_state']['sampler_state']
    else:
        assert payload['progress']['epoch'] == latest and payload['progress']['validation_complete']
    assert payload['optimizer_state_dict']['state'] and len(payload['cuda_rng']) == 1
    assert all(name in payload for name in ('python_rng', 'numpy_rng', 'torch_rng'))
    assert all(torch.isfinite(value).all().item() for value in payload['model_state_dict'].values())
    seconds = max(event['elapsed_seconds'] for event in guard['events']) + 60
    upper = seconds * .00133472
    if recovered_stop is not None:
        # Khoảng local ngắt làm monotonic không phản ánh thời gian container.
        # Đóng toàn bộ cận request đã nghiệm thu, dựa trên timeout server1800s,
        # startup60s, retries0/max_containers1 và CPU preflight có timeout riêng.
        assert remote['gpu_worker_seconds'] < request['function_timeout_seconds']
        upper = json.loads((output / 'budget-admission.json').read_text())['resource']['upper_usd']
    assert upper <= request['reserved_usd_per_run']
    settlement = dict(id=request['allocation_id'], status=terminal['status'],
        reserved_upper_closed_usd=upper, elapsed_upper_seconds=seconds,
        actual_isolated_cost_usd=None, stop_acknowledged=True, complete_epochs=latest,
        verified_files=len(remote['files']), archive_sha256=complete['archive_sha256'],
        checkpoint_sha256=remote['files'][key]['sha256'], optimizer_rng_verified=True,
        resume_scope='exact_partial_epoch_sampler' if partial else 'next_complete_epoch',
        resume_checkpoint_key=key,
        financial_time_basis='provider_hard_timeout_upper_after_local_disconnect' if recovered_stop else 'guard_elapsed_plus60')
    ledger_path = ROOT / 'research_tracking/COMPUTE_BUDGET.json'
    ledger = json.loads(ledger_path.read_text())
    assert len(ledger['new_allocations']) == 1
    assert ledger['new_allocations'][0]['id'] == request['allocation_id']
    ledger['historical_usage_reserved_upper_usd'] += upper
    ledger['closed_reservations'].append(settlement)
    ledger['new_allocations'] = []
    next_request = None
    if args.prepare_resume and not finished:
        next_attempt = f'{args.attempt + 1:02}'
        execution_id = 'modal-junyi-a3-staged-h100-20261114-' + next_attempt
        next_request = dict(request, execution_id=execution_id, allocation_id=execution_id.removeprefix('modal-'),
            resume_checkpoint='experiments/akt/results/' + key.removeprefix('outputs/'),
            resume_sha256=remote['files'][key]['sha256'],
            resume_inventory=(output / 'remote-inventory.json').relative_to(ROOT).as_posix())
        ledger['new_allocations'] = [dict(id=next_request['allocation_id'], cap_usd=2.6,
            purpose_vi='Tiếp tục A3 từ checkpoint đã kiểm, cùng recipe, một H100 tối đa30phút.')]
        envelope = ledger['historical_usage_reserved_upper_usd'] + 2.6 + ledger['safety_and_final_inference_reserve_usd']
        if envelope > 30:
            # Dự phòng3USD là phân bổ nội bộ của agent. Giữ tối thiểu2,50USD và
            # 1USD biên trễ đã nằm trong historical_upper khi ưu tiên hoàn tất A3.
            assert ledger['historical_usage_reserved_upper_usd'] + 2.6 + 2.5 <= 30
            old_reserve = ledger['safety_and_final_inference_reserve_usd']
            ledger['safety_and_final_inference_reserve_usd'] = 2.5
            allocation_note = dict(previous_reserve_usd=old_reserve, temporary_reserve_usd=2.5,
                reason_vi='Dành tối đa0,50USD từ dự phòng nội bộ cho A3. Trần toàn dự án30USD '
                'và1USD biên metering trễ trong historical_upper tiếp tục áp dụng. '
                'Khôi phục dự phòng3USD khi đóng lượt nếu cận chi cho phép.')
            write_new(HERE / f'reserve-reallocation{attempt}.json', allocation_note)
            ledger.setdefault('reserve_reallocations', []).append(dict(
                evidence=(HERE / f'reserve-reallocation{attempt}.json').relative_to(ROOT).as_posix(),
                **allocation_note))
        billing = json.loads((HERE / 'billing-before.json').read_text())
        validate_project_budget(ledger, next_request, float(billing['billing']['metered_cost']))
        write_new(HERE / f'a3-training-request{next_attempt}.json', next_request)
    if finished and ledger['historical_usage_reserved_upper_usd'] + 3 <= 30:
        ledger['safety_and_final_inference_reserve_usd'] = 3
    assert ledger['historical_usage_reserved_upper_usd'] + ledger['safety_and_final_inference_reserve_usd'] + sum(
        item['cap_usd'] for item in ledger['new_allocations']) <= 30
    write_new(HERE / f'a3-settlement{attempt}.json', settlement)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    state = json.loads((HERE / 'STATE.json').read_text())
    state.update(status='A3_SELECTED_COMPLETE_PENDING_FINAL_ACCEPTANCE' if finished else 'A3_PARTIAL_CHECKPOINT_VERIFIED',
        complete_epochs=latest, gpu_stopped_acknowledged=True, gpu_started=False,
        latest_output=output.relative_to(ROOT).as_posix(), active_exec_session=None)
    state.setdefault('verified_tranches', []).append(request['execution_id'])
    if next_request:
        state['execution_id'] = next_request['execution_id']
    (HERE / 'STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=state['status'], complete_epochs=latest, upper_usd=upper,
                         next_execution=next_request['execution_id'] if next_request else None)))


if __name__ == '__main__':
    main()
