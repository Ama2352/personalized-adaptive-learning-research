"""Revision hiệu năng: giữ nguyên payload/phase observer, dispatch bằng code/instance ID."""
import time

from closed_loop_observer import (ConstructorRegistry as OriginalRegistry,
                                  ProfileObserver as OriginalObserver,
                                  fingerprint)


class ConstructorRegistry(OriginalRegistry):
    def __init__(self):
        super().__init__()
        self._policy_keys = {}
        self._environment_keys = {}

    def policy_factory(self, cls, *, empty=False):
        original = super().policy_factory(cls, empty=empty)
        def construct(flag):
            instance = original(flag)
            key = (*self.current, 'empty_graph_package' if empty else
                   ('graph_package' if flag else 'graph_free'))
            self._policy_keys[id(instance)] = key
            return instance
        return construct

    def environment_factory(self, cls):
        original = super().environment_factory(cls)
        def construct(base):
            instance = original(base)
            key = next(key for key, value in self.environments.items() if value is instance)
            self._environment_keys[id(instance)] = key
            return instance
        return construct

    def policy_key(self, instance):
        key = self._policy_keys.get(id(instance))
        return key if key is not None and self.policies.get(key) is instance else None

    def environment_key(self, instance):
        key = self._environment_keys.get(id(instance))
        return key if key is not None and self.environments.get(key) is instance else None


class ProfileObserver(OriginalObserver):
    """Original _observe/primitive/fingerprint/phase checks are inherited verbatim."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._code_bindings = {}
        for (code, globals_id), name in self.bindings.items():
            self._code_bindings.setdefault(id(code), {})[globals_id] = name
        self.code_ids = frozenset(self._code_bindings)

    def _callback(self, frame, event, arg):
        if event not in ('call', 'return'):
            return
        code_id = id(frame.f_code)
        if code_id not in self.code_ids:
            return
        self.observe_matched(frame, event, arg, code_id)

    def observe_matched(self, frame, event, arg, code_id):
        try:
            if event not in ('call', 'return') or code_id != id(frame.f_code):
                raise ValueError('matched frame identity drift')
            name = self._code_bindings[code_id].get(id(frame.f_globals))
            if name is None:
                raise ValueError('matched native code globals drift')
            if self.clock() > self.deadline:
                raise TimeoutError('observer cumulative deadline')
            self._observe(name, frame, event, arg)
        except BaseException as exc:
            self.failure = type(exc).__name__ + ': ' + str(exc)
            raise


def make_profile_dispatch(function, uniform_hashes, observer=None):
    """No native callbacks/hash/clock for unrelated Python or C frames."""
    outer_code_id = id(function.__code__)
    outer_globals_id = id(function.__globals__)
    native_code_ids = observer.code_ids if observer is not None else frozenset()
    def capture(frame, event, arg):
        if event not in ('call', 'return'):
            return
        code_id = id(frame.f_code)
        if code_id == outer_code_id and event == 'return':
            if id(frame.f_globals) != outer_globals_id:
                raise ValueError('outer frame globals drift')
            uniform_hashes.append({'seed': frame.f_locals['seed'], 'profile': frame.f_locals['profile'],
                                   'uniforms_sha256': fingerprint(frame.f_locals['uniforms'])})
        if code_id in native_code_ids:
            observer.observe_matched(frame, event, arg, code_id)
    return capture
