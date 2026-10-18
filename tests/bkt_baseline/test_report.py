import json
from pathlib import Path
import tempfile
import unittest

from knowledge_tracing.bkt_baseline.report import render_report


class ReportTests(unittest.TestCase):
    def test_partial_report_labels_unmeasured_phases(self):
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            root = Path(root)
            (root / "derived").mkdir()
            (root / "derived" / "manifest.json").write_text(
                json.dumps({"raw_rows": 5, "canonical_rows": 4, "duplicate_rows_removed": 1}), encoding="utf-8"
            )
            output = root / "report.md"
            render_report(root, output)
            text = output.read_text(encoding="utf-8")
            self.assertIn("5", text)
            self.assertIn("4", text)
            self.assertIn("Chưa chạy", text)
            self.assertNotIn("AUC: 0.", text)

    def test_report_discloses_measured_scale_blocker(self):
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            root = Path(root)
            (root / "scale_probe_status.json").write_text(
                json.dumps({
                    "status": "stopped_after_one_fit",
                    "skill": "addition_1",
                    "train_rows": 571963,
                    "wall_seconds": 1584.05,
                    "num_fits": 1,
                    "peak_rss_gb": 0.45,
                    "estimated_cv_hours": 63.72,
                    "estimate_method": "linear extrapolation",
                    "reason": "measured scale makes complete CV impractical locally",
                }), encoding="utf-8"
            )
            output = root / "report.md"
            (root / "cv").mkdir()
            (root / "cv" / "cv_progress.json").write_text(
                json.dumps({"protocol": {"skills": [f"s{i}" for i in range(720)], "folds": 5, "num_fits": 1}, "completed": {"s0|0": {}}}),
                encoding="utf-8",
            )
            render_report(root, output)
            text = output.read_text(encoding="utf-8")
            self.assertIn("addition_1", text)
            self.assertIn("1,584.05", text)
            self.assertIn("63.72", text)
            self.assertIn("Ngoại suy tuyến tính", text)
            self.assertIn("1/3600", text)
            self.assertIn("chưa có metric gộp", text)


if __name__ == "__main__":
    unittest.main()
