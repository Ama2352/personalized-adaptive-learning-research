"""Trace fixed-history RQ1; SOURCE PREPARATION, no authority to execute.

Only main loads native NumPy/Pandas/Paper2; pure helpers permit tiny fixtures.
No teacher/oracle/current-answer input to capture(). Legacy admission is exact.
"""
import argparse
from collections import Counter, deque
import copy
from dataclasses import is_dataclass
import gzip
import hashlib
import io
import json
import math
import os
import platform
from pathlib import Path
import struct
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
VARIANTS = ('graph_package', 'empty_graph_package')
SEEDS = (20000, 20001, 20002)
PROFILES = ('PG', 'PY', 'PYH')
TAU_RAW = 0.5637150147511514


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def exact(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, float):
        return struct.pack('>d', left) == struct.pack('>d', right)
    if isinstance(left, dict):
        return set(left) == set(right) and all(exact(left[k], right[k]) for k in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def predicates(theta, pi):
    need(type(theta) is float and type(pi) is float and math.isfinite(theta) and math.isfinite(pi)
         and 0 <= pi <= 1, 'finite native theta/pi')
    a, b = theta >= 1250., pi <= .55
    return a, b, a and b


def reference_items(frame_rows, cid, query):
    rows = [(str(q), float(d)) for q, d in frame_rows]
    need(len(rows) == 3 and len({q for q, d in rows}) == 3
         and sorted(d for q, d in rows) == [1050., 1200., 1350.], 'exact three real references')
    need(query['concept'] == cid and (query['question'], query['difficulty']) in rows,
         'current query is exactly one real reference, no invented item')
    return rows


def capture(policy, query, nodes, refs, timestamp, call, fingerprint):
    """No y parameter. All fields/probes before current update; raw, uncalibrated."""
    before = fingerprint(policy)
    states = []
    for cid in nodes:
        state = policy.states[cid]
        theta, pi = float(state.theta), float(state.pi_task)
        a, b, m = predicates(theta, pi)
        need(bool(call('direct_is_mastered', policy.is_mastered, cid)) == m, 'native M predicate exact')
        states.append([theta, pi, a, b, m])
    p = call('current_predict', policy.predict, query['concept'], query['question'], query['difficulty'], timestamp)
    need(type(p) is float and math.isfinite(p) and 0 <= p <= 1, 'native finite current probability')
    clone = copy.deepcopy(policy)
    need(fingerprint(clone) == before, 'deepcopy frozen state identity')
    values = []
    for qid, difficulty in refs:
        value = p if qid == query['question'] else call('reference_predict', clone.predict,
            query['concept'], qid, difficulty, timestamp)
        need(type(value) is float and math.isfinite(value) and 0 <= value <= 1, 'finite raw reference probability')
        values.append(dict(question=qid, difficulty=difficulty, probability=value))
    need(fingerprint(clone) == before, 'reference probes mutated frozen clone: STOP')
    selected = call('preview_select', clone.select)
    need(type(selected) is tuple and len(selected) == 3, 'native full preview tuple')
    preview = dict(concept=selected[0], question=selected[1], difficulty=float(selected[2]))
    ready = sorted(call('direct_ready_set', policy.ready_set))
    scores = {cid:float(call('direct_mastery_score', policy.mastery_score, cid)) for cid in nodes}
    need(all(math.isfinite(v) and 0 <= v <= 1 for v in scores.values()), 'finite native S28')
    mastered = sorted(cid for cid, state in zip(nodes, states) if state[4])
    need(fingerprint(policy) == before, 'readouts or preview mutated original policy: STOP')
    mean = sum(v['probability'] for v in values)/3
    return dict(probability=p, mastery=scores, ready=ready, mastered=mastered, action=preview['concept']), dict(
        native_state=states, raw_references=values, raw_reference_mean=mean,
        raw_reference_criterion=mean >= TAU_RAW, full_preview=preview, frozen_state_sha256=before)


def admit(actual, preview, legacy, side):
    need(exact(actual, {n:legacy[n] for n in actual}), 'legacy P/S28/M/R/CID mismatch: STOP')
    need(exact(preview, side['preview']), 'legacy full preview tuple mismatch: STOP')


def advance(policy, query, timestamp, y, probability, chapter_map, call):
    need(type(y) is int and y in (0, 1), 'cached binary outcome only after capture/admission')
    call('update', policy.update, query['concept'], query['question'], query['difficulty'], timestamp, y, probability)
    policy.selection_counts[query['concept']] += 1
    policy.question_counts[query['question']] += 1
    policy.recent_concepts.append(query['concept'])
    policy.current_chapter = chapter_map[query['concept']]


def joint_cells(left, right):
    need(len(left) == len(right), 'paired native concept states')
    counts = Counter()
    for a, b in zip(left, right):
        need(len(a) == len(b) == 5, 'theta/pi/predicates state vector')
        counts[''.join(str(int(a[i] != b[i])) for i in (2, 3, 4))] += 1
    return {f'{i:03b}':counts[f'{i:03b}'] for i in range(8)}


def read_gzip(raw, check, limit):
    result = {}
    size = 0
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        while True:
            check()
            line = stream.readline(65537)
            if not line:
                break
            size += len(line)
            need(line.endswith(b'\n') and len(line) <= 65536 and size <= limit and len(result) < 3240,
                 'bounded complete gzip records')
            row = json.loads(line)
            key = row['variant'], row['learner_id'], row['event_id']
            need(key not in result, 'duplicate raw event key')
            result[key] = row
    need(len(result) == 3240, 'all3240 cached rows/CRC, no dropping')
    return result


def windows_metadata_command(executable, command, expected, *, phase, calls):
    """Literal native cmd /c ver whitelist; same semantics as established worker."""
    need(phase is True, 'metadata Popen outside bootstrap phase')
    need(type(calls) is int and 0 <= calls < 3, 'metadata helper count cap')
    need(type(executable) is str and type(command) is str, 'metadata command strings')
    fixed = os.path.normcase(os.path.abspath(expected))
    need(os.path.normcase(os.path.abspath(executable)) == fixed, 'metadata executable not system cmd')
    actual = command.strip().casefold()
    allowed = {fixed.casefold()+' /c "ver"', '"'+fixed.casefold()+'" /c "ver"'}
    need(actual in allowed and actual.endswith('/c "ver"'), 'metadata literal ver only')
    return dict(executable=executable, command=command)


def metadata_audit(receipt, active, expected, check):
    def audit(event, args):
        if event == 'subprocess.Popen':
            if not active[0]:
                receipt['outside_phase_popen_attempts'] += 1
                raise RuntimeError('Popen after metadata phase forbidden')
            try:
                check()
                item = windows_metadata_command(args[0],args[1],expected,phase=active[0],calls=receipt['helper_calls'])
            except BaseException:
                receipt['blocked_bootstrap_attempts'] += 1
                raise
            receipt['helper_calls'] += 1
            receipt['commands'].append(item)
        elif event.startswith('socket.'):
            if active[0] and event == 'socket.gethostname':
                check()
                receipt['local_gethostname_calls'] += 1
                need(receipt['local_gethostname_calls'] <= 3, 'bounded local metadata hostname calls')
                return  # Local OS discovery only; its value is never persisted.
            receipt['outside_phase_socket_attempts' if not active[0] else 'blocked_bootstrap_attempts'] += 1
            raise RuntimeError('socket/network outside exact local metadata discovery forbidden')
    return audit


def require_metadata_closed(receipt):
    need(receipt['phase_closed'] is True and type(receipt['helper_calls']) is int and 0 <= receipt['helper_calls'] <= 3
         and type(receipt['local_gethostname_calls']) is int and 0 <= receipt['local_gethostname_calls'] <= 3,
         'honest bounded metadata receipt/closed phase')
    need(all(type(receipt[n]) is int and receipt[n] == 0 for n in
         ('outside_phase_popen_attempts','outside_phase_socket_attempts','blocked_bootstrap_attempts')),
         'late/caught metadata or network attempt: STOP')


def native_windows_metadata(check, receipt):
    """Real uname+processor cache warmup in owned Job; no fake OS or hostname export."""
    check()
    need(sys.platform == 'win32' and type(os.environ.get('SystemRoot')) is str, 'actual Windows SystemRoot')
    expected = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(expected.is_absolute() and expected.is_file() and not expected.is_symlink()
         and not getattr(expected,'is_junction',lambda:False)(), 'actual native system cmd')
    receipt.update(public_apis=['platform.uname','platform.processor'],phase='REAL_WINDOWS_METADATA_BEFORE_IMPORT_AUDIT',
        helper_calls=0,local_gethostname_calls=0,commands=[],outside_phase_popen_attempts=0,
        outside_phase_socket_attempts=0,blocked_bootstrap_attempts=0,phase_closed=False,
        allowed_executable=str(expected),hostname_persisted=False)
    active = [True]; started = time.perf_counter()
    sys.addaudithook(metadata_audit(receipt,active,str(expected),check))
    try:
        check(); value = platform.uname(); check()
        processor = platform.processor(); check()
        fields = {key:getattr(value,key) for key in ('system','release','version','machine')}
        need(fields['system'] == 'Windows' and all(type(v) is str and 0 < len(v) <= 256 for v in fields.values()), 'real OS fields')
        need(type(processor) is str and len(processor) <= 4096, 'bounded real processor metadata')
        receipt.update(fields=fields,uname_cache_identity_reused=platform.uname() is value,
            processor_repeat_equal=platform.processor() == processor,processor_present=bool(processor),
            processor_sha256=hashlib.sha256(processor.encode()).hexdigest())
    finally:
        active[0] = False; receipt['phase_closed'] = True
        receipt['seconds'] = time.perf_counter()-started
        check()  # Same worker deadline, no new bootstrap allowance.
    require_metadata_closed(receipt)
    need(receipt['uname_cache_identity_reused'] is True and receipt['processor_repeat_equal'] is True, 'actual warmed metadata reuse')

def main():
    started, wall = time.perf_counter(), time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--remaining-seconds', type=float, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()  # Mandatory before NumPy/Pandas/native imports.
    need(owner['status'] == 'OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE'
         and owner['worker']['pid'] == os.getpid(), 'owned pre-native gate')
    need(Path(sys.prefix).resolve() == ROOT/'.venv' and os.environ.get('CUDA_VISIBLE_DEVICES') == '', '.venv CPU-only env')
    plan_path = PREP/'prediction_mastery_trace_plan02.json'
    need(hashlib.sha256(plan_path.read_bytes()).hexdigest() == args.plan_sha256, 'exact plan bytes')
    plan = json.loads(plan_path.read_bytes())
    need(type(args.remaining_seconds) is float and math.isfinite(args.remaining_seconds)
         and 0 < args.remaining_seconds <= 55, 'bounded worker remaining allocation')
    out = PREP/plan['output_name']
    need(out.parent == PREP and out.is_dir(), 'outer owns exclusive attempt directory')
    expected = {**plan['inputs_sha256'], **plan['source_sha256'], plan_path.relative_to(ROOT).as_posix():args.plan_sha256}
    errors = []; memory = []; os_metadata = {}; direct = Counter(); returned = Counter(); native = Counter(); native_returns = Counter()
    complete = []; nodes = []; event_count = 0; profiled = False; active = None; prior_profile = sys.getprofile()
    need(prior_profile is None, 'STOP existing profiler; never replace')
    def elapsed(): return max(time.perf_counter()-started, time.time()-wall)
    def check():
        if elapsed() >= args.remaining_seconds:
            raise TimeoutError('worker allocation exhausted; no retry')
    def bounded(path, cap=4*1024**2):
        check(); path = path.absolute(); need(path.is_relative_to(ROOT), 'workspace read')
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda:False)(), 'physical source/input/output')
        need(path.resolve() == path and path.is_file() and path.stat().st_size <= cap, 'bounded regular file')
        with path.open('rb') as stream: raw = stream.read(cap+1)
        need(len(raw) <= cap and len(raw) == path.stat().st_size, 'stable bounded payload'); check(); return raw
    def sha(path): return hashlib.sha256(bounded(path)).hexdigest()
    def write(name, value):
        check()
        with (out/name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
    def audit(event, values):
        if event == 'subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            raise RuntimeError('no child/network during trace')
        if event == 'import' and str(values[0]).split('.')[0] in {'torch','sklearn','scipy'}:
            raise RuntimeError('no NN/solver import')
        if event == 'open' and isinstance(values[0], (str, bytes)):
            name = str(values[0]).replace('\\','/').lower()
            if any(p in name for p in ('/dataset/','/artifacts/simulator/corpora/','/oracle/','/realdata/','/holdout/')):
                raise RuntimeError('no corpus/oracle/realdata/Holdout access')
    try:
        need(all(sha(ROOT/n) == h for n, h in expected.items()), 'all source/input prehash')
        need(not any(n in sys.modules for n in ('numpy','pandas','torch','knowledge_tracing')), 'fresh pre-native process')
        sys.path.insert(0, str(ROOT/'src'))
        from knowledge_tracing.akt.resources import memory_snapshot
        def guard(stage):
            check(); s = memory_snapshot(); check()
            need(type(s['process_rss_bytes']) is int and type(s['system_available_ram_bytes']) is int, 'known RAM')
            peak = s['process_peak_rss_bytes']
            need(peak is None or type(peak) is int, 'known or unavailable peak RSS')
            need(max(s['process_rss_bytes'], peak or 0) <= plan['max_rss_bytes'], 'RSS/peak ceiling')
            need(s['system_available_ram_bytes'] >= plan['min_free_ram_bytes'], 'free RAM floor')
            memory.append(dict(stage=stage, elapsed_seconds=elapsed(), **s))
            files = [p for p in out.iterdir() if p.is_file()]
            need(len(files) <= 32 and all(p.stat().st_size <= plan['max_output_file_bytes'] for p in files)
                 and sum(p.stat().st_size for p in files) <= plan['max_total_output_bytes'], 'cooperative output cap')
        guard('before_native_import')
        native_windows_metadata(check,os_metadata)
        sys.addaudithook(audit)  # No postmetadata network/Popen relaxation.
        import numpy as np
        import pandas as pd
        from knowledge_tracing.paper2_reference import load_reference
        guard('after_native_import')
        raw = {n:bounded(ROOT/n) for n in plan['inputs_sha256']}
        base = plan['cached_bundle']+'/'
        manifest = json.loads(raw[base+'manifest.json'])
        for name in ('observed_legacy.jsonl.gz','observed_query_sidecar.jsonl.gz','parity.json','historical_runner.py','source__paper2_reference.py'):
            need(manifest['outputs_sha256'][name] == plan['inputs_sha256'][base+name], 'immutable manifest binding')
        legacy = read_gzip(raw[base+'observed_legacy.jsonl.gz'], check, 16*1024**2)
        side = read_gzip(raw[base+'observed_query_sidecar.jsonl.gz'], check, 8*1024**2)
        keys = {(v, f'{s}-{p}', str(t)) for v in ('graph_free', *VARIANTS) for s in SEEDS for p in PROFILES for t in range(120)}
        need(set(legacy) == set(side) == keys, 'full3240 keys, no subset')
        for key in keys:
            a, b = legacy[key], side[key]
            need(b['legacy_row_sha256'] == digest(a) and b['update_pairing_verified'] is True
                 and b['query_capture_phase'] == 'before_delegate_predict' and b['preview_is_served'] is False
                 and b['preview_capture_phase'] == 'after_native_preview_select'
                 and exact(a['probability'], b['probability']) and exact(a['correct'], b['correct']), 'C13 query/label pairing')
        for s in SEEDS:
            for p in PROFILES:
                for t in range(120):
                    a,b = (side[(v,f'{s}-{p}',str(t))] for v in VARIANTS)
                    need(exact(a['query'],b['query']) and exact(a['correct'],b['correct']), '1080 exact same query/y')
        parity = json.loads(raw[base+'parity.json'])
        need(parity['status'] == 'PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY' and parity['new_independent_N'] == 0, 'C13 admission')
        full = load_reference(); empty = load_reference(estimator_edges=[])
        references = {'graph_package':full, 'empty_graph_package':empty}
        expected_provenance = json.loads(raw[plan['historical_provenance']])
        need(exact(full['provenance'], expected_provenance) and exact(empty['provenance'], expected_provenance), 'native source registry exact')
        nodes = full['estimator']['nodes']; need(len(nodes) == len(set(nodes)) == 28, '28 node order')
        def state_data(v):
            if isinstance(v, np.ndarray): return dict(array_shape=list(v.shape),dtype=str(v.dtype),bytes_sha256=hashlib.sha256(v.tobytes()).hexdigest())
            if isinstance(v, np.generic): return state_data(v.item())
            if isinstance(v, pd.Timestamp): return dict(timestamp_iso=v.isoformat(),timestamp_ns=int(v.value))
            if isinstance(v, float): return {'float_hex':v.hex()}
            if isinstance(v, dict): return {str(k):state_data(x) for k,x in v.items()}
            if isinstance(v, deque): return dict(deque_maxlen=v.maxlen,items=[state_data(x) for x in v])
            if isinstance(v, (list,tuple)): return [state_data(x) for x in v]
            if is_dataclass(v): return state_data(vars(v))
            if v is None or type(v) in (str,int,bool): return v
            raise TypeError('unknown native state field '+str(type(v)))
        fingerprint = lambda policy:digest(state_data(vars(policy)))
        codes = {}; forbidden = set()
        for ref in references.values():
            cls = ref['estimator']['GAMKTPolicy']
            for name in ('predict','update','mastery_score','is_mastered','select','ready_set'):
                codes[getattr(cls,name).__code__] = name
            env = ref['environment']
            forbidden.update((env['persona_base_abilities'].__code__,env['LatentStudentEnvironment'].__init__.__code__,env['LatentStudentEnvironment'].interact.__code__))
        def profile(frame, event, arg):
            if event in ('call','return'):
                code = frame.f_code
                if code in forbidden: raise RuntimeError('teacher/persona/RNG world path forbidden')
                name = codes.get(code)
                if name:
                    (native if event == 'call' else native_returns)[name] += 1
                    if event == 'call' and native[name] > plan['native_call_caps'][name]:
                        raise RuntimeError('native all-calls cap '+name)
                if event == 'call' and str(frame.f_globals.get('__name__','')).startswith(('numpy.random','random')):
                    raise RuntimeError('RNG function forbidden after loader')
            elif event == 'c_call':
                module = str(getattr(arg,'__module__',''))
                if module.startswith(('numpy.random','_random')): raise RuntimeError('RNG C function forbidden')
        def call(kind, method, *args):
            check(); need(direct[kind] < plan['direct_call_caps'][kind], 'direct cap '+kind)
            direct[kind] += 1; value = method(*args); returned[kind] += 1; check(); return value
        guard('before_native_work')
        write('reservation.json', dict(status='ALL2160_UPDATES_6480_PREDICT_RESERVED_BEFORE_NATIVE_WORK',
            direct_reservations=plan['direct_call_caps'], native_caps=plan['native_call_caps'],
            hardkill_actual_counts='UNKNOWN_LE_RESERVED; no reset/retry', new_independent_N=0))
        sys.setprofile(profile); profiled = True
        with gzip.open(out/'trace.jsonl.gz','xt',encoding='utf-8') as stream:
            for seed in SEEDS:
                for persona in PROFILES:
                    header = next(h for h in parity['observed']['policy_headers'] if h['seed'] == seed and h['profile'] == persona)
                    stored = next(h for h in parity['observed']['profile_state_rng_fingerprints'] if h['seed'] == seed and h['profile'] == persona)
                    for variant in VARIANTS:
                        active = f'{seed}-{persona}:{variant}'; guard('before_trajectory:'+active)
                        scope = references[variant]['estimator']
                        need(list(scope['nodes']) == nodes, 'same node order')
                        policy = call('constructor', scope['GAMKTPolicy'], True)
                        initial = fingerprint(policy)
                        need(initial == header['initial_policy_state_sha256'][variant] == stored['initial_policy_sha256'][variant], 'initial C13 fingerprint')
                        for t in range(120):
                            key = variant, f'{seed}-{persona}', str(t)
                            old, cached = legacy[key], side[key]; q = cached['query']
                            timestamp = pd.Timestamp(q['timestamp_iso'])
                            need(int(timestamp.value) == q['timestamp_ns'], 'exact native timestamp')
                            frame = scope['questions_by_concept'][q['concept']]
                            refs = reference_items([(r.question_id,r.elo_difficulty) for r in frame.itertuples(index=False)], q['concept'], q)
                            actual, added = capture(policy,q,nodes,refs,timestamp,call,fingerprint)
                            admit(actual,added['full_preview'],old,cached)
                            row = dict(seed=seed,profile=persona,event_id=str(t),variant=variant,query=q,
                                phase='PRE_CURRENT_UPDATE_NO_LABEL_IN_CAPTURE',probability=actual['probability'],legacy_row_sha256=digest(old),**added)
                            text = canonical(row)+'\n'
                            need(len(text.encode()) <= 32768, 'trace row bound')
                            stream.write(text); event_count += 1
                            need(event_count <= 2160, 'trace population cap')
                            advance(policy,q,timestamp,old['correct'],actual['probability'],scope['chapter_map'],call)
                            if t % 10 == 9: guard('events:'+active+':'+str(t))
                        final = fingerprint(policy)
                        need(final == stored['final_policy_sha256'][variant], 'final C13 policy fingerprint')
                        need(sum(s.attempts for s in policy.states.values()) == 120, '120 updates/native states')
                        complete.append(dict(seed=seed,profile=persona,variant=variant,initial_sha256=initial,final_sha256=final,
                            exact_legacy_rows=120,full_preview_exact=120,cumulative_direct_attempts=dict(direct),
                            cumulative_native_attempts=dict(native),elapsed_seconds=elapsed()))
                        stream.flush()
                        write('trajectory-'+str(len(complete))+'.json', complete[-1])
        sys.setprofile(prior_profile); profiled = False
        need(event_count == 2160 and len(complete) == 18 and direct == returned == Counter(plan['direct_call_caps']), 'exact completed direct ledger')
        need(native == native_returns and native['predict'] == 6480 and native['update'] == 2160
             and native['select'] == 2160 and native['mastery_score'] >= 60480, 'actual native ledger/returns')
        need(all(sha(ROOT/n) == h for n,h in expected.items()), 'all source/input posthash')
        require_metadata_closed(os_metadata)
        guard('final_before_receipt')
    except BaseException as exc:
        errors.append(dict(type=type(exc).__name__,message=str(exc),active=active))
        with (out/'failure.log').open('x',encoding='utf-8') as stream: traceback.print_exc(file=stream)
    finally:
        if profiled: sys.setprofile(prior_profile)
    after = {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in expected}
    if after != expected: errors.append(dict(type='SourceDrift',message='after != before'))
    if elapsed() >= args.remaining_seconds: errors.append(dict(type='WorkerBudget',message='postelapsed bound'))
    if not errors:
        try: require_metadata_closed(os_metadata)
        except BaseException as exc: errors.append(dict(type=type(exc).__name__,message=str(exc)))
    files = [p for p in out.iterdir() if p.is_file() and p.name != 'dispatch.json']
    outputs = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    result = dict(status='INNER_ALL2160_LEGACY_AND18_FINAL_FINGERPRINTS_EXACT_PENDING_ROOT' if not errors else 'REJECTED_RETAIN_NO_PARTIAL_INTERPRETATION',
        errors=errors,plan_sha256=args.plan_sha256,source_input_before=expected,source_input_after=after,
        elapsed_before_receipt_seconds=elapsed(),worker_allowance_seconds=args.remaining_seconds,
        node_order=list(nodes),completed_trajectories=complete,legacy_rows_exact=event_count if not errors else None,
        direct_attempts=dict(direct),direct_returns=dict(returned),native_attempts=dict(native),native_returns=dict(native_returns),
        native_windows_metadata=os_metadata,memory_samples=memory,owned_gate=owner,profiler_restored=sys.getprofile() is prior_profile,
        outputs_sha256=outputs,new_independent_N=0,teacher_calls=0,optimizer_steps=0,
        scope='raw reference diagnostic, not calibration/causal teaching/independent replication; online_updates2160 explicit')
    with (out/'worker_run.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    if elapsed() >= args.remaining_seconds:
        with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(status='REJECTED_POSTWRITE_BUDGET',elapsed_seconds=elapsed()),stream)
        errors.append(dict(type='PostwriteBudget'))
    print(canonical(dict(status=result['status'] if not errors else 'REJECTED_RETAIN_NO_PARTIAL_INTERPRETATION',elapsed_seconds=elapsed(),errors=errors)))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()



