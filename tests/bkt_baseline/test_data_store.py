from pathlib import Path
import tempfile
import unittest

import duckdb
import pandas as pd

from knowledge_tracing.bkt_baseline.pipeline import DataStore
from knowledge_tracing.bkt_baseline.splits import create_split_manifest


class DataStoreTests(unittest.TestCase):
    def test_persisted_global_assignment_is_used_by_both_partitions(self):
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            root = Path(root)
            canonical = root / "canonical"
            canonical.mkdir()
            frame = pd.DataFrame(
                {
                    "source_row": list(range(1, 11)),
                    "user_id": [f"u{i}" for i in range(10)],
                    "exercise": ["s"] * 10,
                    "time_done": [10] * 10,
                    "correct": [0, 1] * 5,
                    "suggested": [0] * 10,
                    "order_id": [1] * 10,
                }
            )
            con = duckdb.connect()
            con.register("frame", frame)
            con.execute(f"COPY frame TO '{canonical / 'part.parquet'}' (FORMAT PARQUET)")
            con.close()
            manifest = create_split_manifest(canonical, root / "splits", seed=42)
            self.assertEqual((manifest["development_students"], manifest["test_students"]), (8, 2))
            store = DataStore(canonical, root / "splits" / "assignments.parquet", root / "scratch")
            try:
                self.assertEqual(len(store.load_development_skill("s")), 8)
                self.assertEqual(len(store.load_test_skill("s")), 2)
                self.assertEqual(store.test_skills(), ["s"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
