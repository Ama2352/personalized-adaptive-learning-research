"""SOURCE-ONLY candidate RQ2 learned graph-source; Root duyệt trước dispatch.

59recoveryworlds expert/learned, cùng native Paper2 factories, private U/
base/clock. Oracle chỉ evaluator. Không surrogate refit hoặc neural model.
"""
import time
START, WALL = time.perf_counter(), time.time()
import ast
import ctypes
from ctypes import wintypes
from collections import Counter, deque
from dataclasses import is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import threading
import traceback
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PLAN = PREP/'rq2_fresh_graph_recovery03_plan.json'
OUTPUT_REL = 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


OUTPUT_BYTES = 0
LEAVES = {'oracle.jsonl': 12*1024**2, 'observables.jsonl': 6*1024**2,
          'oracle_endpoints.jsonl': 2*1024**2, 'shared_inputs.json': 256*1024,
          'worker_run.json': 2*1024**2}


def leaf_limit(name):
    return 32*1024 if name.startswith('initial-') else LEAVES.get(name, 1024**2)


def write(path, value):
    global OUTPUT_BYTES
    raw = (canonical(value)+'\n').encode()
    require(len(raw) <= leaf_limit(path.name) and OUTPUT_BYTES+len(raw) <= 32*1024**2,
            'Bounded JSON/total output')
    require(len(list(path.parent.iterdir())) < 160, 'Flat output file cap')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    OUTPUT_BYTES += len(raw)


def main():
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate, Kernel, MAX_PROCESSES
    owner = worker_gate()
    require(sys.argv[1:2] == ['--plan-sha256'] and len(sys.argv) == 3, 'Exact worker argv')
    plan_pin = sys.argv[2]
    require(sha(PLAN) == plan_pin and Path(sys.prefix).resolve() == ROOT/'.venv', 'Plan and actual .venv')
    plan = json.loads(PLAN.read_bytes())
    require(plan['output_relative'] == OUTPUT_REL, 'Fixed scientific output role')
    output = ROOT/plan['output_relative']
    global OUTPUT_BYTES
    OUTPUT_BYTES = (output/'dispatch.json').stat().st_size
    dispatch = json.loads((output/'dispatch.json').read_bytes())
    require(dispatch['plan_sha256'] == plan_pin and dispatch['parent_pid'] == owner['parent_owner']['pid'], 'Owned dispatch')
    expected = {**plan['source_sha256'], **plan['inputs_sha256']}
    require(all(sha(ROOT/name) == pin for name, pin in expected.items()), 'Source/input hash before work')
    old_cache = sys.pycache_prefix
    sys.pycache_prefix = str(output/'unused-fresh-bytecode')
    timer = threading.Timer(max(.001, 155-max(time.perf_counter()-START, time.time()-WALL)), lambda: os._exit(124))
    timer.daemon = True; timer.start()
    counts = Counter({name: 0 for name in plan['direct_call_caps']})
    returns = counts.copy()
    completed = reserved = 0
    active, phase, error = None, 'admission', None
    shared_prepared = False
    memory, monitor_errors = [], []
    stop = threading.Event()
    thread = None
    api = job_handle = None
    job_query_handle_closed = False
    memory_lock = threading.Lock()
    outcomes, high_checks = [], []
    prefix_verified = False
    sizes = Counter()
    files = []
    metadata = None

    def clock():
        require(max(time.perf_counter()-START, time.time()-WALL) < 155, 'Worker global155s')

    try:
        import psutil
        process = psutil.Process()
        api = Kernel()
        job_handle = api.check(api.k.OpenJobObjectW(0x0004, False, owner['job_name']))
        require(api.contains(api.k.GetCurrentProcess(), job_handle), 'Actual worker owned Job')
        class ProcessList(ctypes.Structure):
            _fields_ = [('assigned', wintypes.DWORD), ('listed', wintypes.DWORD),
                        ('pids', ctypes.c_size_t * MAX_PROCESSES)]
        def guard(stage):
            with memory_lock:
                clock()
                row = ProcessList()
                api.check(api.k.QueryInformationJobObject(job_handle, 3, ctypes.byref(row), ctypes.sizeof(row), None))
                pids = [int(row.pids[i]) for i in range(min(int(row.listed), MAX_PROCESSES))]
                require(0 < row.listed == row.assigned <= MAX_PROCESSES and process.pid in pids
                        and len(pids) == len(set(pids)), 'Complete bounded exact owned Job PID list')
                family, exited = 0, 0
                for pid in pids:
                    handle = api.k.OpenProcess(0x1000, False, pid)
                    if not handle:
                        require(not psutil.pid_exists(pid), 'Live Job process query denied')
                        exited += 1
                        continue
                    try:
                        require(api.contains(handle, job_handle), 'Same Job membership at sample')
                        token = api.token(handle)
                        child = psutil.Process(pid)
                        require(abs(child.create_time()-token['create_time']) <= 1e-5, 'Process creation identity')
                        family += int(child.memory_info().rss)
                    except psutil.NoSuchProcess:
                        exited += 1
                    finally:
                        api.close(handle)
                rss = process.memory_info()
                sample = dict(stage=stage, seconds=max(time.perf_counter()-START, time.time()-WALL),
                    family_rss_bytes=family, peak_worker_rss_bytes=getattr(rss, 'peak_wset', rss.rss),
                    available_bytes=psutil.virtual_memory().available, job_member_count=len(pids),
                    exited_during_sample=exited, scope='SAMPLED_EXACT_OWNED_JOB_RSS_AND_WORKER_HIGHWATER_NOT_OS_QUOTA')
                require(len(memory) < 5000, 'Bounded resource journal')
                memory.append(sample)
                require(max(family, sample['peak_worker_rss_bytes']) <= 512*1024**2, 'Exact Job/worker RSS512MiB')
                require(sample['available_bytes'] >= 1536*1024**2, 'Available1536MiB')
                require(not monitor_errors, 'Resource monitor error')

        # Genuine metadata bootstrap, source body được giữ nguyên từ accepted helper.
        bootstrap_path = ROOT/plan['metadata_helper']
        bootstrap = ModuleType('rq2_reviewed_metadata_helper')
        bootstrap.__file__ = str(bootstrap_path)
        exec(compile(bootstrap_path.read_bytes(), str(bootstrap_path), 'exec'), bootstrap.__dict__)
        class MetadataGuard:
            def left(self):
                guard('native_metadata')
        metadata = bootstrap.native_windows_metadata(MetadataGuard())

        allowed_corpus = (ROOT/plan['method24']['bank']['path']).resolve()
        def audit(event, args):
            if event == 'import' and str(args[0]).split('.')[0] in ('torch', 'sklearn', 'scipy', 'tensorflow', 'modal', 'boto3'):
                raise RuntimeError('No fit/neural/cloud import')
            if event in ('subprocess.Popen', 'os.system', 'socket.__new__', 'socket.getaddrinfo'):
                raise RuntimeError('No process/network after genuine metadata bootstrap')
            if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
                path = Path(os.path.abspath(os.fsdecode(args[0])))
                forbidden = any(path.is_relative_to(ROOT/name) for name in ('dataset', 'artifacts/bkt_baseline', 'venv', '.wsl'))
                forbidden |= path.is_relative_to(ROOT/'artifacts/simulator/corpora') and path != allowed_corpus
                flags = args[2] if len(args) > 2 and type(args[2]) is int else 0
                writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
                forbidden |= writing and not path.is_relative_to(output)
                require(not forbidden, 'Protected input or foreign output access')
        sys.addaudithook(audit)
        def watch():
            while not stop.wait(.1):
                try:
                    guard('monitor')
                except BaseException as caught:
                    monitor_errors.append(type(caught).__name__+': '+str(caught))
                    return
        guard('before_native_import')
        thread = threading.Thread(target=watch, daemon=True); thread.start()
        sys.path.insert(0, str(ROOT/'src'))
        import numpy as np
        import pandas as pd
        from knowledge_tracing.paper2_reference import load_reference
        from knowledge_tracing.gam_kt.simulator_mechanisms import build_mechanism_environment
        from knowledge_tracing.gam_kt.simulator_pathways import build_pathway_policy
        shared = json.loads((ROOT/plan['shared_inputs']).read_bytes())
        require((sys.version, np.__version__, pd.__version__) ==
                (shared['python_version'], shared['numpy_version'], shared['pandas_version']), 'Exact old runtime versions')
        require(all(Path(module.__file__).resolve().is_relative_to(ROOT/'.venv') for module in (np, pd, psutil)), 'Actual runtime module origins')

        # Tái dùng nguyên bốn fingerprint functions của worker cũ đã pin, không đổi scheme.
        old_path = ROOT/plan['historical_worker']
        old_ast = ast.parse(old_path.read_bytes())
        names = ('state_data', 'fingerprint', 'graph_id', 'static_id')
        selected = [node for node in ast.walk(old_ast) if isinstance(node, ast.FunctionDef) and node.name in names]
        require(len(selected) == len(names) and {node.name for node in selected} == set(names), 'Exact old helper definitions')
        namespace = dict(np=np, pd=pd, identity=identity, hashlib=hashlib, deque=deque, is_dataclass=is_dataclass)
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(old_path), 'exec'), namespace)
        state_data, fingerprint, graph_id, static_id = (namespace[name] for name in names)
        full = load_reference()
        phase = 'typed_method24_read'
        from knowledge_tracing.edge_confidence_artifact import Method24ArtifactRef, Method24TrainingBinding, Method24ReadLimits, load_method24_scores
        from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem, identity_hash
        from knowledge_tracing.shared_kt import PrerequisiteGraph
        a = plan['method24']
        accepted_bundle = json.loads((ROOT/a['accepted_bundle']['path']).read_bytes())
        require(accepted_bundle['status'] == 'completed' and len(accepted_bundle['outputs_sha256']) == 113
                and accepted_bundle['native']['run_sha256'] == a['artifact']['outer_run_sha256']
                and accepted_bundle['native']['request_sha256'] == a['artifact']['request_sha256']
                and accepted_bundle['native']['source11_sha256'] == a['expected_training']['source_files_sha256'],
                'Actual accepted113 producer envelope')
        bank_json = json.loads((ROOT/a['bank']['path']).read_bytes())
        bank = SimulatorBank(bank_json['environment_id'], tuple(SimulatorItem(**item) for item in bank_json['items']))
        require(bank.identity == a['bank']['identity'], 'Public bank exact binding')
        training = dict(a['expected_training'])
        for name in ('public_files_sha256', 'source_files_sha256', 'runtime_files_sha256'):
            training[name] = tuple(sorted(training[name].items()))
        loaded = load_method24_scores(Method24ArtifactRef(**a['artifact']), expected_training=Method24TrainingBinding(**training),
            bank=bank, declared_graph=PrerequisiteGraph.from_edges(a['declared_graph']['nodes'], a['declared_graph']['edges']),
            graph_binding='method24_learned', limits=Method24ReadLimits(**a['read_limits']))
        require(len(loaded.declared_nodes) == 28 and len(loaded.declared_edges) == 31
                and all(score.supported and score.score is not None for score in loaded.edge_scores)
                and loaded.actual_solver_calls == loaded.processed_fit_slots == 2352, 'Historical supported learned31, no new fit')
        learned = load_reference(estimator_edges=list(loaded.declared_edges), controller_edges=None)
        refs = dict(full=full, learned=learned)
        scope = full['environment']; nodes = list(scope['nodes'])
        require(nodes == shared['node_order'] and set(nodes) == set(loaded.declared_nodes)
                and set(scope['question_features']) == set(bank.item_ids), 'Exact old order/bank and learned endpoints')
        require(shared['model_initial_elo'] == scope['MODEL_INITIAL_ELO'] == 1200., 'Exact old initial estimate constant')
        for reference in refs.values():
            require(graph_id(reference['environment']) == graph_id(reference['controller']) == shared['graphs']['full'], 'Fixed environment/controller expert graph')
            require(reference['estimator']['nodes'] == nodes
                and fingerprint(reference['estimator']['question_features']) == fingerprint(scope['question_features'])
                and fingerprint(reference['estimator']['concept_features']) == fingerprint(scope['concept_features']), 'Same native feature geometry')
        require(graph_id(learned['estimator']) != graph_id(full['estimator']), 'No silent equivalent graph source')
        static = {name: static_id(ref) for name, ref in refs.items()}
        old_admission = json.loads((ROOT/plan['old_admission']).read_bytes())
        require(static['full'] == old_admission['static_namespace_sha256']['full'], 'Exact historical expert namespace fingerprint')
        classes = {strength: build_mechanism_environment(full, prerequisite_strength=strength) for strength in (0., .55)}
        def call(kind, method, *args, **kwargs):
            clock(); require(counts[kind] < plan['direct_call_caps'][kind], 'Direct-call cap '+kind)
            counts[kind] += 1
            value = method(*args, **kwargs)
            returns[kind] += 1; clock()
            return value

        # Exact parent seals, chỉ đọc sau owned GO và trước bất kỳ child world.
        parent = ROOT/plan['parent']['output_relative']
        original = json.loads((ROOT/plan['parent']['plan_path']).read_bytes())
        proof = json.loads((ROOT/plan['parent']['proof_path']).read_bytes())
        parent_worker = json.loads((parent/'worker_run.json').read_bytes())
        parent_outer = json.loads((ROOT/plan['parent']['outer_path']).read_bytes())
        require(plan['cells'] == original['cells'][61:] and len(plan['cells']) == 59
                and plan['cells'][0]['cell_id'] == 'F062' and plan['cells'][-1]['cell_id'] == 'F120', 'Exact59 original cells')
        require(proof['committed_cell_ids'] == [f'F{i:03}' for i in range(1, 62)]
                and proof['partial_cell'] == 'F062' and proof['partial_complete_responses'] == 30, 'Parent prefix admission')
        require(parent_worker['completed_cells'] == 61 and parent_worker['reserved_interact_attempts'] == 7440
                and parent_worker['direct_attempts'] == parent_worker['direct_returns']
                and parent_worker['direct_returns']['interact'] == 7350
                and parent_worker['error']['message'] == 'Available1536MiB', 'Parent actual counters/RAM failure')
        require(parent_outer['owned_receipt']['cleanup_accepted'] is True
                and parent_outer['owned_receipt']['job_active_after_cleanup'] == 0
                and parent_worker['job_query_handle_closed'] is True and parent_worker['monitor_stopped'] is True,
                'Parent terminal and no future work')
        for name, record in proof['native_files_sha256_and_bytes'].items():
            require(sha(parent/name) == record['sha256'] and (parent/name).stat().st_size == record['bytes'], 'Parent72 immutable seals')
        require(parent_worker['worker_seconds']+155 <= 210 and parent_outer['elapsed_seconds']+180 <= 240,
                'Distinct cumulative worker/outer bounds')
        amendment = plan['recovery_amendment']
        require(amendment == dict(parent_reserved=7440, parent_actual=7350, released_unused=90,
            child_reserved=7080, cumulative_gross_reserved=14520, cumulative_physical_response_cap=14430,
            cumulative_constructor_cap=121, added_constructor=1, added_replayed_exposures=30,
            primary_worlds=120, primary_responses=14400), 'Exact ROOT recovery physical amendment')
        require(7440+7080-90 == 14430 and 7350+7080 == 14430 and 62+59 == 121, 'Reconciliation arithmetic')
        write(output/'recovery_accounting.json', dict(status='RESERVED_RECOVERY_BEFORE_ANY_CHILD_WORLD',
            amendment=amendment, plan_sha256=plan_pin, parent=plan['parent'], owner=owner,
            reservation_scope='7080batchallocation; per-cell ledger is breakdown, not added reservation',
            no_parent_ledger_mutation=True, scientific_rng_generators=0, anchor_calls=0, uniform_array_calls=0))
        fresh_shared_path = parent/'shared_inputs.json'
        require(fresh_shared_path.stat().st_size <= 256*1024, 'Parent shared byte cap')
        fresh_shared = json.loads(fresh_shared_path.read_bytes())
        blocks = {}
        for saved in fresh_shared['blocks']:
            block = saved['block']
            u = np.asarray(saved['uniforms'], dtype=np.float64, order='C')
            require(u.shape == (120, 2) and np.isfinite(u).all() and ((0 <= u) & (u < 1)).all()
                    and hashlib.sha256(u.tobytes()).hexdigest() == saved['uniform_sha256'], 'Exact saved U, no draws')
            bases = {int(a): {node: values[node] for node in nodes} for a, values in saved['bases'].items()}
            require(set(bases) == {1000, 1150, 1300} and all(identity(base) == saved['base_sha256'][str(a)]
                    for a, base in bases.items()), 'Exact saved three bases')
            saved = {**saved, 'base_sha256': {int(a): value for a, value in saved['base_sha256'].items()}}
            u.setflags(write=False); blocks[block] = dict(saved=saved, U=u, bases=bases)
        require(set(blocks) == set(range(21010, 21020)), 'Same10 saved blocks')
        write(output/'shared_inputs.json', fresh_shared)
        require(sha(output/'shared_inputs.json') == sha(fresh_shared_path), 'Shared copy raw bytes exact')
        shared_prepared = True
        committed = set(proof['committed_cell_ids'])
        parent_outcomes, parent_endpoints, parent_initial = {}, {}, {}
        for raw in (parent/'cell_ledger.jsonl').read_bytes().splitlines():
            record = json.loads(raw)
            if record['event'] == 'COMPLETED_CELL': parent_outcomes[record['cell_id']] = record['outcome']
        for raw in (parent/'oracle_endpoints.jsonl').read_bytes().splitlines():
            record = json.loads(raw); parent_endpoints[record['cell_id']] = record
        require(set(parent_outcomes) == set(parent_endpoints) == committed, '61committed components only')
        for cell in original['cells'][:62]:
            initial = json.loads((parent/('initial-'+cell['cell_id']+'.json')).read_bytes())
            require(initial['cell'] == cell, 'Parent initial cell seal')
            parent_initial[cell['cell_id']] = initial
        parent_prefix_obs, parent_prefix_oracle, parent_actions = [], [], {}
        for raw in (parent/'observables.jsonl').read_bytes().splitlines():
            record = json.loads(raw); cell_id = record['cell_id']
            if cell_id == 'F062': parent_prefix_obs.append(record)
            else:
                require(cell_id in committed, 'No uncommitted parent component')
                parent_actions.setdefault(cell_id, []).append((record['query']['question'], record['correct']))
        for raw in (parent/'oracle.jsonl').read_bytes().splitlines():
            record = json.loads(raw)
            if record['cell_id'] == 'F062': parent_prefix_oracle.append(record)
        require(len(parent_prefix_obs) == len(parent_prefix_oracle) == 30
                and all(len(values) == 120 for values in parent_actions.values()), 'Complete parent/prefix row populations')
        high_checks = [dict(row, scope='PARENT_RAW_VERIFIED_COMPLETE_HIGH_PAIR') for row in proof['high_pairs']]
        require(len(high_checks) == 20, 'Parent40 complete high controls sealed')
        write(output/'parent_reference.json', dict(parent=plan['parent'], complete_cells=sorted(committed),
            excluded_partial_rows=30, excluded_partial_cell='F062', parent_resource_failure_retained=True))
        write(output/'admission.json', dict(kind='RECOVERY_ADMISSION_NOT_OUTCOME_ACCEPTANCE', source_input_sha256=expected,
            runtime=dict(python=sys.version, numpy=np.__version__, pandas=pd.__version__), static_namespace_sha256=static,
            learned_artifact_identity=loaded.identity, learned_graph=loaded.declared_edges,
            learned_exported_graph_sha256=loaded.exported_graph_sha256, confidence_used_as_GAM_weight=False,
            initial_state_scope='ACTUAL_CHILD59_AND_SEALED_PARENT61', scientific_rng_generators=0))

        def append(stream, name, value):
            global OUTPUT_BYTES
            raw = (canonical(value)+'\n').encode()
            require(len(raw) <= 16384 and sizes[name]+len(raw) <= leaf_limit(name)
                    and OUTPUT_BYTES+len(raw) <= 32*1024**2, 'Trace byte caps')
            stream.write(raw); sizes[name] += len(raw); OUTPUT_BYTES += len(raw)

        initial_nonedge_policy = None
        fresh_environment_hashes, actions, trajectory_pairs = {}, {}, []
        for cell in original['cells'][:61]:
            initial = parent_initial[cell['cell_id']]
            fresh_environment_hashes[cell['block'], cell['ability']] = initial['environment_sha256']
        phase = 'fresh_cells'
        with (output/'cell_ledger.jsonl').open('xb') as ledger, (output/'observables.jsonl').open('xb') as obslog, (output/'oracle.jsonl').open('xb') as oraclelog, (output/'oracle_endpoints.jsonl').open('xb') as endpoints:
            for cell in plan['cells']:
                active = cell['cell_id']; block, ability, graph, strength = (cell[k] for k in ('block', 'ability', 'graph', 'mechanism_strength'))
                phase = cell['phase']
                require(shared_prepared, 'Shared inputs durable before worlds')
                require(len(high_checks) == 20, 'Parent20 high controls before recovery')
                require(active == 'F062' or prefix_verified, 'Strict prefix barrier before F063 and later worlds')
                guard('before_reservation:'+active)
                require(reserved+120 <= 7080, 'Child reservation7080')
                reserved += 120
                info = blocks[block]; base, U = info['bases'][ability], info['U']
                append(ledger, 'cell_ledger.jsonl', dict(event='RESERVED_BEFORE_WORLD', cell=cell,
                    cumulative_reserved=reserved, actual_attempts=None, base_sha256=identity(base), uniform_sha256=info['saved']['uniform_sha256']))
                ledger.flush(); os.fsync(ledger.fileno())
                before = counts.copy()
                environment = call('environment_constructor', classes[strength], base)
                policy = call('policy_builder', build_pathway_policy, refs[graph], signal=True, parent_adaptation=True, local_adaptation=False)
                require(environment.base == base == environment.theta and all(v is None for v in environment.last_seen.values()), 'Fresh source environment')
                require('graph' not in vars(policy), 'Source treatment graph remains namespace-bound, not a hidden policy field')
                initial = fingerprint(vars(policy))
                if initial_nonedge_policy is None: initial_nonedge_policy = initial
                require(initial == initial_nonedge_policy and all(state.theta == 1200. for state in policy.states.values()), 'Same actual fresh nonedge initialization')
                environment_hash = fingerprint(vars(environment))
                pair_key = (block, ability)
                prior_hash = fresh_environment_hashes.setdefault(pair_key, environment_hash)
                require(prior_hash == environment_hash, 'Actual fresh environment pair equality')
                treatment = dict(estimator_graph_sha256=graph_id(refs[graph]['estimator']),
                    environment_graph_sha256=graph_id(full['environment']), controller_graph_sha256=graph_id(full['controller']),
                    nonedge_policy_initial_sha256=initial, signal=True, parent_adaptation=True, local_adaptation=False)
                write(output/('initial-'+active+'.json'), dict(cell=cell, nonedge_policy_state=state_data(vars(policy)),
                    environment_state=state_data(vars(environment)), nonedge_policy_sha256=initial, environment_sha256=fingerprint(vars(environment)),
                    treatment_binding=treatment, treatment_binding_sha256=identity(treatment),
                    initial_state_scope='ACTUAL_FRESH_SNAPSHOT_BEFORE_RESPONSE1'))
                if active == 'F062':
                    require(sha(output/'initial-F062.json') == sha(parent/'initial-F062.json'), 'Exact actual F062 initial snapshot')
                timestamp = pd.Timestamp('2026-01-01', tz='UTC'); action_rows = []; positive_deficit = ceiling_hits = 0
                for step in range(120):
                    if active == 'F062' and step >= 30:
                        require(prefix_verified, 'Durable strict prefix barrier before step31')
                    clock(); timestamp += pd.Timedelta(hours=72 if step > 0 and step % 28 == 0 else 6)
                    cid, qid, difficulty = call('select', policy.select)
                    prediction = call('predict', policy.predict, cid, qid, difficulty, timestamp)
                    require(type(prediction) is float and math.isfinite(prediction) and 0 <= prediction <= 1, 'Native finite prediction')
                    env_before = fingerprint(vars(environment))
                    theta = call('oracle_theta_probe', environment.theta_at, cid, timestamp)
                    p_oracle = call('oracle_probability_probe', scope['elo_probability'], theta, difficulty)
                    require(fingerprint(vars(environment)) == env_before, 'Readonly evaluator probe')
                    uo, ul = float(U[step, 0]), float(U[step, 1])
                    result = call('interact', environment.interact, cid, difficulty, timestamp, uo, ul)
                    require(type(result) is dict and type(result.get('y')) is int and result['y'] in (0, 1), 'Native binary world result')
                    require(result['p_true'] == p_oracle and result['theta_before'] == theta and result['y'] == int(uo < p_oracle), 'Native response identity')
                    challenge = math.exp(-.5*((p_oracle-.65)/.22)**2)
                    gain = scope['TRUE_GAIN_SCALE']*challenge*(1.15 if result['y'] == 0 else .85)*(1.+.20*min(result['gap_days'], 7.)/7.)*(1.-strength*result['prerequisite_deficit'])*(.85+.30*ul)
                    require(result['challenge_match'] == challenge and result['learning_gain'] == gain
                            and environment.theta[cid] == min(1600., theta+gain), 'Unchanged native learning equation')
                    positive_deficit += int(result['prerequisite_deficit'] > 0); ceiling_hits += int(theta+gain >= 1600.)
                    call('update', policy.update, cid, qid, difficulty, timestamp, result['y'], prediction)
                    query = dict(concept=str(cid), question=str(qid), difficulty=float(difficulty), timestamp_iso=timestamp.isoformat(), timestamp_ns=int(timestamp.value))
                    observable = dict(cell_id=active, step=step, query=query, probability=prediction, correct=result['y'])
                    oracle = dict(cell_id=active, step=step, oracle_probability=p_oracle, oracle_theta_before=theta,
                        environment_readonly_probe_sha256=env_before, outcome_uniform=uo, learning_uniform=ul, result=result, ceiling_hit=theta+gain >= 1600.)
                    action_rows.append((str(qid), result['y']))
                    append(obslog, 'observables.jsonl', observable); append(oraclelog, 'oracle.jsonl', oracle)
                    if active == 'F062' and step < 30:
                        require(canonical(observable) == canonical(parent_prefix_obs[step])
                                and canonical(oracle) == canonical(parent_prefix_oracle[step]),
                                'Strict30 original prefix parity, no tolerance')
                        if step == 29:
                            for stream in (obslog, oraclelog): stream.flush(); os.fsync(stream.fileno())
                            write(output/'prefix_parity.json', dict(status='STRICT30_PREFIX_EXACT_BEFORE_STEP31',
                                cell='F062', rows=30, initial_snapshot_exact=True, plan_sha256=plan_pin,
                                compared_after_native_predict_interact_update=True, no_oracle_policy_features=True))
                            prefix_verified = True
                    if step % 10 == 9: guard('progress:'+active+':'+str(step))
                snapshot = call('snapshot', environment.snapshot, timestamp)
                outcome = float(np.mean([snapshot[node]-base[node] for node in nodes]))
                final = dict(environment_state=state_data(vars(environment)), policy_state=state_data(vars(policy)), snapshot=snapshot, outcome=outcome)
                endpoint = dict(cell_id=active, timestamp_iso=timestamp.isoformat(), timestamp_ns=int(timestamp.value),
                    final_snapshot=snapshot, final_environment_state=final['environment_state'], final_policy_state_sha256=identity(final['policy_state']),
                    base_sha256=identity(base), net_mean_theta_gain=outcome, scope='oracle/evaluator only, never policy input')
                actions[active] = action_rows
                expected_delta = Counter(environment_constructor=1, policy_builder=1, select=120, predict=120, interact=120,
                    update=120, oracle_theta_probe=120, oracle_probability_probe=120, snapshot=1)
                require(counts-before == expected_delta and identity(base) == info['saved']['base_sha256'][ability]
                        and hashlib.sha256(U.tobytes()).hexdigest() == info['saved']['uniform_sha256']
                        and {name: static_id(ref) for name, ref in refs.items()} == static, 'Direct counts/static/shared inputs after cell')
                row = dict(block=block, ability=ability, graph_source='expert' if graph == 'full' else 'learned',
                    mechanism_strength=strength, outcome=outcome, latent_identity=identity(base), uniform_identity=info['saved']['uniform_sha256'])
                append(endpoints, 'oracle_endpoints.jsonl', endpoint)
                append(ledger, 'cell_ledger.jsonl', dict(event='COMPLETED_CELL', cell_id=active, outcome=row,
                    cumulative_attempts=dict(counts), cumulative_returns=dict(returns), positive_deficit_events=positive_deficit, ceiling_hit_events=ceiling_hits))
                for stream in (ledger, obslog, oraclelog, endpoints): stream.flush(); os.fsync(stream.fileno())
                outcomes.append(row); completed += 1; guard('after_cell:'+active)
        require(completed == 59 and reserved == 7080 and counts == returns == Counter(plan['direct_call_caps'])
                and prefix_verified and len(high_checks) == 20, '59complete recovery worlds and strict prefix')
        write(output/'child_outcomes.json', outcomes)
        combined = [parent_outcomes[cell['cell_id']] for cell in original['cells'][:61]] + outcomes
        require(len(combined) == 120, 'Complete logical primary120')
        expert = {(r['block'], r['ability'], r['mechanism_strength']): r for r in combined if r['graph_source'] == 'expert'}
        learned_y = {(r['block'], r['ability'], r['mechanism_strength']): r for r in combined if r['graph_source'] == 'learned'}
        require(len(expert) == len(learned_y) == 60 and set(expert) == set(learned_y), 'Exact merged60pairs')
        contrasts = []
        for key in sorted(expert):
            prior, new = expert[key], learned_y[key]
            require(prior['latent_identity'] == new['latent_identity'] and prior['uniform_identity'] == new['uniform_identity'], 'Fresh paired identities')
            contrasts.append(dict(block=key[0], ability=key[1], mechanism_strength=key[2], expert=prior['outcome'],
                learned=new['outcome'], expert_minus_learned=prior['outcome']-new['outcome']))
        q = {(r['block'], r['ability'], r['mechanism_strength']): r['expert_minus_learned'] for r in contrasts}
        interactions = [dict(block=b, ability=a, lambda_difference=q[b, a, .55]-q[b, a, 0.])
                        for b in range(21010, 21020) for a in (1000, 1150, 1300)]
        require(all(r['lambda_difference'] == 0. for r in interactions if r['ability'] == 1300), 'High K zero; other signs unrestricted')
        all_actions = {**parent_actions, **actions}
        for b, a, strength in sorted(expert):
            cells = [c for c in original['cells'] if (c['block'], c['ability'], c['mechanism_strength']) == (b, a, strength)]
            old_id = next(c['cell_id'] for c in cells if c['graph'] == 'full')
            new_id = next(c['cell_id'] for c in cells if c['graph'] == 'learned')
            old_rows, new_rows = all_actions[old_id], all_actions[new_id]
            require(len(old_rows) == len(new_rows) == 120, 'Primary120 per paired history')
            different = [i for i, (old, new) in enumerate(zip(old_rows, new_rows)) if old[0] != new[0]]
            first = different[0] if different else None
            equal = all(old[1] == new[1] for old, new in zip(old_rows[:first], new_rows[:first]))
            require(equal, 'Labels equal before first selected-query divergence')
            trajectory_pairs.append(dict(block=b, ability=a, mechanism_strength=strength, ordinal_rows=120,
                question_id_differences=len(different), question_id_difference_fraction=len(different)/120,
                first_question_difference_step0=first, first_question_difference_ordinal1=None if first is None else first+1,
                labels_equal_before_first_question_difference=equal, scope='different served histories after divergence'))
        write(output/'outcomes.json', combined); write(output/'graph_source_contrasts.json', contrasts)
        write(output/'conditional_lambda_contrasts.json', interactions); write(output/'high_controls.json', high_checks)
        write(output/'trajectory_pairs.json', trajectory_pairs)
        write(output/'summary.json', dict(kind='RECOVERED_FRESH120_NO_INFERENCE_PENDING_OUTER', primary_worlds=120,
            primary_responses=14400, child_worlds=59, child_response_calls=7080, physical_constructors=121,
            physical_response_calls=14430, duplicated_replay_exposures=30, components=60, contrasts=30,
            parent_complete_components=61, parent_failure_retained=True, primary_projection='parent F001-F061 +child F062-F120',
            scientific_rng_generators=0, one_fixed_learned_graph=True, no_causal_human_or_confidence_probability_claim=True))
        require(all(sha(ROOT/name) == pin for name, pin in expected.items()), 'Source/input post hash')
        guard('before_final_receipt')
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught), phase=phase, active_cell=active)
        with (output/'failure.log').open('x', encoding='utf-8') as stream: traceback.print_exc(file=stream)
    finally:
        stop.set()
        if thread is not None: thread.join(timeout=.5)
        if job_handle is not None and (thread is None or not thread.is_alive()):
            try:
                api.close(job_handle); job_query_handle_closed = True
            except BaseException as caught:
                error = error or dict(type=type(caught).__name__, message=str(caught))
        sys.pycache_prefix = old_cache
        timer.cancel()
        after = {name: sha(ROOT/name) for name in expected}
        if after != expected: error = error or dict(type='SourceDrift', message='postsource mismatch')
        duration = max(time.perf_counter()-START, time.time()-WALL)
        if duration >= 155 or monitor_errors or not job_query_handle_closed or (thread is not None and thread.is_alive()):
            error = error or dict(type='ResourceOrMonitor', message='worker boundary rejected')
        files = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
        receipt = dict(status='COMPLETE59_RECOVERY_PENDING_OUTER' if error is None else 'REJECTED_RETAIN_UNKNOWN_ACTIVE_WORK', error=error,
            completed_cells=completed, reserved_interact_attempts=reserved, direct_attempts=dict(counts), direct_returns=dict(returns),
            shared_prepared=shared_prepared, prefix_verified=prefix_verified, source_input_before_sha256=expected, source_input_after_sha256=after,
            owner=owner, native_metadata=metadata, monitor_stopped=thread is not None and not thread.is_alive(), monitor_errors=monitor_errors,
            resources=memory, resource_scope='SAMPLED_EXACT_OWNED_JOB_RSS_AND_WORKER_HIGHWATER_NOT_OS_QUOTA',
            maximum_job_processes=max((row['job_member_count'] for row in memory), default=0),
            job_query_handle_closed=job_query_handle_closed, worker_seconds=duration, outputs_sha256=files, actual_counts_if_hardkill='UNKNOWN<=reserved, never0',
            new_solver_calls=0, nn_optimizer_calls=0, new_scientific_rng_generators=0,
            cumulative_worker_seconds=parent_worker['worker_seconds']+duration if 'parent_worker' in locals() else None)
        receipt.update(new_graph_offline_neural_solver_fits=0,
            actual_online_policy_update_returns=returns['update'], native_GAM_online_updates_are_actual_model_calls=True)
        write(output/'worker_run.json', receipt)
        if max(time.perf_counter()-START, time.time()-WALL) >= 155:
            write(output/'postwrite-rejection.json', dict(reason='worker155s after publication'))
            error = error or dict(type='PostwriteBound')
    return 0 if error is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
