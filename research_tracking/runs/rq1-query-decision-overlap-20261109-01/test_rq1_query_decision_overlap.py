"""Known-answer và rejection fixtures cho phép join snapshot; không model/data."""
import copy
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[2]/'scripts/research/analyze_rq1_query_decision_overlap.py'
spec = importlib.util.spec_from_file_location('rq1_query_overlap_under_test', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    left, right = [], []
    for event in range(8):
        a, b, d = (bool(event & bit) for bit in (4, 2, 1))
        left.append(dict(seed=42, profile='fixture', event_id=str(event), query_index=0,
                         M_any=a, M_changed_indices=[0] if a else [],
                         query_native_M_changed=a, query_raw_criterion_changed=b))
        right.append(dict(seed=42, profile='fixture', event_id=str(event), query={'concept':'c0'},
                          M_changed=a, R_changed=False, C_changed=False, B_changed=False,
                          CID_changed=d, full_preview_changed=d, full={'selected_index':0},
                          empty={'selected_index':int(d)}))
    return left, right


class JoinTests(unittest.TestCase):
    def test_all_eight_cells_known_answer(self):
        m, c = fixture(); result = module.analyze(m, c, ['c0', 'c1'])
        self.assertEqual(result['groups']['pooled']['cells'], {f'{i:03b}':1 for i in range(8)})
        self.assertEqual(result['groups']['pooled']['CID_changes'], 4)
        self.assertEqual(result['new_independent_N'], 0)
    def test_order_independent_and_no_input_mutation(self):
        m, c = fixture(); before = copy.deepcopy((m, c))
        self.assertEqual(module.analyze(m, c, ['c0', 'c1']), module.analyze(m[::-1], c[::-1], ['c0', 'c1']))
        self.assertEqual((m, c), before)
    def test_duplicate_rejected(self):
        m, c = fixture()
        with self.assertRaises(ValueError): module.analyze(m+[m[0]], c, ['c0'])
    def test_missing_rejected(self):
        m, c = fixture()
        with self.assertRaises(ValueError): module.analyze(m, c[:-1], ['c0'])
    def test_query_mismatch_rejected(self):
        m, c = fixture(); c[0]['query']['concept']='other'
        with self.assertRaises(ValueError): module.analyze(m, c, ['c0'])
    def test_M_mismatch_rejected(self):
        m, c = fixture(); c[0]['M_changed']=True
        with self.assertRaises(ValueError): module.analyze(m, c, ['c0'])
    def test_CID_mismatch_rejected(self):
        m, c = fixture(); c[0]['CID_changed']=True
        with self.assertRaises(ValueError): module.analyze(m, c, ['c0'])
    def test_boolean_not_integer(self):
        m, c = fixture(); m[0]['query_native_M_changed']=0
        with self.assertRaises(ValueError): module.analyze(m, c, ['c0'])


if __name__ == '__main__':
    unittest.main()
