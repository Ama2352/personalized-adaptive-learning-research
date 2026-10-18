from pathlib import Path
import unittest

from knowledge_tracing.bkt_baseline.config import DEFAULT_ARTIFACTS, DEFAULT_CSV, PROJECT_ROOT


class ProjectPathTests(unittest.TestCase):
    def test_src_package_resolves_stable_project_data_paths(self):
        expected_root = Path(__file__).resolve().parents[2]
        self.assertEqual(PROJECT_ROOT, expected_root)
        self.assertEqual(DEFAULT_CSV, expected_root / "dataset" / "junyi_ProblemLog_original.csv")
        self.assertEqual(DEFAULT_ARTIFACTS, expected_root / "artifacts" / "bkt_baseline")
        self.assertTrue(DEFAULT_CSV.is_file())


if __name__ == "__main__":
    unittest.main()
