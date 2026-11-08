"""Pure hand-computed source-rule fixtures; no gzip/corpus/native/model/RNG reads."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).with_name('analyze_fixed_controller_candidates02.py')
SPEC = importlib.util.spec_from_file_location('fixed_controller_pure_fixture',PATH)
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)  # Definitions only; analyzer main is not called.


class ControllerSourceRules(unittest.TestCase):
    def call(self,*,nodes=('A','B'),parents=None,chapters=None,mastered=(),ready=None,scores=None,
             visits=None,recent=(),chapter=None,chosen='A'):
        parents = parents if parents is not None else {n:[] for n in nodes}
        chapters = chapters if chapters is not None else {n:'chapter' for n in nodes}
        return a.controller(list(nodes),parents,chapters,set(mastered),list(nodes) if ready is None else ready,
            scores if scores is not None else {n:.5 for n in nodes},
            visits if visits is not None else {n:0 for n in nodes},list(recent),chapter,chosen)

    def test_native_chapter_superset_retained_and_coverage_certified(self):
        rows=[dict(concept_id='A',chapter='left'),dict(concept_id='B',chapter='right'),dict(concept_id='X',chapter='unused')]
        chapters,certificate=a.native_chapter_mapping(['A','B'],rows)
        self.assertEqual(chapters,{'A':'left','B':'right','X':'unused'})
        self.assertEqual((certificate['node_count'],certificate['input_chapter_rows'],certificate['input_unique_chapter_ids']),(2,3,3))
        self.assertEqual(certificate['missing_required_node_ids'],[])
        self.assertEqual(certificate['extra_unused_chapter_ids'],['X'])
        self.assertEqual(certificate['duplicate_chapter_ids'],[])

    def test_missing_required_chapter_is_rejected_without_default_or_node_drop(self):
        rows=[dict(concept_id='A',chapter='left'),dict(concept_id='X',chapter='extra')]
        with self.assertRaisesRegex(ValueError,'missing required node: B'):
            a.native_chapter_mapping(['A','B'],rows)

    def test_native_duplicate_chapter_rows_use_last_value_and_report_duplicate(self):
        rows=[dict(concept_id='A',chapter='old'),dict(concept_id='A',chapter='new'),dict(concept_id='B',chapter='right')]
        chapters,certificate=a.native_chapter_mapping(['A','B'],rows)
        self.assertEqual(chapters['A'],'new')
        self.assertEqual(certificate['duplicate_chapter_ids'],['A'])
        self.assertEqual(certificate['input_chapter_rows'],3)
        self.assertEqual(certificate['input_unique_chapter_ids'],2)

    def test_unused_chapters_do_not_enter_native_chapter_names_or_change_node_ties(self):
        rows=[dict(concept_id='A',chapter='left'),dict(concept_id='B',chapter='right'),dict(concept_id='X',chapter='unused')]
        chapters,certificate=a.native_chapter_mapping(['A','B'],rows)
        self.assertEqual(certificate['native_chapter_names_for_nodes'],['left','right'])
        before=deepcopy(chapters)
        result=self.call(chapters=chapters,visits={'A':0,'B':1},chapter='right',chosen='B')
        self.assertEqual(result['selected_key'],[.5,0,1,'B'])
        self.assertEqual(chapters,before)

    def test_frontier_parent_mastery_or_exposure_and_balance(self):
        parents={'A':[],'B':['A']}
        r=self.call(parents=parents,ready=['A'])
        self.assertEqual(r['R'],['A'])
        r=self.call(parents=parents,ready=['A','B'],visits={'A':6,'B':0},chosen='B')
        self.assertEqual(r['R'],['A','B']);self.assertEqual(r['B'],['B'])
        r=self.call(parents=parents,mastered=('A',),ready=['B'],chosen='B')
        self.assertEqual(r['R'],['B'])

    def test_empty_estimator_edges_cannot_replace_fixed_controller_edges(self):
        self.call(parents={'A':[],'B':['A']},ready=['A'])
        with self.assertRaisesRegex(ValueError,'M-to-R'):
            self.call(parents={'A':[],'B':[]},ready=['A'])

    def test_other_perturbed_controller_graph_is_rejected_by_stored_R(self):
        self.call(nodes=('A','B','C'),parents={'A':[],'B':['A'],'C':['B']},mastered=('A',),ready=['B'],chosen='B')
        with self.assertRaisesRegex(ValueError,'M-to-R'):
            self.call(nodes=('A','B','C'),parents={'A':[],'B':['A'],'C':['A']},mastered=('A',),ready=['B'],chosen='B')

    def test_all_mastered_returns_all_source_nodes(self):
        r=self.call(nodes=('B','A'),mastered=('A','B'),ready=['B','A'],chosen='A')
        self.assertEqual(r['R_branch'],'all_mastered');self.assertEqual(r['R'],['B','A'])

    def test_minimum_deficit_literal_branch_without_claiming_native_DAG_reachability(self):
        # Pure rule branch on a cyclic manufactured graph; actual parser rejects cycles.
        ready,branch=a.source_ready(['A','B'],{'A':['B'],'B':['A']},set(),{'A':6,'B':0})
        self.assertEqual((ready,branch),(['B'],'frontier'))
        ready,branch=a.source_ready(['A','B'],{'A':['B'],'B':['A']},set(),{'A':0,'B':0})
        self.assertEqual((ready,branch),(['A','B'],'minimum_unresolved'))

    def test_anti_repeat_filters_C_inside_ready(self):
        r=self.call(visits={'A':3,'B':0},recent=('A','A','A'),chosen='B')
        self.assertEqual(r['C'],['B']);self.assertEqual(r['C_branch'],'anti_repeat_within_R')

    def test_escape_can_choose_mastered_concept_outside_own_R(self):
        r=self.call(mastered=('B',),ready=['A'],visits={'A':3,'B':0},recent=('A','A','A'),chosen='B')
        self.assertEqual(r['R'],['A']);self.assertEqual(r['C'],['B'])
        self.assertEqual(r['C_branch'],'escape_all_nodes');self.assertNotIn(r['selected'],r['R'])

    def test_no_anti_repeat_alternative_keeps_R(self):
        r=self.call(nodes=('A',),visits={'A':3},recent=('A','A','A'))
        self.assertEqual(r['C_branch'],'anti_repeat_no_alternative_keep_R');self.assertEqual(r['B'],['A'])

    def test_balance_band_and_native_chapter_before_visits_order(self):
        r=self.call(nodes=('A','B','C'),visits={'A':0,'B':1,'C':2},
            chapters={'A':'old','B':'current','C':'current'},chapter='current',chosen='B')
        self.assertEqual(r['B'],['A','B']);self.assertEqual(r['selected_key'],[.5,0,1,'B'])

    def test_visits_then_lexical_ties_do_not_follow_source_node_order(self):
        r=self.call(nodes=('B','A'),visits={'A':1,'B':0},chosen='B')
        self.assertEqual(r['selected'],'B')
        r=self.call(nodes=('B','A'),chosen='A')
        self.assertEqual(r['selected'],'A')

    def test_wrong_CID_and_nonfinite_scores_fail_instead_of_filling_state(self):
        with self.assertRaisesRegex(ValueError,'CID ranking mismatch'):
            self.call(chosen='B')
        for invalid in (float('nan'),float('inf'),True):
            with self.subTest(invalid=repr(invalid)),self.assertRaisesRegex(ValueError,'finite native'):
                self.call(scores={'A':invalid,'B':.5})

    def test_controller_does_not_mutate_caller_state(self):
        args=(['A','B'],{'A':[],'B':['A']},{'A':'x','B':'y'},set(),['A'],
              {'A':.5,'B':.6},{'A':0,'B':0},[],None,'A')
        before=deepcopy(args);a.controller(*args);self.assertEqual(args,before)

    def test_logged_history_advances_only_after_snapshot_and_keeps_last_three(self):
        visits={'A':0,'B':0};recent=[];chapters={'A':'x','B':'y'}
        self.assertEqual((visits,recent),({'A':0,'B':0},[]))
        chapter=a.advance_logged(visits,recent,'A',chapters)
        self.assertEqual((visits,recent,chapter),({'A':1,'B':0},['A'],'x'))
        for cid in ('B','A','A'):
            chapter=a.advance_logged(visits,recent,cid,chapters)
        self.assertEqual((visits,recent,chapter),({'A':3,'B':1},['B','A','A'],'x'))

    def test_summary_retains_all_zero_joint_and_B_CID_cells(self):
        row=dict(M_changed=False,R_changed=False,C_changed=False,B_changed=False,CID_changed=False,full_preview_changed=False)
        summary=a.summarize([row],'hand-fixture')
        self.assertEqual(len(summary['joint_MRCBcid']),32);self.assertEqual(len(summary['B_CID_cells']),4)
        self.assertEqual(sum(r['count'] for r in summary['joint_MRCBcid']),1)
        self.assertEqual(sum(r['count']==0 for r in summary['joint_MRCBcid']),31)
        self.assertEqual(sum(r['count']==0 for r in summary['B_CID_cells']),3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
