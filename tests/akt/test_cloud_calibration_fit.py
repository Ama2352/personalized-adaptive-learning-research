"""CPU fit cloud từ Parquet đã pin, dùng đúng fitter V1 và chặn sai Volume."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest
from test_junyi_calibration_producer import case
from knowledge_tracing.akt import research_junyi_calibration as producer
from knowledge_tracing.akt.cloud_calibration_fit import fit_volume_calibration


@pytest.fixture
def cloud_case(case, tmp_path, monkeypatch):
    monkeypatch.setattr(producer, 'CLOUD_CALIBRATION_ARTIFACT_ROOT', tmp_path)
    case['paths'].canonical.touch()
    case['paths'].assignments.touch()
    case['paths'].canonical_manifest.write_text(json.dumps(dict(
        purpose='JUNYI_REFIT90_RESPONSE_CALIBRATION_SOURCE', roles_identity=case['phase'].roles.identity,
        phase_identity=case['phase'].identity, encoding_identity=case['binding'].vocabulary_sha256,
        train_events_included=False, selection_events_included=False,
        outer_events_included=False, holdout_events_included=False)))
    case['pins'] = {name: producer.sha256_file(getattr(case['paths'], name))
                    for name in ('canonical_manifest', 'split_manifest')}
    case['population'] = producer.prepare_calibration_population(case['paths'], case['phase'],
        source_pins=case['pins'], max_targets=20, max_learner_events=10)
    raw = case['output'] / 'raw'
    manifest = producer.export_refit_calibration_predictions(case['attached'], case['paths'], case['phase'],
        population=case['population'], expected_population_identity=case['population']['identity'],
        source_pins=case['pins'], max_targets=20, max_learner_events=10, prediction_batch_size=2, output=raw)
    case['raw'] = raw
    case['arguments'] = dict(binding=case['binding'], population=case['population'],
        expected_population_identity=case['population']['identity'],
        expected_manifest_sha256=producer.sha256_file(raw / 'manifest.json'),
        shard_sha256={row['path']: producer.sha256_file(raw / row['path']) for row in manifest['shards']},
        source_pins=case['pins'], max_targets=20, max_learner_events=10,
        artifact_root=producer.CalibrationFitArtifactRoot(tmp_path), run_id='cpu-fit', tranche_id='fit01')
    return case


def run(case, **changes):
    arguments = dict(case['arguments'], **changes)
    return fit_volume_calibration(case['raw'], case['paths'], case['phase'], **arguments)


def test_cloud_fit_uses_actual_v1_math_and_returns_explicit_drive_files(cloud_case, monkeypatch):
    case = cloud_case
    arguments = {key: value for key, value in case['arguments'].items()
                 if key not in ('artifact_root', 'run_id', 'tranche_id')}
    baseline = producer.fit_response_temperature_from_raw_export(case['raw'], case['paths'], case['phase'],
        **arguments, output=case['output'] / 'baseline')
    monkeypatch.setattr(producer, 'iter_predictions', lambda *_: pytest.fail('CPU fit cannot invoke model'))
    result = run(case)
    payloads = Path(result['payloads'])
    assert json.loads((payloads / 'fit/temperature.json').read_text()) == json.loads(json.dumps(baseline.to_payload()))
    complete = json.loads((payloads / 'COMPLETE.json').read_text())
    assert complete['total_targets'] == 20 and complete['supported_targets'] == 18
    request = result['publish_request']
    assert request['files'] == ['config.json', 'fit/temperature.json', 'fit/manifest.json',
                                'resource.json', 'COMPLETE.json']
    assert request['max_total_bytes'] == sum((payloads / name).stat().st_size for name in request['files'])
    for name, pin in complete['files'].items():
        assert producer.sha256_file(payloads / name) == pin['sha256']
    with pytest.raises(ValueError, match='new physical'):
        run(case)


@pytest.mark.parametrize('change', ['wrong_root', 'raw_pin', 'wrong_split', 'wrong_source_phase', 'traversal'])
def test_cloud_fit_rejects_wrong_root_or_provenance(cloud_case, change):
    case = cloud_case
    arguments = {}
    if change == 'wrong_root':
        arguments['artifact_root'] = producer.CalibrationFitArtifactRoot(case['output'])
    elif change == 'raw_pin':
        arguments['expected_manifest_sha256'] = '0' * 64
    elif change == 'wrong_split':
        arguments['binding'] = replace(case['binding'], split_sha256='0' * 64)
    elif change == 'wrong_source_phase':
        manifest = json.loads(case['paths'].canonical_manifest.read_text())
        manifest['phase_identity'] = '0' * 64
        case['paths'].canonical_manifest.write_text(json.dumps(manifest))
    else:
        arguments['run_id'] = '../escape'
    with pytest.raises(ValueError):
        run(case, **arguments)
    assert not (Path(case['arguments']['artifact_root'].root) / 'cpu-fit/fit01/payloads/COMPLETE.json').exists()


def test_cloud_fit_module_import_has_no_torch_side_effect():
    code = 'import sys; import knowledge_tracing.akt.cloud_calibration_fit; assert "torch" not in sys.modules'
    subprocess.run([sys.executable, '-B', '-c', code], check=True, capture_output=True, text=True)


def test_trusted_mount_resolves_once_and_rejects_alias_below_root(tmp_path, monkeypatch):
    physical = tmp_path / 'physical'
    physical.mkdir()
    mount = tmp_path / 'artifacts'
    try:
        mount.symlink_to(physical, target_is_directory=True)
    except OSError:
        pytest.skip('Directory symlinks require OS permission on this host')
    monkeypatch.setattr(producer, 'CLOUD_CALIBRATION_ARTIFACT_ROOT', mount)
    root = producer.CalibrationFitArtifactRoot(mount.resolve(strict=True))
    assert root.validate_output(physical / 'run/payloads') == physical / 'run/payloads'
    alias = physical / 'alias'
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='alias'):
        root.validate_output(alias / 'escape')
    with pytest.raises(ValueError, match='physical mounted'):
        producer.CalibrationFitArtifactRoot(mount).validate_output(mount / 'new')


def test_raw_export_writes_actual_parquet_under_typed_volume_root(cloud_case):
    case = cloud_case
    root = case['arguments']['artifact_root']
    raw = root.root / 'gpu-output/tranche01/payloads/raw'
    manifest = producer.export_refit_calibration_predictions(case['attached'], case['paths'], case['phase'],
        population=case['population'], expected_population_identity=case['population']['identity'],
        source_pins=case['pins'], max_targets=20, max_learner_events=10, prediction_batch_size=2,
        output=raw, artifact_root=root)
    pins = {row['path']: producer.sha256_file(raw / row['path']) for row in manifest['shards']}
    records = list(producer.iter_pinned_prediction_export(raw,
        expected_manifest_sha256=producer.sha256_file(raw / 'manifest.json'), shard_sha256=pins))
    assert manifest['status'] == 'complete' and len(records) == 20
    assert sum(row.prediction is None for row in records) == 2
