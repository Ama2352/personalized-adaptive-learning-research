"""Fast revision spies: exact metadata equivalence, no native Paper2/replay/RNG."""
import io
import json
from pathlib import Path
import sys
import time
import types

import pytest

from closed_loop_observer import ProfileObserver as OriginalObserver, ConstructorRegistry as OriginalRegistry
from closed_loop_observer_fast import ProfileObserver, ConstructorRegistry, make_profile_dispatch
from run_closed_loop_reconstruction_fast import write_phase_receipt, CAP, OVERALL_CAP
from test_closed_loop_observer import SpyPolicy, SpyEnvironment, one_event


def setup(registry_type=ConstructorRegistry, observer_type=ProfileObserver):
    registry = registry_type()
    registry.begin(20000, 'PG')
    environment = registry.environment_factory(SpyEnvironment)({'a': 0.0})
    policy = registry.policy_factory(SpyPolicy)(False)
    methods = {name: [getattr(SpyPolicy, name)] for name in
               ('select', 'ready_set', 'is_mastered', 'mastery_score', 'predict', 'update')}
    methods['interact'] = [SpyEnvironment.interact]
    sink = io.StringIO()
    observer = observer_type(registry, methods, ['a', 'b'], sink,
                             deadline=time.perf_counter() + 10, max_rows=3, max_steps=3)
    return registry, policy, environment, observer, sink


def test_exact_slow_fast_payload_and_state_equivalence_all_fields_retained():
    artifacts = []
    for registry_type, observer_type in [(OriginalRegistry, OriginalObserver), (ConstructorRegistry, ProfileObserver)]:
        registry, policy, environment, observer, sink = setup(registry_type, observer_type)
        with observer:
            one_event(policy, environment, observer)
            one_event(policy, environment, observer, step=1)
        observer.finish(expected_rows=2, expected_steps=2)
        artifacts.append((sink.getvalue(), registry.summaries(), dict(observer.calls)))
    assert artifacts[0] == artifacts[1]
    rows = [json.loads(v) for v in artifacts[1][0].splitlines()]
    for row in rows:
        assert row['ready_set'] == ['a'] and row['eligible_candidates'] == ['b']
        assert row['mastered_decisions'] == {'a': True, 'b': False}
        assert row['state_before_selection_sha256'] and row['state_after_selection_sha256']
        assert row['state_after_update_sha256'] and row['legacy_row_sha256']


def test_fast_dispatch_does_not_call_clock_or_native_handler_on_unrelated_frames():
    _, _, _, observer, _ = setup()
    def forbidden():
        raise AssertionError('unrelated callback must be rejected before clock')
    observer.clock = forbidden
    with observer:
        assert json.loads(json.dumps({'x': [1, 2, 3]})) == {'x': [1, 2, 3]}
    assert not observer.calls


def test_same_code_other_globals_rejected_before_native_body():
    _, policy, _, observer, _ = setup()
    original = SpyPolicy.predict
    clone = types.FunctionType(original.__code__, dict(original.__globals__), original.__name__)
    with pytest.raises(ValueError, match='globals drift'):
        with observer:
            clone(policy, 'b', 'b-q', 1200.0, None)
    assert policy.calls['predict'] == 0 and sys.getprofile() is None


def test_instance_cache_preserves_identity_and_rejects_registry_tamper():
    registry, policy, environment, observer, _ = setup()
    assert registry.policy_key(policy) == (20000, 'PG', 'graph_free')
    assert registry.environment_key(environment) == (20000, 'PG', 'graph_free')
    del registry.policies[(20000, 'PG', 'graph_free')]
    with pytest.raises(ValueError, match='unregistered'):
        with observer:
            policy.select()
    assert policy.calls['select'] == 0


@pytest.mark.parametrize('kind', ['query', 'label', 'legacy'])
def test_fast_pairing_guards_not_relaxed(kind):
    _, policy, environment, observer, _ = setup()
    with pytest.raises(ValueError):
        with observer:
            one_event(policy, environment, observer, query_override=kind == 'query',
                      label=0 if kind == 'label' else None, legacy=kind != 'legacy')
    assert sys.getprofile() is None


def test_fast_outer_dispatch_same_uniforms_and_profiler_restore():
    def outer(seed, profile, uniforms):
        return len(uniforms)
    captured = []
    hook = make_profile_dispatch(outer, captured)
    assert sys.getprofile() is None
    sys.setprofile(hook)
    try:
        assert outer(20000, 'PG', [0.1, 0.2]) == 2
    finally:
        sys.setprofile(None)
    assert len(captured) == 1 and captured[0]['seed'] == 20000 and captured[0]['profile'] == 'PG'


def test_phase_receipt_persists_completed_control_without_claiming_final_parity(tmp_path):
    # Fabricated bounded test metadata, explicitly not a native phase result.
    summary = {'pass': 'control', 'legacy_rows': 3240, 'outcome_rows': 27,
               'native_state_fingerprints': [{'test_fixture': True}] * 27,
               'uniform_fingerprints': [{'test_fixture': True}] * 9}
    for suffix in ('legacy', 'metadata'):
        (tmp_path / ('control_' + suffix + '.jsonl.gz')).write_bytes(b'SYNTHETIC_UNIT_TEST_BYTES_NOT_NATIVE_GZIP')
    result = write_phase_receipt(tmp_path, 'control', summary, 0.5, '0' * 64)
    assert json.loads((tmp_path / 'control_phase.json').read_text()) == result
    assert result['overall_control_observed_final_parity_accepted'] is False
    with pytest.raises(FileExistsError):
        write_phase_receipt(tmp_path, 'control', summary, 0.5, '0' * 64)
    summary['legacy_rows'] = 1
    with pytest.raises(ValueError):
        write_phase_receipt(tmp_path, 'control', summary, 0.5, '0' * 64)
    assert CAP == 300 and OVERALL_CAP == 430


def test_existing_profiler_not_replaced_by_fast_observer():
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
