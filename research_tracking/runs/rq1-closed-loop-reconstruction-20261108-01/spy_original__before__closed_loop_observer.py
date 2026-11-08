"""Quan sát calls có sẵn; không gọi scoring/selector/RNG hoặc sửa native object."""
from collections import Counter, deque
from dataclasses import is_dataclass
import hashlib
import json
import math
import struct
import sys
import time


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
        return left.keys() == right.keys() and all(exact(left[k], right[k]) for k in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def primitive(value):
    """Serialize existing fields only, without invoking arbitrary object methods."""
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError('nonfinite state')
        return {'float_hex': value.hex()}
    module = type(value).__module__
    if module.startswith('numpy'):
        import numpy as np
        if isinstance(value, np.ndarray):
            if value.dtype.hasobject:
                raise ValueError('object array forbidden')
            return {'array_shape': list(value.shape), 'dtype': str(value.dtype),
                    'bytes_sha256': hashlib.sha256(value.tobytes()).hexdigest()}
        if isinstance(value, np.generic):
            return primitive(value.item())
    if module.startswith('pandas'):
        import pandas as pd
        if isinstance(value, pd.Timestamp):
            return {'timestamp_iso': value.isoformat(), 'timestamp_ns': int(value.value)}
    if isinstance(value, dict):
        if not all(type(k) in (str, int) for k in value):
            raise TypeError('unsupported state key')
        return {str(k): primitive(v) for k, v in value.items()}
    if isinstance(value, deque):
        return {'deque_maxlen': value.maxlen, 'items': [primitive(v) for v in value]}
    if type(value) in (list, tuple):
        return [primitive(v) for v in value]
    if is_dataclass(value) and not isinstance(value, type):
        return primitive(vars(value))
    raise TypeError('unsupported native state field ' + str(type(value)))


def fingerprint(value):
    return digest(primitive(value))


class ConstructorRegistry:
    """Both passes use identical shims returning untouched native instances."""
    def __init__(self):
        self.policies = {}
        self.environments = {}
        self.initial = {}
        self.current = None

    def begin(self, seed, profile):
        self.current = (seed, profile)

    def policy_factory(self, cls, *, empty=False):
        def construct(flag):
            if type(flag) is not bool or self.current is None or (empty and flag is not True):
                raise ValueError('unexpected native constructor arguments')
            variant = 'empty_graph_package' if empty else ('graph_package' if flag else 'graph_free')
            key = (*self.current, variant)
            if key in self.policies:
                raise ValueError('duplicate native policy constructor')
            native = cls(flag)
            self.policies[key] = native
            self.initial[key] = fingerprint(vars(native))
            return native
        return construct

    def environment_factory(self, cls):
        def construct(base):
            if self.current is None:
                raise ValueError('missing trajectory')
            keys = [(*self.current, variant) for variant in
                    ('graph_free', 'graph_package', 'empty_graph_package')]
            key = next((key for key in keys if key not in self.environments), None)
            if key is None:
                raise ValueError('too many environment constructors')
            native = cls(base)
            self.environments[key] = native
            return native
        return construct

    def policy_key(self, instance):
        return next((key for key, obj in self.policies.items() if obj is instance), None)

    def environment_key(self, instance):
        return next((key for key, obj in self.environments.items() if obj is instance), None)

    def summaries(self):
        if set(self.policies) != set(self.environments):
            raise ValueError('constructor pairing incomplete')
        return [{'seed': key[0], 'profile': key[1], 'variant': key[2],
                 'initial_policy_sha256': self.initial[key],
                 'final_policy_sha256': fingerprint(vars(obj)),
                 'final_environment_sha256': fingerprint(vars(self.environments[key]))}
                for key, obj in self.policies.items()]


class ProfileObserver:
    def __init__(self, registry, methods, nodes, sink, *, deadline, clock=time.perf_counter,
                 max_rows=3240, max_steps=120):
        if not nodes or len(nodes) > 28 or len(set(nodes)) != len(nodes):
            raise ValueError('bounded unique node identities required')
        if type(max_rows) is not int or not 1 <= max_rows <= 3240:
            raise ValueError('row cap')
        if type(max_steps) is not int or not 1 <= max_steps <= 120:
            raise ValueError('step cap')
        if not math.isfinite(deadline):
            raise ValueError('finite deadline required')
        self.registry, self.nodes, self.sink = registry, tuple(nodes), sink
        self.deadline, self.clock = deadline, clock
        self.max_rows, self.max_steps = max_rows, max_steps
        self.bindings = {}
        for name, functions in methods.items():
            for fn in functions:
                binding = (fn.__code__, id(fn.__globals__))
                if binding in self.bindings and self.bindings[binding] != name:
                    raise ValueError('ambiguous method identity')
                self.bindings[binding] = name
        required = {'select', 'ready_set', 'is_mastered', 'mastery_score', 'predict', 'update', 'interact'}
        if set(self.bindings.values()) != required:
            raise ValueError('incomplete native method identities')
        self.pending, self.completed, self.rows = {}, Counter(), []
        self.calls = Counter()
        self.failure = None

    def __enter__(self):
        if sys.getprofile() is not None:
            raise RuntimeError('existing profiler; STOP without replacement')
        sys.setprofile(self._callback)
        return self

    def __exit__(self, kind, value, traceback):
        sys.setprofile(None)
        if kind is None and self.failure is not None:
            raise RuntimeError('observer callback failed')

    def _callback(self, frame, event, arg):
        if event not in ('call', 'return'):
            return
        name = self.bindings.get((frame.f_code, id(frame.f_globals)))
        if name is None:
            return
        try:
            if self.clock() > self.deadline:
                raise TimeoutError('observer cumulative deadline')
            self._observe(name, frame, event, arg)
        except BaseException as exc:
            self.failure = type(exc).__name__ + ': ' + str(exc)
            raise

    def _observe(self, name, frame, event, result):
        obj = frame.f_locals.get('self')
        key = (self.registry.environment_key(obj) if name == 'interact'
               else self.registry.policy_key(obj))
        if key is None:
            raise ValueError('unregistered native instance')
        if event == 'call':
            self.calls[name] += 1
            if sum(self.calls.values()) > 1_000_000:
                raise ValueError('native call ledger cap')
        if name == 'select' and event == 'call':
            if key in self.pending or self.completed[key] >= self.max_steps or len(self.rows) >= self.max_rows:
                raise ValueError('duplicate/overbudget selection')
            # No timestamp argument exists for select; context is captured later from actual predict args.
            self.pending[key] = {'seed': key[0], 'profile': key[1], 'variant': key[2],
                'step': self.completed[key], 'state_before_selection_sha256': fingerprint(vars(obj)),
                'mastery_calls': [], 'mastery_score_calls': [], 'phases': ['before_selection'],
                'select_timestamp_argument': None, 'is_served_in_simulator': True,
                'full_mastery_score_vector_available': False}
            return
        row = self.pending.get(key)
        if row is None:
            raise ValueError('native call outside pending event')
        if name == 'is_mastered' and event == 'return' and row['phases'] == ['before_selection']:
            value = bool(result)
            row['mastery_calls'].append({'concept': frame.f_locals['cid'], 'mastered': value,
                'direct_caller': frame.f_back.f_code.co_name})
        elif name == 'mastery_score' and event == 'return' and row['phases'] == ['before_selection']:
            row['mastery_score_calls'].append({'concept': frame.f_locals['cid'], 'score': float(result)})
        elif name == 'ready_set' and event == 'return':
            if 'ready_set' in row or row['phases'] != ['before_selection']:
                raise ValueError('duplicate/out-of-order ready_set')
            direct = [v for v in row['mastery_calls'] if v['direct_caller'] == 'ready_set']
            first = direct[:len(self.nodes)]
            if [v['concept'] for v in first] != list(self.nodes):
                raise ValueError('native full mastery decision coverage missing')
            decisions = {v['concept']: v['mastered'] for v in first}
            if any(v['concept'] not in decisions or decisions[v['concept']] != v['mastered'] for v in direct):
                raise ValueError('inconsistent repeated native mastery decision')
            if type(result) is not list or not result or not set(result) <= set(self.nodes):
                raise ValueError('invalid native ready_set')
            row['mastered_decisions'] = decisions
            row['ready_set'] = list(result)
            row['mastery_ready_capture_phase'] = 'during_selection_before_bookkeeping'
        elif name == 'select' and event == 'return':
            if 'ready_set' not in row or type(result) is not tuple or len(result) != 3:
                raise ValueError('missing native ready/selection tuple')
            cid, qid, difficulty = result
            candidates, balanced = frame.f_locals.get('candidates'), frame.f_locals.get('balanced')
            if not isinstance(candidates, list) or not isinstance(balanced, list) or not candidates or not balanced:
                raise ValueError('native eligible candidates locals missing')
            if not set(balanced) <= set(candidates) <= set(self.nodes) or cid not in balanced:
                raise ValueError('selection eligibility mismatch')
            if type(cid) is not str or type(qid) is not str or not math.isfinite(difficulty):
                raise ValueError('invalid returned tuple')
            row.update(served_tuple={'concept': cid, 'question': qid, 'difficulty': float(difficulty)},
                       eligible_candidates=list(candidates), balanced_candidates=list(balanced),
                       state_after_selection_sha256=fingerprint(vars(obj)))
            row['phases'].append('after_selection_bookkeeping')
        elif name == 'predict':
            if event == 'call':
                if row['phases'][-1] != 'after_selection_bookkeeping':
                    raise ValueError('predict order')
                args = frame.f_locals
                query = {'concept': args['cid'], 'question': args['qid'], 'difficulty': float(args['difficulty'])}
                if not exact(query, row['served_tuple']):
                    raise ValueError('actual query differs from selected tuple')
                timestamp = args['timestamp']
                row['query'] = {**query, 'timestamp_iso': timestamp.isoformat(), 'timestamp_ns': int(timestamp.value)}
                row['prediction_capture_phase'] = 'after_selection_bookkeeping_before_environment_interact'
                row['phases'].append('before_predict')
            else:
                if row['phases'][-1] != 'before_predict' or not math.isfinite(result):
                    raise ValueError('predict return')
                row['prediction'] = float(result)
                row['phases'].append('after_predict')
        elif name == 'interact':
            if event == 'call':
                if row['phases'][-1] != 'after_predict':
                    raise ValueError('environment order')
                args = frame.f_locals
                if args['cid'] != row['query']['concept'] or float(args['difficulty']) != row['query']['difficulty']:
                    raise ValueError('environment selected target mismatch')
                if args['timestamp'].isoformat() != row['query']['timestamp_iso']:
                    raise ValueError('environment timestamp mismatch')
                row['phases'].append('before_environment_interact')
            else:
                if row['phases'][-1] != 'before_environment_interact' or not isinstance(result, dict):
                    raise ValueError('environment return')
                row['correct'] = result['y']
                row['outcome_sha256'] = digest(result)
                row['phases'].append('after_environment_interact')
        elif name == 'update':
            if event == 'call':
                if row['phases'][-1] != 'legacy_written':
                    raise ValueError('update before verified legacy write')
                args = frame.f_locals
                query = {'concept': args['cid'], 'question': args['qid'], 'difficulty': float(args['difficulty'])}
                if not exact(query, row['served_tuple']) or args['timestamp'].isoformat() != row['query']['timestamp_iso']:
                    raise ValueError('update target mismatch')
                if not exact(args['y'], row['correct']) or not exact(float(args['p_pred']), row['prediction']):
                    raise ValueError('current label/prediction pairing mismatch')
                row['phases'].append('before_update')
            else:
                if row['phases'][-1] != 'before_update':
                    raise ValueError('update return order')
                row['state_after_update_sha256'] = fingerprint(vars(obj))
                row['phases'].append('after_update')
                self.sink.write(canonical(row) + '\n')
                self.rows.append(row)
                self.completed[key] += 1
                del self.pending[key]

    def legacy(self, row):
        key = (row['seed'], row['profile'], row['variant'])
        pending = self.pending.get(key)
        if pending is None or pending['step'] != row['step'] or pending['phases'][-1] != 'after_environment_interact':
            raise ValueError('legacy event order/key mismatch')
        if (row['concept'], row['question'], row['timestamp']) != (
                pending['query']['concept'], pending['query']['question'], pending['query']['timestamp_iso']):
            raise ValueError('legacy query mismatch')
        if not exact(float(row['prediction']), pending['prediction']) or not exact(row['y'], pending['correct']):
            raise ValueError('legacy prediction/label mismatch')
        pending['legacy_row_sha256'] = digest(row)
        pending['phases'].append('legacy_written')

    def finish(self, *, expected_rows, expected_steps):
        if self.failure or self.pending or len(self.rows) != expected_rows:
            raise ValueError('incomplete observer rows')
        if set(self.completed) != set(self.registry.policies) or any(v != expected_steps for v in self.completed.values()):
            raise ValueError('incomplete trajectory')
        for name in ('select', 'ready_set', 'predict', 'update', 'interact'):
            if self.calls[name] != expected_rows:
                raise ValueError('native method count mismatch: ' + name)
