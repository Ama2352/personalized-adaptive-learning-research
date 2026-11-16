"""Ngăn gán nhầm model cuối, metadata hoặc checkpoint cần replay thành unused."""
import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location('audit_retention', Path(__file__).with_name('audit_retention.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_final_refit_is_active():
    assert audit.classify('experiments/akt/results/model-export-a3-refit-20261114-01/A3_JUNYI_REFIT.pt')[0] == 'KEEP_ACTIVE'


def test_recovery_export_is_cold_not_current_refit():
    assert audit.classify('experiments/akt/results/model-export-a3-refit-recovery-20261115-06/COLAB_RESUME.zip')[0] == 'ARCHIVE_ONLY_RECOVERY'


def test_partial_checkpoint_metadata_is_retained():
    path = 'experiments/akt/results/run/files/outputs/junyi-a3-refit-20261114-01/checkpoints/refit-batch-epoch-9-step-1874-abc/'
    assert audit.classify(path + 'state.pt')[0] == 'UNUSED_RESUME_FINISHED_RUN'
    assert audit.classify(path + 'metadata.json')[0] == 'KEEP_AUDIT_OR_SOURCE'


def test_a0_epoch_replay_kept():
    assert audit.classify('experiments/akt/results/modal-junyi-a0-b128-h100-20261112-03/checkpoints/epoch-2/state.pt')[0] == 'KEEP_PENDING_A0_REPLAY'


def test_canonical_source_and_shared_cache_kept():
    assert audit.classify('experiments/akt/results/junyi-a3-refit-20261114-01/checkpoints/epoch-009/state.pt')[0] == 'KEEP_ACTIVE'
    assert audit.classify('artifacts/akt/window-cache/full-refit90/a.npz')[0] == 'KEEP_ACTIVE'


def test_protected_and_private_are_excluded_from_unused():
    assert audit.classify('dataset/original.csv')[0] == 'PROTECTED'
    assert audit.is_excluded('artifacts/akt/private/modal.toml')
    assert audit.is_excluded('experiments/gam_kt/results/holdout/predictions.parquet')


def test_duplicate_recovery_group_keeps_one_archive_witness():
    rows = [dict(path='experiments/akt/results/run' + str(i) + '/state.pt', bytes=100,
                 sha256='a' * 64, category='UNUSED_RESUME_FINISHED_RUN') for i in range(2)]
    audit.flag_duplicates(rows)
    assert sum(row['category'] == 'ARCHIVE_ONLY_RESUME_WITNESS' for row in rows) == 1
    duplicate = next(row for row in rows if row['category'] == 'UNUSED_VERIFIED_DUPLICATE')
    witness = next(row for row in rows if row['category'] == 'ARCHIVE_ONLY_RESUME_WITNESS')
    assert duplicate['keeper'] == witness['path']


def test_gam_historical_predictions_kept():
    assert audit.classify('experiments/gam_kt/results/wsl_cpp/cv/predictions.parquet')[0] == 'KEEP_ACTIVE'
