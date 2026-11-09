"""Sáu fixture thuần stdlib, không Paper2/model/world/cache thật.

Candidate chỉ nạp sibling recorder. Không cài hoặc áp dụng canonical module.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import copy
import math
import random
import unittest

from knowledge_tracing.gam_kt.native_panel_observer import (
    NativePanelRecorder as Recorder, PanelObserverError as PanelError,
)
CONCEPTS = ("a", "b", "c")
STAMP = "2026-01-01T06:00:00+00:00"
NATIVE_CALLS = []


@dataclass
class State:
    theta: float = 1250.0
    pi_task: float = 0.55
    pi_time: float = 0.05
    attempts: int = 0
    last_timestamp: datetime | None = None


class Selector:
    def ready_set(self):
        NATIVE_CALLS.append(("ready_set",))
        unmastered = [cid for cid in CONCEPTS if not self.is_mastered(cid)]
        # Các parent calls lặp/fallback ngoài first pass không tạo thêm rows.
        self.is_mastered("a")
        self.is_mastered("a")
        return unmastered or list(CONCEPTS)


class Policy(Selector):
    def __init__(self):
        self.states = {cid: State() for cid in CONCEPTS}

    def is_mastered(self, cid):
        NATIVE_CALLS.append(("is_mastered", cid))
        state = self.states[cid]
        return state.theta >= 1250.0 and state.pi_task <= 0.55

    def select(self):
        return self.ready_set()[0]


class NativePanelTests(unittest.TestCase):
    def test_existing_calls_passthrough_fallback_and_immutable_rows(self):
        for unmastered in (False, True):
            with self.subTest(unmastered=unmastered):
                policy = Policy()
                if unmastered:
                    policy.states["b"].theta = 1200.0
                NATIVE_CALLS.clear()
                expected = policy.select()
                control_calls = tuple(NATIVE_CALLS)
                NATIVE_CALLS.clear()
                before, rng = copy.deepcopy(vars(policy)), random.getstate()
                class_before = dict(vars(Policy))
                recorder = Recorder(policy, CONCEPTS)
                with recorder.capture(step=0, timestamp=STAMP):
                    self.assertEqual(policy.select(), expected)
                self.assertEqual(tuple(NATIVE_CALLS), control_calls)
                self.assertEqual(recorder.mastery_calls, 5)
                self.assertEqual(recorder.ready_calls, 1)
                self.assertEqual(tuple(r.concept for r in recorder.latest.rows), CONCEPTS)
                self.assertEqual(vars(policy), before)
                self.assertEqual(random.getstate(), rng)
                self.assertEqual(dict(vars(Policy)), class_before)
                self.assertTrue(recorder.restored)
                with self.assertRaises(AttributeError):
                    recorder.latest.rows[0].theta = 0.0

    def test_binary64_thresholds_stored_pi_and_timestamp_are_separate(self):
        policy = Policy()
        policy.states["a"].theta = math.nextafter(1250.0, -math.inf)
        policy.states["b"].pi_task = math.nextafter(0.55, math.inf)
        policy.states["c"].last_timestamp = datetime(2026, 1, 2, tzinfo=timezone.utc)
        before = copy.deepcopy(policy.states)
        recorder = Recorder(policy, CONCEPTS)
        with recorder.capture(step=1, timestamp=STAMP):
            policy.select()
        rows = recorder.latest.rows
        self.assertEqual([(r.theta_gate, r.stored_pi_gate, r.native_M) for r in rows],
                         [(False, True, False), (True, False, False), (True, True, True)])
        self.assertIsNone(rows[0].last_timestamp)
        self.assertEqual(rows[2].last_timestamp, "2026-01-02T00:00:00+00:00")
        self.assertEqual(policy.states, before)

    def test_invalid_first_pass_and_caught_errors_never_publish(self):
        for order in (("a", "b"), ("a", "a", "c"), ("b", "a", "c")):
            with self.subTest(order=order):
                class Bad(Policy):
                    def ready_set(self):
                        return [cid for cid in order if not self.is_mastered(cid)]
                policy = Bad()
                originals = dict(vars(Bad))
                recorder = Recorder(policy, CONCEPTS)
                with self.assertRaises(PanelError):
                    with recorder.capture(step=0, timestamp=STAMP):
                        # Dù caller bắt lỗi từ wrapper, ticket vẫn bị đánh dấu invalid.
                        try:
                            policy.select()
                        except PanelError:
                            pass
                self.assertIsNone(recorder.latest)
                self.assertTrue(recorder.restored)
                self.assertEqual(dict(vars(Bad)), originals)
        class Wrong(Policy):
            def is_mastered(self, cid):
                return False
        recorder = Recorder(Wrong(), CONCEPTS)
        with self.assertRaises(PanelError):
            with recorder.capture(step=0, timestamp=STAMP):
                recorder.policy.select()
        self.assertIsNone(recorder.latest)
        self.assertTrue(recorder.restored)

    def test_partial_install_restores_inherited_descriptor_absence(self):
        class FailSetter(type):
            fail = True
            def __setattr__(cls, name, value):
                super().__setattr__(name, value)
                if name == "is_mastered" and type(cls).fail:
                    type(cls).fail = False
                    raise RuntimeError("setter ghi rồi lỗi")
        class Late(Policy, metaclass=FailSetter):
            pass
        before = dict(vars(Late))
        recorder = Recorder(Late(), CONCEPTS)
        with self.assertRaisesRegex(RuntimeError, "setter ghi rồi lỗi"):
            with recorder.capture(step=0, timestamp=STAMP):
                self.fail("Body không được chạy")
        self.assertEqual(dict(vars(Late)), before)
        self.assertTrue(recorder.restored)
        self.assertFalse(recorder.cleanup_errors)
        self.assertIsNone(recorder.latest)

    def test_body_cancellation_preserves_primary_and_retries_cleanup_only(self):
        class FailDelete(type):
            fail = False
            def __delattr__(cls, name):
                if name == "is_mastered" and type(cls).fail:
                    raise OSError("cleanup lỗi")
                super().__delattr__(name)
        class Owned(Policy, metaclass=FailDelete):
            pass
        before = dict(vars(Owned))
        recorder = Recorder(Owned(), CONCEPTS)
        primary = KeyboardInterrupt("body bị hủy")
        try:
            with self.assertRaises(KeyboardInterrupt) as caught:
                with recorder.capture(step=0, timestamp=STAMP):
                    recorder.policy.select()
                    FailDelete.fail = True
                    raise primary
            self.assertIs(caught.exception, primary)
            self.assertIsNone(recorder.latest)
            self.assertEqual(recorder.pending_attributes, ("is_mastered",))
            self.assertEqual(recorder.cleanup_errors[0][0], "is_mastered")
            self.assertNotIn("ready_set", vars(Owned))
        finally:
            FailDelete.fail = False
            recorder.restore()
        self.assertTrue(recorder.restored)
        self.assertEqual(dict(vars(Owned)), before)

    def test_ticket_scope_no_stale_frame_and_preflight_no_mutations(self):
        policy = Policy()
        recorder = Recorder(policy, CONCEPTS)
        with recorder.capture(step=0, timestamp=STAMP):
            # Getter ngoài ready_set không được dùng để điền panel.
            policy.is_mastered("c")
            policy.select()
            policy.is_mastered("a")
        self.assertEqual(len(recorder.latest.rows), 3)
        self.assertEqual(recorder.mastery_calls, 7)
        before = copy.deepcopy(vars(policy))
        for step, stamp in ((True, STAMP), (120, STAMP), (1, "2026-01-01")):
            with self.subTest(step=step, stamp=stamp):
                with self.assertRaises(ValueError):
                    with recorder.capture(step=step, timestamp=stamp):
                        self.fail("Không được vào body")
                self.assertIsNone(recorder.latest)
                self.assertTrue(recorder.restored)
                self.assertEqual(vars(policy), before)
        with self.assertRaises(PanelError):
            with recorder.capture(step=2, timestamp=STAMP):
                policy.is_mastered("a")
        self.assertIsNone(recorder.latest)
        with self.assertRaises(PanelError):
            Recorder(policy, ("a", "a", "c"))


if __name__ == "__main__":
    unittest.main()
