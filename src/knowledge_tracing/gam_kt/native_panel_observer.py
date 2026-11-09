"""Ghi first-pass native M từ getter sẵn có, không gọi lại policy hoặc world.

Candidate cho gam_kt/native_panel_observer.py. Caller giữ trách nhiệm nguồn,
quyền chạy và timestamp. Module không cấp research authority hoặc latent truth.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import math
from types import FunctionType


class PanelObserverError(ValueError):
    """Panel không đầy đủ hoặc hợp đồng observer không còn đúng."""


@dataclass(frozen=True)
class NativeConceptState:
    concept: str
    theta: float
    pi_task_stored: float
    pi_time_stored: float
    attempts: int
    last_timestamp: str | None
    theta_gate: bool
    stored_pi_gate: bool
    native_M: bool


@dataclass(frozen=True)
class NativePanel:
    step: int
    timestamp: str
    rows: tuple[NativeConceptState, ...]


class NativePanelRecorder:
    """Một capture bao quanh đúng một select thật trên một policy sở hữu riêng.

    Chỉ hai method attributes trên class của policy được thay tạm. Không ghi
    instance, không thêm getter/predict hoặc global profiler. Không thread-safe.
    `latest` chỉ có giá trị khi body, first pass và cleanup đều hoàn tất.
    """
    def __init__(self, policy, concepts):
        if (type(concepts) is not tuple or not 1 <= len(concepts) <= 28
                or any(type(c) is not str or not c or len(c) > 256 for c in concepts)
                or len(set(concepts)) != len(concepts)):
            raise PanelObserverError("Cần tuple concept duy nhất, tối đa28")
        if type(policy.states) is not dict or set(policy.states) != set(concepts):
            raise PanelObserverError("State phải là dict đã có đủ đúng concept")
        self.policy, self.concepts, self.cls = policy, concepts, type(policy)
        self._originals = {}
        for name in ("ready_set", "is_mastered"):
            original = getattr(self.cls, name)
            if name in vars(policy) or type(original) is not FunctionType:
                raise PanelObserverError("Chỉ hỗ trợ method function gốc, không instance shadow")
            self._originals[name] = (name in vars(self.cls), vars(self.cls).get(name), original)
        self._installed = []
        self._active = False
        self._inside_ready = False
        self._invalid = False
        self._rows = []
        self.latest = None
        self.cleanup_errors = []
        self.ready_calls = self.mastery_calls = 0

    def _require(self, condition, message):
        if not condition:
            self._invalid = True
            raise PanelObserverError(message)

    def _originals_match(self):
        return all((name in vars(self.cls)) == present
                   and (not present or vars(self.cls)[name] is local)
                   and getattr(self.cls, name) is original
                   for name, (present, local, original) in self._originals.items())

    def restore(self):
        """Thử mọi attribute theo thứ tự ngược, giữ lỗi để caller kiểm tra."""
        pending, errors = [], []
        for name in reversed(self._installed):
            present, local, original = self._originals[name]
            try:
                if present:
                    setattr(self.cls, name, local)
                elif name in vars(self.cls):
                    delattr(self.cls, name)
                if ((name in vars(self.cls)) != present
                        or present and vars(self.cls)[name] is not local
                        or getattr(self.cls, name) is not original):
                    raise PanelObserverError("Attribute chưa được phục hồi")
            except BaseException as error:
                pending.append(name)
                errors.append((name, type(error).__name__, str(error)))
        self._installed = [name for name in self._installed if name in pending]
        self.cleanup_errors.extend(errors)
        return tuple(errors)

    @property
    def restored(self):
        return not self._installed and self._originals_match()

    @property
    def pending_attributes(self):
        return tuple(self._installed)

    def _record(self, concept, returned):
        self._require(concept == self.concepts[len(self._rows)], "First pass phải đúng thứ tự, không trùng")
        self._require(type(self.policy.states) is dict and set(self.policy.states) == set(self.concepts),
                      "Inventory state đã thay đổi")
        state = self.policy.states[concept]
        theta, task, time = state.theta, state.pi_task, state.pi_time
        self._require(all(type(v) is float and math.isfinite(v) for v in (theta, task, time)),
                      "Theta/pi phải là binary64 hữu hạn")
        self._require(0 <= task <= 1 and 0 <= time <= 1 and type(state.attempts) is int and state.attempts >= 0,
                      "Pi/attempts ngoài miền")
        previous = state.last_timestamp
        self._require(previous is None or isinstance(previous, datetime), "Last timestamp phải là datetime hoặc null")
        theta_gate, pi_gate = theta >= 1250.0, task <= 0.55
        self._require(type(returned) is bool and returned == (theta_gate and pi_gate),
                      "Native M không khớp literal theta/stored-pi predicate")
        self._rows.append(NativeConceptState(concept, theta, task, time, state.attempts,
            None if previous is None else previous.isoformat(), theta_gate, pi_gate, returned))

    def _install(self):
        self._require(self._originals_match(), "Original method attributes đã thay đổi")
        ready = self._originals["ready_set"][2]
        mastered = self._originals["is_mastered"][2]

        def ready_wrapper(instance, *args, **kwargs):
            self._require(instance is self.policy and self._active, "Sai policy hoặc ticket")
            self.ready_calls += 1
            self._require(self.ready_calls == 1 and not self._inside_ready, "Chỉ một ready_set trong capture")
            self._inside_ready = True
            try:
                result = ready(instance, *args, **kwargs)
                self._require(len(self._rows) == len(self.concepts), "Ready first pass thiếu concept")
                return result
            except BaseException:
                self._invalid = True
                raise
            finally:
                self._inside_ready = False

        def mastered_wrapper(instance, *args, **kwargs):
            self._require(instance is self.policy and self._active, "Sai policy hoặc ticket")
            self.mastery_calls += 1
            try:
                result = mastered(instance, *args, **kwargs)
                if self._inside_ready and len(self._rows) < len(self.concepts):
                    concept = args[0] if args else kwargs["cid"]
                    self._record(concept, result)
                return result
            except BaseException:
                self._invalid = True
                raise

        try:
            for name, wrapper in (("ready_set", ready_wrapper), ("is_mastered", mastered_wrapper)):
                # Đăng ký trước setter vì setter có thể mutate rồi raise.
                self._installed.append(name)
                setattr(self.cls, name, wrapper)
        except BaseException:
            self.restore()
            raise

    @contextmanager
    def capture(self, *, step, timestamp):
        self.latest = None
        if self._active or self._installed:
            raise PanelObserverError("Capture đang chạy hoặc cleanup còn pending")
        if (type(step) is not int or not 0 <= step < 120 or type(timestamp) is not str
                or not 1 <= len(timestamp) <= 64):
            raise PanelObserverError("Caller step/time không hợp lệ")
        if datetime.fromisoformat(timestamp).tzinfo is None:
            raise PanelObserverError("Scientific timestamp cần timezone")
        self.cleanup_errors = []
        self._rows = []
        self.ready_calls = self.mastery_calls = 0
        self._invalid = False
        self._active = True
        primary = None
        try:
            self._install()
            yield self
            self._require(not self._invalid and self.ready_calls == 1 and len(self._rows) == len(self.concepts),
                          "Capture không có một panel hoàn tất")
        except BaseException as error:
            primary = error
            raise
        finally:
            cleanup = self.restore()
            self._active = self._inside_ready = False
            if cleanup and primary is None:
                raise PanelObserverError("Cleanup thất bại, xem cleanup_errors")
        self.latest = NativePanel(step, timestamp, tuple(self._rows))
