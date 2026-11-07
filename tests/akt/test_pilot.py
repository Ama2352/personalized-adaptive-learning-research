from dataclasses import replace
import json

import duckdb
import numpy as np
import pytest

from knowledge_tracing.akt.config import PROJECT_ROOT, load_config
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.splits import InnerSplit
from knowledge_tracing.akt.training import EpochStats, select_checkpoint, train_epoch
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows
import knowledge_tracing.akt.config as config_module
import knowledge_tracing.akt.data as data_module
import knowledge_tracing.akt.prediction as prediction_module
import knowledge_tracing.akt.runner as runner
import knowledge_tracing.akt.training as training_module


def make_learner(user, fold, exercises, *, row_start):
    return LearnerEvents(user, fold, tuple(
        KTEvent(user, exercise, index + 1, row_start + index, index % 2, 0, fold)
        for index, exercise in enumerate(exercises)
    ))


def test_epoch_observations_count_actual_windows_batches_and_padding():
    learner = make_learner('train', 1, ['A', 'B', 'A', 'B'], row_start=1)
    encoding = fit_vocabulary([learner])
    config = load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json')
    adapter = runner.AKTAdapter(config, encoding)
    optimizer = runner.torch.optim.Adam(adapter.native.parameters(), lr=config.lr)

    stats = train_epoch(
        adapter,
        lambda: iter_windows(learner, encoding, context=1, target_block=2, training=True),
        optimizer=optimizer,
        epoch=1,
        budget={'max_steps': 10},
    )

    assert stats.complete and stats.stop_reason == 'epoch_complete'
    assert stats.windows_processed == 2
    assert stats.batches == stats.optimizer_steps == 1
    assert stats.sequence_length_counts == {2: 1, 3: 1}
    assert stats.valid_tokens == 5
    assert stats.target_tokens == 4
    assert stats.context_tokens == 1
    assert stats.padding_tokens == 1
    assert stats.forward_seconds >= 0
    assert stats.backward_seconds >= 0
    assert stats.optimizer_seconds >= 0
    assert stats.nonzero_gradient_steps == stats.parameter_update_steps == 1


def test_resource_stop_after_optimizer_update_persists_completed_step(monkeypatch):
    user = make_learner('resource-stop', 1, ['A'], row_start=101)
    encoding = fit_vocabulary([user])
    cfg = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                  d_model=32, heads=4, d_ff=64, final_fc=32,
                  context=1, target_block=1, batch_size=1, dropout=0)
    adapter = runner.AKTAdapter(cfg, encoding)
    optimizer = runner.torch.optim.Adam(adapter.native.parameters(), lr=cfg.lr)
    checks = 0
    progress = []

    def resource_check(budget, *, samples=None, observer=None):
        nonlocal checks
        checks += 1
        snapshot = {'pid': 123, 'process_rss_bytes': 3 * 1024**3,
                    'process_peak_rss_bytes': 3 * 1024**3,
                    'system_available_ram_bytes': 4 * 1024**3}
        if observer is not None:
            observer(snapshot)
        if checks == 1:
            return 0
        raise MemoryError('synthetic worker RSS ceiling exceeded')

    monkeypatch.setattr(training_module, '_check_resource_budget', resource_check)
    with pytest.raises(MemoryError, match='RSS ceiling'):
        train_epoch(adapter,
                    lambda: iter_windows(user, encoding, context=1, target_block=1, training=True),
                    optimizer=optimizer, epoch=1, budget={'max_rss_bytes': 2 * 1024**3},
                    progress_callback=progress.append)

    assert progress
    saved = progress[-1]['training']
    assert saved['optimizer_steps'] == 1
    assert saved['optimized_target_rows'] == 1
    assert saved['loss_sum'] > 0
    assert saved['nonzero_gradient_steps'] == 1
    assert saved['parameter_update_steps'] == 1
    assert progress[-1]['complete_epoch'] is False


def test_partial_selection_preserves_accounting_without_saving_partial_checkpoint(tmp_path, monkeypatch):
    train = make_learner('train', 1, ['A', 'B'], row_start=1)
    val = make_learner('val', 2, ['A'], row_start=10)
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                     output_dir=tmp_path / 'pilot-partial')
    partial = EpochStats(0.7, 1, 1, False, {'wall_seconds': 3.0},
                         nonzero_gradient_steps=1, parameter_update_steps=1,
                         windows_processed=2, processed_target_rows=2,
                         optimized_target_rows=1, batches=1,
                         sequence_length_counts={1: 2}, stop_reason='time_budget')
    monkeypatch.setattr(training_module, 'train_epoch', lambda *args, **kwargs: partial)

    selection = select_checkpoint(
        config,
        inner_split=InnerSplit(('train',), ('val',), 0, 'split'),
        train_learners_factory=lambda: iter([train]),
        val_learners_factory=lambda: iter([val]),
        identity={'synthetic': True},
        budget={'max_seconds': 1},
    )

    assert selection.status == 'bounded'
    assert selection.stop_reason == 'time_budget'
    assert selection.selected_epoch is None
    assert selection.checkpoint is None
    assert selection.history[0]['complete_epoch'] is False
    assert selection.history[0]['training']['optimizer_steps'] == 1
    assert not list(config.output_dir.glob('*.pt'))


def test_pilot_completed_cycle_reloads_checkpoint_and_exports_aligned_predictions(
        tmp_path, monkeypatch):
    base_config = load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json')
    monkeypatch.setattr(config_module, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(runner, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(prediction_module, 'PROJECT_ROOT', tmp_path)
    config = replace(
        base_config,
        project_root=tmp_path,
        source_root=PROJECT_ROOT / 'artifacts/akt/dependencies/upstream',
        run_id='pilot-synthetic-full',
        output_dir=tmp_path / 'experiments/akt/results/pilot-synthetic-full',
        execution_enabled=True,
        max_train_users=4,
        max_val_users=2,
        max_total_targets=20,
    )
    train = make_learner('train', 1, ['A', 'B', 'A', 'B'], row_start=1)
    val = make_learner('val', 2, ['A', 'B', 'A', 'OOV'], row_start=20)
    caps = {'max_train_users': 4, 'max_val_users': 2, 'max_total_targets': 20,
            'max_seconds': 30, 'max_wall_seconds': 60,
            'max_rss_bytes': 2 * 1024**3, 'min_available_ram_bytes': 1024**3}
    approved = {'caps': caps, 'approval_reference': 'synthetic pilot authorization'}
    monkeypatch.setattr(runner, '_require_authorization', lambda *args: approved)
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda _: {'status': 'PASS'})
    monkeypatch.setattr(runner, '_check_resource_budget', lambda budget: 1)
    # Đây là lifecycle fixture. Resource thresholds được kiểm bằng snapshots
    # xác định ở các tests riêng, không phụ thuộc RAM của ứng dụng khác trên máy.
    monkeypatch.setattr(training_module, 'memory_snapshot', lambda: {
        'pid': 123, 'process_rss_bytes': 512 * 1024**2,
        'process_peak_rss_bytes': 512 * 1024**2,
        'system_available_ram_bytes': 4 * 1024**3,
        'system_total_ram_bytes': 8 * 1024**3})
    monkeypatch.setattr(runner, '_load_phase_inputs', lambda _, **kwargs: (
        {'runtime_report_sha256': 'runtime', 'source': {'commit': config.source_commit}},
        InnerSplit(('train',), ('val',), 0, 'split'),
        (train,), (val,),
        {'selected_train_learners': 1, 'selected_validation_learners': 1,
         'loaded_train_learners': 1, 'loaded_validation_learners': 1,
         'selected_train_targets': 4, 'selected_validation_targets': 4,
         'data_loading_seconds': 0.01,
         'chronological_query_sort_and_materialize_seconds': 0.01},
    ))

    result = runner.run_pilot(config, authorization={'synthetic': True})

    assert result.status == 'completed'
    manifest = json.loads((config.output_dir / 'manifest.json').read_text(encoding='utf-8'))
    pilot = json.loads((config.output_dir / 'pilot.json').read_text(encoding='utf-8'))
    summary = pilot['summary']
    assert manifest['status'] == 'completed'
    assert summary['checkpoint_reload_state_exact'] is True
    assert summary['coverage']['expected_rows'] == 4
    assert summary['coverage']['prediction_rows'] == 4
    assert summary['coverage']['fitted_rows'] == 3
    assert summary['coverage']['unseen_rows'] == 1
    assert summary['prediction_distribution']['fitted_count'] == 3
    assert summary['training']['optimizer_steps'] > 0
    assert summary['training']['nonzero_gradient_steps'] > 0
    assert summary['training']['batch_shape_counts']
    assert summary['training']['sequence_length_counts']
    assert summary['training']['target_tokens'] == 4
    assert summary['training']['context_tokens'] + summary['training']['target_tokens'] == summary['training']['valid_tokens']
    assert summary['training']['padding_tokens'] >= 0
    assert summary['timing']['validation_seconds'] >= 0
    assert summary['timing']['checkpoint_save_seconds'] >= 0
    assert summary['timing']['checkpoint_load_seconds'] >= 0
    assert summary['timing']['checkpoint_restore_seconds'] >= 0
    assert summary['timing']['prediction_export_seconds'] >= 0
    assert summary['cohort']['loaded_train_learners'] == 1
    assert summary['cohort']['loaded_validation_learners'] == 1
    assert summary['timing']['data_loading_seconds'] == 0.01
    assert summary['worker_resources']['current_rss_bytes'] > 0
    assert summary['worker_resources']['peak_rss_bytes'] >= summary['worker_resources']['current_rss_bytes']
    assert summary['worker_resources']['minimum_available_ram_bytes'] > 0
    with duckdb.connect() as con:
        rows, unique_rows = con.execute(
            'SELECT count(*), count(DISTINCT source_row) FROM read_parquet(?)',
            [str(config.output_dir / 'predictions' / 'part-*.parquet')],
        ).fetchone()
    assert rows == unique_rows == 4


def test_pilot_partial_epoch_is_bounded_and_skips_checkpoint_export(tmp_path, monkeypatch):
    base_config = load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json')
    monkeypatch.setattr(config_module, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(runner, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(prediction_module, 'PROJECT_ROOT', tmp_path)
    config = replace(
        base_config,
        project_root=tmp_path,
        source_root=PROJECT_ROOT / 'artifacts/akt/dependencies/upstream',
        run_id='pilot-synthetic-bounded',
        output_dir=tmp_path / 'experiments/akt/results/pilot-synthetic-bounded',
        execution_enabled=True,
        max_train_users=4,
        max_val_users=2,
        max_total_targets=20,
    )
    learner = make_learner('train', 1, ['A', 'B'], row_start=1)
    caps = {'max_train_users': 4, 'max_val_users': 2, 'max_total_targets': 20,
            'max_seconds': 30, 'max_wall_seconds': 60,
            'max_rss_bytes': 2 * 1024**3, 'min_available_ram_bytes': 1024**3}
    approved = {'caps': caps, 'approval_reference': 'synthetic pilot authorization'}
    selection = type('Selection', (), {
        'status': 'bounded', 'stop_reason': 'time_budget', 'selected_epoch': None,
        'checkpoint': None, 'history': [{'complete_epoch': False, 'training': {
            'optimizer_steps': 1, 'processed_target_rows': 3, 'optimized_target_rows': 2,
            'windows_processed': 3, 'loss_sum': 1.2, 'nonzero_gradient_steps': 1,
            'max_pre_clip_grad_norm': 0.4, 'max_post_clip_grad_norm': 0.4,
        }}],
    })()
    monkeypatch.setattr(runner, '_require_authorization', lambda *args: approved)
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda _: {'status': 'PASS'})
    monkeypatch.setattr(runner, '_check_resource_budget', lambda budget: 1)
    monkeypatch.setattr(runner, '_load_phase_inputs', lambda _, **kwargs: (
        {'runtime_report_sha256': 'runtime', 'source': {'commit': config.source_commit}},
        InnerSplit(('train',), ('val',), 0, 'split'),
        (learner,), (learner,), {'selected_train_learners': 1, 'selected_validation_learners': 1,
                                 'loaded_train_learners': 1, 'loaded_validation_learners': 1,
                                 'selected_train_targets': 2, 'selected_validation_targets': 2},
    ))
    monkeypatch.setattr(runner, 'select_checkpoint', lambda *args, **kwargs: selection)
    monkeypatch.setattr(runner, 'load_checkpoint', lambda *args, **kwargs: pytest.fail('partial checkpoint loaded'))
    monkeypatch.setattr(runner, 'export_predictions', lambda *args, **kwargs: pytest.fail('partial export run'))

    result = runner.run_pilot(config, authorization={'synthetic': True})

    assert result.status == 'bounded'
    manifest = json.loads((config.output_dir / 'manifest.json').read_text(encoding='utf-8'))
    pilot = json.loads((config.output_dir / 'pilot.json').read_text(encoding='utf-8'))
    assert manifest['status'] == 'bounded'
    assert pilot['status'] == 'bounded'
    assert pilot['summary']['complete_epoch'] is False
    assert pilot['summary']['training']['optimizer_steps'] == 1
    assert pilot['summary']['validation'] is None
    assert pilot['summary']['prediction_export'] is None


def test_pilot_failure_is_not_mislabeled_as_a_bounded_partial(tmp_path, monkeypatch):
    base_config = load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json')
    monkeypatch.setattr(config_module, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(runner, 'PROJECT_ROOT', tmp_path)
    config = replace(base_config, project_root=tmp_path,
                     source_root=PROJECT_ROOT / 'artifacts/akt/dependencies/upstream',
                     run_id='pilot-synthetic-failure',
                     output_dir=tmp_path / 'experiments/akt/results/pilot-synthetic-failure',
                     execution_enabled=True, max_train_users=4, max_val_users=2,
                     max_total_targets=20)
    learner = make_learner('train', 1, ['A', 'B'], row_start=1)
    caps = {'max_train_users': 4, 'max_val_users': 2, 'max_total_targets': 20,
            'max_seconds': 30, 'max_wall_seconds': 60,
            'max_rss_bytes': 2 * 1024**3, 'min_available_ram_bytes': 1024**3}
    monkeypatch.setattr(runner, '_require_authorization', lambda *args: {
        'caps': caps, 'approval_reference': 'synthetic pilot authorization'})
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda _: {'status': 'PASS'})
    monkeypatch.setattr(runner, '_check_resource_budget', lambda budget: 1)
    monkeypatch.setattr(runner, '_load_phase_inputs', lambda _, **kwargs: (
        {'runtime_report_sha256': 'runtime', 'source': {'commit': config.source_commit}},
        InnerSplit(('train',), ('val',), 0, 'split'), (learner,), (learner,),
        {'selected_train_learners': 1, 'selected_validation_learners': 1,
         'loaded_train_learners': 1, 'loaded_validation_learners': 1,
         'selected_train_targets': 2, 'selected_validation_targets': 2},
    ))
    monkeypatch.setattr(runner, 'select_checkpoint', lambda *args, **kwargs: (_ for _ in ()).throw(
        ValueError('synthetic nonfinite failure')))

    with pytest.raises(ValueError, match='synthetic nonfinite'):
        runner.run_pilot(config, authorization={'synthetic': True})

    manifest = json.loads((config.output_dir / 'manifest.json').read_text(encoding='utf-8'))
    pilot = json.loads((config.output_dir / 'pilot.json').read_text(encoding='utf-8'))
    assert manifest['status'] == pilot['status'] == 'failed'
    assert manifest['stop_reason'] == 'implementation_or_numerical_failure'


def test_target_cap_counts_actual_loaded_learner_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(data_module, 'PROJECT_ROOT', tmp_path)
    first = make_learner('a', 1, ['A', 'A', 'A'], row_start=1)
    second = make_learner('b', 2, ['A', 'B'], row_start=10)
    monkeypatch.setattr(runner, 'iter_development_learners',
                        lambda *args, **kwargs: iter((first, second)))
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json'),
                     outer_fold=0)
    stats = {}

    loaded = runner._capped_learners(config, ('a', 'b'), target_cap=4,
                                     phase_dir=tmp_path / 'tmp', stats=stats)

    assert [learner.user_id for learner in loaded] == ['a', 'b']
    assert sum(len(learner.events) for learner in loaded) == 4
    assert len(loaded[1].events) == 1
    assert stats['selected_learners'] == 2
    assert stats['selected_targets'] == 4


def test_pilot_template_preserves_approved_architecture_and_limits():
    config = load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json')
    assert (config.device, config.d_model, config.heads, config.blocks,
            config.d_ff, config.final_fc, config.context, config.target_block,
            config.batch_size, config.max_epochs) == ('cpu', 256, 8, 1, 1024, 512, 100, 100, 4, 1)
    assert (config.max_train_users, config.max_val_users, config.max_total_targets,
            config.max_seconds, config.max_wall_seconds, config.max_rss_bytes,
            config.min_available_ram_bytes) == (
                1024, 256, 100000, 900, 1200, 2 * 1024**3, 1024**3)

