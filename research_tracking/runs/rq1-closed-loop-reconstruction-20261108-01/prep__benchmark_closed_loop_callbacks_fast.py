"""Pure deterministic callback-overhead workload; no native model/replay/RNG."""
import json
import sys
import time

from closed_loop_observer import fingerprint
from closed_loop_observer_fast import make_profile_dispatch
from test_closed_loop_observer_fast import setup


def unrelated_workload(rounds):
    accumulator = 0
    for index in range(rounds):
        value = {'index': index, 'values': [index, index + 1, index + 2]}
        encoded = json.dumps(value, sort_keys=True)
        accumulator += sum(json.loads(encoded)['values'])
    return accumulator


def benchmark(rounds=1000, *, deadline):
    if type(rounds) is not int or not 1 <= rounds <= 1000 or sys.getprofile() is not None:
        raise ValueError('bounded rounds/no existing profiler required')
    def outer(seed, profile, uniforms):
        return unrelated_workload(rounds)
    records = []
    expected = None
    for mode in ('baseline', 'original_all_event_dispatch', 'fast_code_ID_prefilter'):
        if time.perf_counter() > deadline:
            raise TimeoutError('10s spy/benchmark cumulative limit')
        _, _, _, fast_observer, _ = setup()
        from test_closed_loop_observer_fast import setup as create
        from closed_loop_observer import ConstructorRegistry, ProfileObserver
        _, _, _, original_observer, _ = create(ConstructorRegistry, ProfileObserver)
        uniforms = []
        def original_capture(frame, event, arg):
            if frame.f_code is outer.__code__ and event == 'return':
                uniforms.append({'seed': frame.f_locals['seed'], 'profile': frame.f_locals['profile'],
                                 'uniforms_sha256': fingerprint(frame.f_locals['uniforms'])})
            original_observer._callback(frame, event, arg)
        hook = None if mode == 'baseline' else (original_capture if mode == 'original_all_event_dispatch'
                                                else make_profile_dispatch(outer, uniforms, fast_observer))
        start = time.perf_counter()
        if hook is not None:
            sys.setprofile(hook)
        try:
            value = outer(20000, 'PG', [0.1, 0.2])
        finally:
            sys.setprofile(None)
        elapsed = time.perf_counter() - start
        if time.perf_counter() > deadline:
            raise TimeoutError('10s spy/benchmark cumulative limit')
        if expected is None:
            expected = value
        if value != expected or original_observer.calls or fast_observer.calls:
            raise AssertionError('pure-workload equivalence/native-call guard')
        records.append({'mode': mode, 'rounds': rounds, 'elapsed_seconds': elapsed,
                        'deterministic_result': value, 'uniform_fingerprints': uniforms,
                        'native_model_calls': 0})
    if records[1]['uniform_fingerprints'] != records[2]['uniform_fingerprints']:
        raise AssertionError('outer return capture changed')
    return {'kind': 'SYNTHETIC_CALLBACK_OVERHEAD_NOT_NATIVE_RUNTIME_FORECAST', 'records': records,
            'native_model_calls': 0, 'optimizer_steps': 0,
            'limit_vi': 'Workload chỉ json/list/int cố định; không dự báo replay300s sẽ đủ hoặc RQ efficacy.'}
