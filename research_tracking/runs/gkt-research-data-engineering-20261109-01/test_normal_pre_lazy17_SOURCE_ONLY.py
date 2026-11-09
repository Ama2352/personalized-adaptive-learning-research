"""Unittest normal-entry với corpus typed dựng tay, không corpus publication/teacher.

SHA giả chỉ là metadata fixture, không attestation reader/native/trained. NumPy
được import gián tiếp bởi shared data geometry; Torch/model không được import.
"""
from dataclasses import asdict, fields, replace
import builtins
import json
import sys
import unittest

from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, PublicResearchCorpus, PublicRoleData, PUBLIC_FILES
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import (
    ResearchSplitPlan, ResearchProvenance, SelectionFreeze, audit_research_shard,
)

H = 'a'*64


def seal(corpus):
    payload = dict(corpus_id=corpus.corpus_id, plan=asdict(corpus.plan), bank=asdict(corpus.bank),
        roles=[asdict(role) for role in corpus.roles], corpus_manifest_json=corpus.corpus_manifest_json,
        files_sha256=corpus.files_sha256, done_sha256=corpus.done_sha256, source_bindings=corpus.source_bindings)
    return replace(corpus, content_sha256=identity_hash(payload))


def role_data(plan, bank, limits, role, trajectories):
    provenance = ResearchProvenance(role, plan.identity, plan.split_plan.identity, identity_hash(bank.identity),
        'b'*64, (('collector', 'c'*64), ('environment', 'd'*64)), 'e'*64,
        'handmade-observable-policy', 'unix_seconds_utc', 'UTC', False)
    audit = audit_research_shard(trajectories, plan=plan, bank=bank, role=role, provenance=provenance,
        expected_provenance_sha256=provenance.identity, limits=limits.shard_limits, reference_items=bank.item_ids)
    counts = tuple(sum(o.correct == label for t in trajectories for o in t.observations) for label in (0, 1))
    return PublicRoleData(role, provenance, trajectories, json.dumps({'fixture_only': True}),
        json.dumps(audit, sort_keys=True), counts)


def fixture(difficulties=(1050, 1200, 1350)):
    plan = ResearchSplitPlan('gkt-handmade-not-collected', 42, 10, 1, H)
    bank = SimulatorBank('gkt-unverified-handmade-bank', tuple(
        SimulatorItem(f'i{concept:02}-{difficulty}', f'c{concept:02}', difficulty)
        for concept in range(28) for difficulty in difficulties))
    limits = CorpusReadLimits(2**20, 8*2**20, 2**18, 8, 8, 80, 10.)
    ordinals = {a.learner_id: i for i, a in enumerate(plan.split_plan.assignments())}
    roles = []
    for role, indices in (('train', (0, 1, 0, 1)), ('selection', (0, 2, 1, 0)),
                          ('calibration', (1, 0, 1, 0))):
        trajectories = tuple(sorted((ObservableTrajectory(a.learner_id, plan.split_plan.identity,
            identity_hash(bank.identity), 'handmade-observable-policy', tuple(
                Observation(ItemQuery(bank.item_ids[index], 100+rank,
                    ordinals[a.learner_id]*1000000+rank+1), rank % 2)
                for rank, index in enumerate(indices))) for a in plan.split_plan.assignments(role)),
            key=lambda trajectory: trajectory.learner_id))
        roles.append(role_data(plan, bank, limits, role, trajectories))
    return seal(PublicResearchCorpus('handmade-not-published', plan, bank, tuple(roles),
        json.dumps({'fixture_only': True}), tuple((name, H, 1) for name in PUBLIC_FILES),
        H, (('fixture-only-source', H),), limits, 10, 0., ''))


def change_labels(corpus, role, learner_index, rank):
    value = corpus.role_data(role)
    trajectories = list(value.trajectories)
    trajectory = trajectories[learner_index]
    observations = list(trajectory.observations)
    observations[rank] = replace(observations[rank], correct=1-observations[rank].correct)
    trajectories[learner_index] = replace(trajectory, observations=tuple(observations))
    updated = role_data(corpus.plan, corpus.bank, corpus.limits, role, tuple(trajectories))
    return seal(replace(corpus, roles=tuple(updated if r.role == role else r for r in corpus.roles)))


class GKTResearchDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = builtins.__import__
        before = {name for name in sys.modules if name == 'torch' or name.startswith('torch.')}
        def checked(name, *args, **kwargs):
            if name == 'torch' or name.startswith('torch.') or name.startswith((
                'knowledge_tracing.gkt.recurrent', 'knowledge_tracing.sakt.model', 'knowledge_tracing.akt.model')):
                raise AssertionError('Không import model/Torch trong data-only candidate')
            return original(name, *args, **kwargs)
        builtins.__import__ = checked
        try:
            import knowledge_tracing.gkt.research_data as data
            cls.data = data
        finally:
            builtins.__import__ = original
        assert {name for name in sys.modules if name == 'torch' or name.startswith('torch.')} == before

    def setUp(self):
        self.corpus = fixture()
        self.recipe = self.data.GKTResearchDataRecipe('concept', 'full_prefix', 'query_only', 'unsupported_history')
        self.graph = self.data.GKTResearchGraphBinding(identity_hash(self.corpus.bank.identity),
            tuple(f'c{i:02}' for i in range(28)), (('c00', 'c01'),), H,
            self.corpus.role_data('train').audit['audit']['shard_sha256'], 'declared_static_expert')
        self.limits = self.data.GKTResearchInputLimits(1000, 10000)

    def view(self, scope='select_train80', **kwargs):
        return self.data.prepare_gkt_research_view(self.corpus, scope=scope, recipe=self.recipe,
            graph_binding=self.graph, **kwargs)

    def rows(self, view, training=False):
        return tuple(self.data.iter_gkt_research_inputs(view, training=training, limits=self.limits))

    def freeze(self):
        return SelectionFreeze(self.corpus.plan.identity, identity_hash(self.corpus.bank.identity),
            self.corpus.role_data('train').audit['audit']['shard_sha256'],
            self.corpus.role_data('selection').audit['audit']['shard_sha256'], 'f'*64, 2, 'raw_selection_before_refit')

    def test_bank_registry_distinct_from_train_observed_vocabulary(self):
        view = self.view()
        self.assertEqual(len(view.item_node_registry), 84)
        self.assertEqual(len(view.graph.node_ids), 28)
        self.assertEqual(len(view.train_item_node_map), 2)
        self.assertEqual(len({node for _, node in view.train_item_node_map}), 1)
        self.assertNotIn('corpus', vars(view))

    def test_public_shard_boundary_rejects_invalid_reference_bank(self):
        for levels in ((1050, 1200), (1050, 1200, 1201)):
            with self.subTest(levels=levels), self.assertRaisesRegex(ValueError, 'protocol V1 requires'):
                fixture(levels)

    def test_full_chronological_population_and_prefix_inputs(self):
        view = self.view()
        rows = self.rows(view)
        truth = self.data.gkt_research_scoring_targets(view)
        self.assertEqual(len(rows), 32)
        for row, target in zip(rows, truth, strict=True):
            self.assertEqual((row.learner_id, row.query, row.global_rank, row.history_sha256),
                (target.learner_id, target.query, target.global_rank, target.history_sha256))
            self.assertEqual(row.history_hash_scheme, 'observable-prefix-chain-v1')
            self.assertEqual(row.history_used, row.global_rank)
            self.assertEqual(len(row.past_queries), row.global_rank)
            self.assertEqual(row.past_responses, tuple(i % 2 for i in range(row.global_rank)))
            self.assertTrue(all(q.timestamp < row.query.timestamp for q in row.past_queries))

    def test_current_label_only_enters_next_prefix(self):
        left = self.rows(self.view())
        self.corpus = change_labels(self.corpus, 'train', 0, 1)
        self.graph = replace(self.graph, train80_shard_sha256=self.corpus.role_data('train').audit['audit']['shard_sha256'])
        right = self.rows(self.view())
        for index in (0, 1):
            self.assertEqual((left[index].past_queries, left[index].past_responses, left[index].history_sha256),
                (right[index].past_queries, right[index].past_responses, right[index].history_sha256))
        self.assertNotEqual(left[2].past_responses, right[2].past_responses)
        self.assertNotEqual(left[2].history_sha256, right[2].history_sha256)

    def test_future_and_peer_labels_do_not_change_current_features(self):
        left = self.rows(self.view())
        self.corpus = change_labels(change_labels(self.corpus, 'train', 0, 3), 'train', 1, 0)
        self.graph = replace(self.graph, train80_shard_sha256=self.corpus.role_data('train').audit['audit']['shard_sha256'])
        right = self.rows(self.view())
        for a, b in zip(left[:3], right[:3], strict=True):
            self.assertEqual((a.query, a.past_queries, a.past_responses, a.history_sha256),
                (b.query, b.past_queries, b.past_responses, b.history_sha256))

    def test_selection_oov_keeps_all_rows_and_blocks_later_full_prefix(self):
        train = self.view()
        rows = self.rows(self.view('raw_selection10', encoding=train.encoding))
        self.assertEqual([r.support_reason for r in rows],
            ['cold_query_only', 'oov_item', 'unsupported_history', 'unsupported_history'])
        for row in rows[1:]:
            self.assertFalse(row.eligible)
            self.assertIsNone(row.query_node_id)
            self.assertIsNone(row.past_responses)
            self.assertIsNone(row.past_node_ids)
            self.assertEqual(row.history_used, 0)

    def test_training_labels_are_separate_wrappers(self):
        rows = self.rows(self.view(), training=True)
        self.assertTrue(all(type(row) is self.data.GKTResearchTrainingTarget for row in rows))
        self.assertEqual([row.target for row in rows[:4]], [0, 1, 0, 1])
        self.assertFalse({'correct', 'target', 'oracle', 'theta'} & {f.name for f in fields(rows[0].inputs)})

    def test_prediction_roles_cannot_train_or_fit_vocabulary(self):
        with self.assertRaises(ValueError):
            self.view('raw_selection10')
        selection = self.view('raw_selection10', encoding=self.view().encoding)
        with self.assertRaises(ValueError):
            self.rows(selection, training=True)
        with self.assertRaises(ValueError):
            self.view('final')

    def test_refit_encoding_changes_lineage_and_keeps_graph_train80(self):
        train = self.view()
        with self.assertRaises(ValueError):
            self.view('refit_union90')
        refit = self.view('refit_union90', selection_freeze=self.freeze())
        self.assertNotEqual(train.encoding.identity, refit.encoding.identity)
        self.assertEqual(len(refit.train_item_node_map), 3)
        self.assertEqual(refit.graph.identity, train.graph.identity)
        self.assertEqual({r.origin_role for r in self.rows(refit)}, {'train', 'selection'})

    def test_calibration_requires_refit_encoding_and_same_freeze(self):
        train = self.view()
        with self.assertRaises(ValueError):
            self.view('calibration_predict', encoding=train.encoding, selection_freeze=self.freeze())
        refit = self.view('refit_union90', selection_freeze=self.freeze())
        calibration = self.view('calibration_predict', encoding=refit.encoding, selection_freeze=self.freeze())
        self.assertEqual(len(self.rows(calibration)), 4)
        with self.assertRaises(ValueError):
            self.rows(calibration, training=True)

    def test_graph_node_edge_and_kind_rejections(self):
        for changes in ({'node_ids': self.graph.node_ids[:-1]}, {'edges': (('c00', 'c00'),)},
                {'edges': (('c00', 'c01'), ('c00', 'c01'))},
                {'edges': (('c00', 'c01'), ('c01', 'c00'))}, {'graph_kind': 'learned'},
                {'graph_kind': 'oracle'}, {'graph_kind': 'engineering'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.graph, **changes)

    def test_wrong_domain_and_train_role_rejected(self):
        for changes in ({'domain_sha256': 'b'*64}, {'train80_shard_sha256': 'b'*64}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.data.prepare_gkt_research_view(self.corpus, scope='select_train80', recipe=self.recipe,
                    graph_binding=replace(self.graph, **changes))

    def test_recipe_does_not_adopt_difficulty_or_truncated_history(self):
        for changes in ({'node_unit': 'exercise_tag'}, {'history_policy': 'window'},
                        {'first_target_policy': 'skip'}, {'oov_policy': 'reset'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.recipe, **changes)

    def test_target_and_expanded_prefix_caps_reject_before_first_yield(self):
        view = self.view()
        for limits in (self.data.GKTResearchInputLimits(31, 10000), self.data.GKTResearchInputLimits(1000, 47)):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                next(self.data.iter_gkt_research_inputs(view, training=False, limits=limits))
        exact = self.data.GKTResearchInputLimits(32, 48)
        self.assertEqual(len(tuple(self.data.iter_gkt_research_inputs(view, training=False, limits=exact))), 32)

    def test_nested_metadata_tamper_rejected_at_boundary(self):
        view = self.view()
        object.__setattr__(view.graph, 'topology_file_sha256', 'b'*64)
        with self.assertRaises(ValueError):
            next(self.data.iter_gkt_research_inputs(view, training=False, limits=self.limits))

    def test_inputs_immutable_and_repeated_prediction_identical(self):
        view = self.view()
        left, right = self.rows(view), self.rows(view)
        self.assertEqual(left, right)
        self.assertIsInstance(left[1].past_responses, tuple)
        with self.assertRaises(AttributeError):
            left[1].history_used = 999

    def test_calibration_labels_do_not_affect_train_data(self):
        left = self.rows(self.view())
        self.corpus = change_labels(self.corpus, 'calibration', 0, 0)
        right = self.rows(self.view())
        self.assertEqual(left, right)


if __name__ == '__main__':
    unittest.main()
