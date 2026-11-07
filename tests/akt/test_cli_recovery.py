"""Actual CLI parent/worker lifecycle trên isolated synthetic dependency fixtures."""

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess
import sys

import duckdb
import pytest
import torch

from knowledge_tracing.akt.authorization import config_hash
from knowledge_tracing.akt.config import load_config, PROJECT_ROOT, RecoveryOptions
from knowledge_tracing.akt.recovery import digest_file


def launch(config, directory, *, interrupt=''):
    directory.mkdir(parents=True, exist_ok=True)
    config_path, approval_path = directory / 'config.json', directory / 'authorization.json'
    config_path.write_text(json.dumps(asdict(config), default=str), encoding='utf-8')
    approval = {'approved': True, 'scope': 'development-inner-only', 'phase': config.phase,
        'run_id': config.run_id, 'source_commit': config.source_commit, 'config_sha256': config_hash(config),
        'approval_reference': 'isolated synthetic engineering fixture; not real-data authorization',
        'identity': {'source': {'commit': config.source_commit}, 'lock_sha256': 'fixture-lock',
            'runtime_report_sha256': 'fixture-runtime', 'config_sha256': config_hash(config),
            'build_hashes': {'fixture': 'same-source'}, 'assignments_sha256': 'fixture-assignments'},
        'caps': {key: getattr(config, key) for key in ('max_train_users', 'max_val_users',
            'max_targets_per_side', 'max_steps', 'max_seconds', 'max_wall_seconds',
            'max_rss_bytes', 'min_available_ram_bytes')}}
    approval_path.write_text(json.dumps(approval), encoding='utf-8')
    env = {**os.environ, 'AKT_TEST_FIXTURE_ROOT': str(config.project_root), 'AKT_TEST_INTERRUPT': interrupt,
           'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '',
           'PYTHONPATH': os.pathsep.join([str(PROJECT_ROOT / 'src'), str(PROJECT_ROOT / 'third_party')])}
    command = [sys.executable, str(Path(__file__).with_name('cli_recovery_fixture.py')), 'smoke',
               '--config', str(config_path), '--authorization', str(approval_path)]
    result = subprocess.run(command, env=env, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=90)
    (directory / 'stdout.log').write_text(result.stdout, encoding='utf-8')
    (directory / 'stderr.log').write_text(result.stderr, encoding='utf-8')
    return result


def probabilities(directory):
    return duckdb.sql("SELECT user_id, source_row, exercise, correct, prediction, prediction_kind FROM read_parquet(?) "
                      "ORDER BY user_id, source_row", params=[str(directory / 'predictions/part-*.parquet')]).fetchall()


@pytest.mark.parametrize('boundary', ['batch-exit', 'export'])
def test_actual_cli_fresh_attempt_recovery_and_prediction_export(tmp_path, boundary):
    root = tmp_path / 'project'
    root.mkdir()
    template = load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json')
    config = replace(template, project_root=root, execution_enabled=True, run_id='continuous',
        output_dir=root / 'experiments/akt/results/continuous', recovery=RecoveryOptions(),
        dropout=.2, batch_size=2, max_steps=3, max_seconds=60, max_wall_seconds=180)
    result = launch(config, tmp_path / 'continuous-cli')
    assert result.returncode == 0, result.stderr
    interrupted = replace(config, run_id='old', output_dir=config.output_dir.with_name('old'))
    result = launch(interrupted, tmp_path / 'old-cli', interrupt=boundary)
    assert result.returncode != 0
    source = interrupted.output_dir / 'recovery-envelope.json'
    envelope = json.loads(source.read_text(encoding='utf-8'))
    assert envelope['attempt'] == 1 and envelope['cumulative_wall_seconds'] > 0
    assert json.loads((interrupted.output_dir / 'watchdog-resources.json').read_text())['status'] == 'failed'
    before = {path.name: digest_file(path) for path in interrupted.output_dir.iterdir() if path.is_file()}
    resumed = replace(config, run_id='resumed', output_dir=config.output_dir.with_name('resumed'),
                      recovery=RecoveryOptions(source_envelope=source, source_sha256=digest_file(source)))
    result = launch(resumed, tmp_path / 'resumed-cli')
    assert result.returncode == 0, result.stderr
    expected = json.loads((config.output_dir / 'manifest.json').read_text())
    actual = json.loads((resumed.output_dir / 'manifest.json').read_text())
    assert actual['status'] == expected['status'] == 'completed'
    assert actual['attempt'] == 2 and actual['retry_history'][0]['source_run_id'] == 'old'
    assert actual['summary']['training']['valid_targets'] == expected['summary']['training']['valid_targets'] == 85
    assert actual['summary']['training']['optimizer_steps'] == 3
    assert actual['summary']['validation_loss'] == expected['summary']['validation_loss']
    assert probabilities(config.output_dir) == probabilities(resumed.output_dir)
    assert before == {path.name: digest_file(path) for path in interrupted.output_dir.iterdir() if path.is_file()}
    old = torch.load(config.output_dir / expected['summary']['selection_checkpoint'], weights_only=True)
    new = torch.load(resumed.output_dir / actual['summary']['selection_checkpoint'], weights_only=True)
    assert all(torch.equal(value, new['model_state_dict'][key]) for key, value in old['model_state_dict'].items())
