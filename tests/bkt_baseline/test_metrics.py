import math
import unittest

import pandas as pd
import duckdb
from pathlib import Path
import tempfile

from knowledge_tracing.bkt_baseline.metrics import score_predictions, score_prediction_shards


class MetricsTests(unittest.TestCase):
    def test_binary_metrics_and_fixed_ece(self):
        frame = pd.DataFrame(
            {
                "user_id": ["a", "b"],
                "exercise": ["s", "s"],
                "suggested": [0, 1],
                "correct": [0, 1],
                "prediction": [0.25, 0.75],
            }
        )
        result = score_predictions(frame, {"s": 10})
        metrics = result["overall"]["metrics"]
        self.assertEqual(metrics["auc"], 1.0)
        self.assertAlmostEqual(metrics["log_loss"], -math.log(0.75))
        self.assertAlmostEqual(metrics["brier"], 0.0625)
        self.assertAlmostEqual(metrics["ece"], 0.25)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(result["suggested"]["suggested"]["metrics"]["auc"], None)

    def test_unseen_skill_is_counted_but_never_scored(self):
        frame = pd.DataFrame(
            {
                "user_id": ["a", "b", "c"],
                "exercise": ["s", "s", "new"],
                "suggested": [0, 1, 1],
                "correct": [0, 1, 1],
                "prediction": [0.25, 0.75, None],
            }
        )
        result = score_predictions(frame, {"s": 10})
        overall = result["overall"]
        self.assertEqual((overall["total_rows"], overall["scored_rows"]), (3, 2))
        self.assertEqual((overall["unseen_skills"], overall["unseen_rows"], overall["unseen_students"]), (1, 1, 1))
        self.assertAlmostEqual(overall["coverage"], 2 / 3)
        self.assertEqual(result["rarity"]["unseen"]["scored_rows"], 0)
        self.assertEqual(result["rarity"]["10-49"]["scored_rows"], 2)
        frame.loc[2, "prediction"] = 0.5
        with self.assertRaisesRegex(ValueError, "unseen"):
            score_predictions(frame, {"s": 10})

    def test_shard_scoring_matches_in_memory_metrics(self):
        frame = pd.DataFrame(
            {
                "source_row": [1, 2, 3], "user_id": ["a", "b", "c"],
                "exercise": ["s", "s", "new"], "correct": [0, 1, 1],
                "suggested": [0, 1, 1], "prediction": [0.25, 0.75, None],
                "train_skill_students": [10, 10, 0],
            }
        )
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            path = Path(root) / "predictions.parquet"
            con = duckdb.connect()
            con.register("frame", frame)
            con.execute(f"COPY frame TO '{path}' (FORMAT PARQUET)")
            con.close()
            disk = score_prediction_shards(path)
        memory = score_predictions(frame, {"s": 10})
        self.assertEqual(disk["overall"], memory["overall"])
        self.assertEqual(disk["suggested"], memory["suggested"])


if __name__ == "__main__":
    unittest.main()
