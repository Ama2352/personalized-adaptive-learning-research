"""Fixtures dựng tay cho bất biến concept-local có điều kiện và các ranh giới."""
from dataclasses import asdict
import unittest

from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem
from knowledge_tracing.paper1_pdf.episode import initialize_profile, run_continuity_episode_supplied
from knowledge_tracing.paper1_pdf.simulator import DIFFICULTIES, Paper1PdfController


def fixture(chapters=None, z=None):
    chapters = dict(a1='A', b='B', a2='A') if chapters is None else chapters
    bank = SimulatorBank('unverified-concept-local-fixture', tuple(
        SimulatorItem(f'{node}-{int(level)}', node, level) for node in chapters for level in DIFFICULTIES))
    profile = initialize_profile(bank, chapters=chapters, persona='US', function_chapter='A',
        normal_z_by_node=dict.fromkeys(chapters, 0.) if z is None else z)
    return bank, chapters, profile


def episode(value, horizon, *, edges=(), order=None, wrong=None):
    bank, chapters, profile = value
    wrong = {} if wrong is None else wrong
    tapes = {node: (.999,)*wrong.get(node, 0)+(0.,)*(horizon-wrong.get(node, 0)) for node in chapters}
    return run_continuity_episode_supplied(bank, profile, chapters=chapters, edges=edges,
        traversal_order=tuple(chapters) if order is None else order,
        response_uniforms_by_node=tapes, horizon=horizon)


def local_trace(result, concept):
    rows = []
    for seen, truth in zip(result.observable, result.oracle, strict=True):
        if seen.concept_id == concept:
            observed, latent = asdict(seen), asdict(truth)
            observed.pop('step')
            latent.pop('step')
            rows.append((observed, latent))
    return tuple(rows)


def chapter_blocks(result):
    history = [row.chapter for row in result.observable]
    return tuple(chapter for i, chapter in enumerate(history) if not i or chapter != history[i-1])


def aggregate_latent_gain(result, profile):
    initial = dict(profile.initial_latent)
    return sum(value-initial[node] for node, value in result.final_latent)


class ConceptLocalInvarianceTests(unittest.TestCase):
    def assert_complete_local_equality(self, left, right, nodes):
        self.assertEqual(left.stop_reason, 'ALL_ESTIMATED_MASTERED')
        self.assertEqual(right.stop_reason, 'ALL_ESTIMATED_MASTERED')
        self.assertEqual(left.concept_attempts, right.concept_attempts)
        self.assertEqual(left.item_exposures, right.item_exposures)
        self.assertEqual(left.final_estimates, right.final_estimates)
        self.assertEqual(left.final_latent, right.final_latent)
        self.assertEqual(len(left.observable), len(right.observable))
        for node in nodes:
            sequence = local_trace(left, node)
            self.assertTrue(sequence)
            self.assertEqual(sequence, local_trace(right, node))
            self.assertEqual(len(sequence), dict(left.concept_attempts)[node])
            self.assertTrue(all(row[0]['estimated_after'] < 1250. for row in sequence[:-1]))
            self.assertGreaterEqual(sequence[-1][0]['estimated_after'], 1250.)

    def test_complete_dags_preserve_local_stopping_states_but_allow_a_b_a(self):
        value = fixture()
        baseline = episode(value, 30)
        cross = episode(value, 30, edges=(('b', 'a2'),))
        self.assert_complete_local_equality(baseline, cross, value[1])
        self.assertEqual(chapter_blocks(baseline), ('A', 'B'))
        self.assertEqual(chapter_blocks(cross), ('A', 'B', 'A'))
        self.assertEqual(dict(baseline.metrics)['chapter_reentry'], 0)
        self.assertEqual(dict(cross.metrics)['chapter_reentry'], 1)
        self.assertNotEqual(tuple(row.concept_id for row in baseline.observable),
                            tuple(row.concept_id for row in cross.observable))

    def test_complete_local_prefixes_include_nontrivial_wrong_feedback(self):
        value = fixture()
        wrong = dict(a1=1, b=2)
        baseline = episode(value, 60, wrong=wrong)
        cross = episode(value, 60, edges=(('b', 'a2'),), wrong=wrong)
        self.assert_complete_local_equality(baseline, cross, value[1])
        self.assertGreaterEqual(sum(row.correct == 0 for row in baseline.observable), 3)
        self.assertGreater(dict(baseline.concept_attempts)['a1'], dict(baseline.concept_attempts)['a2'])
        for node, count in wrong.items():
            self.assertEqual([row[0]['correct'] for row in local_trace(baseline, node)[:count]], [0]*count)

    def test_finite_horizon_preserves_overlapping_local_prefix_not_allocation(self):
        value = fixture()
        baseline = episode(value, 4)
        cross = episode(value, 4, edges=(('b', 'a2'),))
        self.assertEqual((baseline.stop_reason, cross.stop_reason), ('HORIZON_REACHED', 'HORIZON_REACHED'))
        self.assertTrue(baseline.budget_exhausted and cross.budget_exhausted)
        self.assertEqual(len(baseline.observable), len(cross.observable))
        self.assertNotEqual(baseline.concept_attempts, cross.concept_attempts)
        self.assertNotEqual(baseline.final_estimates, cross.final_estimates)
        self.assertNotEqual(baseline.final_latent, cross.final_latent)
        overlap = 0
        for node in value[1]:
            left, right = local_trace(baseline, node), local_trace(cross, node)
            n = min(len(left), len(right))
            self.assertEqual(left[:n], right[:n])
            overlap += n
        self.assertGreater(overlap, 0)  # Prefix chung có dữ liệu, không chỉ so hai prefix rỗng.

    def test_capped_latent_can_change_aggregate_gain_at_same_horizon(self):
        value = fixture(dict(a='A', b='B'), dict(a=1.96, b=-4.))
        self.assertEqual(dict(value[2].initial_latent), dict(a=1498., b=1200.))
        bank, chapters, profile = value
        blocked = Paper1PdfController(bank, chapters=chapters, edges=(('b', 'a'),),
            traversal_order=('b', 'a'), initial_estimates=dict(profile.initial_estimates))
        self.assertEqual(blocked.ready_set(), ('b',))
        left = episode(value, 1)
        right = episode(value, 1, edges=(('b', 'a'),), order=('b', 'a'))
        self.assertEqual([row.concept_id for row in left.observable], ['a'])
        self.assertEqual([row.concept_id for row in right.observable], ['b'])
        self.assertEqual((aggregate_latent_gain(left, profile), aggregate_latent_gain(right, profile)), (2., 12.))
        self.assertEqual(len(left.observable), len(right.observable))

    def test_without_clipped_updates_fixed_feedback_count_gives_twelve_n(self):
        value = fixture(dict(a='A', b='B'), dict(a=-4., b=-2.))
        left = episode(value, 2, wrong=dict(a=1))
        right = episode(value, 2, edges=(('b', 'a'),), order=('b', 'a'), wrong=dict(a=1))
        self.assertNotEqual(left.concept_attempts, right.concept_attempts)
        self.assertNotEqual(sum(row.correct for row in left.observable), sum(row.correct for row in right.observable))
        for result in (left, right):
            self.assertEqual(len(result.observable), 2)
            self.assertTrue(all(row.latent_after-row.latent_before == 12. for row in result.oracle))
            self.assertEqual(aggregate_latent_gain(result, value[2]), 12.*len(result.observable))

    def test_isolated_concept_matches_complete_interleavings_through_item_and_k_changes(self):
        value = fixture()
        wrong = dict(a1=6)
        baseline = episode(value, 90, wrong=wrong)
        cross = episode(value, 90, edges=(('b', 'a2'),), wrong=wrong)
        isolated = episode(fixture(dict(a1='A')), 90, wrong=wrong)
        self.assert_complete_local_equality(baseline, cross, value[1])
        self.assertEqual(isolated.stop_reason, 'ALL_ESTIMATED_MASTERED')
        self.assertEqual(local_trace(baseline, 'a1'), local_trace(isolated, 'a1'))
        sequence = local_trace(baseline, 'a1')
        self.assertGreaterEqual(sequence[-1][0]['previous_interactions'], 15)
        self.assertGreater(len({row[0]['difficulty'] for row in sequence}), 1)
        self.assertEqual([row[0]['correct'] for row in sequence[:6]], [0]*6)


if __name__ == '__main__':
    unittest.main()
