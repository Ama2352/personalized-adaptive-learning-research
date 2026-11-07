"""Main worker in-process từ Parquet synthetic, không watchdog/cloud/realdata.

Chỉ fixture Gate1/Gate2 và RAM; authorization/caps, split/loader, optimizer,
validation, best checkpoint/reload và prediction exporter dùng code thật.
"""

from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path

import duckdb
import pytest
import torch

from knowledge_tracing.akt import config as config_module
from knowledge_tracing.akt import data as data_module
from knowledge_tracing.akt import prediction as prediction_module
from knowledge_tracing.akt import runner, training, watchdog
from knowledge_tracing.akt.config import PROJECT_ROOT, load_config


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def parquet_worker(tmp_path, monkeypatch):
    """Chỉ ghi dưới pytest basetemp được invocation đặt trong artifacts/akt."""
    root = tmp_path / 'synthetic-project'
    root.mkdir()
    marker = root / 'SYNTHETIC_ONLY.json'
    marker.write_text(json.dumps({'synthetic_only': True, 'real_data_authorized': False}), encoding='utf-8')
    canonical = root / 'fixture-parquet'
    canonical.mkdir()
    assignments = root / 'fixture-assignments.parquet'
    con = duckdb.connect()
    try:
        con.execute('CREATE TABLE assignments(user_id VARCHAR, partition VARCHAR, fold INTEGER)')
        con.executemany('INSERT INTO assignments VALUES (?, ?, ?)',
                        [(f'synthetic-{i}', 'development', 0 if i == 0 else 1 + i % 4) for i in range(6)])
        con.execute('COPY assignments TO ? (FORMAT PARQUET)', [str(assignments)])
        frame = con.execute('SELECT user_id,fold FROM assignments').df()
        split = runner.make_inner_split(frame, outer_fold=0, seed=42)
        val_user = split.inner_val_users[0]
        con.execute('CREATE TABLE events(user_id VARCHAR, exercise VARCHAR, time_done BIGINT, '
                    'source_row BIGINT, correct INTEGER, suggested INTEGER)')
        events = []
        for index, row in frame.iterrows():
            exercises = ['A', 'B', 'A', 'B']
            if row.user_id == val_user:
                exercises[1] = 'SYNTHETIC_OOV'
            if row.fold == 0:
                exercises = ['FORBIDDEN_OUTER_ITEM'] * 4
            events.extend((row.user_id, exercise, position // 2, index * 100 + position + 1,
                           position % 2, position % 2) for position, exercise in enumerate(exercises))
        # Cố ý đảo thứ tự lưu; loader phải order timestamp/source_row và giữ learner.
        con.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)', list(reversed(events)))
        con.execute('COPY events TO ? (FORMAT PARQUET)', [str(canonical / 'events.parquet')])
    finally:
        con.close()
    canonical_manifest = root / 'fixture-canonical.json'
    split_manifest = root / 'fixture-split.json'
    canonical_manifest.write_text(json.dumps({'kind': 'synthetic-main-worker-fixture', 'rows': 24}), encoding='utf-8')
    split_manifest.write_text(json.dumps({'kind': 'synthetic-not-frozen-research-split', 'learners': 6}), encoding='utf-8')
    assert json.loads(marker.read_text())['synthetic_only'] is True
    for module in (config_module, runner, prediction_module, data_module):
        monkeypatch.setattr(module, 'PROJECT_ROOT', root)
    for name, value in [('CANONICAL', canonical), ('ASSIGNMENTS', assignments),
                        ('CANONICAL_MANIFEST', canonical_manifest), ('SPLIT_MANIFEST', split_manifest)]:
        monkeypatch.setattr(runner, name, value)
    fixture_report = {'source': {'commit': runner.SOURCE_COMMIT, 'fixture_provenance_only': True},
                      'lock_sha256': 'test-only-lock', 'runtime_report_sha256': 'test-only-runtime'}
    monkeypatch.setattr(runner, 'preflight', lambda _: fixture_report)
    monkeypatch.setattr(runner, '_require_gate2_evidence', lambda _: {
        'status': 'PASS_CPU_TEST_FIXTURE_ONLY', 'fixture': True,
        'report_sha256': 'test-only-gate', 'test_log_sha256': 'test-only-log',
        'pointer_sha256': 'test-only-pointer'})
    monkeypatch.setattr(runner, '_gate2_build_hashes', lambda: {
        'synthetic-marker': sha(marker), 'worker-test-source': sha(Path(__file__))})
    snapshot = lambda: {'pid': os.getpid(), 'process_rss_bytes': 256 * 1024**2,
                        'process_peak_rss_bytes': 256 * 1024**2,
                        'system_available_ram_bytes': 4 * 1024**3,
                        'system_total_ram_bytes': 8 * 1024**3}
    for module in (runner, training, watchdog):
        monkeypatch.setattr(module, 'memory_snapshot', snapshot)
    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                     project_root=root, source_root=PROJECT_ROOT / 'artifacts/akt/dependencies/upstream',
                     run_id='synthetic-worker',
                     output_dir=root / 'experiments/akt/results/synthetic-worker',
                     execution_enabled=True, max_train_users=2, max_val_users=1,
                     max_targets_per_side=8, max_steps=2, max_seconds=30, max_wall_seconds=90,
                     fetch_rows=2)
    caps = {name: getattr(config, name) for name in (
        'max_train_users', 'max_val_users', 'max_targets_per_side', 'max_steps', 'max_seconds',
        'max_wall_seconds', 'max_rss_bytes', 'min_available_ram_bytes')}
    approval = {'approved': True, 'scope': 'development-inner-only', 'phase': 'smoke',
                'run_id': config.run_id, 'source_commit': config.source_commit,
                'config_sha256': runner._config_hash(config), 'caps': caps,
                'identity': runner._authorization_identity(config),
                'approval_reference': 'TEST_ONLY synthetic Parquet worker; no real-data authorization'}
    config_path, approval_path = root / 'config.json', root / 'authorization.json'
    config_path.write_text(json.dumps(asdict(config), default=str), encoding='utf-8')
    approval_path.write_text(json.dumps(approval), encoding='utf-8')
    inputs = [marker, assignments, canonical / 'events.parquet', canonical_manifest, split_manifest]
    return config, config_path, approval_path, split, inputs


def test_main_worker_reads_parquet_selects_validates_reloads_and_exports(parquet_worker, monkeypatch):
    config, config_path, approval_path, parent_split, inputs = parquet_worker
    before = {str(p): sha(p) for p in inputs}
    loaded = []
    actual_load = runner._load_phase_inputs

    def observe_real_loader(*args, **kwargs):
        result = actual_load(*args, **kwargs)
        loaded.append(result)
        return result

    monkeypatch.setattr(runner, '_load_phase_inputs', observe_real_loader)
    assert runner._worker_main(['smoke', '--config', str(config_path),
                                '--authorization', str(approval_path)]) == 0
    assert len(loaded) == 1
    identity, split, train, val, stats = loaded[0]
    assert set(split.inner_train_users) <= set(parent_split.inner_train_users)
    assert set(split.inner_val_users) == set(parent_split.inner_val_users)
    assert not set(split.inner_train_users) & set(split.inner_val_users)
    assert len(train) == 2 and len(val) == 1
    assert sum(len(u.events) for u in train) == 8 and len(val[0].events) == 4
    assert all(u.fold != config.outer_fold for u in (*train, *val))
    for user in (*train, *val):
        assert [(e.time_done, e.source_row) for e in user.events] == sorted(
            (e.time_done, e.source_row) for e in user.events)
        assert all(e.user_id == user.user_id and e.fold == user.fold for e in user.events)
    assert stats['loader_highwater']['train']['peak_fetch_rows'] == 2
    assert stats['loader_highwater']['validation']['peak_fetch_rows'] == 2
    manifest = json.loads((config.output_dir / 'manifest.json').read_text())
    summary = manifest['summary']
    assert manifest['status'] == 'completed'
    assert manifest['gate_records']['gate2']['fixture'] is True
    assert summary['outer_users_requested'] is summary['holdout_requested'] is False
    assert summary['selected_epoch'] == 1 and summary['checkpoint_reload_state_exact'] is True
    assert summary['training']['optimizer_steps'] == 1
    assert summary['training']['valid_targets'] == 8
    assert summary['training']['nonzero_gradient_steps'] == summary['training']['parameter_update_steps'] == 1
    coverage = summary['coverage']
    assert coverage['status'] == 'complete'
    assert coverage['expected_rows'] == coverage['prediction_rows'] == 4
    assert coverage['fitted_rows'] == 3 and coverage['unseen_rows'] == 1
    checkpoint = config.output_dir / summary['selection_checkpoint']
    assert checkpoint.name == 'inner-best-epoch-1.pt'
    assert sha(checkpoint) == summary['checkpoint_sha256']
    payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
    assert payload['identity']['split_hash'] == split.split_hash
    assert tuple(payload['encoding']['values']) == ('A', 'B')
    assert payload['progress']['history'][0]['validation']['predicted_rows'] == 3
    con = duckdb.connect()
    try:
        rows = con.execute('SELECT user_id,source_row,exercise,correct,prediction,prediction_kind '
                           'FROM read_parquet(?) ORDER BY source_row',
                           [str(config.output_dir / 'predictions/part-*.parquet')]).fetchall()
    finally:
        con.close()
    assert len(rows) == len({r[1] for r in rows}) == 4
    assert [(r[0], r[1], r[2], r[3]) for r in rows] == [
        (val[0].user_id, e.source_row, e.exercise, e.correct) for e in val[0].events]
    assert sum(r[5] == 'unseen_item' and r[4] is None for r in rows) == 1
    assert before == {str(p): sha(p) for p in inputs}
    proof = {'kind': 'TEST_ONLY_SYNTHETIC_PARQUET_MAIN_WORKER_IN_PROCESS',
             'scope': 'actual worker, split/loader/train/validation/checkpoint/export; fake external provenance/RAM; no watchdog/refit/realdata claim',
             'split_hash': split.split_hash, 'parent_split_hash': parent_split.split_hash,
             'train_users': list(split.inner_train_users), 'validation_users': list(split.inner_val_users),
             'input_sha256_unchanged': before, 'checkpoint_sha256': sha(checkpoint),
             'training_targets': 8, 'validation_targets': 4, 'fitted_predictions': 3, 'unseen_predictions': 1,
             'prediction_target_identities': [list(r[:4]) for r in rows],
             'gate1_gate2_and_ram_are_test_fixtures': True, 'new_refit_or_recovery_runs': 0}
    (config.output_dir / 'worker-acceptance.json').write_text(
        json.dumps(proof, indent=2) + '\n', encoding='utf-8')


def test_main_worker_rejects_changed_parquet_identity_before_loading(parquet_worker, monkeypatch):
    config, config_path, approval_path, _, _ = parquet_worker
    approval = json.loads(approval_path.read_text())
    approval['identity']['assignments_sha256'] = 'different-synthetic-assignment-identity'
    approval_path.write_text(json.dumps(approval), encoding='utf-8')

    def forbidden(*args, **kwargs):
        raise AssertionError('authorization identity rejection must precede learner query')

    monkeypatch.setattr(runner, '_load_phase_inputs', forbidden)
    with pytest.raises(PermissionError, match='identity'):
        runner._worker_main(['smoke', '--config', str(config_path),
                             '--authorization', str(approval_path)])
    assert not config.output_dir.exists()
