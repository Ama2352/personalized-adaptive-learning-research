"""Chuẩn bị input AKT dummy riêng; không cấp quyền và không chạy worker/model."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from knowledge_tracing.akt.config import AKTConfig, PROJECT_ROOT, validate_config  # noqa: E402
from knowledge_tracing.akt.context import load_worker_context  # noqa: E402

GIB = 1024**3
CAPS = {'max_train_users': 8, 'max_val_users': 4, 'max_targets_per_side': 64,
        'max_steps': 2, 'max_seconds': 120, 'max_wall_seconds': 300,
        'max_rss_bytes': 2 * GIB}
SCOPE = 'synthetic-development-only'
SOURCE_FILES = ('scripts/akt/prepare_synthetic_context.py',
                'src/knowledge_tracing/akt/context.py',
                'src/knowledge_tracing/akt/config.py',
                'src/knowledge_tracing/akt/watchdog.py')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def _reference(root: Path, text: str, role: str) -> str:
    if (not isinstance(text, str) or not text or '\\' in text or ':' in text
            or any(char in text for char in '*?[]')):
        raise ValueError('references must be project-relative POSIX paths')
    relative = PurePosixPath(text)
    if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != text:
        raise ValueError('references must be normalized project-relative POSIX paths')
    target = (root / text).resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError('reference escapes project')
    if target.is_relative_to((root / 'artifacts/akt/private').resolve()):
        raise ValueError('private references are unavailable')
    if role in {'runtime_report', 'gate2_report'}:
        base = (root / 'artifacts/akt/preflight').resolve()
        valid = target.is_relative_to(base) and target != base
    else:
        base = (root / 'artifacts/akt').resolve()
        valid = ((target.is_relative_to(base) and target != base)
                 or (target.parent == root and target.name.startswith('requirements-akt')
                     and target.name.endswith('.txt')))
    if not valid:
        raise ValueError(f'invalid {role} reference')
    return text


def _bounded_caps(overrides: dict | None) -> dict:
    overrides = {} if overrides is None else overrides
    if not isinstance(overrides, dict) or set(overrides) - set(CAPS):
        raise ValueError('unknown preparation cap')
    result = dict(CAPS)
    for name, value in overrides.items():
        numeric = name in {'max_seconds', 'max_wall_seconds'}
        valid_type = type(value) in (int, float) if numeric else type(value) is int
        if not valid_type or not 0 < value <= CAPS[name] or not math.isfinite(value):
            raise ValueError(f'invalid or increased preparation cap: {name}')
        result[name] = value
    if result['max_targets_per_side'] < max(result['max_train_users'], result['max_val_users']):
        raise ValueError('target cap must allow at least one target per selected learner')
    # Each dummy learner has one window; the fixed split has six train learners.
    if result['max_steps'] < math.ceil(min(6, result['max_train_users']) / 4):
        raise ValueError('step cap cannot complete the selected dummy train windows')
    result['max_total_targets'] = 2 * result['max_targets_per_side']
    return result


def _cuda_limits(mode: str, limits: dict | None) -> dict | None:
    if mode not in {'smoke', 'cuda-smoke'}:
        raise ValueError('only smoke/cuda-smoke preparation is available')
    if mode == 'smoke':
        if limits is not None:
            raise ValueError('CPU preparation cannot declare CUDA limits')
        return None
    if (not isinstance(limits, dict) or set(limits) != {'max_vram_bytes', 'visible_devices'}
            or type(limits['max_vram_bytes']) is not int
            or not 64 * 1024**2 <= limits['max_vram_bytes'] <= 2 * GIB
            or type(limits['visible_devices']) is not int or limits['visible_devices'] != 1):
        raise ValueError('cuda-smoke preparation requires explicit bounded CUDA limits')
    return dict(limits)


def prepare_synthetic_context(dataset_id: str, *, runtime_report: str, lock_file: str,
                              gate2_report: str, mode: str = 'smoke', caps: dict | None = None,
                              cuda_limits: dict | None = None,
                              project_root: Path = PROJECT_ROOT) -> dict:
    """Tạo mới exclusive; project_root chỉ phục vụ API fixture, CLI dùng trusted ROOT.

    Không đọc runtime/lock/Gate2, không tạo authorization, không import Torch/backend.
    Lỗi sau reserve giữ nguyên input dở dang để truy vết; không tự xóa hay ghi đè.
    """
    root = Path(project_root).resolve()
    if root != PROJECT_ROOT.resolve():
        raise ValueError('project root must be the trusted repository root')
    if not isinstance(dataset_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', dataset_id):
        raise ValueError('invalid dataset_id')
    references = {name: _reference(root, value, name) for name, value in (
        ('runtime_report', runtime_report), ('lock_file', lock_file), ('gate2_report', gate2_report))}
    bounds, limits = _bounded_caps(caps), _cuda_limits(mode, cuda_limits)
    base = root / 'artifacts/akt/synthetic'
    for ancestor in (root / 'artifacts', root / 'artifacts/akt', base):
        if ancestor.resolve() != ancestor or ancestor.is_symlink():
            raise ValueError('synthetic destination cannot traverse a link')
    destination = base / dataset_id
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('synthetic dataset_id already exists; choose a new ID')
    output = root / 'experiments/akt/results' / dataset_id
    if output.exists():
        raise FileExistsError('worker output run_id already exists; choose a new ID')
    config = AKTConfig(project_root=root, output_dir=output, source_root=root / 'artifacts/akt/dependencies/upstream',
                       phase=mode, run_id=dataset_id, execution_enabled=False,
                       device='cpu' if mode == 'smoke' else 'cuda', seed=42,
                       d_model=32, heads=4, blocks=1, d_ff=64, final_fc=32, dropout=0.0,
                       batch_size=4, max_epochs=1, min_available_ram_bytes=GIB, **bounds)
    validate_config(config)
    # Snapshot code identity before file generation; no claims about absent reports.
    sources = {name: _sha(ROOT / name) for name in SOURCE_FILES}
    import duckdb  # Local CPU serialization only; no provisioning or model imports.

    destination.mkdir(parents=True, exist_ok=False)
    canonical = destination / 'canonical'
    canonical.mkdir()
    events_path, assignments_path = canonical / 'events.parquet', destination / 'assignments.parquet'
    rng = random.Random(42)
    learners = [f'dummy-{index:02d}' for index in range(8)]
    assignments = [(user, 0 if index == 0 else 1 + (index - 1) % 4, 'development')
                   for index, user in enumerate(learners)]
    events = []
    for index, user in enumerate(learners):
        for position in range(8):
            row = index * 8 + position + 1
            events.append((user, 'A' if position % 2 == 0 else 'B', 1700000000 + row,
                           row, rng.randrange(2), int(position % 3 == 0)))
    with duckdb.connect(config={'memory_limit': '128MB', 'threads': '1', 'temp_directory': ''}) as con:
        con.execute('CREATE TABLE events(user_id VARCHAR, exercise VARCHAR, time_done BIGINT, '
                    'source_row BIGINT, correct INTEGER, suggested INTEGER)')
        con.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)', events)
        con.execute('CREATE TABLE assignments(user_id VARCHAR, fold INTEGER, partition VARCHAR)')
        con.executemany('INSERT INTO assignments VALUES (?, ?, ?)', assignments)
        for table, path in (('events', events_path), ('assignments', assignments_path)):
            con.execute(f'COPY {table} TO ? (FORMAT PARQUET, COMPRESSION UNCOMPRESSED)', [str(path)])
        actual_events = con.execute('SELECT * FROM read_parquet(?) ORDER BY source_row', [str(events_path)]).fetchall()
        actual_assignments = con.execute('SELECT * FROM read_parquet(?) ORDER BY user_id', [str(assignments_path)]).fetchall()
        if actual_events != events or actual_assignments != assignments:
            raise ValueError('synthetic Parquet readback differs from generated rows')
    marker = {'schema_version': 1, 'synthetic_only': True, 'real_data_authorized': False,
              'scope': SCOPE, 'seed': 42, 'data_origin': 'local-dummy-generator',
              'model_metadata': 'FIXTURE; không phải corpus Grade10 hay Junyi',
              'label_semantics': 'dummy PRNG bits; không phải RQ simulator truth hay bằng chứng học tập',
              'execution_enabled': False}
    _write_json(destination / 'SYNTHETIC_ONLY.json', marker)
    _write_json(destination / 'canonical_manifest.json', {
        'schema_version': 1, 'manifest_kind': 'synthetic-fixture-canonical', 'scope': SCOPE,
        'seed': 42, 'row_count': 64, 'learner_count': 8, 'events_per_learner': 8,
        'exercises': ['A', 'B'], 'ordering': ['user_id', 'time_done', 'source_row'],
        'unique_time_done': True, 'unique_source_row': True, 'source_row_range': [1, 64],
        'columns': ['user_id', 'exercise', 'time_done', 'source_row', 'correct', 'suggested'],
        'label_semantics': marker['label_semantics'], 'parquet_sha256': _sha(events_path)})
    _write_json(destination / 'split_manifest.json', {
        'schema_version': 1, 'manifest_kind': 'synthetic-fixture-development-assignments', 'scope': SCOPE,
        'partition_counts': {'development': 8}, 'fold_counts': dict(sorted(Counter(str(a[1]) for a in assignments).items())),
        'outer_fold': 0, 'outer_fold_sentinel_user': learners[0], 'outer_fold_sentinel_events': 8,
        'outer_train_learners': 7, 'outer_train_events': 56,
        'split_rule': 'existing akt-inner-v1; seed42; inner_val_fraction0.1; learner-disjoint',
        'sentinel_semantics': 'dummy outer-fold exclusion sentinel; không phải Holdout Test',
        'assignments_sha256': _sha(assignments_path)})
    relative = lambda path: path.relative_to(root).as_posix()
    data_files = [events_path, assignments_path, destination / 'canonical_manifest.json',
                  destination / 'split_manifest.json', destination / 'SYNTHETIC_ONLY.json']
    context_payload = {'schema_version': 1, 'scope': SCOPE, **references,
                       'dataset_root': relative(destination), 'canonical': relative(canonical),
                       'assignments': relative(assignments_path),
                       'canonical_manifest': relative(destination / 'canonical_manifest.json'),
                       'split_manifest': relative(destination / 'split_manifest.json'),
                       'input_hashes': {relative(path): _sha(path) for path in sorted(data_files)}}
    if limits is not None:
        context_payload['cuda_limits'] = limits
    context_path, config_path = destination / 'worker-context.json', destination / 'config.json'
    _write_json(context_path, context_payload)
    config_payload = asdict(config)
    for key in ('project_root', 'output_dir', 'source_root'):
        path = config_payload[key]
        config_payload[key] = '.' if path == root else relative(path)
    _write_json(config_path, config_payload)
    context = load_worker_context(context_path, expected_sha256=_sha(context_path), project_root=root)
    context.validate_for(config)
    if sources != {name: _sha(ROOT / name) for name in SOURCE_FILES}:
        raise ValueError('source contract changed during preparation; preserve this attempt')
    inventory = {'schema_version': 1, 'status': 'prepared-only', 'scope': SCOPE,
                 'execution_enabled': False, 'dataset_root': relative(destination),
                 'config_file': relative(config_path), 'context_file': relative(context_path),
                 'context_sha256': context.manifest_sha256, 'source_sha256': sources,
                 'duckdb_version': duckdb.__version__, 'generated_rows': 64, 'generated_learners': 8,
                 'readback_rows_equal': True, 'readback_assignments_equal': True,
                 'runtime_gate2_lock_contents_checked': False, 'optimizer_steps': 0,
                 'outputs_sha256': {relative(path): _sha(path) for path in sorted(data_files + [config_path, context_path])},
                 'limitations': ['Input dummy chỉ kiểm kỹ thuật; không là benchmark hay RQ evidence.',
                                 'Không kiểm runtime/Gate2/lock, không cấp quyền hoặc chạy worker.',
                                 'CUDA mode chỉ là đặc tả; chưa kiểm GPU/VRAM/throughput.']}
    _write_json(destination / 'preparation-inventory.json', inventory)
    return inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-id', required=True)
    for name in ('runtime-report', 'lock-file', 'gate2-report'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--mode', choices=('smoke', 'cuda-smoke'), default='smoke')
    parser.add_argument('--cuda-max-vram-bytes', type=int)
    parser.add_argument('--cuda-visible-devices', type=int)
    for name in CAPS:
        parser.add_argument('--' + name.replace('_', '-'), type=float if name in {'max_seconds', 'max_wall_seconds'} else int)
    args = parser.parse_args(argv)
    caps = {name: getattr(args, name) for name in CAPS if getattr(args, name) is not None}
    limits = None
    if args.cuda_max_vram_bytes is not None or args.cuda_visible_devices is not None:
        limits = {'max_vram_bytes': args.cuda_max_vram_bytes, 'visible_devices': args.cuda_visible_devices}
    result = prepare_synthetic_context(args.dataset_id, runtime_report=args.runtime_report,
        lock_file=args.lock_file, gate2_report=args.gate2_report, mode=args.mode, caps=caps,
        cuda_limits=limits, project_root=PROJECT_ROOT)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
