"""Kiểm generator trên đồ thị giả nhỏ, không dùng graph Junyi thật."""

from collections import Counter
import json
from pathlib import Path
import sys
import unittest

from generator import construct_control, support_bin
from knowledge_tracing.shared_kt import PrerequisiteGraph


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.graph = PrerequisiteGraph.from_edges(('a', 'b', 'c', 'd'), (('a', 'c'), ('b', 'd')))
        self.phase = dict(scope='select_train80', outer_fold=4, phase_view_identity='a' * 64,
                          encoding_identity='b' * 64, roles_sha256='c' * 64, cache_manifest_sha256='d' * 64)
        self.recipe = json.loads((Path(__file__).parent / 'recipe.json').read_text())
        self.recipe.update(swaps=1, expected_changed_entries=4)
        self.kwargs = dict(graph=self.graph, topics=dict.fromkeys(self.graph.nodes, 'topic'),
                           areas=dict.fromkeys(self.graph.nodes, 'area'),
                           train_support=dict.fromkeys(self.graph.nodes, 100),
                           phase=self.phase, recipe=self.recipe, seed=0)

    def test_degree_and_strata_preserved(self):
        result = construct_control(**self.kwargs)
        self.assertEqual(result['status'], 'CONSTRUCTED_PENDING_NEW_EDGE_EXPOSURE_AUDIT')
        self.assertEqual(set(map(tuple, result['edges'])), {('a', 'd'), ('b', 'c')})
        for endpoint in (0, 1):
            self.assertEqual(Counter(e[endpoint] for e in result['edges']),
                             Counter(e[endpoint] for e in self.graph.edges))

    def test_deterministic_and_no_global_rng(self):
        import random
        before = random.getstate()
        self.assertEqual(construct_control(**self.kwargs), construct_control(**self.kwargs))
        self.assertEqual(before, random.getstate())

    def test_new_edge_exposure_not_inferred(self):
        result = construct_control(**self.kwargs)
        self.assertFalse(result['benchmark_eligible'])
        self.assertEqual(result['effective_exposure_status'], 'NOT_MEASURED')
        self.assertIsNone(result['active_new_edge_counts'])

    def test_infeasible_does_not_reduce_swaps(self):
        self.recipe['swaps'] = 2
        result = construct_control(**self.kwargs)
        self.assertEqual(result['status'], 'INCONCLUSIVE_CONSTRUCTION_UNAVAILABLE')
        self.assertEqual(result['requested_swaps'], 2)
        self.assertEqual(result['retries'], 0)

    def test_topic_mismatch_constrains_swaps(self):
        self.kwargs['topics'] = {node: node for node in self.graph.nodes}
        result = construct_control(**self.kwargs)
        self.assertEqual(result['status'], 'INCONCLUSIVE_CONSTRUCTION_UNAVAILABLE')

    def test_support_bins_constrain_swaps(self):
        self.kwargs['train_support'] = dict(a=1, b=1000, c=100, d=0)
        result = construct_control(**self.kwargs)
        self.assertEqual(result['status'], 'INCONCLUSIVE_CONSTRUCTION_UNAVAILABLE')

    def test_support_bin_boundaries(self):
        self.assertEqual([support_bin(n) for n in (0, 1, 9, 10, 99, 100, 999, 1000, 9999, 10000)],
                         ['0', '1-9', '1-9', '10-99', '10-99', '100-999', '100-999', '1000-9999', '1000-9999', '10000+'])

    def test_foreign_bin_recipe_rejected(self):
        self.recipe['support_bins'] = ['0', '1-2', '3-5', '6+']
        with self.assertRaises(ValueError):
            construct_control(**self.kwargs)

    def test_negative_and_bool_support_rejected(self):
        for value in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                support_bin(value)

    def test_wrong_phase_rejected(self):
        for scope, fold in (('select_validation10', 4), ('refit_train90', 4), ('select_train80', 0)):
            self.phase.update(scope=scope, outer_fold=fold)
            with self.assertRaises(ValueError):
                construct_control(**self.kwargs)

    def test_missing_pin_rejected(self):
        del self.phase['encoding_identity']
        with self.assertRaises(ValueError):
            construct_control(**self.kwargs)

    def test_foreign_support_rejected(self):
        self.kwargs['train_support']['foreign'] = 1
        with self.assertRaises(ValueError):
            construct_control(**self.kwargs)

    def test_undeclared_seed_rejected(self):
        self.kwargs['seed'] = 999
        with self.assertRaises(ValueError):
            construct_control(**self.kwargs)

    def test_incomplete_static_mapping_rejected(self):
        del self.kwargs['areas']['a']
        with self.assertRaises(ValueError):
            construct_control(**self.kwargs)

    def test_cycle_rejected_as_unavailable(self):
        graph = PrerequisiteGraph.from_edges(('a', 'b', 'c', 'd'), (('a', 'b'), ('b', 'a')))
        self.kwargs['graph'] = graph
        result = construct_control(**self.kwargs)
        self.assertEqual(result['status'], 'INCONCLUSIVE_CONSTRUCTION_UNAVAILABLE')

    def test_no_torch_loaded(self):
        self.assertNotIn('torch', sys.modules)


if __name__ == '__main__':
    unittest.main(verbosity=2)
