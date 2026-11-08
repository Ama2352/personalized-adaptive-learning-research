from pathlib import Path
import subprocess

import pytest

import knowledge_tracing.akt.config as config_module
from knowledge_tracing.akt.config import AKTConfig, validate_config
from knowledge_tracing.akt.provenance import verify_upstream


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ['git', '-C', str(root), *args], text=True, stderr=subprocess.STDOUT
    ).strip()


@pytest.fixture
def source_repo(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    git(root, 'init', '-q')
    git(root, 'remote', 'add', 'origin', 'https://github.com/arghosh/AKT.git')
    (root / 'akt.py').write_text('model = 1\n', encoding='utf-8')
    (root / 'README.md').write_text('AKT\n', encoding='utf-8')
    (root / 'LICENSE').write_text('MIT License\n', encoding='utf-8')
    git(root, 'add', 'akt.py', 'README.md', 'LICENSE')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'fixture')
    return root, git(root, 'rev-parse', 'HEAD')


def config_with(tmp_path, **overrides):
    values = dict(project_root=tmp_path, output_dir=tmp_path / 'experiments/akt/results/run')
    values.update(overrides)
    return AKTConfig(**values)


@pytest.fixture(autouse=True)
def trusted_project_root(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, 'PROJECT_ROOT', tmp_path)


def test_verify_upstream_rejects_wrong_commit_or_dirty_source(source_repo):
    root, commit = source_repo
    result = verify_upstream(root, commit)
    assert result['commit'] == commit
    assert set(result['files']) == {'akt.py', 'README.md', 'LICENSE'}
    assert len(result['files']['akt.py']) == 64
    with pytest.raises(ValueError, match='commit'):
        verify_upstream(root, '0' * 40)
    (root / 'akt.py').write_text('changed\n', encoding='utf-8')
    with pytest.raises(ValueError, match='dirty'):
        verify_upstream(root, commit)


def test_verify_detects_source_change_hidden_from_git_status(source_repo):
    root, commit = source_repo
    git(root, 'update-index', '--assume-unchanged', 'akt.py')
    (root / 'akt.py').write_text('silently modified\n', encoding='utf-8')
    assert subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip() == ''
    with pytest.raises(ValueError, match='source content'):
        verify_upstream(root, commit)


def test_config_rejects_graph_holdout_and_protected_output(tmp_path):
    validate_config(config_with(tmp_path))
    with pytest.raises(ValueError, match='protected output'):
        validate_config(config_with(tmp_path, output_dir=tmp_path / 'artifacts/bkt_baseline/new'))
    with pytest.raises(ValueError, match='graph'):
        validate_config(config_with(tmp_path, graph=True))
    with pytest.raises(ValueError, match='partition'):
        validate_config(config_with(tmp_path, partition='test'))


def test_phase_and_source_are_explicit(tmp_path):
    cfg = config_with(tmp_path)
    assert cfg.source_commit == '01b7e8d7d7c862cabc9467108e3e7f2555653a88'
    assert cfg.phase == 'preflight'
    with pytest.raises(ValueError, match='phase'):
        validate_config(config_with(tmp_path, phase='holdout'))
    with pytest.raises(ValueError, match='output'):
        validate_config(config_with(tmp_path, output_dir=Path('')))


def test_readiness_output_has_its_own_approved_directory(tmp_path):
    validate_config(config_with(tmp_path, phase='fold-readiness',
                                output_dir=tmp_path / 'experiments/akt/readiness/fold0'))


def test_provisional_training_and_resource_settings_are_explicit(tmp_path):
    cfg = config_with(tmp_path)
    assert cfg.betas == (0.9, 0.999)
    assert cfg.eps == 1e-8
    assert cfg.inner_val_fraction == 0.1
    assert cfg.patience == 3
    assert cfg.max_epochs == 20
    assert cfg.max_train_users is None
    assert cfg.protocol_version
    with pytest.raises(ValueError, match='training'):
        validate_config(config_with(tmp_path, lr=0))


def test_completed_run_cannot_be_overwritten(tmp_path):
    output = tmp_path / 'experiments/akt/results/run'
    output.mkdir(parents=True)
    (output / 'manifest.json').write_text('{"status":"completed"}', encoding='utf-8')
    with pytest.raises(ValueError, match='completed'):
        validate_config(config_with(tmp_path, output_dir=output))


def test_spoofed_project_root_cannot_authorize_a_protected_output(tmp_path):
    spoofed = tmp_path / 'artifacts/bkt_baseline'
    cfg = config_with(tmp_path, project_root=spoofed,
                      output_dir=spoofed / 'artifacts/akt/run')
    with pytest.raises(ValueError, match='project root'):
        validate_config(cfg)
