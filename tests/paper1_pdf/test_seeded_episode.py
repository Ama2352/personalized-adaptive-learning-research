"""Private RNG trên bank dựng tay; không actual domain pilot hoặc matrix."""
from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import random
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem
from knowledge_tracing.paper1_pdf import seeded_episode as seeded
from knowledge_tracing.paper1_pdf.episode import run_continuity_episode_supplied
from knowledge_tracing.paper1_pdf.simulator import DIFFICULTIES


def domain(nodes=('a', 'b')):
    bank = SimulatorBank('unverified-keyed-RNG-fixture', tuple(SimulatorItem(f'{node}-{int(level)}', node, level)
        for node in nodes for level in DIFFICULTIES))
    return bank, {node: 'F' if node == 'a' else 'O' for node in nodes}


def prepare(bank, declared_chapters, **changes):
    request = dict(chapters=declared_chapters, persona='US', function_chapter='F', root_seed=42,
                   replicate_id='learner-01', horizon=4)
    return seeded.prepare_seeded_draws(bank, **(request | changes))


def run(bank, chapters, draws, *, edges=(), order=None):
    return seeded.run_continuity_episode_seeded(bank, chapters=chapters, edges=edges,
        traversal_order=tuple(sorted(chapters)) if order is None else order, draws=draws)


def zero_rng(**key):
    # Test-only injected RNG outputs, không gắn chứng nhận Gaussian thật.
    return SimpleNamespace(gauss=lambda mu, sigma: 0., random=lambda: 0.)


class SeededEpisodeTests(unittest.TestCase):
    def test_event_seed_is_exact_canonical_utf8_sha256(self):
        raw = ('{"concept_id":"khái","event":"response_uniform","persona":"US",'
               '"previous_interactions":2,"replicate_id":"learner-01","root_seed":42,'
               '"version":"paper1-pdf-keyed-private-random-v1"}').encode('utf-8')
        actual = seeded._event_seed(root_seed=42, replicate_id='learner-01', persona='US',
            event='response_uniform', concept_id='khái', previous_interactions=2)
        self.assertEqual(actual, int.from_bytes(hashlib.sha256(raw).digest(), 'big'))

    def test_private_factory_calls_standard_normal_then_single_scale(self):
        bank, chapters = domain()
        for persona, expected_latent in (('US', {'a': 1450., 'b': 1350.}),
                                         ('UW', {'a': 1100., 'b': 1000.}),
                                         ('FW', {'a': 1050., 'b': 1200.})):
            events, methods = [], []
            def factory(**key):
                events.append(key)
                def gaussian(mu, sigma):
                    methods.append(('gauss', mu, sigma))
                    return 1. if key['concept_id'] == 'a' else -1.
                def uniform():
                    methods.append(('random',))
                    return .25
                return SimpleNamespace(gauss=gaussian, random=uniform)
            with self.subTest(persona=persona), patch.object(seeded, '_random_for_event', side_effect=factory):
                draws = prepare(bank, chapters, persona=persona, horizon=3)
            self.assertEqual(dict(draws.profile.initial_latent), expected_latent)
            self.assertEqual(methods.count(('gauss', 0., 1.)), 2)
            self.assertEqual(methods.count(('random',)), 6)
            self.assertEqual(draws.logical_draw_counts, dict(initial_normal_events=2, response_uniform_events=6))
            self.assertTrue(all(key['persona'] == persona for key in events))
            self.assertEqual([key['previous_interactions'] for key in events if key['event'] == 'response_uniform'],
                             [0, 1, 2, 0, 1, 2])

    def test_all_invalid_requests_reject_before_rng(self):
        bank, chapters = domain()
        changes = ({'root_seed': True}, {'root_seed': -1}, {'root_seed': 2**63}, {'root_seed': 42.},
                   {'replicate_id': ''}, {'replicate_id': '../other'}, {'replicate_id': 'x'*81},
                   {'horizon': 0}, {'horizon': 501}, {'horizon': True}, {'persona': 'PG'},
                   {'function_chapter': 'missing'}, {'chapters': {'a': 'F'}})
        with patch.object(seeded, '_random_for_event', side_effect=AssertionError('must not create RNG')):
            for change in changes:
                with self.subTest(change=change), self.assertRaises(ValueError):
                    prepare(bank, chapters, **change)
        for seed in (0, 2**63-1):
            self.assertEqual(prepare(bank, chapters, root_seed=seed, horizon=1).root_seed, seed)

    def test_same_request_deterministic_without_global_rng_mutation(self):
        bank, chapters = domain()
        before = random.getstate()
        first = prepare(bank, chapters)
        second = prepare(bank, chapters)
        self.assertEqual(first, second)
        self.assertEqual(first.identity, second.identity)
        self.assertEqual(run(bank, chapters, first), run(bank, chapters, second))
        self.assertEqual(random.getstate(), before)

    def test_event_namespaces_include_persona_replicate_seed_and_local_count(self):
        base = dict(root_seed=42, replicate_id='learner-01', persona='US', event='response_uniform',
                    concept_id='a', previous_interactions=0)
        original = seeded._event_seed(**base)
        for change in ({'root_seed': 43}, {'replicate_id': 'learner-02'}, {'persona': 'UW'},
                       {'concept_id': 'b'}, {'previous_interactions': 1}, {'event': 'initial_normal'}):
            with self.subTest(change=change):
                self.assertNotEqual(seeded._event_seed(**(base | change)), original)
        with self.assertRaises(TypeError):
            seeded._event_seed(**base, graph='GA')

    def test_node_order_and_unrelated_node_do_not_advance_shared_event_streams(self):
        bank, chapters = domain()
        original = prepare(bank, chapters)
        reversed_map = dict(reversed(tuple(chapters.items())))
        self.assertEqual(original, prepare(bank, reversed_map))
        larger_bank, larger_chapters = domain(('a', 'b', 'c'))
        larger = prepare(larger_bank, larger_chapters)
        for node in chapters:
            self.assertEqual(dict(original.profile.normal_z)[node], dict(larger.profile.normal_z)[node])
            self.assertEqual(dict(original.response_uniforms)[node], dict(larger.response_uniforms)[node])
        self.assertNotEqual(original.identity, larger.identity)

    def test_frozen_draws_own_caller_mapping_and_nested_tapes(self):
        bank, chapters = domain()
        draws = prepare(bank, chapters)
        identity = draws.identity
        chapters['b'] = 'F'
        self.assertEqual(dict(draws.profile.chapters), {'a': 'F', 'b': 'O'})
        self.assertEqual(draws.identity, identity)
        self.assertIsInstance(draws.response_uniforms, tuple)
        self.assertTrue(all(type(values) is tuple for _, values in draws.response_uniforms))
        with self.assertRaises(FrozenInstanceError):
            draws.root_seed = 43

    def test_seeded_runner_delegates_to_existing_supplied_core(self):
        bank, chapters = domain()
        draws = prepare(bank, chapters)
        expected = run_continuity_episode_supplied(bank, draws.profile, chapters=chapters, edges=(),
            traversal_order=('a', 'b'), response_uniforms_by_node=dict(draws.response_uniforms), horizon=draws.horizon)
        with patch.object(seeded, 'run_continuity_episode_supplied', wraps=run_continuity_episode_supplied) as original:
            result = run(bank, chapters, draws)
        self.assertEqual(original.call_count, 1)
        self.assertEqual(result.result, expected)
        self.assertEqual(result.draws_sha256, draws.identity)

    def test_branch_order_and_concept_local_coupling(self):
        bank, chapters = domain()
        with patch.object(seeded, '_random_for_event', side_effect=zero_rng):
            draws = prepare(bank, chapters, horizon=6)
        first_a = run(bank, chapters, draws)
        first_b = run(bank, chapters, draws, edges=(('b', 'a'),), order=('b', 'a'))
        self.assertEqual(first_b, run(bank, chapters, draws, edges=(('b', 'a'),), order=('b', 'a')))
        self.assertEqual(first_a, run(bank, chapters, draws))
        self.assertNotEqual(first_a.result.graph_sha256, first_b.result.graph_sha256)
        self.assertEqual(tuple(row.concept_id for row in first_a.result.observable), ('a', 'a', 'a', 'b', 'b', 'b'))
        self.assertEqual(tuple(row.concept_id for row in first_b.result.observable), ('b', 'b', 'b', 'a', 'a', 'a'))
        local = {(row.concept_id, row.previous_interactions): (row, truth)
                 for row, truth in zip(first_a.result.observable, first_a.result.oracle, strict=True)}
        for row, truth in zip(first_b.result.observable, first_b.result.oracle, strict=True):
            other, other_truth = local[(row.concept_id, row.previous_interactions)]
            self.assertNotEqual(row.step, other.step)
            self.assertEqual((row.correct, row.probability), (other.correct, other.probability))
            self.assertEqual(truth.latent_before, other_truth.latent_before)

    def test_prepare_captures_actual_python_random_source_provenance(self):
        bank, chapters = domain()
        draws = prepare(bank, chapters)
        runtime = draws.runtime
        self.assertEqual((runtime.implementation, runtime.python_version, runtime.python_build),
                         (sys.implementation.name, tuple(sys.version_info), sys.version))
        self.assertEqual((runtime.executable, runtime.prefix), (sys.executable, sys.prefix))
        self.assertEqual(Path(runtime.random_source_path), Path(random.__file__).resolve())
        self.assertEqual(runtime.random_source_sha256, hashlib.sha256(Path(random.__file__).read_bytes()).hexdigest())

    def test_runtime_drift_rejects_prepare_and_run_before_interaction(self):
        bank, chapters = domain()
        draws = prepare(bank, chapters)
        changed = replace(draws.runtime, python_build='different-runtime')
        with patch.object(seeded, '_runtime_provenance', side_effect=(draws.runtime, changed)):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                prepare(bank, chapters)
        with (patch.object(seeded, '_runtime_provenance', return_value=changed),
              patch.object(seeded, 'run_continuity_episode_supplied', side_effect=AssertionError('no interaction'))):
            with self.assertRaisesRegex(ValueError, 'current process'):
                run(bank, chapters, draws)

    def test_seal_and_domain_drift_reject_without_redrawing(self):
        bank, chapters = domain()
        draws = prepare(bank, chapters)
        changes = (replace(draws, root_seed=43), replace(draws, horizon=3),
                   replace(draws, response_uniforms=(('a', (0.,)*4), ('b', (0.,)*4))))
        with (patch.object(seeded, '_random_for_event', side_effect=AssertionError('no redraw')),
              patch.object(seeded, 'run_continuity_episode_supplied', side_effect=AssertionError('no interaction'))):
            for changed in changes:
                with self.subTest(draws=changed), self.assertRaises(ValueError):
                    run(bank, chapters, changed)
        foreign = SimulatorBank('other-environment', bank.items)
        with self.assertRaises(ValueError):
            run(foreign, chapters, draws)

    def test_unused_uniforms_and_early_stop_are_separate_from_generation(self):
        bank, chapters = domain(('a',))
        with patch.object(seeded, '_random_for_event', side_effect=zero_rng):
            draws = prepare(bank, chapters, horizon=4)
        with patch.object(seeded, '_random_for_event', side_effect=AssertionError('run cannot draw again')):
            result = run(bank, chapters, draws).result
        self.assertEqual(draws.logical_draw_counts, dict(initial_normal_events=1, response_uniform_events=4))
        self.assertEqual(len(result.observable), 3)
        self.assertEqual(result.stop_reason, 'ALL_ESTIMATED_MASTERED')
        self.assertFalse(result.budget_exhausted)
        self.assertEqual(len(dict(draws.response_uniforms)['a']), 4)


if __name__ == '__main__':
    unittest.main()
