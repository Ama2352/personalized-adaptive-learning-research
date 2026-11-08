"""Paired learner-cluster bootstrap for saved per-fold BKT/GAM predictions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class PairedFoldSufficientStats:
    user_ids: np.ndarray
    row_count: np.ndarray
    log_loss_bkt: np.ndarray
    log_loss_gam: np.ndarray
    brier_bkt: np.ndarray
    brier_gam: np.ndarray
    correct_bkt: np.ndarray
    correct_gam: np.ndarray
    ece_residual_bkt: np.ndarray
    ece_residual_gam: np.ndarray
    ece_count_bkt: np.ndarray
    ece_count_gam: np.ndarray

    def __post_init__(self) -> None:
        n = len(self.user_ids)
        vectors = (self.row_count, self.log_loss_bkt, self.log_loss_gam, self.brier_bkt,
                   self.brier_gam, self.correct_bkt, self.correct_gam)
        if any(np.asarray(value).shape != (n,) for value in vectors):
            raise ValueError("per-user vectors must have one value per user")
        if np.asarray(self.ece_residual_bkt).ndim != 2 or np.asarray(self.ece_residual_bkt).shape[0] != n:
            raise ValueError("ECE residuals must have shape users by bins")
        if np.asarray(self.ece_residual_gam).shape != np.asarray(self.ece_residual_bkt).shape:
            raise ValueError("BKT and GAM ECE residual arrays must match")
        if np.asarray(self.ece_count_bkt).shape != np.asarray(self.ece_residual_bkt).shape:
            raise ValueError("BKT ECE counts must match the residual array shape")
        if np.asarray(self.ece_count_gam).shape != np.asarray(self.ece_residual_gam).shape:
            raise ValueError("GAM ECE counts must match the residual array shape")


def _metrics(stats: PairedFoldSufficientStats, sampled_user_indexes: np.ndarray) -> dict[str, float]:
    weights = np.asarray(sampled_user_indexes, dtype=np.int64)
    n = float(weights @ np.asarray(stats.row_count, dtype=np.float64))
    if n <= 0:
        raise ValueError("bootstrap sample has no rows")
    select = lambda value: weights @ np.asarray(value, dtype=np.float64)
    residual_bkt = select(stats.ece_residual_bkt)
    residual_gam = select(stats.ece_residual_gam)
    bins_bkt = select(stats.ece_count_bkt)
    bins_gam = select(stats.ece_count_gam)
    ece_bkt = float(np.abs(residual_bkt[bins_bkt > 0]).sum() / n)
    ece_gam = float(np.abs(residual_gam[bins_gam > 0]).sum() / n)
    return {
        "log_loss": float((select(stats.log_loss_gam) - select(stats.log_loss_bkt)) / n),
        "brier": float((select(stats.brier_gam) - select(stats.brier_bkt)) / n),
        "ece": ece_gam - ece_bkt,
        "accuracy": float((select(stats.correct_gam) - select(stats.correct_bkt)) / n),
    }


def fold_differences(stats: PairedFoldSufficientStats, user_multiplicities: np.ndarray) -> dict[str, float]:
    """Return GAM−BKT metric differences for a user-level resample."""
    multiplicities = np.asarray(user_multiplicities, dtype=np.int64)
    if multiplicities.shape != np.asarray(stats.user_ids).shape or np.any(multiplicities < 0):
        raise ValueError("user_multiplicities must be a nonnegative count per user")
    return _metrics(stats, multiplicities)


def paired_cluster_bootstrap(
    folds: Sequence[PairedFoldSufficientStats], *, replicates: int = 1000, seed: int = 20261030
) -> dict[str, dict[str, float | list[float]]]:
    """Resample learners independently inside folds and average fold estimates."""
    if not folds or replicates < 1:
        raise ValueError("at least one fold and one bootstrap replicate are required")
    fold_sizes = [len(fold.user_ids) for fold in folds]
    if any(size == 0 for size in fold_sizes):
        raise ValueError("each fold must contain at least one supported user")
    point = np.mean([list(fold_differences(fold, np.ones(size, dtype=np.int64)).values())
                     for fold, size in zip(folds, fold_sizes)], axis=0)
    metric_names = ("log_loss", "brier", "ece", "accuracy")
    draws = np.empty((replicates, len(metric_names)), dtype=np.float64)
    rng = np.random.default_rng(seed)
    for replicate in range(replicates):
        fold_values = []
        for fold, size in zip(folds, fold_sizes):
            sampled = rng.integers(0, size, size=size)
            counts = np.bincount(sampled, minlength=size).astype(np.int64)
            fold_values.append(fold_differences(fold, counts))
        draws[replicate] = [np.mean([values[name] for values in fold_values]) for name in metric_names]
    return {
        name: {
            "estimate": float(point[index]),
            "ci95": [float(np.quantile(draws[:, index], 0.025)), float(np.quantile(draws[:, index], 0.975))],
        }
        for index, name in enumerate(metric_names)
    }
