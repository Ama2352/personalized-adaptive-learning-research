"""Authorization and preflight checks shared by the light watchdog and AKT worker."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Callable

from .config import AKTConfig, PROJECT_ROOT, validate_config
from .provenance import sha256_file, verify_upstream


ASSIGNMENTS = PROJECT_ROOT / 'artifacts/bkt_baseline/splits/assignments.parquet'
SPLIT_MANIFEST = PROJECT_ROOT / 'artifacts/bkt_baseline/splits/manifest.json'
CANONICAL_MANIFEST = PROJECT_ROOT / 'artifacts/bkt_baseline/derived/manifest.json'
RUNTIME_REPORT = PROJECT_ROOT / 'artifacts/akt/preflight/runtime-v2.json'
LOCK_FILE = PROJECT_ROOT / 'requirements-akt.lock.txt'
GATE2_CURRENT = PROJECT_ROOT / 'artifacts/akt/preflight/gate2-current.json'


def gate2_build_hashes(project_root: Path = PROJECT_ROOT) -> dict:
    paths = list((project_root / 'src/knowledge_tracing/akt').glob('*.py'))
    paths += list((project_root / 'tests/akt').glob('*.py'))
    paths += list((project_root / 'tests/shared_kt').glob('*.py'))
    paths += [project_root / 'src/knowledge_tracing/shared_kt.py',
              project_root / 'src/knowledge_tracing/paired_bootstrap.py',
              project_root / 'src/knowledge_tracing/gam_kt/evaluation.py']
    paths += list((project_root / 'src/knowledge_tracing').glob('*.py'))
    paths += list((project_root / 'scripts/research').glob('*.py'))
    paths += list((project_root / 'scripts/akt').glob('*.py'))
    paper = project_root / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
    paths += [path for path in (paper / 'data/simulator_inputs').glob('*.csv')]
    paths += [path for path in (paper / 'source').glob('*.ipynb') if path.name in {
        'adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb',
        'junyi_cycle_corrected_ablation_confirmation.ipynb'}]
    paths += list((project_root / 'paper1').glob('*.ipynb'))
    return {path.relative_to(project_root).as_posix(): sha256_file(path)
            for path in sorted(set(paths))}


def require_gate2_evidence(config: AKTConfig, *, project_root: Path = PROJECT_ROOT,
                           gate2_report: Path = GATE2_CURRENT,
                           lock_file: Path = LOCK_FILE,
                           build_hashes_fn: Callable[[], dict] | None = None) -> dict:
    if build_hashes_fn is None:
        build_hashes_fn = lambda: gate2_build_hashes(project_root)
    try:
        pointer = json.loads(gate2_report.read_text(encoding='utf-8'))
        if pointer.get('schema_version') != 1:
            raise ValueError('unsupported Gate 2 pointer schema')
        evidence_name = pointer.get('evidence_file')
        log_name = pointer.get('test_log_file')
        if (not isinstance(evidence_name, str) or Path(evidence_name).name != evidence_name
                or not evidence_name.startswith('gate2-') or not evidence_name.endswith('.json')
                or not isinstance(log_name, str) or Path(log_name).name != log_name
                or not log_name.startswith('gate2-tests-') or not log_name.endswith('.log')):
            raise ValueError('invalid Gate 2 evidence pointer paths')
        evidence_path = gate2_report.parent / evidence_name
        log_path = gate2_report.parent / log_name
        report_sha256 = sha256_file(evidence_path)
        log_sha256 = sha256_file(log_path)
        if (pointer.get('evidence_sha256') != report_sha256
                or pointer.get('test_log_sha256') != log_sha256):
            raise ValueError('Gate 2 evidence pointer digest mismatch')
        evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
        test_result = evidence.get('test_result')
        test_counts_valid = (
            isinstance(test_result, dict)
            and isinstance(test_result.get('passed'), int)
            and not isinstance(test_result.get('passed'), bool)
            and test_result['passed'] > 0
            and all(test_result.get(key) == 0 for key in ('failed', 'errors', 'skipped'))
        )
        if (evidence.get('status') != 'PASS' or evidence.get('source_commit') != config.source_commit
                or evidence.get('lock_sha256') != sha256_file(lock_file)
                or evidence.get('build_hashes') != build_hashes_fn()
                or evidence.get('test_log_sha256') != log_sha256
                or evidence.get('schema_version') != 1
                or evidence.get('suite') != 'tests/akt tests/shared_kt'
                or not test_counts_valid):
            raise ValueError('Gate 2 evidence is stale or mismatched')
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError('Gate 2 evidence is missing or invalid') from exc
    return {'status': 'PASS', 'report_sha256': report_sha256,
            'test_log_sha256': log_sha256,
            'pointer_sha256': sha256_file(gate2_report),
            'evidence_path': str(evidence_path), 'test_log_path': str(log_path)}


def preflight(config: AKTConfig, *, project_root: Path = PROJECT_ROOT,
              runtime_report_path: Path = RUNTIME_REPORT, lock_file: Path = LOCK_FILE) -> dict:
    """Verify pinned source/runtime/lock; never opens learner assignments or interactions."""
    validate_config(config)
    source = verify_upstream(config.source_root, config.source_commit)
    lock_hash = sha256_file(lock_file)
    report = json.loads(runtime_report_path.read_text(encoding='utf-8'))
    if (report.get('source') != source or report.get('lock_sha256') != lock_hash
            or report.get('python') != str((project_root / '.venv/Scripts/python.exe').resolve())
            or Path(sys.prefix).resolve() != (project_root / '.venv').resolve()):
        raise ValueError('Gate 1 runtime/source evidence mismatch')
    return {
        'status': 'ready', 'phase': config.phase, 'source': source,
        'lock_sha256': lock_hash, 'runtime_report_sha256': sha256_file(runtime_report_path),
        'runtime': report,
    }


def config_hash(config: AKTConfig) -> str:
    return hashlib.sha256(json.dumps(asdict(config), sort_keys=True, default=str).encode()).hexdigest()


def identity(config: AKTConfig, preflight_result: dict, *, project_root: Path = PROJECT_ROOT,
             canonical_manifest: Path = CANONICAL_MANIFEST, assignments: Path = ASSIGNMENTS,
             split_manifest: Path = SPLIT_MANIFEST) -> dict:
    return {
        'protocol': config.protocol_version,
        'config_sha256': config_hash(config),
        'source': preflight_result['source'],
        'lock_sha256': preflight_result['lock_sha256'],
        'runtime_report_sha256': preflight_result['runtime_report_sha256'],
        'canonical_manifest_sha256': sha256_file(canonical_manifest),
        'assignments_sha256': sha256_file(assignments),
        'split_manifest_sha256': sha256_file(split_manifest),
    }


def authorization_identity(config: AKTConfig, *,
                           preflight_fn: Callable[[AKTConfig], dict] | None = None,
                           identity_fn: Callable[[AKTConfig, dict], dict] | None = None,
                           build_hashes_fn: Callable[[], dict] | None = None,
                           gate2_report: Path = GATE2_CURRENT,
                           project_root: Path = PROJECT_ROOT,
                           lock_file: Path = LOCK_FILE) -> dict:
    preflight_fn = preflight_fn or preflight
    identity_fn = identity_fn or identity
    build_hashes_fn = build_hashes_fn or gate2_build_hashes
    gate2 = require_gate2_evidence(config, project_root=project_root,
                                   gate2_report=gate2_report, lock_file=lock_file,
                                   build_hashes_fn=build_hashes_fn)
    result = identity_fn(config, preflight_fn(config))
    return {**result, 'build_hashes': build_hashes_fn(),
            'gate2_report_sha256': gate2['report_sha256'],
            'gate2_test_log_sha256': gate2['test_log_sha256'],
            'gate2_pointer_sha256': gate2['pointer_sha256']}


def require_authorization(config: AKTConfig, authorization: dict | None, *,
                          identity_fn: Callable[[AKTConfig], dict] = authorization_identity) -> dict:
    if not config.execution_enabled or not isinstance(authorization, dict):
        raise PermissionError('explicit phase authorization is required')
    if (authorization.get('approved') is not True
            or authorization.get('scope') != 'development-inner-only'
            or authorization.get('phase') != config.phase
            or authorization.get('run_id') != config.run_id
            or authorization.get('source_commit') != config.source_commit
            or authorization.get('config_sha256') != config_hash(config)
            or not isinstance(authorization.get('approval_reference'), str)
            or not authorization['approval_reference'].strip()):
        raise PermissionError('authorization does not match this AKT run')
    if authorization.get('identity') != identity_fn(config):
        raise PermissionError('authorization identity does not match current source and data inputs')
    caps = {'max_train_users': config.max_train_users, 'max_val_users': config.max_val_users,
            'max_targets_per_side': config.max_targets_per_side, 'max_total_targets': config.max_total_targets,
            'max_steps': config.max_steps, 'max_seconds': config.max_seconds,
            'max_wall_seconds': config.max_wall_seconds, 'max_rss_bytes': config.max_rss_bytes,
            'min_available_ram_bytes': config.min_available_ram_bytes}
    required_caps = ({'max_train_users', 'max_val_users', 'max_targets_per_side', 'max_steps',
                     'max_seconds', 'max_wall_seconds', 'max_rss_bytes', 'min_available_ram_bytes'}
                    if config.phase == 'smoke' else
                    {'max_train_users', 'max_val_users', 'max_total_targets', 'max_seconds',
                     'max_wall_seconds', 'max_rss_bytes', 'min_available_ram_bytes'})
    requested = authorization.get('caps')
    if not isinstance(requested, dict) or set(requested) != required_caps:
        raise PermissionError('authorization must enumerate every phase cap exactly')
    for name, value in requested.items():
        integer_cap = name not in {'max_seconds', 'max_wall_seconds'}
        if (name not in caps or caps[name] is None or isinstance(value, bool)
                or (integer_cap and not isinstance(value, int))
                or not isinstance(value, (int, float)) or not math.isfinite(value)
                or value <= 0 or (name == 'min_available_ram_bytes' and value < caps[name])
                or (name != 'min_available_ram_bytes' and value > caps[name])):
            raise PermissionError(f'authorization exceeds or changes configured cap: {name}')
    if authorization.get('gate_pass') or authorization.get('status') == 'PASS':
        raise PermissionError('gate evidence cannot grant execution authorization')
    return authorization
