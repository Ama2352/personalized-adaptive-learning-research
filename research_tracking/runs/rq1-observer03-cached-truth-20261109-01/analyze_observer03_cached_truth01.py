"""Đối chiếu witness observer03 đã lưu, parser và thống kê chỉ dùng stdlib."""
import datetime as dt
import hashlib
import json
import math
import struct
import types

KEY = (21000, 'PG', False, False)
THETA = 1250.0
PI = .55
READOUT_FIELDS = frozenset(('native_M', 'pi_task_decayed', 'pi_task_stored', 'pi_time_decayed',
    'pi_time_stored', 'prediction', 'selected', 'step', 'stored_pi_gate', 'theta_est', 'theta_gate', 'timestamp'))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def exact(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is float:
        return struct.pack('>d', left) == struct.pack('>d', right)
    if type(left) is dict:
        return left.keys() == right.keys() and all(exact(left[k], right[k]) for k in left)
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def decode(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON token')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def clock(steps):
    need(type(steps) is int and 1 <= steps <= 120, 'Bounded ordered steps')
    current = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    result = []
    for step in range(steps):
        current += dt.timedelta(hours=72 if step > 0 and step % 28 == 0 else 6)
        result.append(current.isoformat())
    return result


def phases(on, off, *, steps=120):
    """OFF là integrity control, không thêm rows vào population."""
    for value, phase in ((on, 'targeted_on'), (off, 'targeted_off')):
        need(type(value) is dict and value['phase'] == phase and exact(value['key'], list(KEY)), 'Fixed history key/phase')
        need(type(value['events']) is int and value['events'] == steps
             and type(value['readouts']) is list and len(value['readouts']) == steps, 'Whole readout population')
        for key in ('initial_state_sha256', 'final_state_sha256'):
            need(type(value[key]) is str and len(value[key]) == 64
                 and all(c in '0123456789abcdef' for c in value[key]), 'State identity')
        need(value['profiler_installed'] is False and value['instance_attributes_added'] is False, 'Closed observer state')
    need(exact(on['readouts'], off['readouts'])
         and on['initial_state_sha256'] == off['initial_state_sha256']
         and on['final_state_sha256'] == off['final_state_sha256'], 'OFF/ON scientific parity')
    observer = on['observer']
    need(observer['live'] is False and observer['class_attributes_restored'] is True
         and observer['cleanup_errors'] == [] and observer['pending_attributes'] == [], 'Observer restored')
    return on['readouts']


def joined_rows(readouts, history, questions, *, steps=120):
    need(type(readouts) is list and len(readouts) == steps and len(history) == steps, 'No dropped/extra rows')
    times = clock(steps)
    result = []
    for step, (native, stored) in enumerate(zip(readouts, history)):
        need(type(native) is dict and set(native) == READOUT_FIELDS, 'Closed native readout schema')
        need(type(native['step']) is int and type(stored['step']) is int
             and native['step'] == stored['step'] == step, 'Unique ordered step identity')
        key = tuple(stored[name] for name in ('seed', 'profile', 'graph_on', 'mechanism_on'))
        need(exact(key, KEY), 'Exact source history key')
        question = stored['question']
        need(question in questions and type(native['selected']) is list and len(native['selected']) == 3,
             'Question/full selected tuple')
        bank = questions[question]
        need(exact(native['selected'], [stored['concept'], question, bank['difficulty']])
             and stored['concept'] == bank['concept'], 'Query/bank/full tuple mismatch')
        need(type(native['prediction']) is float and type(stored['prediction']) is float
             and exact(native['prediction'], stored['prediction']), 'Prediction bits mismatch')
        need(native['timestamp'] == times[step], 'Exact source clock mismatch')
        for name in ('theta_est', 'pi_task_stored', 'pi_time_stored', 'pi_task_decayed', 'pi_time_decayed', 'prediction'):
            need(finite(native[name]), 'Finite native values')
        need(all(0 <= native[name] <= 1 for name in
             ('pi_task_stored', 'pi_time_stored', 'pi_task_decayed', 'pi_time_decayed', 'prediction')),
             'Probability/uncertainty ranges')
        theta_gate = native['theta_est'] >= THETA
        pi_gate = native['pi_task_stored'] <= PI
        need(all(type(native[name]) is bool for name in ('theta_gate', 'stored_pi_gate', 'native_M'))
             and native['theta_gate'] == theta_gate and native['stored_pi_gate'] == pi_gate
             and native['native_M'] == (theta_gate and pi_gate), 'Literal native predicates')
        need(finite(stored['theta_before']), 'Finite simulator theta_before')
        latent = stored['theta_before'] >= THETA
        result.append(dict(seed=KEY[0], profile=KEY[1], graph_on=KEY[2], mechanism_on=KEY[3], step=step,
            concept=stored['concept'], question=question, difficulty=bank['difficulty'], timestamp=times[step],
            prediction=native['prediction'], theta_est=native['theta_est'], pi_task_stored=native['pi_task_stored'],
            theta_gate=theta_gate, stored_pi_gate=pi_gate, native_M=native['native_M'],
            simulator_theta_before=stored['theta_before'], simulator_latent_criterion=latent,
            uncertainty_suppresses_native_M=theta_gate and not pi_gate))
    return result


def summarize(rows):
    native = {f'{a}{b}': 0 for a in (0, 1) for b in (0, 1)}
    theta = dict(native)
    suppression = {'latent_false': 0, 'latent_true': 0}
    for row in rows:
        latent = row['simulator_latent_criterion']
        native[f"{int(row['native_M'])}{int(latent)}"] += 1
        theta[f"{int(row['theta_gate'])}{int(latent)}"] += 1
        if row['uncertainty_suppresses_native_M']:
            suppression['latent_true' if latent else 'latent_false'] += 1
    need(sum(native.values()) == sum(theta.values()) == len(rows), 'Complete two-by-two partitions')
    return dict(history_key=list(KEY), queried_concept_time_rows=len(rows), history_count=1,
        native_M_by_latent=native, theta_gate_by_latent=theta, cell_order='estimator_boolean,simulator_latent_boolean',
        uncertainty_suppression_by_latent=suppression, theta_threshold=THETA, stored_pi_threshold=PI,
        comparisons='inclusive binary64 without rounding or epsilon', new_independent_N=0,
        graph_comparison=False, calibration_claim=False, human_mastery_truth_claim=False,
        full_RQDIAG23_population=False)


def load_reader(raw, path):
    """Exact reviewed stdlib definitions, không chạy historical entrypoint hoặc PYC."""
    module = types.ModuleType('observer03_reviewed_cpu09_reader')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def analyze_files(root, packet, read, guard):
    paths = packet['paths']
    raw = {name: read(root / path) for name, path in paths.items() if name != 'traces'}
    reader = load_reader(raw['reader'], root / paths['reader'])
    cache_contract = reader.decode(raw['cache_contract'])
    for name, value in packet['inputs'].items():
        if name in cache_contract['inputs']:
            need(value == cache_contract['inputs'][name], 'Original cache-contract input identity')
    reader.validate_manifest(reader.decode(raw['cache_manifest']), cache_contract)
    questions, roots = reader.topology({name: raw[name] for name in ('nodes', 'edges', 'questions')})
    grid = cache_contract['grid']
    need(exact(grid, packet['cache_grid']) and grid['seeds'] == list(range(21000, 21010))
         and grid['profiles'] == ['PG', 'PY', 'PYH'] and grid['steps'] == 120, 'Exact full cache grid')
    # Scientific cache inputs used here retain the original contract hash/size pins.
    # Only strict parser/validator run here. Its downstream analysis is never called.
    rows = reader.trace_rows(root / paths['traces'], max_compressed=1024**2, max_uncompressed=8*1024**2,
        max_line=8192, max_rows=14400, guard=guard)
    buckets = reader.validate_trace(rows, seeds=grid['seeds'], profiles=grid['profiles'], steps=120,
        questions=questions, roots=roots)
    need(len(buckets) == 120 and sum(map(len, buckets.values())) == 14400, 'All original rows admitted')
    outer = decode(raw['pilot_outer'])
    need(outer['status'] == 'ACCEPTED_ONE_HISTORY_TARGETED_OBSERVER_OPERATIONAL_PILOT' and outer['errors'] == []
         and outer['receipt']['accepted'] is True and outer['receipt']['cleanup_accepted'] is True
         and outer['receipt']['job_active_after_cleanup'] == 0 and outer['environment_restored'] is True
         and outer['source_input_before'] == outer['source_input_after'], 'Actual pilot outer/source/cleanup')
    owned = decode(raw['pilot_owned'])
    need(owned == outer['receipt'] and owned['errors'] == owned['cleanup_errors'] == []
         and owned['actual_worker_in_job_before_GO'] is True and owned['popen_handle_closed'] is True,
         'Actual pilot owned receipt')
    manifest = decode(raw['observer_manifest'])
    need(manifest['status'] == 'completed', 'Closed observer bundle')
    for name, pin in outer['source_input_before'].items():
        if name in packet['inputs']:
            need(pin == packet['inputs'][name]['sha256'], 'Same pilot source/cache bytes')
    for role, alias, original in (('on', '03__on.json', 'on.json'), ('off', '03__off.json', 'off.json')):
        pin = hashlib.sha256(raw[role]).hexdigest()
        need(manifest['outputs_sha256'][alias] == pin
             and outer['outputs'][original] == dict(sha256=pin, bytes=len(raw[role])), 'Closed ON/OFF output binding')
    on, off = decode(raw['on']), decode(raw['off'])
    admitted = phases(on, off)
    guard()
    joined = joined_rows(admitted, buckets[KEY], questions)
    summary = summarize(joined)
    validation = dict(status='ALL120_ADMITTED_BEFORE_DESCRIPTIVE_SUMMARY', cache_rows=14400, cache_histories=120,
        joined_rows=120, unique_keys=len({(r['seed'], r['profile'], r['graph_on'], r['mechanism_on'], r['step']) for r in joined}),
        exact_query_prediction_clock=True, native_predicates_recomputed=True, ON_used_once=True,
        OFF_integrity_only=True, all_zero_cells_retained=True, model_calls=0, world_calls=0, RNG_draws=0,
        new_independent_N=0, oracle_scope='ONLY_STORED_SIMULATOR_THETA_BEFORE_AFTER_NATIVE_READOUT_ADMISSION')
    guard()
    return joined, summary, validation
