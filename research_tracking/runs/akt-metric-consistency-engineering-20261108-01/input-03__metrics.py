"""Metrics and explicit fitted-skill coverage for one-step BKT predictions."""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd
import duckdb
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score


ECE_BINS = 15
RARITY_BANDS = ("unseen", "1-9", "10-49", "50-99", "100-999", ">=1000")


def _band(student_count: int) -> str:
    if student_count == 0:
        return "unseen"
    if student_count < 10:
        return "1-9"
    if student_count < 50:
        return "10-49"
    if student_count < 100:
        return "50-99"
    if student_count < 1000:
        return "100-999"
    return ">=1000"


def _ece(y: np.ndarray, p: np.ndarray) -> float:
    bins = np.minimum((p * ECE_BINS).astype(np.int64), ECE_BINS - 1)
    error = 0.0
    for index in range(ECE_BINS):
        included = bins == index
        if included.any():
            error += included.mean() * abs(float(y[included].mean() - p[included].mean()))
    return error


def _metrics(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return dict.fromkeys(("auc", "log_loss", "brier", "ece", "accuracy"))
    y = frame["correct"].to_numpy(dtype=np.int64)
    p = frame["prediction"].to_numpy(dtype=np.float64)
    return {
        "auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "ece": _ece(y, p),
        "accuracy": float(accuracy_score(y, p >= 0.5)),
    }


def _summary(group: pd.DataFrame) -> dict:
    fitted = group[group["_known"]]
    unseen = group[~group["_known"]]
    total_rows = len(group)
    all_students = group["user_id"].nunique()
    return {
        "total_rows": total_rows,
        "scored_rows": len(fitted),
        "coverage": len(fitted) / total_rows if total_rows else None,
        "total_students": all_students,
        "scored_students": fitted["user_id"].nunique(),
        "unseen_students": unseen["user_id"].nunique(),
        "unseen_skills": unseen["exercise"].nunique(),
        "unseen_rows": len(unseen),
        "skill_count": group["exercise"].nunique(),
        "metrics": _metrics(fitted),
    }


def score_predictions(frame: pd.DataFrame, train_skill_support: Mapping[str, int]) -> dict:
    """Score only fitted skills; require null predictions for unseen skills."""
    required = {"user_id", "exercise", "suggested", "correct", "prediction"}
    if not required <= set(frame):
        raise ValueError(f"Missing evaluation columns: {sorted(required - set(frame))}")
    scored = frame.copy()
    if not scored["correct"].isin([0, 1]).all() or not scored["suggested"].isin([0, 1]).all():
        raise ValueError("correct and suggested must be binary")
    scored["_support"] = scored["exercise"].map(train_skill_support).fillna(0).astype(int)
    scored["_known"] = scored["_support"] > 0
    scored["prediction"] = pd.to_numeric(scored["prediction"], errors="coerce")
    if scored.loc[~scored["_known"], "prediction"].notna().any():
        raise ValueError("unseen skills must have no fitted prediction, including 0.5 fallback")
    supported_p = scored.loc[scored["_known"], "prediction"]
    if supported_p.isna().any() or not np.isfinite(supported_p).all() or not supported_p.between(0, 1).all():
        raise ValueError("fitted predictions must be finite probabilities in [0,1]")
    scored["_rarity"] = scored["_support"].map(_band)
    return {
        "overall": _summary(scored),
        "suggested": {
            "suggested": _summary(scored[scored["suggested"] == 1]),
            "non_suggested": _summary(scored[scored["suggested"] == 0]),
        },
        "rarity": {band: _summary(scored[scored["_rarity"] == band]) for band in RARITY_BANDS},
        "definitions": {
            "ece_bins": ECE_BINS,
            "ece_rule": "equal-width [k/15,(k+1)/15), last bin includes 1",
            "accuracy_threshold": 0.5,
            "unseen_policy": "null prediction; exclude from fitted BKT metrics",
        },
    }


def score_prediction_shards(glob_path) -> dict:
    """Score Parquet shards while loading only numeric prediction vectors into RAM."""
    pattern = str(glob_path).replace("'", "''")
    con = duckdb.connect()
    try:
        con.execute(f"CREATE VIEW shards AS SELECT * FROM read_parquet('{pattern}')")
        bad = con.execute(
            "SELECT COUNT(*) FROM shards WHERE train_skill_students=0 "
            "AND prediction IS NOT NULL AND NOT isnan(prediction)"
        ).fetchone()[0]
        if bad:
            raise ValueError(f"{bad} unseen rows carry fallback predictions")

        def summary(where: str) -> dict:
            counts = con.execute(
                "SELECT COUNT(*), "
                "COUNT(*) FILTER (WHERE train_skill_students>0), "
                "COUNT(DISTINCT user_id), "
                "COUNT(DISTINCT user_id) FILTER (WHERE train_skill_students>0), "
                "COUNT(DISTINCT user_id) FILTER (WHERE train_skill_students=0), "
                "COUNT(DISTINCT exercise) FILTER (WHERE train_skill_students=0), "
                "COUNT(*) FILTER (WHERE train_skill_students=0), "
                "COUNT(DISTINCT exercise) FROM shards WHERE " + where
            ).fetchone()
            pairs = con.execute(
                "SELECT correct, prediction FROM shards WHERE " + where + " AND train_skill_students>0"
            ).fetchnumpy()
            known = pd.DataFrame({"correct": pairs["correct"], "prediction": pairs["prediction"]})
            if not known.empty and (
                known["prediction"].isna().any()
                or not np.isfinite(known["prediction"]).all()
                or not known["prediction"].between(0, 1).all()
            ):
                raise ValueError("Invalid fitted probabilities in prediction shards")
            total, scored, users, scored_users, unseen_users, unseen_skills, unseen_rows, skills = counts
            return {
                "total_rows": total,
                "scored_rows": scored,
                "coverage": scored / total if total else None,
                "total_students": users,
                "scored_students": scored_users,
                "unseen_students": unseen_users,
                "unseen_skills": unseen_skills,
                "unseen_rows": unseen_rows,
                "skill_count": skills,
                "metrics": _metrics(known),
            }

        rarity_conditions = {
            "unseen": "train_skill_students=0",
            "1-9": "train_skill_students BETWEEN 1 AND 9",
            "10-49": "train_skill_students BETWEEN 10 AND 49",
            "50-99": "train_skill_students BETWEEN 50 AND 99",
            "100-999": "train_skill_students BETWEEN 100 AND 999",
            ">=1000": "train_skill_students>=1000",
        }
        return {
            "overall": summary("TRUE"),
            "suggested": {
                "suggested": summary("suggested=1"),
                "non_suggested": summary("suggested=0"),
            },
            "rarity": {name: summary(condition) for name, condition in rarity_conditions.items()},
            "definitions": {
                "ece_bins": ECE_BINS,
                "ece_rule": "equal-width [k/15,(k+1)/15), last bin includes 1",
                "accuracy_threshold": 0.5,
                "unseen_policy": "null prediction; exclude from fitted BKT metrics",
            },
        }
    finally:
        con.close()
