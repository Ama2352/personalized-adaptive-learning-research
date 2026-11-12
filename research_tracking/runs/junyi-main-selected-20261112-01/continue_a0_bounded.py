"""Tiếp tục hữu hạn cùng A0 sau execution03, giữ nguyên protocol đã duyệt."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
FIRST = 'modal-junyi-main-selected-t4-20261112-03'
FOLLOWING = tuple(f'modal-junyi-main-selected-t4-20261112-{number:02d}' for number in (4, 5, 6))


def disposition(receipt, guard):
    if guard.get('stop_acknowledged') is not True:
        raise ValueError('Previous App stop must be acknowledged')
    if receipt.get('download_inventory_verified') is not True:
        raise ValueError('Previous archive inventory must be verified')
    status = receipt['status']
    if status == 'JUNYI_A0_SELECTED_ONLY_COMPLETE':
        return 'complete'
    if status == 'PARTIAL_SELECTED_ONLY_NOT_FINAL':
        return 'continue'
    raise ValueError('Failed or preempted execution requires manual recovery review')


def read_receipt(execution):
    native = ROOT / 'experiments/akt/results' / execution
    receipt = json.loads((native / 'receipt.json').read_text())
    guard = json.loads((native / 'app-budget-guard.json').read_text())
    return receipt, guard


def run_command(arguments, log, timeout):
    with log.open('xb') as stream:
        subprocess.run([sys.executable, '-B', *arguments], cwd=ROOT,
                       stdout=stream, stderr=subprocess.STDOUT,
                       check=True, timeout=timeout)


def validate_frozen_request(previous, prepared, execution):
    for field in ('logical_run_id', 'inputs', 'purpose', 'workload_epochs',
                  'train_targets', 'selection_targets', 'max_optimizer_steps',
                  'max_total_training_targets', 'native_max_seconds',
                  'native_max_wall_seconds', 'gpu'):
        if prepared[field] != previous[field]:
            raise ValueError(f'Frozen request changed at {field}')
    for key in ('source', 'data', 'cpu_gate'):
        if prepared['archives'][key] != previous['archives'][key]:
            raise ValueError(f'Frozen input changed at {key}')
    if prepared['run_id'] != execution or prepared['resume_from_execution_id'] != previous['run_id']:
        raise ValueError('Sequential execution lineage required')
    if prepared['gpu'] != 'T4' or prepared['reserved_usd_per_run'] != .85:
        raise ValueError('Bounded T4 allocation required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    plan = dict(scope='same_a0_selected_only', wait_for=FIRST, following=FOLLOWING,
                max_additional_runs=3, reserved_upper_usd=2.55,
                refit_allowed=False, graph_fit_allowed=False, protocol_change_allowed=False)
    print(json.dumps(plan), flush=True)
    if not args.run:
        return
    state_path = BUNDLE / 'bounded-continuation-state.json'
    with (BUNDLE / 'bounded-continuation.lock').open('x') as stream:
        json.dump(plan, stream)
    state = dict(plan, status='WAITING_FOR_EXECUTION03', events=[])

    def record(status, **event):
        state['status'] = status
        state['events'].append(dict(status=status, **event))
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(state['events'][-1], ensure_ascii=False), flush=True)

    try:
        waiting_started = time.monotonic()
        first_native = ROOT / 'experiments/akt/results' / FIRST
        while not (first_native / 'receipt.json').exists():
            if (first_native / 'preemption-receipt.json').exists():
                raise ValueError('Execution03 preempted, manual recovery required')
            if time.monotonic() - waiting_started > 3700:
                raise TimeoutError('Execution03 receipt wait exhausted')
            time.sleep(5)
        previous_id = FIRST
        previous_path = BUNDLE / 'request03.json'
        for execution in FOLLOWING:
            receipt, guard = read_receipt(previous_id)
            if disposition(receipt, guard) == 'complete':
                record('A0_SELECTED_ONLY_COMPLETE', execution=previous_id)
                return
            ledger = json.loads((ROOT / 'research_tracking/COMPUTE_BUDGET.json').read_text(encoding='utf-8'))
            allocation = execution.removeprefix('modal-')
            declared = [row for row in ledger['new_allocations'] if row['id'] == allocation]
            if len(declared) != 1 or declared[0]['cap_usd'] != .85:
                raise PermissionError('Root-preallocated continuation required')
            output = BUNDLE / f'request{execution[-2:]}.json'
            run_command([str(BUNDLE / 'prepare_resume.py'), '--previous-execution', previous_id,
                         '--execution', execution, '--previous-request', str(previous_path),
                         '--output-request', str(output)],
                        BUNDLE / f'prepare-execution{execution[-2:]}.log', 120)
            previous = json.loads(previous_path.read_text(encoding='utf-8'))
            prepared = json.loads(output.read_text(encoding='utf-8'))
            validate_frozen_request(previous, prepared, execution)
            prepared['root_review_status'] = 'ROOT_PREAPPROVED_IDENTICAL_PROTOCOL_BOUNDED_CONTINUATION'
            output.write_text(json.dumps(prepared, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            record('DISPATCHING_SAME_A0', execution=execution, checkpoint=prepared['resume_checkpoint_name'])
            run_command([str(ROOT / 'experiments/akt/modal_junyi_main_resume.py'),
                         '--request', str(output), '--gpu', 'T4', '--run'],
                        BUNDLE / f'gpu-execution{execution[-2:]}.log', 3900)
            current, guard = read_receipt(execution)
            outcome = disposition(current, guard)
            record('VERIFIED_STOPPED_EXECUTION', execution=execution, receipt_status=current['status'])
            if outcome == 'complete':
                record('A0_SELECTED_ONLY_COMPLETE', execution=execution)
                return
            previous_id, previous_path = execution, output
        record('BOUNDED_TRANCHE_EXHAUSTED_PARTIAL', execution=previous_id)
    except BaseException as error:
        record('STOPPED_REVIEW_REQUIRED', error_type=type(error).__name__, error=str(error))
        raise


if __name__ == '__main__':
    main()
