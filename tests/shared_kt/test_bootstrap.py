import numpy as np
import pytest
from dataclasses import replace

from knowledge_tracing.paired_bootstrap import (
    PairedFoldSufficientStats,
    fold_differences,
    paired_cluster_bootstrap,
)


def _stats():
    # Each row is one learner; counts and sums retain the cluster as the unit.
    return PairedFoldSufficientStats(
        user_ids=np.array(["u1", "u2", "u3"], dtype=object),
        row_count=np.array([2, 1, 3], dtype=np.int64),
        log_loss_bkt=np.array([0.6, 0.4, 1.2]),
        log_loss_gam=np.array([0.8, 0.3, 1.5]),
        brier_bkt=np.array([0.2, 0.1, 0.4]),
        brier_gam=np.array([0.3, 0.08, 0.5]),
        correct_bkt=np.array([1, 1, 2], dtype=np.int64),
        correct_gam=np.array([2, 0, 2], dtype=np.int64),
        ece_residual_bkt=np.zeros((3, 15), dtype=np.float64),
        ece_residual_gam=np.zeros((3, 15), dtype=np.float64),
        ece_count_bkt=np.array([[2] + [0] * 14, [1] + [0] * 14, [3] + [0] * 14]),
        ece_count_gam=np.array([[2] + [0] * 14, [1] + [0] * 14, [3] + [0] * 14]),
    )


def test_fold_differences_use_event_weighted_paired_counts():
    result = fold_differences(_stats(), np.ones(3, dtype=np.int64))

    assert result["log_loss"] == pytest.approx((2.6 - 2.2) / 6)
    assert result["brier"] == pytest.approx((0.88 - 0.7) / 6)
    assert result["accuracy"] == pytest.approx((4 - 4) / 6)
    assert result["ece"] == 0.0


def test_ece_uses_each_models_own_probability_bins():
    stats = _stats()
    residual_bkt = stats.ece_residual_bkt.copy()
    residual_gam = stats.ece_residual_gam.copy()
    counts_bkt = stats.ece_count_bkt.copy()
    counts_gam = stats.ece_count_gam.copy()
    residual_bkt[0, 0] = 0.2
    residual_gam[0, 1] = 0.4
    counts_bkt[0, 0] = 2
    counts_gam[0, 1] = 2
    stats = replace(stats, ece_residual_bkt=residual_bkt, ece_residual_gam=residual_gam,
                    ece_count_bkt=counts_bkt, ece_count_gam=counts_gam)

    assert fold_differences(stats, np.array([1, 0, 0]))["ece"] == pytest.approx(0.1)


def test_paired_cluster_bootstrap_is_seeded_and_returns_metric_intervals():
    stats = [_stats(), _stats()]
    first = paired_cluster_bootstrap(stats, replicates=80, seed=20261030)
    second = paired_cluster_bootstrap(stats, replicates=80, seed=20261030)

    assert first == second
    assert set(first) == {"log_loss", "brier", "ece", "accuracy"}
    for interval in first.values():
        assert len(interval["ci95"]) == 2
        assert interval["ci95"][0] <= interval["estimate"] <= interval["ci95"][1]

