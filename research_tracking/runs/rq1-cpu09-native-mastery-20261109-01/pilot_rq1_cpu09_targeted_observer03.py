"""Pilot vận hành một history CPU09. Source-only cho tới ROOT dispatch.

Loader được parse stored truth CHỈ để validation cũ. Policy chỉ nhận query,
time, p trước update rồi y hiện tại. Không evaluator/truth metric hoặc world.
"""
import argparse
from collections import Counter, deque
from contextlib import contextmanager, nullcontext
from dataclasses import is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import random
import struct
import sys
import time
import types
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONTRACT = PREP / 'rq1_cpu09_targeted_observer_contract03.json'
KEY = (21000, 'PG', False, False)
METHOD_CAPS = {'__init__': 1, 'select': 120, 'predict': 120, 'update': 120, '_decayed_pi': 360}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def value_sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def exact(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is float:
        return struct.pack('>d', left) == struct.pack('>d', right)
    if type(left) is dict:
        return set(left) == set(right) and all(exact(left[k], right[k]) for k in left)
    if type(left) in (tuple, list):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def denial_context(event, values, phase):
    """Đọc tối đa6frames đang có, không traceback/linecache/source rereads."""
    raw = values[0] if event == 'open' and values else None
    mode = values[1] if event == 'open' and len(values) > 1 else None
    flags = values[2] if event == 'open' and len(values) > 2 else None
    if type(raw) is str:
        path_text, length = raw[:4096], len(raw)
    elif type(raw) is bytes:
        path_text, length = repr(raw[:4096]), len(raw)
    else:
        path_text, length = None, None
    record = dict(event=str(event)[:64], phase=str(phase)[:128],
        raw_path=path_text, raw_path_type=type(raw).__name__, raw_path_length=length,
        raw_path_truncated=length is not None and length > 4096,
        mode=mode[:64] if type(mode) is str else None,
        flags=flags if type(flags) is int else None, frames=[])
    frame = sys._getframe(1)
    try:
        while frame is not None and len(record['frames']) < 6:
            record['frames'].append(dict(co_filename=frame.f_code.co_filename[:1024],
                co_name=frame.f_code.co_name[:160], lineno=frame.f_lineno))
            frame = frame.f_back
    finally:
        del frame
    return record


class TargetedObserver:
    """Chỉ genuine class methods. Không thêm instance attributes/profiler."""
    def __init__(self, cls, caps):
        self.cls, self.caps = cls, dict(caps)
        self.started, self.returned, self.raised = Counter(), Counter(), Counter()
        self.originals = {name: (name in vars(cls), vars(cls).get(name), getattr(cls, name)) for name in caps}
        self.live = False
        self.target = None
        self.installed = []
        self.cleanup_errors = []

    def originals_match(self):
        return all((name in vars(self.cls)) == present and (not present or vars(self.cls)[name] is local)
                   and getattr(self.cls, name) is original
                   for name, (present, local, original) in self.originals.items())

    def install(self):
        need(not self.live and not self.installed, 'observer already installed or rollback pending')
        need(self.originals_match(), 'all original class attributes verified before any mutation')
        try:
            for name, (present, local, original) in self.originals.items():
                def wrapper(instance, *args, _name=name, _original=original, **kwargs):
                    if _name == '__init__' and self.target is None:
                        self.target = id(instance)
                    need(id(instance) == self.target, 'observer exact one policy identity')
                    self.started[_name] += 1
                    need(self.started[_name] <= self.caps[_name], 'targeted method cap before original body')
                    try:
                        value = _original(instance, *args, **kwargs)
                    except BaseException:
                        self.raised[_name] += 1
                        raise
                    self.returned[_name] += 1  # Count actual body return before postchecks.
                    return value

                # A setter may mutate and then raise, so register before attempting it.
                self.installed.append(name)
                setattr(self.cls, name, wrapper)
        except BaseException:
            self.restore()  # Reports rollback errors without replacing the installation error.
            raise
        self.live = True

    def restore(self):
        errors, pending = [], set()
        for name in reversed(self.installed):
            present, local, original = self.originals[name]
            try:
                if present:
                    if vars(self.cls).get(name) is not local:
                        setattr(self.cls, name, local)
                elif name in vars(self.cls):
                    delattr(self.cls, name)
                need((name in vars(self.cls)) == present and (not present or vars(self.cls)[name] is local)
                     and getattr(self.cls, name) is original, 'attribute restoration verification')
            except BaseException as error:
                pending.add(name)
                errors.append(dict(attribute=name, type=type(error).__name__, message=str(error)))
        self.installed = [name for name in self.installed if name in pending]
        self.live = bool(self.installed)
        try:
            need(not self.installed and self.originals_match(), 'exact original attributes not fully restored')
        except BaseException as error:
            errors.append(dict(attribute='ALL', type=type(error).__name__, message=str(error)))
        self.cleanup_errors.extend(errors)
        return errors

    @contextmanager
    def active(self):
        self.install()
        primary = None
        try:
            yield self
        except BaseException as error:
            primary = error
            raise
        finally:
            cleanup = self.restore()
            if cleanup and primary is None:
                raise RuntimeError('observer cleanup failed; details retained separately')

    def receipt(self):
        return dict(started=dict(self.started), returned=dict(self.returned), raised=dict(self.raised),
                    live=self.live, class_attributes_restored=not self.installed and self.originals_match(),
                    cleanup_errors=list(self.cleanup_errors), pending_attributes=list(self.installed),
                    instance_attributes_added=False, scope='FIVE_DECLARED_METHOD_BODIES_ONLY_NO_GLOBAL_PROFILER')


def public_stream(histories, key, expected_fields):
    need(key in histories and len(histories[key]) == 120, 'real complete requested stream')
    result = []
    for step, row in enumerate(histories[key]):
        need(set(row) == expected_fields and row['step'] == step, 'public-only ordered history')
        result.append(MappingProxyType(dict(row)))
    return tuple(result)


def pure_checks():
    """Năm manufactured checks, không import scientific modules hoặc cache."""
    class Base:
        def inherited(self, value):
            return value + 1

    class Fake(Base):
        def __init__(self):
            self.x = 0

        def action(self, fail=False):
            self.x += 1
            if fail:
                raise LookupError('original body exception')
            return self.inherited(self.x)

    observer = TargetedObserver(Fake, {'__init__': 1, 'action': 2, 'inherited': 1})
    original = dict(vars(Fake))
    observer.install()
    obj = Fake()
    observer.restore()
    need(vars(obj) == {'x': 0} and dict(vars(Fake)) == original, 'constructor observer has no instance pollution')
    observer.install()
    try:
        need(obj.action() == 2, 'passthrough actual returned value')
        try:
            obj.action(True)
        except LookupError as error:
            need(str(error) == 'original body exception', 'original exception preserved')
        else:
            raise AssertionError('missing original exception')
    finally:
        observer.restore()
    need(dict(vars(Fake)) == original and observer.started['action'] == 2
         and observer.returned['action'] == 1 and observer.raised['action'] == 1,
         'original absence/value and started/returned/raised scope')
    rows = tuple(dict(step=t, concept='c', question='q', prediction=.5, y=t % 2) for t in range(120))
    fields = frozenset(rows[0])
    stream = public_stream({KEY: rows}, KEY, fields)
    try:
        stream[0]['y'] = 0
    except TypeError:
        pass
    else:
        raise AssertionError('public rows mutable')
    try:
        public_stream({KEY: rows[:-1]}, KEY, fields)
    except ValueError:
        pass
    else:
        raise AssertionError('short stream admitted')

    class LateInstallMeta(type):
        blocked = True

        def __setattr__(cls, name, value):
            type.__setattr__(cls, name, value)
            if name == 'action' and LateInstallMeta.blocked:
                LateInstallMeta.blocked = False
                raise OSError('late install mutated then raised')

    class LateInstall(Fake, metaclass=LateInstallMeta):
        pass

    late = TargetedObserver(LateInstall, {'__init__': 1, 'action': 1, 'inherited': 1})
    try:
        late.install()
    except OSError as error:
        need(str(error) == 'late install mutated then raised', 'installation primary preserved')
    else:
        raise AssertionError('late install failure missing')
    need(late.originals_match() and not late.installed and not late.live and not late.cleanup_errors,
         'partial installation fully rolled back without live flag')

    class CleanupMeta(type):
        blocked = {'action', 'inherited'}
        originals = {}

        def __setattr__(cls, name, value):
            if name in CleanupMeta.blocked and value is CleanupMeta.originals[name]:
                CleanupMeta.blocked.remove(name)
                raise OSError('cleanup ' + name)
            type.__setattr__(cls, name, value)

        def __delattr__(cls, name):
            if name in CleanupMeta.blocked:
                CleanupMeta.blocked.remove(name)
                raise OSError('cleanup ' + name)
            type.__delattr__(cls, name)

    class CleanupFailure(Fake, metaclass=CleanupMeta):
        pass

    CleanupMeta.originals = {name: getattr(CleanupFailure, name) for name in ('__init__', 'action', 'inherited')}
    cleanup = TargetedObserver(CleanupFailure, {'__init__': 1, 'action': 1, 'inherited': 1})
    try:
        with cleanup.active():
            failing = CleanupFailure()
            failing.action(True)
    except LookupError as error:
        need(str(error) == 'original body exception', 'native body primary survives concurrent cleanup failures')
    else:
        raise AssertionError('original body exception was lost')
    need({item['attribute'] for item in cleanup.cleanup_errors if item['attribute'] != 'ALL'}
         == {'action', 'inherited'} and '__init__' not in vars(CleanupFailure),
         'rollback continues and reports both failing attributes')
    need(cleanup.restore() == [] and cleanup.originals_match() and not cleanup.installed
         and bool(cleanup.cleanup_errors), 'retry restores pending attributes without erasing error history')

    return dict(manufactured_checks=5, source_only_helpers=True, native_calls=0,
                claims=('passthrough+original_exception', 'attribute_presence_restoration',
                        'immutable_complete_one_stream', 'partial_install_rollback', 'primary_and_two_cleanup_failures'))


def main():
    started, wall = time.perf_counter(), time.time()
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--phase', choices=('pure', 'native'), required=True)
    args = parser.parse_args()
    need(Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT / '.venv'
         and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'actual repository CPU context')
    need(sys.getprofile() is None, 'STOP existing profiler, never install a replacement')

    def elapsed():
        return max(time.perf_counter() - started, time.time() - wall)

    def check():
        need(math.isfinite(elapsed()) and elapsed() < 53, 'single worker53 allocation')

    def safe(path):
        need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace path')
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no aliases')

    def sha(path):
        check()
        safe(path)
        need(path.is_file() and path.stat().st_size <= 4 * 1024**2, 'bounded source/input')
        raw = path.read_bytes()
        need(len(raw) == path.stat().st_size, 'stable input bytes')
        return hashlib.sha256(raw).hexdigest()

    need(sha(Path(__file__).resolve()) == args.source_sha256 and sha(CONTRACT) == args.contract_sha256,
         'externally reviewed source/contract pins')
    contract = json.loads(CONTRACT.read_bytes())
    need(contract['worker_sha256'] == args.source_sha256 and contract['selected_key'] == list(KEY), 'fixed prospective scope')
    out = PREP / contract['output_names'][args.phase]
    safe(out)
    need(not out.exists(), 'exclusive new output namespace')
    out.mkdir()
    errors, memory, compiled = [], [], []
    os_metadata = {}
    phase = 'source_preflight'
    phases = []
    observer = None
    reservations = dict(constructors=2, select=240, predict=240, native_capture=240, update=240)
    native_started = Counter()
    native_returned = Counter()
    guards, restoration_errors = [], []
    denied = []
    deny_contexts = []
    audit_denial_count = 0
    before = {}
    metadata_module = None
    truth_validation_started = False
    truth_validation_completed = False

    def write(name, value):
        raw = encode(value) + b'\n'
        need(len(raw) <= 1024**2, 'small bounded output')
        with (out / name).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())

    def verify():
        result = {}
        for name, row in contract['bindings'].items():
            path = ROOT / name
            need(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'frozen source/input binding')
            result[name] = row['sha256']
        need(not before or result == before, 'all bindings unchanged')
        return result

    try:
        before = verify()
        checks = pure_checks()  # Inline manufactured checks consume the same worker53 budget.
        write('pure_checks.json', checks)
        if args.phase == 'pure':
            need(not any(n in sys.modules for n in ('numpy', 'pandas', 'torch', 'knowledge_tracing')), 'pure phase cold')
        else:
            # Unchanged reviewed real-module source compiler, not a fabricated package.
            helper_path = PREP / 'worker_rq1_cpu09_native_mastery04.py'
            helper = types.ModuleType('reviewed_cpu09_source_compiler')
            helper.__file__ = str(helper_path)
            exec(compile(helper_path.read_bytes(), str(helper_path), 'exec'), helper.__dict__)
            load = helper.load_source
            old = json.loads((PREP / 'rq1_cpu09_native_mastery_contract04.json').read_bytes())
            sources = old['source_pins']
            replay = load('reviewed_cpu09_replay_primitives', PREP / 'replay_rq1_cpu09_native_mastery01.py')
            cache = load('reviewed_cpu09_strict_cache', PREP / 'analyze_rq2_cached_mechanism01.py')
            base = cache.decode((PREP / 'rq2_cache_mechanism_contract01.json').read_bytes())
            accepted = cache.decode((PREP / 'rq2-cached-mechanism-native02-outer/final.json').read_bytes())
            need(accepted['status'] == 'ACCEPTED_CACHED_RQ2_SECONDARY_ANALYSIS' and accepted['errors'] == []
                 and accepted['inputs_before'] == accepted['inputs_after']
                 == {n: r['sha256'] for n, r in base['inputs'].items()}, 'actual existing cache admission')

            def project(name):
                relative = 'src/' + name.replace('.', '/')
                relative += '/__init__.py' if name in ('knowledge_tracing', 'knowledge_tracing.akt', 'knowledge_tracing.gam_kt') else '.py'
                need(relative in contract['bindings'], 'source-compiled project file declared')
                return helper.load_pinned_project_source(name, sources[relative], compiled)

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
                         'actual RAM metadata')
                    need(max(sample['process_rss_bytes'], sample['process_peak_rss_bytes'] or 0) <= 1024**3
                         and sample['system_available_ram_bytes'] >= 2 * 1024**3, 'worker actual RSS/freeRAM')
                    memory.append(dict(phase=phase, elapsed_seconds=elapsed(), **sample))
                    need(len(memory) <= 1000, 'bounded resource samples')

            guard(True)
            metadata_module = load('reviewed_real_windows_metadata', PREP / 'prediction_mastery_trace_worker03.py')
            metadata_module.native_windows_metadata(check, os_metadata)
            write('native_metadata.json', os_metadata)
            allowed = {os.path.normcase(str((ROOT / name).resolve())) for name in contract['bindings']}
            # Explicit read-only entitlement; the contract cannot contain its own byte hash.
            need(sha(CONTRACT) == args.contract_sha256, 'external contract pin revalidated before audit entitlement')
            allowed.add(os.path.normcase(str(CONTRACT.resolve())))
            runtime_roots = tuple({Path(sys.prefix), Path(sys.base_prefix)})
            output_names = {'pure_checks.json', 'native_metadata.json', 'reservation.json', 'off.json', 'on.json', 'result.json', 'failure.json'}

            def audit(event, values):
                def deny(message):
                    nonlocal audit_denial_count
                    audit_denial_count += 1
                    if len(deny_contexts) < 8:
                        context = denial_context(event, values, phase)
                        context['message'] = message
                        deny_contexts.append(context)
                    denied.append(message)
                    raise RuntimeError(message)
                if event == 'subprocess.Popen' or event.startswith('socket.') or event in ('os.system', 'os.posix_spawn', 'os.spawn'):
                    deny('no process/network after real metadata')
                if event == 'import' and str(values[0]).split('.')[0] in ('torch', 'scipy', 'sklearn', 'networkx'):
                    deny('no NN/solver import')
                if event == 'open' and values and not isinstance(values[0], int):
                    path = Path(values[0]).absolute()
                    mode, flags = values[1] or '', values[2] if type(values[2]) is int else 0
                    writing = any(c in mode for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR))
                    if writing:
                        if path.parent != out or path.name not in output_names:
                            deny('write outside exact owned outputs')
                    else:
                        resolved = path.resolve()
                        runtime = path.suffix.lower() in ('.py', '.pyc', '.pyd', '.dll') and any(resolved.is_relative_to(p.resolve()) for p in runtime_roots)
                        if os.path.normcase(str(resolved)) not in allowed and not runtime and not (path.parent == out and path.name in output_names):
                            deny('read outside pinned sources/inputs/runtime')
                if event in ('os.remove', 'os.rename', 'os.rmdir', 'os.link', 'os.symlink', 'os.mkdir'):
                    deny('no historical mutation/new directory')

            sys.addaudithook(audit)
            phase = 'native_import_and_full_cache_validation'
            need(not any(n in sys.modules for n in ('numpy', 'pandas', 'torch')), 'cold pre-native')
            import numpy as np
            import pandas as pd
            project('knowledge_tracing.gam_kt')
            reference = project('knowledge_tracing.paper2_reference').load_reference()
            build = project('knowledge_tracing.gam_kt.simulator_pathways').build_pathway_policy
            need(reference['provenance'] == cache.decode((ROOT / base['paths']['provenance']).read_bytes()), 'original source registry')
            cache.validate_manifest(cache.decode((ROOT / base['paths']['manifest']).read_bytes()), base)
            questions, roots = cache.topology({n: (ROOT / base['paths'][n]).read_bytes() for n in ('nodes', 'edges', 'questions')})
            rows = cache.trace_rows(ROOT / base['paths']['traces'], max_compressed=1024**2,
                max_uncompressed=8 * 1024**2, max_line=8192, max_rows=14400, guard=guard)
            # Explicit ROOT revision: existing oracle fields may be parsed ONLY by strict validation.
            truth_validation_started = True
            buckets = cache.validate_trace(rows, seeds=base['grid']['seeds'], profiles=base['grid']['profiles'],
                                           steps=120, questions=questions, roots=roots)
            truth_validation_completed = True
            histories = replay.observable_histories(buckets, seeds=base['grid']['seeds'], profiles=base['grid']['profiles'], steps=120)
            history = public_stream(histories, KEY, replay.OBSERVABLE_FIELDS)
            need(len(buckets) == len(histories) == 120 and sum(map(len, histories.values())) == 14400, 'full grid before one real stream')
            del buckets, histories  # No truth-bearing object passed to factory/policy/observer.
            guard(True)

            def state_data(value):
                if isinstance(value, np.ndarray):
                    return dict(array_shape=list(value.shape), dtype=str(value.dtype), bytes_sha256=hashlib.sha256(value.tobytes()).hexdigest())
                if isinstance(value, np.generic):
                    return state_data(value.item())
                if isinstance(value, pd.Timestamp):
                    return dict(timestamp_iso=value.isoformat(), timestamp_ns=int(value.value))
                if type(value) is float:
                    return dict(float_hex=value.hex())
                if isinstance(value, dict):
                    return {str(k): state_data(v) for k, v in value.items()}
                if isinstance(value, deque):
                    return dict(deque_maxlen=value.maxlen, items=[state_data(v) for v in value])
                if isinstance(value, (tuple, list)):
                    return [state_data(v) for v in value]
                if is_dataclass(value):
                    return state_data(vars(value))
                need(value is None or type(value) in (str, int, bool), 'full actual state serializer coverage')
                return value

            def fingerprint(policy):
                return value_sha(state_data(vars(policy)))

            def deny_known(*args, **kwargs):
                denied.append('known world/persona/RNG route attempted')
                raise RuntimeError(denied[-1])

            def replace(obj, name, replacement):
                # Class attributes may be inherited: preserve actual original absence as well as value.
                local = vars(obj)
                present, value = name in local, local.get(name)
                guards.append((obj, name, present, value))
                setattr(obj, name, replacement)

            for scope_name in ('environment', 'controller', 'estimator'):
                scope = reference[scope_name]
                for name in ('__init__', 'interact'):
                    replace(scope['LatentStudentEnvironment'], name, deny_known)
                original_persona = scope['persona_base_abilities']
                guards.append((scope, 'persona_base_abilities', True, original_persona))
                scope['persona_base_abilities'] = deny_known
            for module, names in ((random, ('random', 'seed', 'randrange', 'randint', 'choice', 'choices', 'shuffle', 'sample', 'uniform', 'gauss', 'getrandbits')),
                                   (np.random, ('default_rng', 'seed', 'random', 'random_sample', 'rand', 'randn', 'randint', 'choice', 'shuffle', 'permutation', 'uniform', 'normal'))):
                for name in names:
                    replace(module, name, deny_known)
            rng_before = value_sha(state_data(dict(python=random.getstate(), numpy=np.random.get_state())))
            write('reservation.json', dict(status='RESERVED_TWO_FRESH_POLICIES_BEFORE_ANY_CONSTRUCTOR',
                  counts=reservations, selected_key=KEY, source_before=before,
                  loader_truth_scope='EXISTING_STRICT_VALIDATION_ONLY_NO_TRUTH_ANALYSIS',
                  hardkill_actual_counts='UNKNOWN_LE_RESERVED_UNTIL_TERMINAL'))
            offsets = replay.clock_hours(120)
            origin = pd.Timestamp('2026-01-01', tz='UTC')

            def invoke(name, fn, *values):
                native_started[name] += 1
                need(native_started[name] <= reservations[name], 'global direct reservation before body')
                value = fn(*values)
                native_returned[name] += 1
                return value

            for enabled in (False, True):
                phase = 'targeted_on' if enabled else 'targeted_off'
                guard(True)
                phase_start = elapsed()
                observer = TargetedObserver(reference['estimator']['GAMKTPolicy'], METHOD_CAPS) if enabled else None
                with observer.active() if observer else nullcontext():
                    policy = invoke('constructors', lambda: build(reference, signal=False, parent_adaptation=False, local_adaptation=False))
                initial = fingerprint(policy)  # Every monkeypatch restored before full vars fingerprint.
                observed = []
                loop_start = elapsed()
                with observer.active() if observer else nullcontext():
                    for step, row in enumerate(history):
                        guard()
                        need(set(row) == replay.OBSERVABLE_FIELDS and row['step'] == step, 'exact public current row')
                        timestamp = origin + pd.Timedelta(hours=offsets[step])
                        selected = invoke('select', policy.select)
                        expected = questions[row['question']]
                        need(type(selected) is tuple and len(selected) == 3 and selected[:2] == (row['concept'], row['question'])
                             and type(selected[2]) is float and exact(selected[2], expected['difficulty'])
                             and row['concept'] == expected['concept'], 'all120 exact archived selected tuples')
                        p = invoke('predict', policy.predict, *selected, timestamp)
                        need(type(p) is float and math.isfinite(p) and exact(p, row['prediction']), 'all120 archived P bits')
                        native = invoke('native_capture', replay.capture_native, policy, row['concept'], timestamp)
                        observed.append(dict(step=step, selected=list(selected), prediction=p, timestamp=timestamp.isoformat(), **native))
                        invoke('update', policy.update, *selected, timestamp, row['y'], p)
                        guard()
                loop_seconds = elapsed() - loop_start
                final_state = fingerprint(policy)
                need(sum(state.attempts for state in policy.states.values()) == 120, '120actual updates in native state')
                if observer:
                    need(observer.started == observer.returned == Counter(METHOD_CAPS) and not observer.raised
                         and not observer.cleanup_errors and not observer.installed and observer.originals_match(),
                         'all declared ON original bodies returned / exact nestedpi360')
                record = dict(phase=phase, key=KEY, events=120, initial_state_sha256=initial, final_state_sha256=final_state,
                    readouts=observed, phase_seconds=elapsed() - phase_start, loop_seconds=loop_seconds,
                    direct_started_cumulative=dict(native_started), direct_returned_cumulative=dict(native_returned),
                    observer=observer.receipt() if observer else dict(enabled=False, nested_calls_observed=False),
                    instance_attributes_added=False, profiler_installed=False)
                phases.append(record)
                write('on.json' if enabled else 'off.json', record)
                guard(True)
            need(phases[0]['initial_state_sha256'] == phases[1]['initial_state_sha256']
                 and phases[0]['final_state_sha256'] == phases[1]['final_state_sha256']
                 and exact(phases[0]['readouts'], phases[1]['readouts']), 'all120 OFF/ON readouts / full endpoint states exact')
            need(native_started == native_returned == Counter(reservations), 'all global direct attempts returned exactly')
            need(rng_before == value_sha(state_data(dict(python=random.getstate(), numpy=np.random.get_state()))), 'legacy RNG states unchanged')
            need(not denied, 'no guarded route attempts')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error), phase=phase))
    finally:
        if observer:
            try:
                observer.restore()
            except BaseException as error:
                restoration_errors.append(repr(error))
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
                restoration_errors.append(repr(error))
    after = {}
    phase = 'postchecks'
    try:
        after = verify()
        need(sha(CONTRACT) == args.contract_sha256 and sha(Path(__file__).resolve()) == args.source_sha256,
             'external source/contract postchecks')
        if metadata_module is not None:
            metadata_module.require_metadata_closed(os_metadata)
        check()
        need(sys.getprofile() is None and not restoration_errors and not denied, 'all observer/guard restoration and closed metadata')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error), phase='postchecks'))
    payload = dict(status=('ACCEPTED_FIVE_MANUFACTURED_PILOT_CHECKS' if args.phase == 'pure' else
                    'COMPLETE_ONE_HISTORY_OFF_ON_PARITY_PENDING_ROOT') if not errors else 'REJECTED_KEEP_PILOT_NO_RETRY',
        errors=errors, restoration_errors=restoration_errors, denied=denied, phase=args.phase,
        deny_contexts=deny_contexts, audit_denial_count=audit_denial_count,
        deny_contexts_truncated=audit_denial_count > len(deny_contexts),
        self_contract_read_entitlement=dict(path=CONTRACT.relative_to(ROOT).as_posix(),
            external_sha256=args.contract_sha256, read_only=True,
            hash_not_embedded_in_own_bindings=True),
        elapsed_before_receipt_seconds=elapsed(), source_before=before, source_after=after,
        direct_started=dict(native_started), direct_returned=dict(native_returned), reservation=reservations,
        phases=[{k: v for k, v in row.items() if k != 'readouts'} for row in phases],
        native_windows_metadata=os_metadata, compiled_sources=compiled, memory_samples=memory,
        owner=owner, profiler_installed=False, existing_profiler_replaced=False,
        teacher_world_optimizer_calls_authorized=0, new_independent_N=0,
        policy_oracle_exposure=False, loader_truth_validation_started=truth_validation_started,
        loader_truth_validation_completed=truth_validation_completed,
        universal_RNG_call_observation_claimed=False, truth_accuracy_or_full120streams_claimed=False,
        old_five_attempt_lane_reopened=False)
    write('result.json' if not errors else 'failure.json', payload)
    check()
    print(json.dumps(dict(status=payload['status'], errors=errors, elapsed_seconds=elapsed()), ensure_ascii=False))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
