"""Builder dummy prepare-only: input thật Parquet nhưng không thực thi model."""

import builtins
import hashlib
import json

import duckdb
import pytest

import scripts.akt.prepare_synthetic_context as builder
from knowledge_tracing.akt import config as config_module
from knowledge_tracing.akt.config import load_config
from knowledge_tracing.akt.context import load_worker_context
from knowledge_tracing.akt.data import read_development_assignments, iter_development_learners
from knowledge_tracing.akt.splits import make_inner_split


@pytest.fixture
def prepared_root(tmp_path, monkeypatch):
    root = (tmp_path / 'repo').resolve()
    root.mkdir()
    monkeypatch.setattr(builder, 'PROJECT_ROOT', root)
    monkeypatch.setattr(config_module, 'PROJECT_ROOT', root)
    return root


def prepare(root, name='fixture-01', **kwargs):
    return builder.prepare_synthetic_context(name, project_root=root,
        runtime_report='artifacts/akt/preflight/not-yet-runtime.json',
        lock_file='requirements-akt-linux.lock.txt',
        gate2_report='artifacts/akt/preflight/not-yet-gate2.json', **kwargs)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_actual_parquet_dummy_coverage_chronology_and_outer_sentinel(prepared_root):
    root = prepared_root
    inventory = prepare(root)
    context = load_worker_context(root / inventory['context_file'],
        expected_sha256=inventory['context_sha256'], project_root=root)
    config = load_config(root / inventory['config_file'])
    assert config.execution_enabled is False and config.phase == 'smoke' and config.device == 'cpu'
    context.validate_for(config)
    assignments = read_development_assignments(context.data_paths)
    assert len(assignments) == 8 and assignments.user_id.nunique() == 8
    assert dict(assignments.groupby('fold').size()) == {0: 1, 1: 2, 2: 2, 3: 2, 4: 1}
    split = make_inner_split(assignments, outer_fold=0, seed=42)
    assert (len(split.inner_train_users), len(split.inner_val_users)) == (6, 1)
    assert 'dummy-00' not in split.inner_train_users + split.inner_val_users
    learners = tuple(iter_development_learners(context.data_paths,
        user_ids=tuple(assignments.user_id), allowed_folds=tuple(range(5))))
    assert len(learners) == 8 and all(len(item.events) == 8 for item in learners)
    with duckdb.connect() as con:
        rows = con.execute('SELECT * FROM read_parquet(?) ORDER BY user_id,time_done,source_row',
                           [str(context.data_paths.canonical / 'events.parquet')]).fetchall()
        assert con.execute('SELECT DISTINCT partition FROM read_parquet(?)',
                           [str(context.data_paths.assignments)]).fetchall() == [('development',)]
    assert len(rows) == 64
    assert {row[1] for row in rows} == {'A', 'B'}
    assert len({row[2] for row in rows}) == len({row[3] for row in rows}) == 64
    assert {row[4] for row in rows} == {0, 1}
    assert {row[5] for row in rows} == {0, 1}
    marker = json.loads((context.dataset_root / 'SYNTHETIC_ONLY.json').read_text(encoding='utf-8'))
    assert marker['synthetic_only'] is True and marker['real_data_authorized'] is False
    assert 'dummy' in marker['label_semantics'] and 'FIXTURE' in marker['model_metadata']
    assert inventory['optimizer_steps'] == 0 and inventory['readback_rows_equal'] is True


def test_default_hypers_and_budget_are_exact(prepared_root):
    result = prepare(prepared_root)
    config = load_config(prepared_root / result['config_file'])
    assert (config.context, config.target_block, config.max_length) == (100, 100, 200)
    assert (config.d_model, config.heads, config.blocks, config.d_ff, config.final_fc) == (32, 4, 1, 64, 32)
    assert (config.batch_size, config.max_epochs, config.dropout, config.n_pid) == (4, 1, 0.0, 0)
    for name, cap in builder.CAPS.items():
        assert getattr(config, name) == cap
    assert config.max_total_targets == 128 and config.min_available_ram_bytes == 1024**3
    assert config.seed == 42 and config.partition == 'development' and config.outer_fold == 0


def test_no_model_backend_cloud_import_or_execution_output(prepared_root, monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        assert name.split('.')[0] not in {'torch', 'modal'}
        assert name not in {'knowledge_tracing.akt.runner', 'knowledge_tracing.akt.backend'}
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    result = prepare(prepared_root)
    dataset = prepared_root / result['dataset_root']
    assert not (prepared_root / 'experiments').exists()
    assert len(result['outputs_sha256']) == 7 and len(list(dataset.rglob('*.parquet'))) == 2
    assert not list(dataset.rglob('authorization.json'))
    def check_keys(value):
        if isinstance(value, dict):
            assert not any('approved' in key for key in value)
            for key, item in value.items():
                if key == 'execution_enabled':
                    assert item is False
                check_keys(item)
        elif isinstance(value, list):
            for item in value:
                check_keys(item)
    for path in dataset.rglob('*.json'):
        check_keys(json.loads(path.read_text(encoding='utf-8')))
    assert result['runtime_gate2_lock_contents_checked'] is False


def test_input_and_output_hash_membership_match_loader_and_tamper_rejected(prepared_root):
    result = prepare(prepared_root)
    sidecar = prepared_root / result['context_file']
    context = load_worker_context(sidecar, expected_sha256=result['context_sha256'], project_root=prepared_root)
    assert len(context.input_hashes) == 5
    assert set(dict(context.input_hashes)) == {str(path.relative_to(prepared_root).as_posix()) for path in (
        context.data_paths.canonical / 'events.parquet', context.data_paths.assignments,
        context.data_paths.canonical_manifest, context.data_paths.split_manifest,
        context.dataset_root / 'SYNTHETIC_ONLY.json')}
    for path, digest in result['outputs_sha256'].items():
        assert sha(prepared_root / path) == digest
    marker = context.dataset_root / 'SYNTHETIC_ONLY.json'
    marker.write_text('{"synthetic_only":true,"real_data_authorized":false}', encoding='utf-8')
    with pytest.raises(ValueError, match='hashes'):
        context.revalidate(prepared_root)


def test_deterministic_same_dummy_rows_and_data_bytes_across_ids(prepared_root):
    first, second = prepare(prepared_root, 'repeat-a'), prepare(prepared_root, 'repeat-b')
    a, b = prepared_root / first['dataset_root'], prepared_root / second['dataset_root']
    for name in ('canonical/events.parquet', 'assignments.parquet', 'canonical_manifest.json',
                 'split_manifest.json', 'SYNTHETIC_ONLY.json'):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_exclusive_id_and_existing_output_preserve_bytes(prepared_root):
    result = prepare(prepared_root)
    before = {path: sha(prepared_root / path) for path in result['outputs_sha256']}
    with pytest.raises(FileExistsError):
        prepare(prepared_root)
    assert before == {path: sha(prepared_root / path) for path in before}
    output = prepared_root / 'experiments/akt/results/occupied'
    output.mkdir(parents=True)
    (output / 'sentinel').write_bytes(b'preserve')
    with pytest.raises(FileExistsError):
        prepare(prepared_root, 'occupied')
    assert (output / 'sentinel').read_bytes() == b'preserve'
    assert not (prepared_root / 'artifacts/akt/synthetic/occupied').exists()


@pytest.mark.parametrize('caps', [
    {'max_steps': True}, {'max_seconds': False}, {'max_steps': 0}, {'max_steps': -1},
    {'max_steps': 3}, {'max_train_users': 9}, {'max_val_users': 5},
    {'max_targets_per_side': 65}, {'max_seconds': 121}, {'max_wall_seconds': 301},
    {'max_rss_bytes': 2 * 1024**3 + 1}, {'max_seconds': float('nan')},
    {'max_wall_seconds': float('inf')}, {'max_train_users': 2.0},
    {'max_total_targets': 128}, {'min_available_ram_bytes': 1},
    {'max_targets_per_side': 7}, {'max_steps': 1}, {'execution_enabled': True},
])
def test_invalid_or_increased_caps_rejected_before_reservation(prepared_root, caps):
    with pytest.raises(ValueError):
        prepare(prepared_root, caps=caps)
    assert not (prepared_root / 'artifacts').exists()


def test_lower_caps_derive_total_and_keep_ram_floor(prepared_root):
    result = prepare(prepared_root, caps={'max_train_users': 4, 'max_val_users': 2,
        'max_targets_per_side': 8, 'max_steps': 1, 'max_seconds': 60,
        'max_wall_seconds': 120, 'max_rss_bytes': 1024**3})
    config = load_config(prepared_root / result['config_file'])
    assert config.max_total_targets == 16 and config.max_steps == 1
    assert config.min_available_ram_bytes == 1024**3


@pytest.mark.parametrize('mode,limits', [
    ('pilot', None), ('cuda-smoke', None), ('smoke', {'max_vram_bytes': 1024**3, 'visible_devices': 1}),
    ('cuda-smoke', {'max_vram_bytes': True, 'visible_devices': 1}),
    ('cuda-smoke', {'max_vram_bytes': 1024**3, 'visible_devices': True}),
    ('cuda-smoke', {'max_vram_bytes': 63 * 1024**2, 'visible_devices': 1}),
    ('cuda-smoke', {'max_vram_bytes': 2 * 1024**3 + 1, 'visible_devices': 1}),
    ('cuda-smoke', {'max_vram_bytes': 1024**3, 'visible_devices': 2}),
    ('cuda-smoke', {'max_vram_bytes': 1024**3, 'visible_devices': 1, 'extra': 1}),
])
def test_cuda_requires_explicit_strict_limits_without_gpu_calls(prepared_root, mode, limits):
    with pytest.raises(ValueError):
        prepare(prepared_root, mode=mode, cuda_limits=limits)
    assert not (prepared_root / 'artifacts').exists()


def test_cuda_spec_only_context_validates_without_torch(prepared_root):
    limits = {'max_vram_bytes': 64 * 1024**2, 'visible_devices': 1}
    result = prepare(prepared_root, mode='cuda-smoke', cuda_limits=limits)
    config = load_config(prepared_root / result['config_file'])
    context = load_worker_context(prepared_root / result['context_file'],
        expected_sha256=result['context_sha256'], project_root=prepared_root)
    assert config.device == 'cuda' and config.execution_enabled is False
    assert context.validate_for(config).cuda_limits.max_vram_bytes == limits['max_vram_bytes']
    assert not (prepared_root / 'experiments').exists()


@pytest.mark.parametrize('key,path', [
    ('runtime_report', 'dataset/private.json'), ('runtime_report', '/absolute.json'),
    ('runtime_report', 'artifacts/akt/preflight/../other.json'),
    ('runtime_report', r'artifacts\akt\preflight\r.json'),
    ('runtime_report', 'artifacts/akt/preflight/*.json'),
    ('gate2_report', 'artifacts/akt/preflight'),
    ('lock_file', 'artifacts/akt/private/key.txt'), ('lock_file', 'requirements.txt'),
    ('lock_file', 'C:/lock.txt'),
])
def test_unsafe_references_rejected_before_reservation(prepared_root, key, path):
    args = {'runtime_report': 'artifacts/akt/preflight/r.json',
            'gate2_report': 'artifacts/akt/preflight/g.json', 'lock_file': 'requirements-akt.lock.txt'}
    args[key] = path
    with pytest.raises(ValueError):
        builder.prepare_synthetic_context('bad', project_root=prepared_root, **args)
    assert not (prepared_root / 'artifacts').exists()


@pytest.mark.parametrize('dataset_id', ['', '../escape', '/absolute', 'a/b', 'a\\b', '.'])
def test_unsafe_ids_rejected(prepared_root, dataset_id):
    with pytest.raises(ValueError):
        prepare(prepared_root, dataset_id)
    assert not (prepared_root / 'artifacts').exists()


def test_cli_has_no_execution_or_arbitrary_root_flag(prepared_root, capsys):
    assert builder.main(['--dataset-id', 'cli', '--runtime-report', 'artifacts/akt/preflight/r.json',
        '--lock-file', 'requirements-akt.lock.txt', '--gate2-report', 'artifacts/akt/preflight/g.json']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['execution_enabled'] is False
    with pytest.raises(SystemExit):
        builder.main(['--project-root', str(prepared_root)])


def test_partial_failure_is_preserved_and_cannot_be_reused(prepared_root, monkeypatch):
    original = builder._write_json
    def fail_marker(path, value):
        if path.name == 'SYNTHETIC_ONLY.json':
            raise OSError('injected write failure')
        return original(path, value)
    monkeypatch.setattr(builder, '_write_json', fail_marker)
    with pytest.raises(OSError, match='injected'):
        prepare(prepared_root)
    root = prepared_root / 'artifacts/akt/synthetic/fixture-01'
    assert (root / 'canonical/events.parquet').is_file()
    assert not (root / 'preparation-inventory.json').exists()
    with pytest.raises(FileExistsError):
        prepare(prepared_root)
