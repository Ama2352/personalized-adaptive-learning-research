"""Root-only candidate dispatch120freshworlds, pending source/pilot-allocation review."""
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
PLAN = PREP/'rq2_fresh_graph_source01_plan.json'
WORKER = PREP/'worker_rq2_fresh_graph_source01.py'
OUT = ROOT/'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-01'
OWNED = PREP/'rq2-fresh-graph-source01-owned'
OUTER = PREP/'rq2-fresh-graph-source01-outer'


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
    need(plan['output_relative'] == OUT.relative_to(ROOT).as_posix() and len(plan['cells']) == 120
         and plan['blocks'] == list(range(21010, 21020))
         and plan['resource_limits'] == dict(whole_seconds=240, worker_seconds=210, owned_seconds=235, cleanup_seconds=5,
            max_rss_bytes=536870912, min_available_ram_bytes=1610612736, prelaunch_available_ram_bytes=2147483648,
            max_output_bytes=33554432, max_flat_files=160, max_worker_resource_samples=5000), 'Exact finite120 plan')
    wanted_cells = {(b, a, g, m) for b in plan['blocks'] for a in (1000, 1150, 1300)
                    for g in ('full', 'learned') for m in (0., .55)}
    need({(c['block'], c['ability'], c['graph'], c['mechanism_strength']) for c in plan['cells']} == wanted_cells
         and len({c['cell_id'] for c in plan['cells']}) == 120
         and all(c['ability'] == 1300 for c in plan['cells'][:40]), 'Exact120 keys/high-first order')
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
            worlds=120, max_interact_reservations=14400, whole_seconds=240, worker_seconds=210,
            initial_policy_scope='ALL120_FRESH_ACTUAL_SNAPSHOTS', preflight_memory=memory,
            hardkill_actual_counts='UNKNOWN<=durable reservations, never zero/reset/retry'))
        sys.path.insert(0, str(ROOT/'scripts/research'))
        from windows_owned_worker import run_owned
        allowance = min(235., 240-elapsed()-5.)
        need(allowance > 5, 'Remaining owned+cleanup allocation')
        receipt = run_owned(WORKER, ['--plan-sha256', pin], OWNED, expected_worker_sha256=plan['source_sha256'][WORKER.relative_to(ROOT).as_posix()],
            approval_reference=approval, max_seconds=allowance, cleanup_reserve_seconds=5, max_output_bytes=65536)
        if OWNED.exists(): write(OWNED/'receipt.json', receipt)
        if (OUT/'worker_run.json').is_file():
            worker = json.loads((OUT/'worker_run.json').read_bytes())
        need(receipt['accepted'] and receipt['returncode'] == 0 and receipt['cleanup_accepted']
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed']
             and receipt['actual_worker_in_job_before_GO'] and receipt['GO_released'], 'Terminal owned cleanup/return required')
        worker = json.loads((OUT/'worker_run.json').read_bytes())
        need(worker['status'] == 'COMPLETE120_PENDING_OUTER' and worker['error'] is None
             and worker['completed_cells'] == 120 and worker['reserved_interact_attempts'] == 14400
             and worker['direct_attempts'] == worker['direct_returns'] == plan['direct_call_caps']
             and worker['shared_prepared'] and worker['monitor_stopped'] and not worker['monitor_errors']
             and worker['worker_seconds'] < 210 and not (OUT/'failure.log').exists()
             and not (OUT/'postwrite-rejection.json').exists(), 'Complete worlds/control/counters, not exit0 alone')
        need(worker['source_input_before_sha256'] == worker['source_input_after_sha256'] == expected, 'Native source/input hashes')
        need(all(sha(OUT/name) == value for name, value in worker['outputs_sha256'].items()), 'Raw native artifact hashes')
        outcomes = json.loads((OUT/'outcomes.json').read_bytes())
        q = json.loads((OUT/'graph_source_contrasts.json').read_bytes())
        k = json.loads((OUT/'conditional_lambda_contrasts.json').read_bytes())
        high = json.loads((OUT/'high_controls.json').read_bytes())
        need(len(outcomes) == 120 and len(q) == 60 and len(k) == 30 and len(high) == 20
             and sum(r['graph_source'] == 'learned' for r in outcomes) == 60, 'All finite components')
        wanted = {(b, a, m) for b in plan['blocks'] for a in (1000, 1150, 1300) for m in (0., .55)}
        need({(r['block'], r['ability'], r['mechanism_strength']) for r in q} == wanted, 'All60Q keys')
        omap = {(r['block'], r['ability'], r['mechanism_strength'], r['graph_source']): r for r in outcomes}
        need(len(omap) == 120, 'Unique120 outcomes')
        for row in q:
            key = (row['block'], row['ability'], row['mechanism_strength'])
            old, new = omap[(*key, 'expert')], omap[(*key, 'learned')]
            need(old['latent_identity'] == new['latent_identity'] and old['uniform_identity'] == new['uniform_identity']
                 and row['expert'] == old['outcome'] and row['learned'] == new['outcome']
                 and row['expert_minus_learned'] == old['outcome']-new['outcome'], 'Fresh component coupling/Q')
        qmap = {(r['block'], r['ability'], r['mechanism_strength']): r['expert_minus_learned'] for r in q}
        need({(r['block'], r['ability']) for r in k} == {(b, a) for b in plan['blocks'] for a in (1000, 1150, 1300)}, 'All30K keys')
        for row in k:
            key = (row['block'], row['ability'])
            need(row['lambda_difference'] == qmap[(*key, .55)]-qmap[(*key, 0.)], 'K arithmetic')
            if row['ability'] == 1300: need(row['lambda_difference'] == 0., 'High K zero')
        need({(r['block'], r['graph']) for r in high} == {(b, g) for b in plan['blocks'] for g in ('full', 'learned')}
             and all(r['trace_exact'] and r['endpoint_exact'] for r in high), '20high controls')
        for name, count in (('observables.jsonl', 14400), ('oracle.jsonl', 14400),
                            ('oracle_endpoints.jsonl', 120), ('cell_ledger.jsonl', 240)):
            with (OUT/name).open('rb') as stream:
                rows = 0
                for raw in stream:
                    need(len(raw) <= 16384 and raw.strip(), 'Bounded nonempty raw row')
                    rows += 1
                    need(rows <= count, 'Raw row upper bound')
            need(rows == count, 'Actual raw row count '+name)
        snapshots = list(OUT.glob('initial-*.json'))
        need(len(snapshots) == 120, 'All120actual initial snapshots')
        environment_pairs, policy_hashes, source_graphs, fixed_graphs = {}, set(), {}, set()
        def semantic_sha(value):
            return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        for cell in plan['cells']:
            initial = json.loads((OUT/('initial-'+cell['cell_id']+'.json')).read_bytes())
            need(initial['cell'] == cell and initial['initial_state_scope'] == 'ACTUAL_FRESH_SNAPSHOT_BEFORE_RESPONSE1', 'Initial cell binding')
            need(semantic_sha(initial['environment_state']) == initial['environment_sha256']
                 and semantic_sha(initial['nonedge_policy_state']) == initial['nonedge_policy_sha256']
                 and semantic_sha(initial['treatment_binding']) == initial['treatment_binding_sha256'], 'Actual initial payload hashes')
            binding = initial['treatment_binding']
            need(binding['environment_graph_sha256'] == binding['controller_graph_sha256']
                 and binding['signal'] is True and binding['parent_adaptation'] is True and binding['local_adaptation'] is False, 'Fixed graph/package')
            fixed_graphs.add(binding['environment_graph_sha256'])
            need(source_graphs.setdefault(cell['graph'], binding['estimator_graph_sha256']) == binding['estimator_graph_sha256'], 'Graph source consistent')
            digest = initial['environment_sha256']
            need(environment_pairs.setdefault((cell['block'], cell['ability']), digest) == digest, 'Four actual environment snapshots equal')
            policy_hashes.add(initial['nonedge_policy_sha256'])
            need(initial['treatment_binding']['nonedge_policy_initial_sha256'] == initial['nonedge_policy_sha256'], 'Nonedge/treatment split')
        need(len(policy_hashes) == 1 and len(fixed_graphs) == 1 and len(set(source_graphs.values())) == 2, 'Fresh nonedge policies/fixed and distinct graph sources')
        shared = json.loads((OUT/'shared_inputs.json').read_bytes())
        reservation = json.loads((OUT/'seed_reservation.json').read_bytes())
        need(reservation['status'] == 'RESERVED_BEFORE_ANY_DRAW' and reservation['blocks'] == plan['blocks']
             and shared['global_numpy_rng_unchanged'] is True and len(shared['blocks']) == 10, 'Seed/residual generation receipts')
        trajectories = json.loads((OUT/'trajectory_pairs.json').read_bytes())
        need(len(trajectories) == 60 and {(r['block'], r['ability'], r['mechanism_strength']) for r in trajectories} == wanted
             and all(r['ordinal_rows'] == 120 and r['labels_equal_before_first_question_difference']
                     and r['question_id_difference_fraction'] == r['question_id_differences']/120 for r in trajectories), 'Trajectory scope')
        expected_names = {'dispatch.json', 'seed_reservation.json', 'shared_inputs.json', 'admission.json',
            'cell_ledger.jsonl', 'observables.jsonl', 'oracle.jsonl', 'oracle_endpoints.jsonl', 'outcomes.json',
            'graph_source_contrasts.json', 'conditional_lambda_contrasts.json', 'high_controls.json',
            'trajectory_pairs.json', 'summary.json', 'worker_run.json'}
        expected_names.update('initial-'+c['cell_id']+'.json' for c in plan['cells'])
        need(len(expected_names) == 135 and {p.name for p in OUT.iterdir()} == expected_names, 'Exact135 scientific files')
        samples = worker['resources']
        need(samples and len(samples) <= 5000 and all(max(r['family_rss_bytes'], r['peak_worker_rss_bytes']) <= 512*1024**2
             and r['available_bytes'] >= 1536*1024**2 for r in samples), 'Observed family RSS/free floor')
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught), traceback=traceback.format_exc())
    after = {name: sha(ROOT/name) for name in expected}
    if after != expected: error = error or dict(type='SourceDrift')
    files = list(OUT.iterdir()) if OUT.exists() else []
    def limit(name):
        if name.startswith('initial-'): return 32768
        return plan['leaf_caps_bytes'].get(name, 1048576)
    if any(not p.is_file() or p.is_symlink() or p.stat().st_size > limit(p.name) for p in files) or len(files) > 160 or sum(p.stat().st_size for p in files) > 32*1024**2:
        error = error or dict(type='ArtifactBound')
    if elapsed() >= 240: error = error or dict(type='Whole240Bound')
    result = dict(status='ACCEPTED120_FRESH_GRAPH_SOURCE_ROBUSTNESS_NO_INFERENCE' if error is None else 'REJECTED_RETAIN_NO_RETRY',
        error=error, elapsed_seconds=elapsed(), whole_seconds=240, plan_sha256=pin, approval_reference=approval,
        preflight_memory=memory, source_input_before_sha256=expected, source_input_after_sha256=after,
        owned_receipt=receipt, worker_result=worker, outputs_sha256={p.name: sha(p) for p in files if p.is_file()},
        actual_calls_if_worker_missing='UNKNOWN<=reserved not zero', new_predeclared_scientific_blocks=10,
        initial_policy_scope='ALL120_FRESH_ACTUAL_SNAPSHOTS',
        no_full_matrix_or_RQ_completion=True, automatic_retry=False)
    write(OUTER/'final.json', result)
    if elapsed() >= 240:
        write(OUTER/'postwrite-rejection.json', dict(reason='whole240 after final publication'))
        error = error or dict(type='PostwriteWholeBound')
    print(json.dumps(dict(status=result['status'], elapsed_seconds=elapsed()), ensure_ascii=False))
    return 0 if error is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
