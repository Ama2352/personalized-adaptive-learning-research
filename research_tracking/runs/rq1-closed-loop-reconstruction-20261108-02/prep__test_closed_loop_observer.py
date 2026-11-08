"""Synthetic spies only: no Paper2/native model, data replay, fitting or RNG."""
from collections import Counter
import io
import json
from pathlib import Path
import sys
import time

import pytest

from closed_loop_observer import ConstructorRegistry, ProfileObserver, exact, fingerprint, primitive
from run_closed_loop_reconstruction import TraceSink, fresh_output, main


class Stamp:
    value = 123
    def isoformat(self):
        return '2026-01-01T06:00:00+00:00'


class SpyPolicy:
    def __init__(self, flag):
        self.flag = flag
        self.nodes = ['a', 'b']
        self.visits = Counter()
        self.labels = []
        self.calls = Counter()

    def is_mastered(self, cid):
        self.calls['is_mastered'] += 1
        return cid == 'a'

    def ready_set(self):
        decisions = [self.is_mastered(cid) for cid in self.nodes]
        return [cid for cid, mastered in zip(self.nodes, decisions) if mastered]

    def mastery_score(self, cid):
        self.calls['mastery_score'] += 1
        return 0.25

    def select(self):
        self.calls['select'] += 1
        candidates = self.ready_set()
        # Deliberately demonstrate R != final eligible candidates without new calls.
        candidates = ['b']
        balanced = candidates[:]
        cid = min(balanced, key=self.mastery_score)
        self.visits[cid] += 1
        return cid, cid + '-q', 1200.0

    def predict(self, cid, qid, difficulty, timestamp):
        self.calls['predict'] += 1
        return 0.5

    def update(self, cid, qid, difficulty, timestamp, y, p_pred):
        self.calls['update'] += 1
        self.labels.append(y)


class SpyEnvironment:
    def __init__(self, base):
        self.base = dict(base)
        self.calls = 0

    def interact(self, cid, difficulty, timestamp, outcome_uniform, learning_uniform):
        self.calls += 1
        return {'y': 1, 'synthetic_marker': 9}


def setup(cls=SpyPolicy, *, max_rows=3, deadline=None):
    registry = ConstructorRegistry()
    registry.begin(20000, 'PG')
    environment = registry.environment_factory(SpyEnvironment)({'a': 0.0})
    policy = registry.policy_factory(cls)(False)
    methods = {name: [getattr(cls, name)] for name in
               ('select', 'ready_set', 'is_mastered', 'mastery_score', 'predict', 'update')}
    methods['interact'] = [SpyEnvironment.interact]
    sink = io.StringIO()
    observer = ProfileObserver(registry, methods, ['a', 'b'], sink,
        deadline=time.perf_counter() + 10 if deadline is None else deadline,
        max_rows=max_rows, max_steps=3)
    return registry, policy, environment, observer, sink


def one_event(policy, environment, observer=None, *, step=0, label=None, query_override=False, legacy=True):
    timestamp = Stamp()
    cid, qid, difficulty = policy.select()
    if query_override:
        qid = 'different-q'
    prediction = policy.predict(cid, qid, difficulty, timestamp)
    outcome = environment.interact(cid, difficulty, timestamp, 0.1, 0.2)
    row = {'seed': 20000, 'profile': 'PG', 'variant': 'graph_free', 'step': step,
           'concept': cid, 'question': qid, 'prediction': prediction,
           'timestamp': timestamp.isoformat(), **outcome}
    if observer is not None and legacy:
        observer.legacy(row)
    policy.update(cid, qid, difficulty, timestamp, outcome['y'] if label is None else label, prediction)
    return row


def test_control_observed_native_identity_state_and_call_equivalence():
    control_registry, control, env0, _, _ = setup()
    one_event(control, env0)
    registry, policy, env, observer, sink = setup()
    methods_before = (SpyPolicy.select, SpyPolicy.ready_set, SpyPolicy.predict, SpyPolicy.update)
    with observer:
        legacy = one_event(policy, env, observer)
    observer.finish(expected_rows=1, expected_steps=1)
    assert type(policy) is SpyPolicy and type(env) is SpyEnvironment
    assert fingerprint(vars(control)) == fingerprint(vars(policy))
    assert fingerprint(vars(env0)) == fingerprint(vars(env))
    assert control_registry.summaries() == registry.summaries()
    assert methods_before == (SpyPolicy.select, SpyPolicy.ready_set, SpyPolicy.predict, SpyPolicy.update)
    row = json.loads(sink.getvalue())
    assert row['mastered_decisions'] == {'a': True, 'b': False}
    assert row['ready_set'] == ['a'] and row['eligible_candidates'] == ['b']
    assert row['balanced_candidates'] == ['b'] and row['served_tuple']['question'] == legacy['question']
    assert len(row['mastery_score_calls']) == 1 and row['full_mastery_score_vector_available'] is False
    assert row['select_timestamp_argument'] is None and row['is_served_in_simulator'] is True
    assert row['phases'] == ['before_selection', 'after_selection_bookkeeping', 'before_predict',
        'after_predict', 'before_environment_interact', 'after_environment_interact', 'legacy_written',
        'before_update', 'after_update']
    assert observer.calls == {'select': 1, 'ready_set': 1, 'is_mastered': 2,
                             'mastery_score': 1, 'predict': 1, 'interact': 1, 'update': 1}
    assert policy.calls == control.calls and sys.getprofile() is None


def test_two_events_current_label_only_enters_existing_update():
    _, policy, env, observer, _ = setup()
    with observer:
        one_event(policy, env, observer)
        one_event(policy, env, observer, step=1)
    observer.finish(expected_rows=2, expected_steps=2)
    assert policy.labels == [1, 1] and [r['prediction'] for r in observer.rows] == [0.5, 0.5]


def test_existing_profiler_rejected_without_replacing_it():
    _, _, _, observer, _ = setup()
    hook = lambda *args: None
    sys.setprofile(hook)
    try:
        with pytest.raises(RuntimeError, match='existing profiler'):
            with observer:
                pass
        assert sys.getprofile() is hook
    finally:
        sys.setprofile(None)


@pytest.mark.parametrize('kind', ['query', 'label', 'legacy'])
def test_pairing_guards_stop_and_restore_profile(kind):
    _, policy, env, observer, _ = setup()
    with pytest.raises(ValueError):
        with observer:
            one_event(policy, env, observer, query_override=kind == 'query',
                      label=0 if kind == 'label' else None, legacy=kind != 'legacy')
    assert sys.getprofile() is None


def test_missing_mastery_coverage_is_not_filled_with_extra_calls():
    class Incomplete(SpyPolicy):
        def ready_set(self):
            self.is_mastered('a')
            return ['a']
    _, policy, _, observer, _ = setup(Incomplete)
    with pytest.raises(ValueError, match='coverage missing'):
        with observer:
            policy.select()
    assert policy.calls['is_mastered'] == 1 and not observer.rows


def test_deadline_fails_before_first_spy_selection_body():
    _, policy, _, observer, _ = setup(deadline=0)
    with pytest.raises(TimeoutError):
        with observer:
            policy.select()
    assert policy.calls['select'] == 0 and sys.getprofile() is None


def test_row_limit_stops_before_second_selection_body():
    _, policy, env, observer, _ = setup(max_rows=1)
    with pytest.raises(ValueError, match='overbudget'):
        with observer:
            one_event(policy, env, observer)
            one_event(policy, env, observer, step=1)
    assert policy.calls['select'] == 1 and len(observer.rows) == 1


def test_finish_rejects_partial_update_and_missing_trajectories():
    _, policy, _, observer, _ = setup()
    with observer:
        policy.select()
    with pytest.raises(ValueError, match='incomplete'):
        observer.finish(expected_rows=1, expected_steps=1)


def test_registry_preserves_return_identity_and_rejects_duplicate_or_wrong_flag():
    registry = ConstructorRegistry()
    registry.begin(20000, 'PG')
    factory = registry.policy_factory(SpyPolicy)
    native = factory(False)
    assert registry.policies[(20000, 'PG', 'graph_free')] is native
    with pytest.raises(ValueError, match='duplicate'):
        factory(False)
    with pytest.raises(ValueError):
        factory(0)
    with pytest.raises(ValueError):
        registry.policy_factory(SpyPolicy, empty=True)(False)


def test_unregistered_instance_is_rejected():
    _, _, _, observer, _ = setup()
    other = SpyPolicy(False)
    with pytest.raises(ValueError, match='unregistered'):
        with observer:
            other.select()


def test_unknown_state_rejected_without_invoking_object_serialization():
    class Forbidden:
        def __repr__(self):
            raise AssertionError('must not invoke arbitrary repr')
    with pytest.raises(TypeError):
        primitive({'unexpected': Forbidden()})


def test_exact_float_no_tolerance_and_type_coercion():
    assert exact(0.5, 0.5)
    assert not exact(0.0, -0.0) and not exact(1, True) and not exact(0.5, 0.5000000000000001)


def test_trace_sink_requires_exact_population_and_does_not_repair():
    value = {'seed': 1, 'profile': 'PG', 'variant': 'graph_free', 'step': 0, 'prediction': 0.5}
    sink = TraceSink(io.StringIO(), {(1, 'PG', 'graph_free', 0): value}, lambda: None)
    sink.write(json.dumps(value))
    with pytest.raises(ValueError):
        sink.write(json.dumps(value))
    value['prediction'] += 0.01
    fresh = TraceSink(io.StringIO(), {(1, 'PG', 'graph_free', 0): {**value, 'prediction': 0.5}}, lambda: None)
    with pytest.raises(ValueError):
        fresh.write(json.dumps(value))


def test_fresh_output_disallows_outside_and_existing_without_writes():
    with pytest.raises(ValueError):
        fresh_output(Path.cwd())
    with pytest.raises(ValueError):
        fresh_output(Path(__file__).resolve())


def test_cli_import_cannot_dispatch_model_without_explicit_flag(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['runner', '--output', 'unused', '--source-inventory', 'unused',
                                     '--source-inventory-sha256', '0' * 64])
    with pytest.raises(ValueError, match='not authorized'):
        main()
