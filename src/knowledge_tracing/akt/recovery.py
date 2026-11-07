"""Hợp đồng recovery có hash, không import Torch hoặc mở nguồn learner.

Envelope chỉ được công bố sau khi watchdog đã kết thúc worker. Mỗi retry
phải dùng run mới và authorization mới, cùng semantic identity và tổng caps.
"""

from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import re
import os
import uuid

from .config import AKTConfig, RecoveryOptions
from .filesystem import publish_new_file


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_hash(config: AKTConfig) -> str:
    payload = asdict(config)
    # Chỉ ba trường thuộc attempt; mọi model/data/protocol/resource field giữ lại.
    for name in ('run_id', 'output_dir', 'recovery'):
        payload.pop(name)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def training_config_hash(config: AKTConfig) -> str:
    if config.recovery is not None:
        return semantic_hash(config)
    return hashlib.sha256(json.dumps(asdict(config), sort_keys=True, default=str).encode()).hexdigest()


def training_budget(config: AKTConfig, budget: dict) -> dict:
    return {key: value for key, value in budget.items()
            if config.recovery is None or key != 'run_id'}


def preserve_checkpoint(source: Path, destination: Path) -> Path:
    """Copy byte-identical vào attempt mới, không thay checkpoint/identity nguồn."""
    if source.resolve() == destination.resolve():
        return source
    expected = digest_file(source)
    temp = destination.with_name(destination.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with source.open('rb') as old, temp.open('xb') as new:
            for chunk in iter(lambda: old.read(1024 * 1024), b''):
                new.write(chunk)
            new.flush()
            os.fsync(new.fileno())
        if digest_file(temp) != expected or digest_file(source) != expected:
            raise ValueError('checkpoint changed during preservation')
        publish_new_file(temp, destination)
    finally:
        temp.unlink(missing_ok=True)
    return destination


def stable_inputs(identity: dict) -> dict:
    # Gate2 report/pointer có thể được cấp lại cho cùng build, không phải training input.
    return {key: value for key, value in identity.items()
            if key not in {'config_sha256', 'gate2_report_sha256',
                           'gate2_test_log_sha256', 'gate2_pointer_sha256'}}


def validate_options(config: AKTConfig) -> None:
    options = config.recovery
    if (not isinstance(options, RecoveryOptions)
            or type(options.checkpoint_every_steps) is not int
            or options.checkpoint_every_steps < 1):
        raise ValueError('invalid recovery options or checkpoint cadence')
    root = (config.project_root / 'experiments/akt/results').resolve()
    if config.output_dir.resolve().parent != root:
        raise ValueError('recovery requires a unique results run directory')
    if (options.source_envelope is None) != (options.source_sha256 is None):
        raise ValueError('recovery requires both source envelope and SHA-256')
    if options.source_envelope is None:
        return
    if (not isinstance(options.source_sha256, str)
            or not re.fullmatch('[a-f0-9]{64}', options.source_sha256)):
        raise ValueError('invalid recovery envelope SHA-256')
    source = options.source_envelope.resolve()
    if (source.name != 'recovery-envelope.json' or source.parent.parent != root
            or source.parent == config.output_dir.resolve()):
        raise ValueError('recovery source must belong to a different results run')


def _read_json(path: Path) -> dict:
    if path.stat().st_size > 4 * 1024**2:
        raise ValueError('recovery JSON exceeds size limit')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('invalid recovery JSON object')
    return value


def _checked_file(directory: Path, reference: dict) -> Path:
    if not isinstance(reference, dict):
        raise ValueError('invalid recovery file reference')
    name, digest = reference.get('name'), reference.get('sha256')
    if (not isinstance(name, str) or not name or Path(name).name != name
            or ':' in name or '\\' in name or '/' in name):
        raise ValueError('invalid recovery file name')
    path = (directory / name).resolve()
    if path.parent != directory.resolve() or digest_file(path) != digest:
        raise ValueError('recovery file hash or path mismatch')
    return path


def validate_source(config: AKTConfig, *, current_identity: dict, caps: dict) -> dict | None:
    """Kiểm cả envelope, manifest, watchdog, checkpoint trước data load/Torch load."""
    if config.recovery is None or config.recovery.source_envelope is None:
        return None
    validate_options(config)
    path = config.recovery.source_envelope.resolve()
    if digest_file(path) != config.recovery.source_sha256:
        raise ValueError('recovery envelope hash mismatch')
    value = _read_json(path)
    effective = replace(config, **caps)
    if (value.get('schema_version') != 1
            or value.get('source_run_id') != path.parent.name
            or value.get('semantic_sha256') != semantic_hash(effective)
            or value.get('input_identity') != stable_inputs(current_identity)):
        raise ValueError('recovery semantic or input identity mismatch')
    if type(value.get('attempt')) is not int or value['attempt'] < 1:
        raise ValueError('invalid recovery attempt counter')
    elapsed = value.get('cumulative_wall_seconds')
    if (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float))
            or not math.isfinite(elapsed) or elapsed < 0):
        raise ValueError('invalid cumulative recovery wall time')
    if elapsed >= caps['max_wall_seconds']:
        raise ValueError('cumulative recovery wall budget exhausted')
    manifest = _read_json(_checked_file(path.parent, value.get('manifest')))
    watchdog = _read_json(_checked_file(path.parent, value.get('watchdog')))
    if (manifest.get('run_id') != path.parent.name
            or manifest.get('status') not in {'incomplete', 'failed', 'bounded'}
            or watchdog.get('run_id') != path.parent.name
            or watchdog.get('status') not in {'incomplete', 'failed', 'bounded'}):
        raise ValueError('recovery source is not a terminated incomplete attempt')
    files = value.get('files')
    if not isinstance(files, list) or not files:
        raise ValueError('recovery envelope has no checkpoint files')
    names = [_checked_file(path.parent, item).name for item in files]
    checkpoint = value.get('checkpoint')
    if checkpoint not in names or not checkpoint.endswith('.pt'):
        raise ValueError('recovery checkpoint is missing from file contract')
    return value


def publish_envelope(config: AKTConfig, *, authorization: dict, elapsed_seconds: float) -> None:
    """Parent-only terminal snapshot. Không tìm checkpoint bằng glob/newest-file."""
    if config.recovery is None:
        return
    directory = config.output_dir.resolve()
    pointer = directory / 'recovery-progress.json'
    if not pointer.is_file():
        return
    source = validate_source(config, current_identity=authorization['identity'], caps=authorization['caps'])
    progress = _read_json(pointer)
    files = progress.get('files')
    if not isinstance(files, list) or not files:
        raise ValueError('missing committed recovery files')
    for reference in files:
        _checked_file(directory, reference)
    value = {'schema_version': 1, 'source_run_id': config.run_id,
             'semantic_sha256': semantic_hash(replace(config, **authorization['caps'])),
             'input_identity': stable_inputs(authorization['identity']),
             'attempt': (source['attempt'] if source else 0) + 1,
             'cumulative_wall_seconds': (source['cumulative_wall_seconds'] if source else 0.0) + elapsed_seconds,
             'checkpoint': progress['checkpoint'], 'files': files,
             'manifest': {'name': 'manifest.json', 'sha256': digest_file(directory / 'manifest.json')},
             'watchdog': {'name': 'watchdog-resources.json',
                          'sha256': digest_file(directory / 'watchdog-resources.json')}}
    destination = directory / 'recovery-envelope.json'
    temp = destination.with_suffix('.json.tmp')
    try:
        with temp.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, sort_keys=True, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        publish_new_file(temp, destination)
    finally:
        temp.unlink(missing_ok=True)
