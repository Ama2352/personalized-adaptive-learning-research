"""Fixtures Paper1 PDF dựng tay, không đọc CSV hoặc chạy matrix lịch sử.

Bank mang nhãn unverified-unit. Các state/history script chỉ kiểm quy tắc,
không là empirical reproduction hoặc provenance của domain đã được review.
"""

from dataclasses import replace
import math
import unittest

from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem
from knowledge_tracing.paper1_pdf.simulator import (
    DIFFICULTIES, PDF_SHA256, PROSPECTIVE_INPUT_SHA256, Paper1PdfController,
    Paper1PdfLearner, dynamic_k, elo_probability, validate_prospective_domain,
)


def bank(nodes):
    return SimulatorBank('paper1-pdf-unverified-unit', tuple(
        SimulatorItem(f'{node}-{int(difficulty)}', node, difficulty)
        for node in nodes for difficulty in DIFFICULTIES))


def controller(nodes=('a',), *, chapters=None, edges=(), order=None, initial=None):
    return Paper1PdfController(bank(nodes), chapters={node: 'A' for node in nodes} if chapters is None else chapters,
        edges=edges, traversal_order=nodes if order is None else order,
        initial_estimates={node: 1200. for node in nodes} if initial is None else initial)


def committed(value):
    return {key: item for key, item in value.snapshot().items() if key != 'pending_prediction'}


class Paper1PdfPrimitiveTests(unittest.TestCase):
    def test_probability_known_points_and_no_numerical_clip(self):
        self.assertEqual(elo_probability(1200., 1200.), .5)
        self.assertAlmostEqual(elo_probability(1050., 1200.), 1/(1+10**.375), places=15)
        self.assertEqual(elo_probability(-1e9, 1200.), 0.)
        self.assertEqual(elo_probability(1e9, 1200.), 1.)
        for invalid in (math.nan, math.inf, True):
            with self.subTest(invalid=repr(invalid)), self.assertRaises(ValueError):
                elo_probability(invalid, 1200.)

    def test_k_uses_previous_count_and_exact_five_fifteen_boundaries(self):
        for n, expected in ((0, 40.), (4, 40.), (5, 24.), (14, 24.), (15, 16.), (100, 16.)):
            with self.subTest(n=n):
                self.assertEqual(dynamic_k(n), expected)
        for invalid in (-1, 1., True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                dynamic_k(invalid)

    def test_prediction_before_label_and_one_selected_estimate_update(self):
        value = controller(('a', 'b'))
        before = committed(value)
        predicted = value.predict_next()
        self.assertEqual(committed(value), before)
        self.assertEqual((predicted.concept_id, predicted.item_id, predicted.probability), ('a', 'a-1200', .5))
        value.observe(predicted, 1)
        state = value.snapshot()
        self.assertEqual(state['estimated_elo'], {'a': 1220., 'b': 1200.})
        self.assertEqual(state['concept_attempts'], {'a': 1, 'b': 0})
        self.assertEqual(state['item_exposures']['a-1200'], 1)
        self.assertEqual((state['current_chapter'], state['committed_interactions']), ('A', 1))

    def test_ready_set_all_parents_before_weak_child(self):
        value = controller(('p', 'c'), chapters={'p': 'A', 'c': 'B'}, edges=(('p', 'c'),),
                           initial={'p': 1249., 'c': 900.})
        self.assertEqual(value.ready_set(), ('p',))
        predicted = value.predict_next()
        self.assertEqual(predicted.concept_id, 'p')
        value.observe(predicted, 1)
        self.assertEqual(value.ready_set(), ('c',))
        self.assertEqual(value.predict_next().concept_id, 'c')

    def test_continuity_is_hard_filter_before_global_elo_rank(self):
        value = controller(('a1', 'a2', 'b'), chapters={'a1': 'A', 'a2': 'A', 'b': 'B'},
                           initial={'a1': 900., 'a2': 1150., 'b': 910.})
        first = value.predict_next()
        self.assertEqual(first.concept_id, 'a1')
        value.observe(first, 1)
        state = value.snapshot()
        self.assertGreater(state['estimated_elo']['a1'], state['estimated_elo']['b'])
        self.assertEqual(value.predict_next().chapter, 'A')

    def test_leaves_current_chapter_when_no_local_ready_concept(self):
        value = controller(('a', 'b'), chapters={'a': 'A', 'b': 'B'}, initial={'a': 1249., 'b': 1249.})
        value.observe(value.predict_next(), 1)
        self.assertEqual(value.predict_next().concept_id, 'b')

    def test_fixed_traversal_rank_breaks_equal_elo_tie(self):
        value = controller(('a', 'b'), order=('b', 'a'))
        self.assertEqual(value.predict_next().concept_id, 'b')

    def test_item_equal_distance_uses_exposure_then_identifier(self):
        value = controller(initial={'a': 1125.})
        self.assertEqual(value.predict_next().item_id, 'a-1050')
        # Handmade exposure-state unit, không tuyên bố trajectory tạo state này.
        second = controller(initial={'a': 1125.})
        second._exposures['a-1050'] = 1
        self.assertEqual(second.predict_next().item_id, 'a-1200')

    def test_all_estimated_mastered_returns_none_without_new_event(self):
        value = controller(('a', 'b'), initial={'a': 1250., 'b': 1300.})
        before = value.snapshot()
        self.assertEqual(value.ready_set(), ())
        self.assertIsNone(value.predict_next())
        self.assertEqual(value.snapshot(), before)

    def test_dependency_can_force_a_b_a_on_synthetic_domain(self):
        # Scripted unit phản ví dụ cho universal zero-reentry, không phải PDF run.
        value = controller(('a1', 'b1', 'a2'), chapters={'a1': 'A', 'b1': 'B', 'a2': 'A'},
            edges=(('a1', 'b1'), ('b1', 'a2')), initial={'a1': 1249., 'b1': 1249., 'a2': 1200.})
        for _ in range(3):
            value.observe(value.predict_next(), 1)
        self.assertEqual(value.snapshot()['chapter_history'], ('A', 'B', 'A'))
        self.assertEqual((value.metrics()['chapter_switches'], value.metrics()['chapter_reentry']), (2, 1))

    def test_invalid_labels_leave_pending_and_all_committed_state_unchanged(self):
        for invalid in (True, 1., -1, 2, '1', None):
            value = controller()
            predicted = value.predict_next()
            before = committed(value)
            with self.subTest(invalid=repr(invalid)), self.assertRaises(ValueError):
                value.observe(predicted, invalid)
            self.assertEqual(committed(value), before)
            self.assertIs(value.snapshot()['pending_prediction'], predicted)

    def test_wrong_pending_copy_and_repeat_observe_cannot_double_commit(self):
        value = controller()
        predicted = value.predict_next()
        before = committed(value)
        with self.assertRaises(ValueError):
            value.observe(replace(predicted), 1)
        self.assertEqual(committed(value), before)
        with self.assertRaises(ValueError):
            value.predict_next()
        value.observe(predicted, 1)
        after = committed(value)
        with self.assertRaises(ValueError):
            value.observe(predicted, 1)
        self.assertEqual(committed(value), after)

    def test_nonfinite_or_changed_pending_probability_rejects_before_mutation(self):
        for invalid in (math.nan, math.inf, .7):
            value = controller()
            predicted = value.predict_next()
            before = committed(value)
            # Cố tình phá frozen record để kiểm cheap caller-consistency guard.
            object.__setattr__(predicted, 'probability', invalid)
            with self.subTest(invalid=repr(invalid)), self.assertRaises(ValueError):
                value.observe(predicted, 1)
            self.assertEqual(committed(value), before)

    def test_current_label_changes_update_but_not_prior_prediction(self):
        left, right = controller(), controller()
        p0, p1 = left.predict_next(), right.predict_next()
        self.assertEqual(p0.probability, p1.probability)
        left.observe(p0, 0)
        right.observe(p1, 1)
        self.assertEqual(left.snapshot()['estimated_elo']['a'], 1180.)
        self.assertEqual(right.snapshot()['estimated_elo']['a'], 1220.)

    def test_latent_and_estimated_states_and_probability_are_separate(self):
        items = bank(('a',))
        learner = Paper1PdfLearner(items, initial_latent={'a': 1400.})
        value = controller()
        predicted = value.predict_next()
        response = learner.respond(predicted.item_id, outcome_uniform=.5)
        self.assertEqual(predicted.probability, .5)
        self.assertGreater(response.probability_true, predicted.probability)
        self.assertEqual(value.snapshot()['estimated_elo']['a'], 1200.)
        self.assertEqual(learner.diagnostic_snapshot()['latent_ability']['a'], 1412.)
        with self.assertRaises(ValueError):
            value.observe(predicted, response)
        value.observe(predicted, response.correct)
        self.assertEqual(value.snapshot()['estimated_elo']['a'], 1220.)

    def test_same_observable_history_has_same_controller_state_despite_world_change(self):
        left, right = controller(), controller()
        low = Paper1PdfLearner(bank(('a',)), initial_latent={'a': 1000.})
        high = Paper1PdfLearner(bank(('a',)), initial_latent={'a': 1400.})
        low.respond('a-1200', outcome_uniform=.5)
        high.respond('a-1200', outcome_uniform=.5)
        for correct in (0, 1, 0):
            p0, p1 = left.predict_next(), right.predict_next()
            self.assertEqual(p0, p1)
            left.observe(p0, correct)
            right.observe(p1, correct)
        self.assertEqual(left.snapshot(), right.snapshot())

    def test_world_uniform_endpoints_and_gain_independent_of_response(self):
        for uniform, expected in ((0., 1), (.5, 0), (.999, 0)):
            learner = Paper1PdfLearner(bank(('a', 'b')), initial_latent={'a': 1200., 'b': 1100.})
            response = learner.respond('a-1200', outcome_uniform=uniform)
            with self.subTest(uniform=uniform):
                self.assertEqual((response.correct, response.latent_before, response.latent_after), (expected, 1200., 1212.))
                self.assertEqual(learner.diagnostic_snapshot()['latent_ability']['b'], 1100.)

    def test_world_cap_is_post_feedback_literal_without_initial_clip(self):
        for initial, expected in ((1496., 1500.), (1500., 1500.), (1510., 1500.)):
            learner = Paper1PdfLearner(bank(('a',)), initial_latent={'a': initial})
            self.assertEqual(learner.diagnostic_snapshot()['latent_ability']['a'], initial)
            response = learner.respond('a-1200', outcome_uniform=0.)
            with self.subTest(initial=initial):
                self.assertEqual(response.latent_after, expected)

    def test_invalid_uniform_or_item_does_not_mutate_world(self):
        learner = Paper1PdfLearner(bank(('a',)), initial_latent={'a': 1200.})
        before = learner.diagnostic_snapshot()
        for invalid in (-.1, 1., math.nan, math.inf, True, None):
            with self.subTest(invalid=repr(invalid)), self.assertRaises(ValueError):
                learner.respond('a-1200', outcome_uniform=invalid)
            self.assertEqual(learner.diagnostic_snapshot(), before)
        with self.assertRaises(ValueError):
            learner.respond('unknown', outcome_uniform=0.)
        self.assertEqual(learner.diagnostic_snapshot(), before)

    def test_input_and_returned_snapshot_mappings_are_not_live_state(self):
        initial = {'a': 1200.}
        value = controller(initial=initial)
        learner = Paper1PdfLearner(bank(('a',)), initial_latent=initial)
        initial['a'] = 900.
        snapshot = value.snapshot()
        snapshot['estimated_elo']['a'] = 800.
        diagnostic = learner.diagnostic_snapshot()
        diagnostic['latent_ability']['a'] = 800.
        self.assertEqual(value.snapshot()['estimated_elo']['a'], 1200.)
        self.assertEqual(learner.diagnostic_snapshot()['latent_ability']['a'], 1200.)

    def test_invalid_graph_mapping_order_and_initial_state_refuse(self):
        for edges in ((('a', 'a'),), (('a', 'b'), ('a', 'b')), (('a', 'b'), ('b', 'a')), (('x', 'a'),)):
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                controller(('a', 'b'), edges=edges)
        for order in (('a',), ('a', 'a'), ('a', 'x')):
            with self.subTest(order=order), self.assertRaises(ValueError):
                controller(('a', 'b'), order=order)
        for initial in ({'a': 1200.}, {'a': math.nan, 'b': 1200.}, {'a': True, 'b': 1200.}):
            with self.subTest(initial=initial), self.assertRaises(ValueError):
                controller(('a', 'b'), initial=initial)
        with self.assertRaises(ValueError):
            controller(('a', 'b'), chapters={'a': 'A'})

    def test_bank_must_have_three_fixed_difficulties(self):
        items = SimulatorBank('paper1-pdf-unverified-unit', (SimulatorItem('one', 'a', 1200.),))
        with self.assertRaises(ValueError):
            Paper1PdfLearner(items, initial_latent={'a': 1200.})

    def test_metrics_handmade_history_counts_switches_and_reentry(self):
        for history, switches, reentry in (((), 0, 0), (('A', 'A'), 0, 0),
                (('A', 'A', 'B', 'B', 'C'), 2, 0), (('A', 'B', 'A'), 2, 1)):
            value = controller(('a', 'b'), initial={'a': 1250., 'b': 1200.})
            value._history = list(history)  # Metric-only handfixture, không run trajectory.
            result = value.metrics()
            with self.subTest(history=history):
                self.assertEqual((result['chapter_switches'], result['chapter_reentry']), (switches, reentry))
                self.assertEqual((result['concept_denominator'], result['estimated_mastery_rate']), (2, .5))

    def test_prospective_28node_shape_is_not_file_provenance(self):
        nodes = tuple(f'c{i:02d}' for i in range(28))
        chapters = {node: ('A' if i < 9 else 'B' if i < 17 else 'C') for i, node in enumerate(nodes)}
        baseline = tuple((nodes[i], nodes[i+1]) for i in range(27) if chapters[nodes[i]] == chapters[nodes[i+1]])
        added = ((nodes[0], nodes[2]), (nodes[9], nodes[11]), (nodes[17], nodes[19]),
                 (nodes[8], nodes[9]), (nodes[16], nodes[17]), (nodes[7], nodes[18]))
        result = validate_prospective_domain(bank(nodes), chapters=chapters, baseline_edges=baseline, advanced_edges=baseline+added)
        self.assertEqual((result['baseline_edges'], result['advanced_edges'], result['added_intra'], result['added_cross']), (25, 31, 3, 3))
        self.assertIs(result['source_bytes_verified'], False)
        self.assertIs(result['historical_identity_claimed'], False)
        with self.assertRaises(ValueError):
            validate_prospective_domain(bank(nodes), chapters=chapters, baseline_edges=baseline[:-1], advanced_edges=baseline+added)

    def test_authority_and_candidate_input_pins_are_explicit(self):
        self.assertEqual(PDF_SHA256, '984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4')
        pins = dict(PROSPECTIVE_INPUT_SHA256)
        self.assertEqual(len(pins), 5)
        self.assertEqual(pins['edges_baseline.csv'], '9d795fb88d00e5c2ec1d3b2215bb93038a944354c3c4709b6b0aa9d66906c39d')


if __name__ == '__main__':
    unittest.main()
