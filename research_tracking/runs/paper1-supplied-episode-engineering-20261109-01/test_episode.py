"""Episode supplied trên bank dựng tay, không đọc canonical CSV hoặc sinh RNG."""
from dataclasses import FrozenInstanceError, fields, replace
import random
import unittest
from unittest.mock import patch

from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem
from knowledge_tracing.paper1_pdf import episode
from knowledge_tracing.paper1_pdf.simulator import DIFFICULTIES


def case(nodes=('a',), *, persona='US', z=None):
    bank = SimulatorBank('unverified-supplied-episode-fixture', tuple(
        SimulatorItem(f'{node}-{int(level)}', node, level) for node in nodes for level in DIFFICULTIES))
    chapters = {node: 'F' if i == 0 else 'O' for i, node in enumerate(nodes)}
    profile = episode.initialize_profile(bank, chapters=chapters, persona=persona,
        function_chapter='F', normal_z_by_node=dict.fromkeys(nodes, 0.) if z is None else z)
    return bank, chapters, profile


def run(value, horizon, tape=None, *, edges=(), order=None):
    bank, chapters, profile = value
    return episode.run_continuity_episode_supplied(bank, profile, chapters=chapters, edges=edges,
        traversal_order=tuple(chapters) if order is None else order, horizon=horizon,
        response_uniforms_by_node={node: (0.,)*horizon for node in chapters} if tape is None else tape)


class SuppliedEpisodeTests(unittest.TestCase):
    def test_pdf_profile_means_and_explicit_function_unit(self):
        for persona, latent, estimates in (
            ('US', (1400., 1400.), (1200., 1200.)),
            ('UW', (1050., 1050.), (1200., 1200.)),
            ('FW', (1000., 1250.), (1050., 1200.))):
            with self.subTest(persona=persona):
                _, _, profile = case(('a', 'b'), persona=persona)
                self.assertEqual(tuple(dict(profile.initial_latent).values()), latent)
                self.assertEqual(tuple(dict(profile.initial_estimates).values()), estimates)

    def test_supplied_z_scaling_and_literal_post_feedback_cap(self):
        value = case(z={'a': 3.})
        self.assertEqual(dict(value[2].initial_latent), {'a': 1550.})
        result = run(value, 1)
        self.assertEqual((result.oracle[0].latent_before, result.oracle[0].latent_after), (1550., 1500.))
        self.assertEqual(result.observable[0].estimated_before, 1200.)

    def test_profile_rejects_invalid_scope_keys_and_nonfinite_draws(self):
        bank, chapters, _ = case()
        base = dict(chapters=chapters, persona='US', function_chapter='F', normal_z_by_node={'a': 0.})
        changes = [dict(persona='PG'), dict(function_chapter='missing'), dict(normal_z_by_node={}),
                   dict(normal_z_by_node={'a': 0., 'outside': 0.})]
        changes += [dict(normal_z_by_node={'a': value}) for value in (True, float('nan'), float('inf'), 1e308)]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                episode.initialize_profile(bank, **(base | change))

    def test_profile_bank_chapter_and_derived_state_drift_rejected(self):
        bank, chapters, profile = case()
        changes = (replace(profile, initial_latent=(('a', 1401.),)),
                   replace(profile, initial_estimates=(('a', 1249.),)),
                   replace(profile, persona='UW'))
        for changed in changes:
            with self.subTest(profile=changed), self.assertRaises(ValueError):
                run((bank, chapters, changed), 1)
        foreign_bank = SimulatorBank('different-fixture', bank.items)
        with self.assertRaises(ValueError):
            run((foreign_bank, chapters, profile), 1)
        with self.assertRaises(ValueError):
            run((bank, {'a': 'different'}, profile), 1)

    def test_horizon_requires_integer_one_to_five_hundred(self):
        value = case()
        for horizon in (0, 501, True, 1., None):
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                run(value, horizon, {'a': (0.,)})

    def test_all_tapes_validated_before_any_controller_or_world(self):
        value = case(('a', 'b'))
        tapes = ({'a': (0., 0.)}, {'a': (0., 0.), 'b': (0., 0.), 'extra': (0., 0.)},
                 {'a': (0., 0.), 'b': (0.,)}, {'a': (0., 0.), 'b': (0., float('nan'))},
                 {'a': (0., 0.), 'b': (0., 1.)}, {'a': (0., 0.), 'b': (0., -0.1)},
                 {'a': (0., 0.), 'b': (0., True)}, {'a': (0., 0.), 'b': '00'})
        with (patch.object(episode, 'Paper1PdfController', side_effect=AssertionError('no controller')),
              patch.object(episode, 'Paper1PdfLearner', side_effect=AssertionError('no world'))):
            for tape in tapes:
                with self.subTest(tape=tape), self.assertRaises(ValueError):
                    run(value, 2, tape)

    def test_graph_and_traversal_rejected_before_world(self):
        value = case(('a', 'b'))
        with patch.object(episode, 'Paper1PdfLearner', side_effect=AssertionError('no world')):
            for edges, order in (((('a', 'b'), ('b', 'a')), ('a', 'b')),
                                 ((('a', 'outside'),), ('a', 'b')),
                                 ((('a', 'a'),), ('a', 'b')),
                                 ((('a', 'b'), ('a', 'b')), ('a', 'b')),
                                 ((), ('a', 'a'))):
                with self.subTest(edges=edges, order=order), self.assertRaises(ValueError):
                    run(value, 1, edges=edges, order=order)

    def test_wrong_answer_still_learns_only_selected_concept(self):
        result = run(case(('a', 'b')), 1, {'a': (.999,), 'b': (0.,)})
        row = result.observable[0]
        self.assertEqual((row.concept_id, row.correct), ('a', 0))
        self.assertLess(row.estimated_after, row.estimated_before)
        self.assertEqual((result.oracle[0].latent_before, result.oracle[0].latent_after), (1400., 1412.))
        self.assertEqual(dict(result.final_latent)['b'], 1400.)
        self.assertEqual(dict(result.final_estimates)['b'], 1200.)
        self.assertEqual(dict(result.concept_attempts), {'a': 1, 'b': 0})

    def test_current_response_never_changes_its_own_prediction(self):
        yes = run(case(), 1, {'a': (0.,)}).observable[0]
        no = run(case(), 1, {'a': (.999,)}).observable[0]
        self.assertEqual((yes.probability, yes.estimated_before, yes.previous_interactions), (.5, 1200., 0))
        self.assertEqual((yes.item_id, yes.probability, yes.estimated_before),
                         (no.item_id, no.probability, no.estimated_before))
        self.assertEqual((yes.correct, no.correct), (1, 0))
        self.assertNotEqual(yes.estimated_after, no.estimated_after)

    def test_future_uniform_cannot_change_past_or_preupdate_readout(self):
        first = run(case(), 2, {'a': (0., 0.)})
        changed = run(case(), 2, {'a': (0., .999)})
        self.assertEqual(first.observable[0], changed.observable[0])
        self.assertEqual(first.oracle[0], changed.oracle[0])
        self.assertEqual(first.observable[1].probability, changed.observable[1].probability)
        self.assertEqual(first.observable[1].estimated_before, changed.observable[1].estimated_before)
        self.assertNotEqual(first.observable[1].correct, changed.observable[1].correct)

    def test_deterministic_immutable_output_and_unchanged_supplied_inputs(self):
        value = case()
        tape = {'a': [0., .999]}
        profile_before = value[2].identity
        first = run(value, 2, tape)
        second = run(value, 2, tape)
        self.assertEqual(first, second)
        self.assertEqual(first.identity, second.identity)
        self.assertEqual(tape, {'a': [0., .999]})
        self.assertEqual(value[2].identity, profile_before)
        with self.assertRaises(FrozenInstanceError):
            first.observable[0].correct = 0
        self.assertIsInstance(first.observable, tuple)
        self.assertIsInstance(first.final_latent, tuple)

    def test_response_tape_uses_concept_local_previous_count(self):
        result = run(case(('a', 'b')), 4, {'a': (0., 0., 0., 0.), 'b': (.999, 0., 0., 0.)})
        self.assertEqual(tuple(row.concept_id for row in result.observable), ('a', 'a', 'a', 'b'))
        last = result.observable[-1]
        self.assertEqual((last.previous_interactions, last.previous_item_exposures, last.correct), (0, 0, 0))
        self.assertEqual(dict(result.metrics)['interactions'], 4)

    def test_completion_before_horizon_does_not_consume_extra_draw(self):
        result = run(case(), 4)
        self.assertEqual((len(result.observable), len(result.oracle)), (3, 3))
        self.assertEqual((result.stop_reason, result.budget_exhausted), ('ALL_ESTIMATED_MASTERED', False))
        self.assertEqual(dict(result.final_latent), {'a': 1436.})
        self.assertEqual(dict(result.concept_attempts), {'a': 3})

    def test_completion_on_final_step_wins_stop_reason_but_records_cap(self):
        result = run(case(), 3)
        self.assertEqual((result.stop_reason, result.budget_exhausted), ('ALL_ESTIMATED_MASTERED', True))
        self.assertEqual(dict(result.metrics)['estimated_mastery_rate'], 1.)

    def test_horizon_stop_has_remaining_estimated_work(self):
        result = run(case(), 1)
        self.assertEqual((result.stop_reason, result.budget_exhausted), ('HORIZON_REACHED', True))
        self.assertEqual(dict(result.metrics)['estimated_mastery_rate'], 0.)
        self.assertEqual(dict(result.final_estimates), {'a': 1220.})

    def test_maximum_horizon_commits_exactly_five_hundred_supplied_responses(self):
        result = run(case(), 500, {'a': (.999,)*500})
        self.assertEqual((len(result.observable), len(result.oracle)), (500, 500))
        self.assertTrue(all(row.correct == 0 for row in result.observable))
        self.assertEqual(dict(result.concept_attempts), {'a': 500})
        self.assertEqual(sum(dict(result.item_exposures).values()), 500)
        self.assertEqual((result.stop_reason, result.budget_exhausted), ('HORIZON_REACHED', True))

    def test_oracle_separate_and_never_supplied_to_controller(self):
        original = episode.Paper1PdfController
        calls = []
        def construct(bank, **kwargs):
            calls.append(kwargs)
            return original(bank, **kwargs)
        with patch.object(episode, 'Paper1PdfController', side_effect=construct):
            high = run(case(z={'a': 0.}), 1)
            low = run(case(z={'a': -4.}), 1)
        self.assertEqual(high.observable, low.observable)
        self.assertNotEqual(high.oracle, low.oracle)
        for kwargs in calls:
            self.assertEqual(set(kwargs), {'chapters', 'edges', 'traversal_order', 'initial_estimates'})
            self.assertEqual(kwargs['initial_estimates'], {'a': 1200.})
        observable_fields = {field.name for field in fields(episode.ObservableInteraction)}
        self.assertFalse(observable_fields & {'latent_before', 'latent_after', 'probability_true'})

    def test_no_global_rng_use_and_profile_pairs_immutable(self):
        state = random.getstate()
        value = case()
        run(value, 3)
        self.assertEqual(random.getstate(), state)
        self.assertIsInstance(value[2].initial_latent, tuple)
        with self.assertRaises(FrozenInstanceError):
            value[2].persona = 'FW'


if __name__ == '__main__':
    unittest.main()
