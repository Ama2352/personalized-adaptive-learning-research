"""Operation mới full CPU09, source-only tới khi ROOT review/dispatch.

Dùng nguyên matched_replay rồi freeze pretruth trước attach_truth_and_group.
Không world/teacher/RNG/NN/optimizer mới; không tiếp tục lane5failure cũ.
"""
import argparse
from collections import Counter, deque
from dataclasses import is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import types

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONTRACT = PREP / 'rq1_cpu09_targeted_full_contract01.json'
METHOD_CAPS = {'__init__': 1, 'select': 120, 'predict': 120, 'update': 120, '_decayed_pi': 360}
DIRECT = dict(estimator_constructors=120, select=14400, predict=14400, native_capture=14400, update=14400)
METHOD_TOTAL = {'__init__': 120, 'select': 14400, 'predict': 14400, 'update': 14400, '_decayed_pi': 43200}
READOUT_COLUMNS = ('seed', 'profile', 'graph_on', 'mechanism_on', 'step', 'concept', 'question',
    'difficulty', 'timestamp', 'source_clock_hours', 'prediction', 'theta_est', 'pi_task_stored',
    'pi_time_stored', 'pi_task_decayed', 'pi_time_decayed', 'native_M', 'theta_gate', 'stored_pi_gate')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def load(name, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def main():
    import time
    started, wall = time.perf_counter(), time.time()
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    need(Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT / '.venv'
         and os.environ.get('CUDA_VISIBLE_DEVICES') == '' and sys.getprofile() is None, 'owned CPU/no existing profiler')

    def elapsed():
        return max(time.perf_counter() - started, time.time() - wall)

    def check():
        need(math.isfinite(elapsed()) and elapsed() < 270, 'single worker270 allocation')

    def sha(path, cap=4 * 1024**2):
        check()
        need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical root-bound path')
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no aliases')
        need(path.is_file() and path.stat().st_size <= cap, 'bounded regular file')
        digest, size = hashlib.sha256(), 0
        with path.open('rb') as stream:
            while block := stream.read(65536):
                check()
                size += len(block)
                need(size <= cap, 'stream byte cap')
                digest.update(block)
        need(size == path.stat().st_size, 'stable file size')
        return digest.hexdigest()

    need(sha(Path(__file__).resolve()) == args.source_sha256 and sha(CONTRACT) == args.contract_sha256, 'external source/contract pins')
    contract = json.loads(CONTRACT.read_bytes())
    need(contract['worker_sha256'] == args.source_sha256 and contract['direct_call_caps'] == DIRECT
         and contract['native_method_total'] == METHOD_TOTAL, 'fixed full operation contract')
    output_relative = 'experiments/gam_kt/results/rq1-cpu09-native-mastery-20261109-01'
    need(contract['output_relative'] == output_relative, 'fixed scientific output role/path')
    out = ROOT / output_relative
    need(out.parent.is_dir() and out.resolve() == out and not out.exists(), 'exclusive scientific run output')
    cursor = ROOT
    for part in out.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no output aliases')
    out.mkdir()
    phase, errors, restoration_errors, denied = 'source_preflight', [], [], []
    deny_contexts, audit_denial_count = [], 0
    memory, compiled, policies = [], [], []
    before, after, os_metadata = {}, {}, {}
    guards, observer, active_policy, active_key = [], None, None, None
    factory_attempted = factory_returned = 0
    method_started, method_returned = Counter(), Counter()
    metadata = None
    pretruth_frozen = truth_join_started = truth_join_completed = False
    output_bytes = 0

    def write(name, value):
        nonlocal output_bytes
        if name != 'failure.json':
            check()
        raw = encode(value) + b'\n'
        need(len(raw) <= 1024**2 and output_bytes + len(raw) <= 16 * 1024**2, 'metadata1MiB / total16MiB')
        with (out / name).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        output_bytes += len(raw)
        actual = hashlib.sha256((out / name).read_bytes()).hexdigest() if name == 'failure.json' else sha(out / name)
        need(actual == hashlib.sha256(raw).hexdigest(), 'actual metadata readback SHA')

    def write_rows(name, rows, cap, expected_count):
        nonlocal output_bytes
        count, size, digest = 0, 0, hashlib.sha256()
        with (out / name).open('xb') as stream:
            for row in rows:
                check()
                raw = encode(row) + b'\n'
                size += len(raw)
                count += 1
                need(len(raw) <= 8192 and count <= expected_count and size <= cap
                     and output_bytes + size <= 16 * 1024**2, 'bounded complete JSONL / total16MiB')
                stream.write(raw)
                digest.update(raw)
            stream.flush()
            os.fsync(stream.fileno())
        output_bytes += size
        need(count == expected_count and sha(out / name, cap) == digest.hexdigest(), 'actual JSONL count/readback SHA')
        return dict(path=name, rows=count, bytes=size, sha256=digest.hexdigest())

    def verify():
        value = {}
        for name, record in contract['bindings'].items():
            path = ROOT / name
            need(path.stat().st_size == record['bytes'] and sha(path) == record['sha256'], 'source/input byte identity')
            value[name] = record['sha256']
        need(not before or value == before, 'source/input before=after')
        return value

    try:
        before = verify()
        pilot = load('reviewed_targeted_helpers03', PREP / 'pilot_rq1_cpu09_targeted_observer03.py')
        write('pure_checks.json', pilot.pure_checks())
        accepted_pilot = json.loads((PREP / 'cpu09-targeted-observer-native03-outer/final.json').read_bytes())
        need(accepted_pilot['status'] == 'ACCEPTED_ONE_HISTORY_TARGETED_OBSERVER_OPERATIONAL_PILOT'
             and accepted_pilot['errors'] == [] and accepted_pilot['receipt']['cleanup_accepted'] is True
             and accepted_pilot['receipt']['accepted'] is True and accepted_pilot['receipt']['job_active_after_cleanup'] == 0,
             'actual03 pilot admission, not permission inferred from source')
        for name in ('result.json', 'off.json', 'on.json'):
            expected = accepted_pilot['outputs'][name]
            path = PREP / 'cpu09-targeted-observer-native03' / name
            need(sha(path) == expected['sha256'] and path.stat().st_size == expected['bytes'], 'actual03 unchanged evidence')
        compiler = load('reviewed_real_project_source_compiler', PREP / 'worker_rq1_cpu09_native_mastery04.py')
        old = json.loads((PREP / 'rq1_cpu09_native_mastery_contract04.json').read_bytes())
        replay = load('genuine_cpu09_replay', PREP / 'replay_rq1_cpu09_native_mastery01.py')
        cache = load('genuine_cpu09_cache_validator', PREP / 'analyze_rq2_cached_mechanism01.py')
        base = cache.decode((PREP / 'rq2_cache_mechanism_contract01.json').read_bytes())
        cache_admission = cache.decode((PREP / 'rq2-cached-mechanism-native02-outer/final.json').read_bytes())
        need(cache_admission['status'] == 'ACCEPTED_CACHED_RQ2_SECONDARY_ANALYSIS' and cache_admission['errors'] == []
             and cache_admission['inputs_before'] == cache_admission['inputs_after']
             == {name: row['sha256'] for name, row in base['inputs'].items()}, 'original cache lineage')

        def project(name):
            relative = 'src/' + name.replace('.', '/')
            relative += '/__init__.py' if name in ('knowledge_tracing', 'knowledge_tracing.akt', 'knowledge_tracing.gam_kt') else '.py'
            need(relative in contract['bindings'], 'source compiler exact allowlist')
            return compiler.load_pinned_project_source(name, old['source_pins'][relative], compiled)

        project('knowledge_tracing')
        project('knowledge_tracing.akt')
        snapshot = project('knowledge_tracing.akt.resources').memory_snapshot
        guard_calls = 0

        def guard(force=False):
            nonlocal guard_calls
            check()
            guard_calls += 1
            if force or guard_calls % 64 == 0:
                sample = snapshot()
                need(type(sample['process_rss_bytes']) is int and type(sample['system_available_ram_bytes']) is int,
                     'actual RAM known')
                need(max(sample['process_rss_bytes'], sample['process_peak_rss_bytes'] or 0) <= 1024**3
                     and sample['system_available_ram_bytes'] >= 2 * 1024**3, 'worker RSS1GiB/free2GiB')
                memory.append(dict(phase=phase, seconds=elapsed(), **sample))
                need(len(memory) <= 1200, 'bounded worker resource metadata')

        guard(True)
        metadata = load('genuine_windows_metadata_phase', PREP / 'prediction_mastery_trace_worker03.py')
        metadata.native_windows_metadata(check, os_metadata)
        write('native_metadata.json', os_metadata)
        allowed = {os.path.normcase(str((ROOT / name).resolve())) for name in contract['bindings']}
        need(sha(CONTRACT) == args.contract_sha256, 'exact external self-contract pin before read entitlement')
        allowed.add(os.path.normcase(str(CONTRACT.resolve())))
        runtime_roots = tuple({Path(sys.prefix), Path(sys.base_prefix)})
        output_names = {'pure_checks.json', 'native_metadata.json', 'reservation.json', 'pretruth_readouts.jsonl',
                        'parity.json', 'policy_observers.json', 'truth_sidecar.jsonl', 'groups.json', 'result.json', 'failure.json'}

        def audit(event, values):
            def deny(message):
                nonlocal audit_denial_count
                audit_denial_count += 1
                if len(deny_contexts) < 8:
                    record = pilot.denial_context(event, values, phase)
                    record['message'] = message
                    deny_contexts.append(record)
                denied.append(message)
                raise RuntimeError(message)
            if event == 'subprocess.Popen' or event.startswith('socket.') or event in ('os.system', 'os.posix_spawn', 'os.spawn'):
                deny('no process/network after metadata')
            if event == 'import' and str(values[0]).split('.')[0] in ('torch', 'scipy', 'sklearn', 'networkx'):
                deny('no NN/solver import')
            if event == 'open' and values and not isinstance(values[0], int):
                path = Path(values[0]).absolute()
                mode, flags = values[1] or '', values[2] if type(values[2]) is int else 0
                writing = any(c in mode for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR))
                if writing:
                    if path.parent != out or path.name not in output_names:
                        deny('write outside exact new outputs')
                else:
                    resolved = path.resolve()
                    runtime = path.suffix.lower() in ('.py', '.pyc', '.pyd', '.dll') and any(resolved.is_relative_to(p.resolve()) for p in runtime_roots)
                    if os.path.normcase(str(resolved)) not in allowed and not runtime and not (path.parent == out and path.name in output_names):
                        deny('read outside exact pinned input/runtime')
            if event in ('os.remove', 'os.rename', 'os.rmdir', 'os.link', 'os.symlink', 'os.mkdir'):
                deny('no historical filesystem mutation')

        sys.addaudithook(audit)
        phase = 'native_import_and_cache_validation'
        need(not any(name in sys.modules for name in ('numpy', 'pandas', 'torch')), 'cold native import')
        import numpy as np
        import pandas as pd
        project('knowledge_tracing.gam_kt')
        reference = project('knowledge_tracing.paper2_reference').load_reference()
        build = project('knowledge_tracing.gam_kt.simulator_pathways').build_pathway_policy
        need(reference['provenance'] == cache.decode((ROOT / base['paths']['provenance']).read_bytes())
             and reference['estimator']['MASTERY_ELO'] == replay.MASTERY_ELO == 1250., 'genuine source registry / threshold')
        cache.validate_manifest(cache.decode((ROOT / base['paths']['manifest']).read_bytes()), base)
        questions, roots = cache.topology({name: (ROOT / base['paths'][name]).read_bytes() for name in ('nodes', 'edges', 'questions')})
        rows = cache.trace_rows(ROOT / base['paths']['traces'], max_compressed=1024**2,
            max_uncompressed=8 * 1024**2, max_line=8192, max_rows=14400, guard=guard)
        buckets = cache.validate_trace(rows, seeds=base['grid']['seeds'], profiles=base['grid']['profiles'],
                                       steps=120, questions=questions, roots=roots)
        histories = replay.observable_histories(buckets, seeds=base['grid']['seeds'], profiles=base['grid']['profiles'], steps=120)
        public = types.MappingProxyType({key: pilot.public_stream(histories, key, replay.OBSERVABLE_FIELDS) for key in histories})
        del histories
        keys = [(s, p, g, m) for s in base['grid']['seeds'] for p in base['grid']['profiles']
                for g in (False, True) for m in (False, True)]
        need(len(keys) == len(buckets) == len(public) == 120 and sum(map(len, public.values())) == 14400
             and base['grid']['seeds'] == list(range(21000, 21010)) and base['grid']['profiles'] == ['PG', 'PY', 'PYH'], 'full fixed grid before model')

        def state_data(value):
            if isinstance(value, np.ndarray):
                return dict(shape=list(value.shape), dtype=str(value.dtype), sha256=hashlib.sha256(value.tobytes()).hexdigest())
            if isinstance(value, np.generic):
                return state_data(value.item())
            if type(value) is float:
                return dict(float_hex=value.hex())
            if isinstance(value, dict):
                return {str(k): state_data(v) for k, v in value.items()}
            if isinstance(value, (tuple, list)):
                return [state_data(v) for v in value]
            need(value is None or type(value) in (str, int, bool), 'RNG snapshot schema')
            return value

        def deny_known(*args, **kwargs):
            denied.append('known world/persona/RNG route attempted')
            raise RuntimeError(denied[-1])

        def replace(obj, name):
            local = vars(obj)
            guards.append((obj, name, name in local, local.get(name)))
            setattr(obj, name, deny_known)

        for scope in (reference[name] for name in ('environment', 'controller', 'estimator')):
            for name in ('__init__', 'interact'):
                replace(scope['LatentStudentEnvironment'], name)
            guards.append((scope, 'persona_base_abilities', True, scope['persona_base_abilities']))
            scope['persona_base_abilities'] = deny_known
        for module, names in ((random, ('random', 'seed', 'randrange', 'randint', 'choice', 'choices', 'shuffle', 'sample', 'uniform', 'gauss', 'getrandbits')),
                              (np.random, ('default_rng', 'seed', 'random', 'random_sample', 'rand', 'randn', 'randint', 'choice', 'shuffle', 'permutation', 'uniform', 'normal'))):
            for name in names:
                replace(module, name)
        rng_before = hashlib.sha256(encode(state_data(dict(python=random.getstate(), numpy=np.random.get_state())))).hexdigest()
        write('reservation.json', dict(status='RESERVED_ALL120_POLICIES_BEFORE_ANY_FACTORY', direct_caps=DIRECT,
            method_totals=METHOD_TOTAL, methods_per_policy=METHOD_CAPS, hardkill_counts='UNKNOWN_LE_RESERVED_UNTIL_TERMINAL',
            new_operation_not_old_lane_resume=True, source_before=before))

        def finish_policy():
            nonlocal observer, active_policy, active_key
            if observer is None:
                return
            observer.restore()
            restoration_errors.extend(observer.cleanup_errors)
            need(not observer.cleanup_errors and not observer.installed and observer.originals_match(), 'full class restoration between policies')
            need(observer.started == observer.returned == Counter(METHOD_CAPS) and not observer.raised
                 and sum(state.attempts for state in active_policy.states.values()) == 120,
                 'each genuine policy completed120updates/exact observed original bodies')
            method_started.update(observer.started)
            method_returned.update(observer.returned)
            policies.append(dict(key=active_key, completed_updates=120, observer=observer.receipt()))
            observer = active_policy = active_key = None

        def factory(*, graph_on):
            nonlocal observer, active_policy, active_key, factory_attempted, factory_returned
            guard()
            finish_policy()
            need(factory_attempted < 120, 'factory reservation before construction')
            active_key = keys[factory_attempted]
            need(type(graph_on) is bool and graph_on == active_key[2], 'genuine matcher factory ordering')
            factory_attempted += 1
            observer = pilot.TargetedObserver(reference['estimator']['GAMKTPolicy'], METHOD_CAPS)
            observer.install()
            active_policy = build(reference, signal=graph_on, parent_adaptation=graph_on, local_adaptation=False)
            factory_returned += 1
            return active_policy

        phase = 'full_matched_replay_before_truth'
        guard(True)
        start = pd.Timestamp('2026-01-01', tz='UTC')
        readouts, parity = replay.matched_replay(public, seeds=base['grid']['seeds'], profiles=base['grid']['profiles'],
            steps=120, questions=questions, policy_factory=factory,
            timestamp_factory=lambda hours: start + pd.Timedelta(hours=hours), guard=guard)
        finish_policy()  # Last original methods restored before any truth join.
        need(factory_attempted == factory_returned == len(policies) == 120 and len(readouts) == 14400
             and parity['calls'] == DIRECT and method_started == method_returned == Counter(METHOD_TOTAL), 'all full native bodies/parity complete')
        need(rng_before == hashlib.sha256(encode(state_data(dict(python=random.getstate(), numpy=np.random.get_state())))).hexdigest(), 'legacy RNG states unchanged')
        verify()
        need(sha(CONTRACT) == args.contract_sha256 and not denied and not restoration_errors and sys.getprofile() is None,
             'genuine pretruth source/guard/restoration admission')
        need(all(set(row) == set(READOUT_COLUMNS) for row in readouts), 'lossless full genuine readout schema')
        frozen = write_rows('pretruth_readouts.jsonl', ([row[name] for name in READOUT_COLUMNS] for row in readouts), 8 * 1024**2, 14400)
        write('policy_observers.json', dict(policies=policies, method_started=dict(method_started), method_returned=dict(method_returned)))
        write('parity.json', dict(genuine_parity=parity, pretruth_readouts=frozen, readout_columns=READOUT_COLUMNS,
            readout_encoding='LOSSLESS_JSONL_ARRAYS_ALL19_GENUINE_FIELDS', all_classes_restored=True,
            source_checked_before_truth=True, clock='SOURCE_DERIVED_UTC_2026_01_01_PLUS6H_OR72H_AT_POSITIVE_STEP_DIVISIBLE28',
            temporal_fields_not_claimed_logged=True))
        verify()
        need(sha(out / 'pretruth_readouts.jsonl', 8 * 1024**2) == frozen['sha256']
             and sha(CONTRACT) == args.contract_sha256, 'frozen bytes/source rechecked immediately before truth')
        pretruth_frozen = True
        phase = 'post_full_parity_truth_evaluator_only'
        guard(True)
        truth_join_started = True
        evaluated, groups = replay.attach_truth_and_group(readouts, buckets, seeds=base['grid']['seeds'],
            profiles=base['grid']['profiles'], steps=120)
        need(len(evaluated) == 14400 and len(groups) == 136, 'complete unchanged truth API population')
        sidecar = (dict(seed=row['seed'], profile=row['profile'], graph_on=row['graph_on'], mechanism_on=row['mechanism_on'],
                       step=row['step'], theta_before=row['source_true_theta_before'], sourceTrueM=row['source_true_M']) for row in evaluated)
        truth_file = write_rows('truth_sidecar.jsonl', sidecar, 4 * 1024**2, 14400)
        write('groups.json', dict(groups=groups, truth_sidecar=truth_file,
            target='QUERIED_CONCEPT_PREUPDATE_SOURCE_THETA_GE_1250', native_M='THETA_EST_GE_1250_AND_STORED_PI_TASK_LE_0_55',
            new_independent_N=0, inference='DESCRIPTIVE_REUSED_CPU09_NO_CI_PVALUES_CAUSAL_OR_LEARNING_BENEFIT'))
        truth_join_completed = True
        guard(True)
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error), phase=phase))
    finally:
        if observer is not None:
            observer.restore()
            restoration_errors.extend(observer.cleanup_errors)
        for obj, name, present, value in reversed(guards):
            try:
                if type(obj) is dict:
                    obj[name] = value
                elif present:
                    setattr(obj, name, value)
                else:
                    delattr(obj, name)
            except BaseException as error:
                restoration_errors.append(dict(type=type(error).__name__, message=str(error), attribute=name))
    phase = 'terminal_source_resource_checks'
    try:
        after = verify()
        need(sha(CONTRACT) == args.contract_sha256 and not restoration_errors and not denied and sys.getprofile() is None, 'all terminal source/guard checks')
        if metadata is not None:
            metadata.require_metadata_closed(os_metadata)
        check()
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error), phase=phase))
    result = dict(status='COMPLETE_ALL120_CPU09_NATIVE_MASTERY_PENDING_ROOT' if not errors else 'REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY',
        errors=errors, restoration_errors=restoration_errors, denied=denied, deny_contexts=deny_contexts,
        output_relative=output_relative,
        audit_denial_count=audit_denial_count, source_before=before, source_after=after,
        factory_attempted=factory_attempted, factory_returned=factory_returned, policies_complete=len(policies),
        method_started=dict(method_started), method_returned=dict(method_returned),
        pending_policy_observer=observer.receipt() if observer is not None else None,
        pretruth_frozen=pretruth_frozen, truth_join_started=truth_join_started, truth_join_completed=truth_join_completed,
        memory_samples=memory, compiled_sources=compiled, native_windows_metadata=os_metadata, owner=owner,
        elapsed_before_receipt_seconds=elapsed(), profiler_installed=False, old_five_attempt_lane_reopened=False,
        world_teacher_optimizer_authorized_calls=0, new_independent_N=0, universal_RNG_monitor_claimed=False,
        scope='NEW_FULL_CACHED_NATIVE_MASTERY_DESCRIPTIVE_REPLAY_NOT_RESEARCH_MODEL_FIT')
    write('result.json' if not errors else 'failure.json', result)
    check()
    print(json.dumps(dict(status=result['status'], errors=errors, elapsed_seconds=elapsed())))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
