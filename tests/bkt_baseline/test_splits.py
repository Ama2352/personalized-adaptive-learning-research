import unittest

from knowledge_tracing.bkt_baseline.splits import assign_students


class SplitTests(unittest.TestCase):
    def test_global_assignment_is_balanced_disjoint_and_input_order_independent(self):
        ids = [f"u{i}" for i in range(10)]
        first = assign_students(ids + ["u0"], seed=42)
        second = assign_students(list(reversed(ids)), seed=42)
        self.assertEqual(first.to_dict("records"), second.to_dict("records"))
        self.assertEqual(len(first), 10)
        self.assertEqual((first.partition == "development").sum(), 8)
        self.assertEqual((first.partition == "test").sum(), 2)
        self.assertEqual(sorted(first.loc[first.partition == "development", "fold"].value_counts().tolist()), [1, 1, 2, 2, 2])
        self.assertTrue((first.loc[first.partition == "test", "fold"] == -1).all())
        self.assertEqual(set(first.user_id), set(ids))

    def test_same_student_across_skills_has_one_partition(self):
        assignments = assign_students(["repeat", "other", "repeat"], seed=42)
        self.assertEqual((assignments.user_id == "repeat").sum(), 1)


if __name__ == "__main__":
    unittest.main()
