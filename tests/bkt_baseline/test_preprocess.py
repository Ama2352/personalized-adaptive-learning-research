import csv
from pathlib import Path
import tempfile
import unittest

import duckdb

from knowledge_tracing.bkt_baseline.preprocess import ORIGINAL_COLUMNS, preprocess_csv


class PreprocessTests(unittest.TestCase):
    def test_exact_dedupe_lineage_and_timestamp_tie_order(self):
        tmp_parent = Path("artifacts/bkt_baseline/test_tmp")
        tmp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_parent) as temporary:
            root = Path(temporary)
            input_csv = root / "raw.csv"

            def row(problem, correct, time, problem_type="x,y"):
                values = dict.fromkeys(ORIGINAL_COLUMNS, "")
                values.update(
                    user_id="u",
                    exercise="s",
                    problem_type=problem_type,
                    problem_number=problem,
                    suggested="false",
                    time_done=str(time),
                    correct=correct,
                )
                return values

            with input_csv.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=ORIGINAL_COLUMNS)
                writer.writeheader()
                writer.writerows(
                    [
                        row("01", "false", 10),
                        row("01", "false", 10),
                        row("1", "false", 10),
                        row("01", "true", 10),
                        row("2", "true", 12),
                    ]
                )

            manifest = preprocess_csv(input_csv, root / "derived", chunk_size=2)
            self.assertEqual((manifest["raw_rows"], manifest["canonical_rows"]), (5, 4))
            self.assertEqual(manifest["duplicate_rows_removed"], 1)
            con = duckdb.connect()
            canonical = con.execute(
                "SELECT source_row, time_done, correct, order_id FROM "
                "read_parquet(?) ORDER BY order_id",
                [str(root / "derived" / "canonical" / "**" / "*.parquet")],
            ).fetchall()
            self.assertEqual(canonical, [(1, 10, 0, 1), (3, 10, 0, 2), (4, 10, 1, 3), (5, 12, 1, 4)])
            lineage = con.execute(
                "SELECT duplicate_source_row, retained_source_row FROM read_parquet(?)",
                [str(root / "derived" / "duplicate_lineage.parquet")],
            ).fetchall()
            self.assertEqual(lineage, [(2, 1)])


if __name__ == "__main__":
    unittest.main()
