"""Fit temperature V1 trên CPU từ raw calibration đã pin trong cloud Volume.

Module không tạo cloud resource, không nhập Torch và không thực hiện upload.
Caller commit Volume trước khi chuyển publish_request cho Drive CPU worker.
"""
from dataclasses import asdict
import json
from pathlib import Path
import re
import time

from .research_junyi_calibration import (
    CalibrationFitArtifactRoot, fit_response_temperature_from_raw_export)
from .prediction import _write_json_atomic
from .provenance import sha256_file
from .resources import memory_snapshot


def _need(value, message):
    if not value:
        raise ValueError(message)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}', value),
          'explicit run/tranche identifier required')
    return value


def _volume_input(path, root):
    path = Path(path).absolute()
    _need(path.is_file() and path.is_relative_to(root), 'calibration input must be a Volume file')
    for component in (path, *path.parents):
        if component == root:
            break
        _need(not component.is_symlink()
              and not getattr(component, 'is_junction', lambda: False)(), 'Volume input alias rejected')
    _need(path.resolve(strict=True) == path, 'canonical Volume input required')
    return path


def fit_volume_calibration(raw, paths, view, *, binding, population,
        expected_population_identity, expected_manifest_sha256, shard_sha256,
        source_pins, max_targets, max_learner_events, artifact_root, run_id, tranche_id):
    """CPU fit độc lập, trả danh sách publish rõ ràng sau khi ghi completion."""
    _need(type(artifact_root) is CalibrationFitArtifactRoot, 'typed calibration artifact root required')
    run_id = _identifier(run_id)
    tranche_id = _identifier(tranche_id)
    payloads = Path(artifact_root.root) / run_id / tranche_id / 'payloads'
    artifact_root.validate_output(payloads)
    root = Path(artifact_root.root).resolve(strict=True)
    view.assert_integrity()
    _need(view.scope == 'calibration_predict' and view.full_role_coverage
          and binding.split_sha256 == view.roles.identity,
          'full calibration10 phase and matching binding required')
    for name in ('canonical', 'assignments', 'canonical_manifest', 'split_manifest'):
        _volume_input(getattr(paths, name), root)
    raw = Path(raw).absolute()
    _volume_input(raw / 'manifest.json', root)
    for filename in shard_sha256:
        _need(Path(filename).name == filename, 'raw shard basename required')
        _volume_input(raw / filename, root)
    source_manifest = json.loads(paths.canonical_manifest.read_text(encoding='utf-8'))
    _need(source_manifest.get('purpose') == 'JUNYI_REFIT90_RESPONSE_CALIBRATION_SOURCE'
          and source_manifest.get('roles_identity') == view.roles.identity
          and source_manifest.get('phase_identity') == view.identity
          and source_manifest.get('encoding_identity') == binding.vocabulary_sha256
          and all(source_manifest.get(name) is False for name in ('train_events_included',
              'selection_events_included', 'outer_events_included', 'holdout_events_included')),
          'calibration10-only source manifest required')
    config = dict(kind='JUNYI_CLOUD_CPU_CALIBRATION_FIT_V1', run_id=run_id, tranche_id=tranche_id,
        binding=asdict(binding), population_identity=expected_population_identity,
        source_pins=source_pins, raw_manifest_sha256=expected_manifest_sha256,
        raw_shard_sha256=shard_sha256, max_targets=max_targets,
        max_learner_events=max_learner_events, algorithm='fit_temperature_v1', device='cpu')
    payloads.mkdir(parents=True, exist_ok=False)
    _write_json_atomic(payloads / 'config.json', config)
    started = time.monotonic()
    before = memory_snapshot()
    try:
        calibration = fit_response_temperature_from_raw_export(raw, paths, view,
            binding=binding, population=population,
            expected_population_identity=expected_population_identity,
            expected_manifest_sha256=expected_manifest_sha256, shard_sha256=shard_sha256,
            source_pins=source_pins, max_targets=max_targets, max_learner_events=max_learner_events,
            output=payloads / 'fit', artifact_root=artifact_root)
    except Exception as exc:
        _write_json_atomic(payloads / 'FAILED.json', dict(status='CPU_CALIBRATION_FIT_FAILED',
            error_type=type(exc).__name__, wall_seconds=time.monotonic()-started))
        raise
    _write_json_atomic(payloads / 'resource.json', dict(wall_seconds=time.monotonic()-started,
        before=before, after=memory_snapshot(), device='cpu'))
    files = ['config.json', 'fit/temperature.json', 'fit/manifest.json', 'resource.json']
    inventory = {name: dict(bytes=(payloads / name).stat().st_size,
                           sha256=sha256_file(payloads / name)) for name in files}
    _write_json_atomic(payloads / 'COMPLETE.json', dict(status='JUNYI_CLOUD_CPU_CALIBRATION_FIT_COMPLETE',
        calibration_status=calibration.status, calibration_identity=calibration.identity,
        files=inventory, total_targets=calibration.total_targets,
        supported_targets=calibration.supported_targets))
    files.append('COMPLETE.json')
    return dict(status='CPU_FIT_ARTIFACTS_READY_FOR_VOLUME_COMMIT',
        calibration_identity=calibration.identity, payloads=str(payloads),
        publish_request=dict(run_id=run_id, tranche_id=tranche_id, files=files,
            max_total_bytes=sum((payloads / name).stat().st_size for name in files)))
