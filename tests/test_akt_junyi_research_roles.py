"""Các lỗi có thể làm lẫn người học hoặc sai tỷ lệ của Junyi research roles."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles


class JunyiResearchRoleTests(unittest.TestCase):
    def rows(self, count=40):
        return [(f'user-{index}', index % 5, 'development') for index in range(count)]

    def test_disjoint_exhaustive_and_outer_fold_preserved(self):
        rows = self.rows()
        result = make_junyi_research_roles(rows)
        groups = [set(result.train_users), set(result.selection_users),
                  set(result.calibration_users), set(result.outer_validation_users)]
        self.assertEqual(set.union(*groups), {row[0] for row in rows})
        self.assertEqual(sum(map(len, groups)), len(rows))
        self.assertEqual(groups[-1], {user for user, fold, _ in rows if fold == 4})
        self.assertEqual([len(group) for group in groups], [24, 4, 4, 8])

    def test_order_invariant_and_reproducible(self):
        rows = self.rows()
        self.assertEqual(make_junyi_research_roles(rows), make_junyi_research_roles(reversed(rows)))
        self.assertEqual(make_junyi_research_roles(rows).identity, make_junyi_research_roles(rows).identity)

    def test_rounding_for_full_outer_train_size(self):
        rows = [(str(index), 0, 'development') for index in range(158468)]
        rows.append(('outer', 4, 'development'))
        result = make_junyi_research_roles(rows)
        self.assertEqual((len(result.train_users), len(result.selection_users), len(result.calibration_users)),
                         (126774, 15847, 15847))

    def test_reject_duplicate_learners(self):
        rows = self.rows()
        with self.assertRaises(ValueError):
            make_junyi_research_roles(rows + [rows[0]])

    def test_reject_other_partition(self):
        with self.assertRaises(ValueError):
            make_junyi_research_roles(self.rows() + [('other', 0, 'test')])

    def test_reject_invalid_fold_or_identity(self):
        for invalid in [('', 0, 'development'), ('u', True, 'development'), ('u', 5, 'development')]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                make_junyi_research_roles(self.rows() + [invalid])

    def test_reject_invalid_fields_before_normalization(self):
        invalid_rows = [(None, 0, 'development'), (True, 0, 'development'),
                        (1.25, 0, 'development'), ('u', 0.5, 'development'),
                        ('u', True, 'development')]
        for invalid in invalid_rows:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                make_junyi_research_roles(self.rows() + [invalid])

    def test_integer_identifiers_share_the_canonical_string_namespace(self):
        rows = [(index, index % 5, 'development') for index in range(40)]
        strings = [(str(user), fold, partition) for user, fold, partition in rows]
        self.assertEqual(make_junyi_research_roles(rows), make_junyi_research_roles(strings))
        with self.assertRaises(ValueError):
            make_junyi_research_roles(rows + [('0', 0, 'development')])

    def test_reject_small_or_missing_validation(self):
        for rows in [[], self.rows(10), [('u'+str(i), 0, 'development') for i in range(20)]]:
            with self.subTest(count=len(rows)), self.assertRaises(ValueError):
                make_junyi_research_roles(rows)


if __name__ == '__main__':
    unittest.main()
