"""Manufactured boolean fixtures only; no artifact, corpus, native or oracle read."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[2] / 'scripts/research/analyze_rq1_mastery_ready_masking.py'
SPEC = importlib.util.spec_from_file_location('rq1_masking_pure', SOURCE)
analyzer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyzer)


def simple_case(visits=0):
    nodes = ['parent', 'child']
    parents = {'parent': [], 'child': ['parent']}
    full = {'parent': True, 'child': False}
    empty = {'parent': False, 'child': False}
    counts = {'parent': visits, 'child': 0}
    return nodes, parents, full, empty, counts


class MasteryReadyMaskingTests(unittest.TestCase):
    def test_canonical_prefix_types_and_event_range(self):
        row = dict(seed=20000, profile='PG', event_id='0')
        self.assertEqual(analyzer.event_key(row), (20000, 'PG', 0))
        for field, value in [('seed', 20000.0), ('seed', True), ('profile', 'other'),
                             ('event_id', '00'), ('event_id', 0), ('event_id', '120')]:
            bad = dict(row)
            bad[field] = value
            with self.assertRaises(ValueError):
                analyzer.event_key(bad)

    def test_exposure_six_masks_parent_eligibility_but_not_parent_self_exclusion(self):
        row = analyzer.paired_predicates(*simple_case(6))
        self.assertEqual(row['concept_codes'], ['101', '000'])
        self.assertEqual(row['changed_parent_opportunities'], [dict(parent_index=0, child_index=1,
            prior_visits=6, exposure_masked=True, E_changed=False,
            A_changed=False, I_changed=False, F_changed=False)])

    def test_visits_five_exposes_child_readiness_difference(self):
        row = analyzer.paired_predicates(*simple_case(5))
        self.assertEqual(row['concept_codes'], ['101', '011'])
        parent = row['changed_parent_opportunities'][0]
        self.assertFalse(parent['exposure_masked'])
        self.assertTrue(parent['E_changed'] and parent['A_changed'] and parent['F_changed'])

    def test_other_unready_parent_masks_changed_parent_without_exposure(self):
        nodes = ['p', 'q', 'c']
        parents = {'p': [], 'q': [], 'c': ['p', 'q']}
        full = {'p': True, 'q': False, 'c': False}
        empty = {'p': False, 'q': False, 'c': False}
        row = analyzer.paired_predicates(nodes, parents, full, empty, dict.fromkeys(nodes, 0))
        self.assertEqual(row['concept_codes'][2], '000')
        self.assertTrue(row['changed_parent_opportunities'][0]['E_changed'])
        self.assertFalse(row['changed_parent_opportunities'][0]['A_changed'])
        # Exposure masks this parent's E, while a different parent can still change A.
        full['q'] = True
        counts = {'p': 6, 'q': 0, 'c': 0}
        row = analyzer.paired_predicates(nodes, parents, full, empty, counts)
        exposed, unexposed = row['changed_parent_opportunities']
        self.assertTrue(exposed['exposure_masked'] and exposed['A_changed'])
        self.assertFalse(exposed['E_changed'])
        self.assertTrue(unexposed['E_changed'] and unexposed['A_changed'])

    def test_child_self_mastered_can_mask_changed_all_parent_gate(self):
        nodes, parents, full, empty, counts = simple_case()
        full['child'] = empty['child'] = True
        row = analyzer.paired_predicates(nodes, parents, full, empty, counts)
        self.assertEqual(row['concept_codes'][1], '010')
        self.assertTrue(row['changed_parent_opportunities'][0]['A_changed'])
        self.assertFalse(row['changed_parent_opportunities'][0]['F_changed'])

    def test_root_and_parent_units_and_all_zero_cells_remain_distinct(self):
        measured = analyzer.paired_predicates(*simple_case(6))
        event = dict(**measured, full_R_branch='frontier', empty_R_branch='frontier',
                     M_changed=True, R_changed=True)
        summary = analyzer.summary_group([event], 'manufactured')
        self.assertEqual(summary['paired_events'], 1)
        self.assertEqual(summary['paired_concept_snapshots'], 2)
        self.assertEqual(summary['root_concept_snapshots'], 1)
        self.assertEqual(summary['all_parent_opportunities'], 1)
        self.assertEqual(summary['changed_mastery_parent_opportunities'], 1)
        self.assertEqual(len(summary['concept_IAF_cells']), 8)
        self.assertEqual(len(summary['parent_exposure_A_I_F_cells']), 16)
        self.assertEqual(len(summary['R_branch_pairs']), 9)
        self.assertEqual(sum(row['count'] for row in summary['concept_IAF_cells']), 2)
        self.assertEqual(sum(row['count'] for row in summary['parent_exposure_A_I_F_cells']), 1)
        self.assertEqual(summary['concept_IAF_cells'][1]['count'], 0)
        empty_summary = analyzer.summary_group([], 'empty')
        self.assertEqual(sum(row['count'] for row in empty_summary['concept_IAF_cells']), 0)
        self.assertEqual(sum(row['count'] for row in empty_summary['parent_exposure_A_I_F_cells']), 0)

    def test_bool_visit_missing_domain_and_duplicate_parent_rejected(self):
        nodes, parents, full, empty, counts = simple_case()
        counts['parent'] = True
        with self.assertRaises(ValueError):
            analyzer.paired_predicates(nodes, parents, full, empty, counts)
        counts['parent'] = 0
        with self.assertRaises(ValueError):
            analyzer.paired_predicates(nodes, parents, {'parent': True}, empty, counts)
        parents['child'] = ['parent', 'parent']
        with self.assertRaises(ValueError):
            analyzer.paired_predicates(nodes, parents, full, empty, counts)

    def test_frontier_and_fallback_are_not_conflated(self):
        nodes, parents, full, empty, counts = simple_case()
        frame = analyzer.predicate_frame(nodes, parents, full, counts)
        analyzer.frontier_matches(frame, ['child'], 'frontier')
        with self.assertRaises(ValueError):
            analyzer.frontier_matches(frame, ['child'], 'minimum_unresolved')
        mastered = dict.fromkeys(nodes, True)
        all_frame = analyzer.predicate_frame(nodes, parents, mastered, counts)
        analyzer.frontier_matches(all_frame, nodes, 'all_mastered')
        with self.assertRaises(ValueError):
            analyzer.frontier_matches(all_frame, [], 'frontier')
        # Cyclic manufactured domain exercises a retained source fallback branch.
        # The actual cached domain separately requires the pinned31-edge DAG.
        cyclic = {'parent': ['child'], 'child': ['parent']}
        blocked = analyzer.predicate_frame(nodes, cyclic, dict.fromkeys(nodes, False), counts)
        analyzer.frontier_matches(blocked, nodes, 'minimum_unresolved')

    def test_all_controller_fields_and_index_order_are_admitted_exactly(self):
        actual = dict(R=['c'], C=['c'], B=['c'], R_branch='frontier', C_branch='unchanged',
                      selected='c', selected_key=[.25, 1, 0, 'c'])
        recorded = dict(R=[1], C=[1], B=[1], R_branch='frontier', C_branch='unchanged',
                        selected_index=1, native_key=[.25, 1, 0, 'c'])
        analyzer.controller_match(actual, recorded, {'p': 0, 'c': 1}, lambda a, b: a == b)
        changed = deepcopy(recorded)
        changed['B'] = [0]
        with self.assertRaises(ValueError):
            analyzer.controller_match(actual, changed, {'p': 0, 'c': 1}, lambda a, b: a == b)
        changed = deepcopy(recorded)
        changed['native_key'][2] = 1
        with self.assertRaises(ValueError):
            analyzer.controller_match(actual, changed, {'p': 0, 'c': 1}, lambda a, b: a == b)


if __name__ == '__main__':
    unittest.main()
