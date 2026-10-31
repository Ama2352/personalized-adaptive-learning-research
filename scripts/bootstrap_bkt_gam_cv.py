"""Paired learner bootstrap over already saved Development CV predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from knowledge_tracing.paired_bootstrap import PairedFoldSufficientStats, paired_cluster_bootstrap  # noqa: E402


GAM_ROOT = ROOT / "experiments/gam_kt/results/wsl_cpp/cv"
BKT_ROOT = ROOT / "experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv"


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def load_fold_stats(connection: duckdb.DuckDBPyConnection, fold: int) -> tuple[PairedFoldSufficientStats, dict]:
    gam_path = _sql_path(GAM_ROOT / f"fold={fold}/predictions/*.parquet")
    bkt_path = _sql_path(BKT_ROOT / f"fold={fold}/*.parquet")
    connection.execute(f"CREATE OR REPLACE TEMP VIEW gam AS SELECT * FROM read_parquet('{gam_path}')")
    connection.execute(f"CREATE OR REPLACE TEMP VIEW bkt AS SELECT * FROM read_parquet('{bkt_path}')")
    audit = connection.execute("""
        SELECT COUNT(*) AS joined_rows,
               COUNT(DISTINCT g.source_row) AS unique_source_rows,
               COUNT(*) FILTER (WHERE g.source_row IS DISTINCT FROM b.source_row
                    OR g.user_id IS DISTINCT FROM b.user_id
                    OR g.exercise IS DISTINCT FROM b.exercise
                    OR g.correct IS DISTINCT FROM b.correct
                    OR g.suggested IS DISTINCT FROM b.suggested) AS identity_mismatches,
               COUNT(*) FILTER (WHERE g.train_support_students IS DISTINCT FROM b.train_skill_students) AS support_mismatches,
               COUNT(*) FILTER (WHERE g.is_fallback) AS fallback_rows,
               COUNT(*) FILTER (WHERE (NOT g.is_fallback AND g.prediction IS NULL)
                    OR (NOT g.is_fallback AND b.prediction IS NULL)
                    OR (g.is_fallback AND g.train_support_students > 0)
                    OR (NOT g.is_fallback AND g.train_support_students = 0)) AS invalid_prediction_coverage
        FROM gam g FULL OUTER JOIN bkt b USING (source_row)
    """).fetchone()
    joined, unique_rows, identity_bad, support_bad, fallback_rows, invalid_coverage = audit
    gam_count = connection.execute("SELECT COUNT(*) FROM gam").fetchone()[0]
    bkt_count = connection.execute("SELECT COUNT(*) FROM bkt").fetchone()[0]
    if joined != unique_rows or gam_count != bkt_count or joined != gam_count:
        raise ValueError(f"fold {fold}: row count or source_row uniqueness mismatch")
    if identity_bad or support_bad or invalid_coverage:
        raise ValueError(f"fold {fold}: identity={identity_bad}, support={support_bad}, coverage={invalid_coverage}")

    columns: list[str] = []
    for index in range(15):
        columns.extend([
            f"COUNT(*) FILTER (WHERE bin_g={index}) AS count_g_{index}",
            f"SUM(g_prediction - correct) FILTER (WHERE bin_g={index}) AS residual_gam_{index}",
            f"COUNT(*) FILTER (WHERE bin_b={index}) AS count_b_{index}",
            f"SUM(b_prediction - correct) FILTER (WHERE bin_b={index}) AS residual_bkt_{index}",
        ])
    aggregate_sql = f"""
        WITH paired AS (
            SELECT g.user_id, g.correct,
                   g.prediction AS g_prediction, b.prediction AS b_prediction,
                   LEAST(CAST(FLOOR(g.prediction * 15) AS INTEGER), 14) AS bin_g,
                   LEAST(CAST(FLOOR(b.prediction * 15) AS INTEGER), 14) AS bin_b,
                   -LN(GREATEST(CASE WHEN g.correct=1 THEN g.prediction ELSE 1-g.prediction END, 2.220446049250313e-16)) AS ll_g,
                   -LN(GREATEST(CASE WHEN b.correct=1 THEN b.prediction ELSE 1-b.prediction END, 2.220446049250313e-16)) AS ll_b,
                   POW(g.prediction-g.correct, 2) AS br_g,
                   POW(b.prediction-b.correct, 2) AS br_b
            FROM gam g JOIN bkt b USING (source_row)
            WHERE NOT g.is_fallback AND g.prediction IS NOT NULL AND b.prediction IS NOT NULL
        )
        SELECT user_id, COUNT(*) AS row_count,
               SUM(ll_b) AS log_loss_bkt, SUM(ll_g) AS log_loss_gam,
               SUM(br_b) AS brier_bkt, SUM(br_g) AS brier_gam,
               SUM(CAST((b_prediction >= 0.5) = (correct = 1) AS INTEGER)) AS correct_bkt,
               SUM(CAST((g_prediction >= 0.5) = (correct = 1) AS INTEGER)) AS correct_gam,
               {', '.join(columns)}
        FROM paired GROUP BY user_id ORDER BY user_id
    """
    result = connection.execute(aggregate_sql).fetchall()
    ids = [row[0] for row in result]
    row_count = np.asarray([row[1] for row in result], dtype=np.int64)
    log_bkt = np.asarray([row[2] for row in result], dtype=np.float64)
    log_gam = np.asarray([row[3] for row in result], dtype=np.float64)
    brier_bkt = np.asarray([row[4] for row in result], dtype=np.float64)
    brier_gam = np.asarray([row[5] for row in result], dtype=np.float64)
    correct_bkt = np.asarray([row[6] for row in result], dtype=np.int64)
    correct_gam = np.asarray([row[7] for row in result], dtype=np.int64)
    counts_bkt = np.zeros((len(result), 15), dtype=np.int64)
    counts_gam = np.zeros((len(result), 15), dtype=np.int64)
    residual_gam = np.zeros((len(result), 15), dtype=np.float64)
    residual_bkt = np.zeros((len(result), 15), dtype=np.float64)
    for index, row in enumerate(result):
        for bin_index in range(15):
            count_g, gam_resid, count_b, bkt_resid = row[8 + bin_index * 4:12 + bin_index * 4]
            counts_gam[index, bin_index] = count_g or 0
            counts_bkt[index, bin_index] = count_b or 0
            residual_gam[index, bin_index] = gam_resid or 0.0
            residual_bkt[index, bin_index] = bkt_resid or 0.0
    stats = PairedFoldSufficientStats(
        user_ids=np.asarray(ids, dtype=object), row_count=row_count,
        log_loss_bkt=log_bkt, log_loss_gam=log_gam,
        brier_bkt=brier_bkt, brier_gam=brier_gam,
        correct_bkt=correct_bkt, correct_gam=correct_gam,
        ece_residual_bkt=residual_bkt, ece_residual_gam=residual_gam,
        ece_count_bkt=counts_bkt, ece_count_gam=counts_gam,
    )
    return stats, {
        "fold": fold, "joined_rows": joined, "supported_rows": int(row_count.sum()),
        "learners": len(ids), "fallback_rows": fallback_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--output", type=Path, help="optional path for the JSON result")
    args = parser.parse_args()
    con = duckdb.connect()
    try:
        folds, audit = zip(*(load_fold_stats(con, fold) for fold in range(5)))
    finally:
        con.close()
    result = {
        "estimand": "unweighted mean of five fold-level GAM-KT minus BKT differences; learners sampled with replacement within each fold",
        "replicates": args.replicates,
        "seed": args.seed,
        "ci": "percentile 95%",
        "fold_audit": list(audit),
        "metrics": paired_cluster_bootstrap(folds, replicates=args.replicates, seed=args.seed),
    }
    serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
