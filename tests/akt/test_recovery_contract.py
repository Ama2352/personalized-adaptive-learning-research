"""Recovery contract không đọc Junyi hoặc unpickle checkpoint."""

from dataclasses import asdict, replace
import json

import pytest

from knowledge_tracing.akt.config import AKTConfig, RecoveryOptions, PROJECT_ROOT, load_config
from knowledge_tracing.akt import recovery


def fixture_source(tmp_path):
    directory = tmp_path / 'experiments/akt/results/old'
    directory.mkdir(parents=True)
    identity = {'config_sha256': 'attempt-old', 'build_hashes': {'source.py': 'sha'},
                'assignments_sha256': 'split-sha', 'source': {'commit': 'pinned'}}
    config = AKTConfig(project_root=tmp_path, output_dir=directory, run_id='old',
                       max_wall_seconds=100, recovery=RecoveryOptions())
    files = {'manifest.json': {'run_id': 'old', 'status': 'incomplete'},
             'watchdog-resources.json': {'run_id': 'old', 'status': 'failed'}}
    for name, value in files.items():
        (directory / name).write_text(json.dumps(value), encoding='utf-8')
    (directory / 'snapshot.pt').write_bytes(b'synthetic checkpoint, never torch.load')
    reference = {'name': 'snapshot.pt', 'sha256': recovery.digest_file(directory / 'snapshot.pt')}
    (directory / 'recovery-progress.json').write_text(json.dumps({
        'checkpoint': 'snapshot.pt', 'files': [reference]}), encoding='utf-8')
    approval = {'identity': identity, 'caps': {'max_wall_seconds': 100}}
    recovery.publish_envelope(config, authorization=approval, elapsed_seconds=12.5)
    envelope = directory / 'recovery-envelope.json'
    destination = replace(config, run_id='new', output_dir=directory.with_name('new'),
                          recovery=RecoveryOptions(source_envelope=envelope,
                              source_sha256=recovery.digest_file(envelope)))
    return config, destination, approval


def test_default_off_and_json_options_roundtrip(tmp_path):
    config = AKTConfig(output_dir=PROJECT_ROOT / 'experiments/akt/results/recovery-schema',
                       run_id='recovery-schema', recovery=RecoveryOptions(5))
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(asdict(config), default=str), encoding='utf-8')
    assert load_config(path) == config
    assert AKTConfig().recovery is None
    value = json.loads(path.read_text(encoding='utf-8'))
    value['recovery']['unknown_field'] = True
    path.write_text(json.dumps(value), encoding='utf-8')
    with pytest.raises(TypeError):
        load_config(path)


def test_fork_preserves_semantics_and_source_bytes(tmp_path):
    original, config, approval = fixture_source(tmp_path)
    before = {path.name: recovery.digest_file(path) for path in original.output_dir.iterdir()}
    result = recovery.validate_source(config, current_identity={
        **approval['identity'], 'config_sha256': 'attempt-new', 'gate2_report_sha256': 'new-report'},
        caps=approval['caps'])
    assert result['attempt'] == 1 and result['cumulative_wall_seconds'] == 12.5
    assert recovery.semantic_hash(original) == recovery.semantic_hash(config)
    assert before == {path.name: recovery.digest_file(path) for path in original.output_dir.iterdir()}
    with pytest.raises(FileExistsError):
        recovery.publish_envelope(original, authorization=approval, elapsed_seconds=1)


@pytest.mark.parametrize('field,value', [
    ('lr', 0.1), ('seed', 5), ('context', 50), ('max_epochs', 21),
    ('graph', True), ('device', 'cuda'), ('max_wall_seconds', 200), ('outer_fold', 1)])
def test_semantic_changes_rejected_before_checkpoint_load(tmp_path, field, value):
    _, config, approval = fixture_source(tmp_path)
    config = replace(config, **{field: value})
    caps = {**approval['caps']}
    if field == 'max_wall_seconds':
        caps[field] = value
    with pytest.raises(ValueError, match='semantic or input identity'):
        recovery.validate_source(config, current_identity=approval['identity'], caps=caps)


@pytest.mark.parametrize('name', ['snapshot.pt', 'manifest.json', 'watchdog-resources.json',
                                 'recovery-envelope.json'])
def test_referenced_file_tampering_is_rejected(tmp_path, name):
    original, config, approval = fixture_source(tmp_path)
    with (original.output_dir / name).open('ab') as stream:
        stream.write(b'tampered')
    with pytest.raises(ValueError, match='hash'):
        recovery.validate_source(config, current_identity=approval['identity'], caps=approval['caps'])


def test_source_build_split_and_cumulative_wall_are_not_reset(tmp_path):
    _, config, approval = fixture_source(tmp_path)
    for field in ('build_hashes', 'assignments_sha256', 'source'):
        with pytest.raises(ValueError, match='identity'):
            recovery.validate_source(config, current_identity={**approval['identity'], field: 'changed'},
                                     caps=approval['caps'])
    # Budget nhỏ hơn source vừa đổi semantics, không được dùng để cấp lại thời gian.
    with pytest.raises(ValueError):
        recovery.validate_source(config, current_identity=approval['identity'], caps={'max_wall_seconds': 12})


@pytest.mark.parametrize('options', [RecoveryOptions(True), RecoveryOptions(0),
    RecoveryOptions(source_sha256='a' * 64), RecoveryOptions(source_envelope=PROJECT_ROOT / 'dataset/x'),
    RecoveryOptions(source_envelope=PROJECT_ROOT / 'dataset/recovery-envelope.json', source_sha256='a' * 64)])
def test_unsafe_or_incomplete_request_rejected(options):
    with pytest.raises(ValueError):
        recovery.validate_options(AKTConfig(recovery=options))


def test_symlink_reference_cannot_escape_run(tmp_path):
    _, config, approval = fixture_source(tmp_path)
    envelope = config.recovery.source_envelope
    value = json.loads(envelope.read_text(encoding='utf-8'))
    value['files'][0]['name'] = '../outside.pt'
    envelope.write_text(json.dumps(value), encoding='utf-8')
    config = replace(config, recovery=replace(config.recovery, source_sha256=recovery.digest_file(envelope)))
    with pytest.raises(ValueError, match='file name'):
        recovery.validate_source(config, current_identity=approval['identity'], caps=approval['caps'])
