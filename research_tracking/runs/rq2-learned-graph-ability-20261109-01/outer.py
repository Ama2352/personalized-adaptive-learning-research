"""Root-only candidate dispatch19worlds, pending source/pilot-allocation review."""
import time
START, WALL = time.perf_counter(), time.time()
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PLAN = PREP/'rq2_learned_graph_ability01_plan.json'
WORKER = PREP/'worker_rq2_learned_graph_ability01.py'
OUT = ROOT/'experiments/simulator/results/rq2-learned-graph-ability-20261109-01'
OWNED = PREP/'rq2-learned-graph-ability01-owned'
OUTER = PREP/'rq2-learned-graph-ability01-outer'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def main():
    args = sys.argv[1:]
    need(len(args) == 4 and args[0] == '--plan-sha256' and args[2] == '--approval-reference'
         and args[3].strip(), 'Exact ROOT-reviewed argv required, no automatic dispatch')
    pin, approval = args[1], args[3]
    need(sha(PLAN) == pin and Path(sys.prefix).resolve() == ROOT/'.venv', 'Reviewed plan/actual .venv')
    plan = json.loads(PLAN.read_bytes())
    need(plan['output_relative'] == OUT.relative_to(ROOT).as_posix() and len(plan['cells']) == 19
         and plan['resource_limits'] == dict(whole_seconds=60, worker_seconds=50, owned_seconds=55, cleanup_seconds=3,
            max_rss_bytes=536870912, min_available_ram_bytes=1610612736, prelaunch_available_ram_bytes=2147483648,
            max_output_bytes=16777216), 'Exact finite pilot plan')
    expected = {**plan['source_sha256'], **plan['inputs_sha256']}
    need(all(sha(ROOT/name) == value for name, value in expected.items()), 'Source/input prehash')
    need(not OUT.exists() and not OWNED.exists() and not OUTER.exists(), 'Exclusive new output/owned/outer paths')
    OUTER.mkdir(exist_ok=False)
    receipt = worker = error = None
    memory = None
    try:
        import psutil
        memory = dict(available_bytes=psutil.virtual_memory().available, outer_rss_bytes=psutil.Process().memory_info().rss)
        need(memory['available_bytes'] >= 2*1024**3, 'Prelaunch floor2GiB, no fallback')
        need(OUT.parent.resolve() == OUT.parent and not OUT.parent.is_symlink(), 'Existing physical scientific output parent')
        OUT.mkdir(exist_ok=False)
        write(OUT/'dispatch.json', dict(status='RESERVED_ROOT_REVIEWED_ONE_ATTEMPT', approval_reference=approval,
            parent_pid=os.getpid(), plan_sha256=pin, source_input_before_sha256=expected,
            worlds=19, max_interact_reservations=2280, whole_seconds=60, worker_seconds=50,
            old_initial_policy_scope='SOURCE_RECONSTRUCTED_INITIAL_STATE_NOT_OLD_RAW_HASH', preflight_memory=memory,
            hardkill_actual_counts='UNKNOWN<=durable reservations, never zero/reset/retry'))
        sys.path.insert(0, str(ROOT/'scripts/research'))
        from windows_owned_worker import run_owned
        allowance = min(55., 60-elapsed()-5.)
        need(allowance > 3, 'Remaining owned+cleanup allocation')
        receipt = run_owned(WORKER, ['--plan-sha256', pin], OWNED, expected_worker_sha256=plan['source_sha256'][WORKER.relative_to(ROOT).as_posix()],
            approval_reference=approval, max_seconds=allowance, cleanup_reserve_seconds=3, max_output_bytes=65536)
        if OWNED.exists(): write(OWNED/'receipt.json', receipt)
        need(receipt['accepted'] and receipt['returncode'] == 0 and receipt['cleanup_accepted']
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed']
             and receipt['actual_worker_in_job_before_GO'] and receipt['GO_released'], 'Terminal owned cleanup/return required')
        worker = json.loads((OUT/'worker_run.json').read_bytes())
        need(worker['status'] == 'COMPLETE19_PENDING_OUTER' and worker['error'] is None
             and worker['completed_cells'] == 19 and worker['reserved_interact_attempts'] == 2280
             and worker['direct_attempts'] == worker['direct_returns'] == plan['direct_call_caps']
             and worker['sentinel_pass'] and worker['monitor_stopped'] and not worker['monitor_errors']
             and worker['worker_seconds'] < 50 and not (OUT/'failure.log').exists()
             and not (OUT/'postwrite-rejection.json').exists(), 'Complete worlds/control/counters, not exit0 alone')
        need(worker['source_input_before_sha256'] == worker['source_input_after_sha256'] == expected, 'Native source/input hashes')
        need(all(sha(OUT/name) == value for name, value in worker['outputs_sha256'].items()), 'Raw native artifact hashes')
        outcomes = json.loads((OUT/'outcomes.json').read_bytes())
        q = json.loads((OUT/'graph_source_contrasts.json').read_bytes())
        k = json.loads((OUT/'conditional_lambda_contrasts.json').read_bytes())
        high = json.loads((OUT/'high_controls.json').read_bytes())
        need(len(outcomes) == 19 and len(q) == 18 and len(k) == 9 and len(high) == 3
             and sum(row['graph_source'] == 'learned' for row in outcomes) == 18, 'Exact finite components')
        wanted = {(block, ability, strength) for block in (21000, 21001, 21002) for ability in (1000, 1150, 1300) for strength in (0., .55)}
        need({(r['block'], r['ability'], r['mechanism_strength']) for r in q} == wanted, 'All18contrast keys')
        for name, count in (('observables.jsonl', 2280), ('oracle.jsonl', 2280), ('oracle_endpoints.jsonl', 19), ('cell_ledger.jsonl', 38)):
            with (OUT/name).open('rb') as stream:
                rows = sum(1 for raw in stream if raw.strip())
            need(rows == count, 'Actual raw row count '+name)
        need(len(list(OUT.glob('initial-*.json'))) == 19, 'All19actual initial snapshots')
        samples = worker['resources']
        need(samples and all(max(r['family_rss_bytes'], r['peak_worker_rss_bytes']) <= 512*1024**2
             and r['available_bytes'] >= 1536*1024**2 for r in samples), 'Observed family RSS/free floor')
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught), traceback=traceback.format_exc())
    after = {name: sha(ROOT/name) for name in expected}
    if after != expected: error = error or dict(type='SourceDrift')
    files = list(OUT.iterdir()) if OUT.exists() else []
    if any(not p.is_file() or p.is_symlink() or p.stat().st_size > 4*1024**2 for p in files) or len(files) > 40 or sum(p.stat().st_size for p in files) > 16*1024**2:
        error = error or dict(type='ArtifactBound')
    if elapsed() >= 60: error = error or dict(type='Whole60Bound')
    result = dict(status='ACCEPTED19_FINITE_LEARNED_GRAPH_SOURCE_EXTENSION' if error is None else 'REJECTED_RETAIN_NO_RETRY',
        error=error, elapsed_seconds=elapsed(), whole_seconds=60, plan_sha256=pin, approval_reference=approval,
        preflight_memory=memory, source_input_before_sha256=expected, source_input_after_sha256=after,
        owned_receipt=receipt, worker_result=worker, outputs_sha256={p.name: sha(p) for p in files if p.is_file()},
        actual_calls_if_worker_missing='UNKNOWN<=reserved not zero', new_independent_seed_blocks=0,
        old_initial_policy_scope='SOURCE_RECONSTRUCTED_INITIAL_STATE_NOT_OLD_RAW_POLICY_HASH',
        no_full_matrix_or_RQ_completion=True, automatic_retry=False)
    write(OUTER/'final.json', result)
    if elapsed() >= 60:
        write(OUTER/'postwrite-rejection.json', dict(reason='whole60 after final publication'))
        error = error or dict(type='PostwriteWholeBound')
    print(json.dumps(dict(status=result['status'], elapsed_seconds=elapsed()), ensure_ascii=False))
    return 0 if error is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
