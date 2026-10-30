"""Native, supported-only, subgroup, and common-row GAM-KT metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score


def _metrics(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {key: None for key in ("auc", "log_loss", "brier", "ece", "accuracy", "prevalence")}
    y = frame.correct.to_numpy(dtype=np.int64)
    p = frame.prediction.to_numpy(dtype=np.float64)
    bins = np.minimum((p * 15).astype(np.int64), 14)
    ece = sum(float((bins == index).mean()) * abs(float(y[bins == index].mean() - p[bins == index].mean())) for index in range(15) if (bins == index).any())
    return {
        "positive_count": int((y == 1).sum()),
        "negative_count": int((y == 0).sum()),
        "auc": float(roc_auc_score(y, p)) if np.unique(y).size == 2 else None,
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "ece": float(ece),
        "accuracy": float(accuracy_score(y, p >= 0.5)),
        "prevalence": float(y.mean()),
    }


def _evaluate(group: pd.DataFrame) -> dict:
    valid = group[group.prediction.notna()]
    if not valid.empty and (not np.isfinite(valid.prediction).all() or not valid.prediction.between(0, 1).all()):
        raise ValueError("Predictions must be finite probabilities in [0,1]")
    return {"rows": int(len(valid)), "metrics": _metrics(valid)}


def score_frame(frame: pd.DataFrame) -> dict:
    required = {"correct", "prediction", "suggested", "exercise", "is_fallback"}
    if not required <= set(frame.columns):
        raise ValueError(f"Missing metrics fields: {sorted(required - set(frame.columns))}")
    if not frame.correct.isin([0, 1]).all() or not frame.suggested.isin([0, 1]).all():
        raise ValueError("correct/suggested must be binary")
    native = _evaluate(frame)
    supported = _evaluate(frame[~frame.is_fallback.astype(bool)])
    suggested = {
        "suggested": _evaluate(frame[frame.suggested == 1]),
        "non_suggested": _evaluate(frame[frame.suggested == 0]),
    }
    support_bands = {}
    if "train_support_students" in frame.columns:
        support = pd.to_numeric(frame.train_support_students, errors="raise").astype(int)
        bands = pd.cut(
            support,
            bins=[-1, 0, 9, 49, 99, 999, np.inf],
            labels=["unseen", "1-9", "10-49", "50-99", "100-999", ">=1000"],
        )
        support_bands = {
            str(band): {
                **_evaluate(frame[bands == band]),
                "fallback_rows": int(frame.loc[bands == band, "is_fallback"].astype(bool).sum()),
            }
            for band in bands.cat.categories
        }
    return {
        "native": native,
        "supported": supported,
        "suggested": suggested,
        "coverage": {
            "total_rows": int(len(frame)),
            "predicted_rows": int(frame.prediction.notna().sum()),
            "fallback_rows": int(frame.is_fallback.astype(bool).sum()),
            "fallback_exercises": int(frame.loc[frame.is_fallback.astype(bool), "exercise"].nunique()),
            "unseen_exercises": int(frame.loc[frame.is_fallback.astype(bool), "exercise"].nunique()),
            "unpredicted_rows": int(frame.prediction.isna().sum()),
        },
        "train_support_bands": support_bands,
        "definitions": {"ece_bins": 15, "ece_edges": "equal width [k/15,(k+1)/15), with p=1 in final bin", "accuracy_threshold": 0.5, "auc_undefined": "null when only one target class is present"},
    }
