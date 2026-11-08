"""Eight manufactured boolean fixtures; no cache/native/model/oracle reads."""
import importlib.util
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('mastery_analysis_pure',Path(__file__).with_name('analyze_prediction_mastery_trace01.py'))
a=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(a)  # Definitions only.


def state(theta,pi):
    theta,pi=float(theta),float(pi)
    return [theta,pi,theta>=1250.,pi<=.55,theta>=1250. and pi<=.55]


def row(full,empty,fc=False,ec=False):
    return dict(seed=20000,profile='PG',event_id='0',query_index=0,full_state=full,empty_state=empty,
        full_raw_criterion=fc,empty_raw_criterion=ec)


class NativeBooleanDiagnostics(unittest.TestCase):
    def test_native_inclusive_theta_and_uncertainty_boundaries(self):
        self.assertEqual(a.gates(state(1250.,.55)),(True,True,True))
        self.assertEqual(a.gates(state(1249.,.55)),(False,True,False))
        self.assertEqual(a.gates(state(1250.,.5501)),(True,False,False))
    def test_impossible001_rejected_not_silently_counted(self):
        with self.assertRaises(ValueError):a.joint_cells(['001'])
        bad=state(1200.,.3);bad[4]=True
        with self.assertRaises(ValueError):a.gates(bad)
    def test_all_eight_cells_retained_including_zero(self):
        cells=a.joint_cells(['000','100','100'])
        self.assertEqual([c['signature'] for c in cells],[f'{i:03b}' for i in range(8)])
        self.assertEqual(sum(c['count'] for c in cells),3)
        self.assertEqual(cells[1]['count'],0)
    def test_one_event_can_have_two_concept_M_crossings(self):
        value=row([state(1300,.3),state(1400,.3)],[state(1200,.3),state(1100,.3)])
        summary=a.summarize([value],['A','B'],'pooled')
        self.assertEqual((summary['M_any_events'],summary['M_concept_crossings']),(1,2))
        self.assertEqual(summary['paired_concept_snapshots'],2)
    def test_raw_value_changes_can_be_masked_by_unchanged_gates(self):
        value=row([state(1201,.3)],[state(1200,.3)])
        summary=a.summarize([value],['A'],'pooled')
        self.assertEqual(summary['joint_predicate_change_cells'][0]['count'],1)
        self.assertEqual(summary['raw_theta_full_minus_empty']['numerically_changed'],1)
        self.assertEqual(summary['raw_theta_full_minus_empty']['mean_absolute'],1.)
        self.assertEqual(summary['M_any_events'],0)
    def test_nativeM_and_rawcriterion_table_is_agreement_not_truth(self):
        value=row([state(1200,.3)],[state(1200,.3)],fc=True,ec=False)
        summary=a.summarize([value],['A'],'pooled')
        cells=summary['queried_nativeM_vs_raw_reference']
        self.assertEqual([(r['native_M'],r['raw_reference_criterion'],r['count']) for r in cells],
            [(False,False,1),(False,True,1),(True,False,0),(True,True,0)])
        self.assertEqual(summary['queried_arm_rows'],2)
        self.assertNotIn('accuracy',summary)
    def test_paired_rawcriterion_change_and_queryM_change_are_separate(self):
        values=[row([state(1200,.3)],[state(1200,.3)],True,False),
            row([state(1300,.3)],[state(1200,.3)],False,False)]
        summary=a.summarize(values,['A'],'pooled')
        cells=summary['paired_query_Mchange_vs_raw_criterion_change']
        self.assertEqual([r['count'] for r in cells],[0,1,1,0])
        self.assertEqual(sum(r['count'] for r in cells),2)
    def test_empty_delta_summaries_null_and_nonfinite_rejected(self):
        empty=a.finite_delta_summary([])
        self.assertIsNone(empty['mean']);self.assertIsNone(empty['maximum_absolute'])
        zeros=a.finite_delta_summary([0.,-0.])
        self.assertEqual((zeros['zero'],zeros['numerically_changed'],zeros['mean_absolute']),(2,0,0.))
        with self.assertRaises(ValueError):a.finite_delta_summary([float('nan')])


if __name__=='__main__':unittest.main(verbosity=2)
