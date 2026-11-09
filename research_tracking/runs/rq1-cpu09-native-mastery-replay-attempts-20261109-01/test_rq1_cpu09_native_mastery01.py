"""Fixtures stdlib cho orchestration, không Paper2/NumPy/Pandas/cache."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import replay_rq1_cpu09_native_mastery01 as replay


SEEDS = (1,)
PROFILES = ('PG',)
QUESTIONS = {'q': dict(concept='c', difficulty=1200.)}


class FakePolicy:
    def __init__(self, events):
        self.events = events
        self.states = {'c': SimpleNamespace(theta=1250., pi_task=.5, pi_time=.05, attempts=0)}
        self.previous_y = 0
        self.selected = 0

    def select(self):
        self.events.append('select')
        self.selected += 1
        return ('c', 'q', 1200.)

    def predict(self, cid, qid, difficulty, timestamp):
        if self.selected != self.states['c'].attempts + 1:
            raise AssertionError('missing or duplicated selector sideeffect')
        self.events.append('predict')
        return .25 if self.previous_y == 0 else .75

    def _decayed_pi(self, cid, timestamp):
        self.events.append('decayed')
        return .9, .8, {}

    def is_mastered(self, cid):
        self.events.append('M')
        state = self.states[cid]
        return state.theta >= 1250. and state.pi_task <= .55

    def update(self, cid, qid, difficulty, timestamp, y, prediction):
        if self.events[-1] != 'M':
            raise AssertionError('current label update before native readout')
        self.events.append('update')
        self.previous_y = y
        self.states[cid].attempts += 1


def fixtures():
    return {(1, 'PG', g, m): (
        dict(step=0, concept='c', question='q', prediction=.25, y=1, theta_before=1250.),
        dict(step=1, concept='c', question='q', prediction=.75, y=0, theta_before=1249.),
    ) for g in (False, True) for m in (False, True)}


def timestamp(offset):
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=offset)


class CPU09MasteryReplayTests(unittest.TestCase):
    def execute(self, buckets=None, factory=None, verify_after=lambda: None):
        self.events = []
        return replay.replay_then_evaluate(fixtures() if buckets is None else buckets,
            seeds=SEEDS, profiles=PROFILES, steps=2, questions=QUESTIONS,
            policy_factory=factory or (lambda *, graph_on: FakePolicy(self.events)),
            timestamp_factory=timestamp, verify_after=verify_after)

    def test_clock_exact_step_zero_28_56_and_later_boundary(self):
        values = replay.clock_hours(120)
        for step, hours in ((0, 6), (27, 168), (28, 240), (55, 402), (56, 474), (84, 708)):
            with self.subTest(step=step):
                self.assertEqual(values[step], hours)
        self.assertEqual([i for i in range(1, 120) if values[i] - values[i-1] == 72], [28, 56, 84, 112])

    def test_full_matched_parity_all_four_arms_and_calls(self):
        result = self.execute()
        self.assertEqual(result['parity']['calls'], dict(estimator_constructors=4, select=8,
            predict=8, native_capture=8, update=8))
        self.assertEqual((len(result['evaluated']), len(result['groups'])), (8, 12))
        self.assertEqual([r['source_true_M'] for r in result['evaluated']], [True, False]*4)
        for row in result['groups']:
            self.assertEqual((row['rows'], row['M_TP'], row['M_FP'], row['M_FN'], row['M_TN']), (2, 1, 1, 0, 0))

    def test_label_update_follows_preupdate_prediction_and_readout(self):
        result = self.execute()
        self.assertEqual(self.events, ['select', 'predict', 'decayed', 'M', 'update']*8)
        self.assertEqual([r['prediction'] for r in result['evaluated']], [.25, .75]*4)

    def test_stored_and_decayed_pi_stay_distinct(self):
        result = self.execute()
        row = result['evaluated'][0]
        self.assertEqual((row['pi_task_stored'], row['pi_task_decayed']), (.5, .9))
        self.assertIs(row['native_M'], True)

    def test_only_graph_switch_is_sent_to_policy_factory(self):
        received = []
        def factory(**kwargs):
            received.append(kwargs)
            return FakePolicy(self.events)
        self.execute(factory=factory)
        self.assertEqual(received, [dict(graph_on=False)]*2 + [dict(graph_on=True)]*2)

    def test_projection_never_accesses_truth_or_extra_latent_fields(self):
        class TruthTrap(dict):
            def __getitem__(self, key):
                if key not in replay.OBSERVABLE_FIELDS:
                    raise AssertionError('truth accessed during projection')
                return super().__getitem__(key)
        source = {key: tuple(TruthTrap(row, latent_vector='not for estimator') for row in rows)
                  for key, rows in fixtures().items()}
        projected = replay.observable_histories(source, seeds=SEEDS, profiles=PROFILES, steps=2)
        self.assertTrue(all(set(row) == replay.OBSERVABLE_FIELDS for rows in projected.values() for row in rows))

    def test_truth_join_only_after_all_streams_and_revalidated_sources(self):
        permission = {'truth': False, 'reads': 0}
        class TruthTrap(dict):
            def __getitem__(self, key):
                if key == 'theta_before':
                    if not permission['truth']:
                        raise AssertionError('truth interpreted before full parity/source recheck')
                    permission['reads'] += 1
                return super().__getitem__(key)
        buckets = {key: tuple(TruthTrap(row) for row in rows) for key, rows in fixtures().items()}
        def verified():
            self.assertEqual(self.events.count('update'), 8)
            permission['truth'] = True
        self.execute(buckets=buckets, verify_after=verified)
        self.assertGreater(permission['reads'], 0)

    def test_last_stream_probability_mismatch_blocks_all_truth_acceptance(self):
        buckets = fixtures()
        buckets[(1, 'PG', True, True)][1]['prediction'] = .7500000000000001
        with patch.object(replay, 'attach_truth_and_group', side_effect=AssertionError('must not read truth')) as truth:
            with self.assertRaisesRegex(ValueError, 'probability bits'):
                self.execute(buckets=buckets)
            truth.assert_not_called()
        self.assertEqual(self.events.count('update'), 7)

    def test_selected_query_mismatch_blocks_current_prediction_and_truth(self):
        class WrongQuery(FakePolicy):
            def select(self):
                super().select()
                return ('c', 'wrong', 1200.)
        with patch.object(replay, 'attach_truth_and_group') as truth:
            with self.assertRaisesRegex(ValueError, 'query/difficulty'):
                self.execute(factory=lambda *, graph_on: WrongQuery(self.events))
            truth.assert_not_called()
        self.assertNotIn('predict', self.events)

    def test_source_recheck_failure_blocks_truth_despite_successful_P(self):
        def fail():
            raise ValueError('source drift')
        with patch.object(replay, 'attach_truth_and_group') as truth:
            with self.assertRaisesRegex(ValueError, 'source drift'):
                self.execute(verify_after=fail)
            truth.assert_not_called()

    def test_missing_stream_and_duplicate_or_reordered_steps_reject(self):
        for mode in ('missing', 'duplicate', 'reorder'):
            buckets = fixtures()
            key = (1, 'PG', False, False)
            if mode == 'missing':
                del buckets[key]
            elif mode == 'duplicate':
                buckets[key][1]['step'] = 0
            else:
                buckets[key] = tuple(reversed(buckets[key]))
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.execute(buckets=buckets)

    def test_confusion_keeps_zeroes_and_pi_blocked_true_mastery(self):
        values = []
        for truth, theta, pi in ((True, True, True), (False, True, True),
                                  (True, True, False), (False, False, False)):
            values.append(dict(source_true_M=truth, theta_gate=theta, stored_pi_gate=pi, native_M=theta and pi))
        result = replay.confusion(values)
        self.assertEqual([result['M_'+name] for name in ('TP', 'FP', 'FN', 'TN')], [1, 1, 1, 1])
        self.assertEqual((result['theta_gate_true_pi_blocked'], result['oracle_true_pi_blocked']), (1, 1))
        self.assertEqual(replay.confusion([])['M_FP'], 0)


if __name__ == '__main__':
    unittest.main()
