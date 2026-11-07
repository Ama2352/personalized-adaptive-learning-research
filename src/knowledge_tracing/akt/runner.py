"""Bộ điều phối AKT có cổng quyền chạy và ngân sách cố định."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import argparse
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import sys
import time
from typing import Any
import uuid

import duckdb
import pandas as pd
import torch

from knowledge_tracing.shared_kt import StableVocabulary
from . import authorization as authorization_module
from .checkpoint import load_checkpoint, restore_checkpoint, save_checkpoint
from .config import AKTConfig, DataPaths, PROJECT_ROOT, SOURCE_COMMIT, load_config, validate_config
from .data import iter_development_learners, read_development_assignments
from .encoding import ExerciseEncoding, fit_vocabulary
from .evaluation import score_akt_shards
from .model import AKTAdapter
from .prediction import export_predictions, iter_predictions, order_prediction_learners
from .provenance import sha256_file
from .resources import memory_snapshot
from .splits import InnerSplit, make_inner_split
from .training import _check_resource_budget, _encoding_hash, refit_outer_train, select_checkpoint
from .types import LearnerEvents
from .watchdog import _emit_memory_event


ASSIGNMENTS = PROJECT_ROOT / 'artifacts/bkt_baseline/splits/assignments.parquet'
SPLIT_MANIFEST = PROJECT_ROOT / 'artifacts/bkt_baseline/splits/manifest.json'
CANONICAL = PROJECT_ROOT / 'artifacts/bkt_baseline/derived/canonical'
CANONICAL_MANIFEST = PROJECT_ROOT / 'artifacts/bkt_baseline/derived/manifest.json'
RUNTIME_REPORT = PROJECT_ROOT / 'artifacts/akt/preflight/runtime-v2.json'
LOCK_FILE = PROJECT_ROOT / 'requirements-akt.lock.txt'
GATE2_REPORT = PROJECT_ROOT / 'artifacts/akt/preflight/gate2-current.json'
_JSON_REPLACE_RETRY_DELAYS = (0.05, 0.1, 0.2, 0.4)
_WINDOWS_TRANSIENT_REPLACE_ERRORS = {5, 32, 33}
_LOGGER = logging.getLogger(__name__)


def _gate2_build_hashes() -> dict:
    return authorization_module.gate2_build_hashes(PROJECT_ROOT)


def _require_gate2_evidence(config: AKTConfig) -> dict:
    return authorization_module.require_gate2_evidence(
        config, project_root=PROJECT_ROOT, gate2_report=GATE2_REPORT,
        lock_file=LOCK_FILE, build_hashes_fn=_gate2_build_hashes)


@dataclass(frozen=True)
class RunResult:
    phase: str
    run_id: str
    status: str
    output_dir: Path
    summary: dict


def preflight(config: AKTConfig) -> dict:
    """Read only source, lock and Gate 1 evidence; never opens the dataset."""
    return authorization_module.preflight(config, project_root=PROJECT_ROOT,
                                          runtime_report_path=RUNTIME_REPORT, lock_file=LOCK_FILE)


def _config_hash(config: AKTConfig) -> str:
    return authorization_module.config_hash(config)


def _require_authorization(config: AKTConfig, authorization: dict | None) -> dict:
    return authorization_module.require_authorization(
        config, authorization, identity_fn=_authorization_identity)


def _select_inner_cohort(assignments: pd.DataFrame, *, outer_fold: int, seed: int, phase: str,
                         max_train_users: int, max_val_users: int) -> tuple[tuple[str, ...], tuple[str, ...], InnerSplit]:
    split = make_inner_split(assignments, outer_fold=outer_fold, seed=seed)
    tag = 'akt-smoke-v1' if phase == 'smoke' else 'akt-pilot-v1'

    def sample(users: tuple[str, ...], maximum: int) -> tuple[str, ...]:
        ranked = sorted(users, key=lambda user: (
            hashlib.sha256(f'{tag}|{seed}|{outer_fold}|{user}'.encode()).hexdigest(), user))
        return tuple(ranked[:maximum])

    train = sample(split.inner_train_users, max_train_users)
    val = sample(split.inner_val_users, max_val_users)
    if not train or not val or set(train) & set(val):
        raise ValueError('bounded inner cohort is empty or overlapping')
    payload = json.dumps({'parent': split.split_hash, 'phase': phase, 'train': train, 'val': val},
                         sort_keys=True, separators=(',', ':')).encode()
    subset = InnerSplit(train, val, outer_fold, hashlib.sha256(payload).hexdigest())
    return train, val, subset


def _data_paths() -> DataPaths:
    return DataPaths(CANONICAL, ASSIGNMENTS, CANONICAL_MANIFEST, SPLIT_MANIFEST)


def _capped_learners(config: AKTConfig, users: tuple[str, ...], *, target_cap: int,
                     phase_dir: Path, stats: dict | None = None) -> tuple[LearnerEvents, ...]:
    if not users or target_cap < len(users):
        raise ValueError('target cap cannot provide one chronological target per selected learner')
    output = []
    remaining = target_cap
    allowed_folds = tuple(fold for fold in range(5) if fold != config.outer_fold)
    paths = _data_paths()
    for learner in iter_development_learners(
            paths, user_ids=users, allowed_folds=allowed_folds, fetch_rows=config.fetch_rows,
            temp_dir=phase_dir / 'duckdb-tmp', preserve_user_order=True, stats=stats):
        if remaining <= 0:
            break
        events = learner.events[:remaining]
        if events:
            output.append(LearnerEvents(learner.user_id, learner.fold, tuple(events)))
            remaining -= len(events)
    if not output:
        raise ValueError('bounded cohort has no Development targets')
    result = tuple(output)
    if stats is not None:
        stats['selected_learners'] = len(result)
        stats['selected_targets'] = sum(len(learner.events) for learner in result)
    return result


def _identity(config: AKTConfig, preflight_result: dict) -> dict:
    return {
        'protocol': config.protocol_version,
        'config_sha256': _config_hash(config),
        'source': preflight_result['source'], 'lock_sha256': preflight_result['lock_sha256'],
        'runtime_report_sha256': preflight_result['runtime_report_sha256'],
        'canonical_manifest_sha256': sha256_file(CANONICAL_MANIFEST),
        'assignments_sha256': sha256_file(ASSIGNMENTS),
        'split_manifest_sha256': sha256_file(SPLIT_MANIFEST),
    }


def _authorization_identity(config: AKTConfig) -> dict:
    """Bind approval to current source, runtime, split and frozen data manifests."""
    identity = _identity(config, preflight(config))
    gate2 = _require_gate2_evidence(config)
    identity.update({'build_hashes': _gate2_build_hashes(),
                     'gate2_report_sha256': gate2['report_sha256'],
                     'gate2_test_log_sha256': gate2['test_log_sha256'],
                     'gate2_pointer_sha256': gate2['pointer_sha256']})
    return identity


def _checkpoint_state_matches(adapter: AKTAdapter, payload: dict) -> bool:
    current = adapter.native.state_dict()
    saved = payload.get('model_state_dict')
    return (isinstance(saved, dict) and set(current) == set(saved)
            and all(torch.equal(current[name].detach().cpu(), saved[name].detach().cpu())
                    for name in current))


def _write_json(path: Path, payload: dict) -> None:
    temp = path.with_name(f'{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp')
    try:
        with temp.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(payload, stream, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        for attempt, delay in enumerate((*_JSON_REPLACE_RETRY_DELAYS, None), start=1):
            try:
                os.replace(temp, path)
                break
            except PermissionError as exc:
                winerror = getattr(exc, 'winerror', None)
                if (os.name != 'nt' or winerror not in _WINDOWS_TRANSIENT_REPLACE_ERRORS
                        or delay is None):
                    raise
                _LOGGER.warning(
                    'Transient Windows JSON replace denial: path=%s winerror=%s attempt=%d/%d; retrying',
                    path, winerror, attempt, len(_JSON_REPLACE_RETRY_DELAYS) + 1)
                time.sleep(delay)
    except BaseException:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            _LOGGER.exception('Could not remove failed atomic JSON temporary file: %s', temp)
        raise


def _load_phase_inputs(config: AKTConfig, *, output_reserved: bool = False
                       ) -> tuple[dict, InnerSplit, tuple[LearnerEvents, ...], tuple[LearnerEvents, ...], dict]:
    loading_started = time.perf_counter()
    preflight_result = preflight(config)
    assignments_started = time.perf_counter()
    assignments = read_development_assignments(_data_paths())
    assignments_seconds = time.perf_counter() - assignments_started
    train_users, val_users, split = _select_inner_cohort(
        assignments, outer_fold=config.outer_fold, seed=config.seed, phase=config.phase,
        max_train_users=config.max_train_users or 0, max_val_users=config.max_val_users or 0)
    output = config.output_dir.resolve()
    if output_reserved:
        if not output.is_dir():
            raise FileNotFoundError('reserved pilot output directory is missing')
    elif output.exists():
        raise FileExistsError('AKT run_id already exists; choose a new run_id')
    phase_dir = (PROJECT_ROOT / 'artifacts/akt/tmp' / config.run_id).resolve()
    phase_dir.mkdir(parents=True, exist_ok=False)
    if config.phase == 'smoke':
        train_cap = config.max_targets_per_side
        val_cap = config.max_targets_per_side
    else:
        train_cap = config.max_total_targets // 2
        val_cap = config.max_total_targets - train_cap
    loading_stats = {'train': {}, 'validation': {}}
    train_started = time.perf_counter()
    train_data = _capped_learners(config, train_users, target_cap=train_cap, phase_dir=phase_dir / 'train',
                                  stats=loading_stats['train'])
    train_loading_seconds = time.perf_counter() - train_started
    validation_started = time.perf_counter()
    val_data = _capped_learners(config, val_users, target_cap=val_cap, phase_dir=phase_dir / 'validation',
                                stats=loading_stats['validation'])
    validation_loading_seconds = time.perf_counter() - validation_started
    active_train = tuple(learner.user_id for learner in train_data)
    active_val = tuple(learner.user_id for learner in val_data)
    if len(active_train) < 1 or len(active_val) < 1 or set(active_train) & set(active_val):
        raise ValueError('bounded learner cohorts are invalid')
    subset_payload = json.dumps({'original': split.split_hash, 'train': active_train, 'val': active_val},
                                sort_keys=True, separators=(',', ':')).encode()
    split = InnerSplit(active_train, active_val, config.outer_fold, hashlib.sha256(subset_payload).hexdigest())
    identity = _identity(config, preflight_result)
    identity['loader_highwater'] = loading_stats
    observations = {
        'selected_train_learners': len(train_users),
        'selected_validation_learners': len(val_users),
        'loaded_train_learners': len(train_data),
        'loaded_validation_learners': len(val_data),
        'selected_train_targets': sum(len(user.events) for user in train_data),
        'selected_validation_targets': sum(len(user.events) for user in val_data),
        'assignments_and_cohort_selection_seconds': assignments_seconds,
        'train_data_loading_seconds': train_loading_seconds,
        'validation_data_loading_seconds': validation_loading_seconds,
        'data_loading_seconds': time.perf_counter() - loading_started,
        'chronological_query_sort_and_materialize_seconds': sum(
            float(item.get('chronological_query_sort_and_materialize_seconds', 0.0))
            for item in loading_stats.values()),
        'loader_highwater': loading_stats,
    }
    return identity, split, train_data, val_data, observations


def _mark_manifest(config: AKTConfig, identity: dict, status: str, **extra) -> None:
    path = config.output_dir / 'manifest.json'
    payload = {'schema_version': 1, 'phase': config.phase, 'run_id': config.run_id,
               'status': status, 'identity': identity, **extra}
    _write_json(path, payload)


def _prediction_distribution(prediction_dir: Path) -> dict:
    with duckdb.connect(config={'memory_limit': '512MB', 'threads': '2'}) as con:
        row = con.execute(
            "SELECT count(*), min(CAST(prediction AS DOUBLE)), max(CAST(prediction AS DOUBLE)), "
            "stddev_pop(CAST(prediction AS DOUBLE)), count(DISTINCT prediction) "
            "FROM read_parquet(?) WHERE prediction_kind='fitted'",
            [str(prediction_dir / 'part-*.parquet')],
        ).fetchone()
    return {'fitted_count': int(row[0]), 'minimum': row[1], 'maximum': row[2],
            'standard_deviation': row[3], 'distinct_values': int(row[4])}


def _resource_summary(samples: list[dict]) -> dict:
    if not samples:
        return {'samples': [], 'sample_count': 0, 'current_rss_bytes': None,
                'peak_rss_bytes': None, 'minimum_available_ram_bytes': None}
    return {
        'samples': samples,
        'sample_count': len(samples),
        'current_rss_bytes': samples[-1].get('process_rss_bytes'),
        'peak_rss_bytes': max(
            max(int(sample.get('process_rss_bytes') or 0),
                int(sample.get('process_peak_rss_bytes') or 0)) for sample in samples),
        'minimum_available_ram_bytes': min(
            int(sample['system_available_ram_bytes']) for sample in samples),
    }


def _run_phase(config: AKTConfig, authorization: dict | None, *, pilot: bool,
               invocation: dict | None = None) -> RunResult:
    validate_config(config)
    approved = _require_authorization(config, authorization)
    caps = approved['caps']
    # The approved limits may be stricter than the template. Use them for
    # cohort selection and loading as well as the optimizer/watchdog.
    config = replace(config, **caps)
    validate_config(config)
    expected_phase = 'pilot' if pilot else 'smoke'
    if config.phase != expected_phase:
        raise ValueError(f'{expected_phase} runner requires phase={expected_phase}')
    gate2 = _require_gate2_evidence(config)
    _emit_memory_event('worker-before-data-load', config.phase, config.run_id,
                       max_rss_bytes=caps['max_rss_bytes'],
                       min_available_ram_bytes=caps['min_available_ram_bytes'])
    _check_resource_budget({'max_rss_bytes': caps['max_rss_bytes'],
                            'min_available_ram_bytes': caps['min_available_ram_bytes'],
                            'phase': config.phase, 'run_id': config.run_id})
    started = time.perf_counter()
    audit = {'invocation': invocation or {'kind': 'python-api', 'phase': expected_phase},
             'authorization_reference': approved['approval_reference'],
             'authorized_config_sha256': approved.get('config_sha256'), 'approved_caps': caps,
             'attempt': 1, 'retry_history': [],
             'gate_records': {'gate1': {'status': 'verified'}, 'gate2': gate2}}
    identity: dict = approved.get('identity', {})
    resource_samples: list[dict] = []
    latest_progress: dict | None = None

    def record_resource(snapshot: dict | None = None, *, phase: str) -> None:
        sample = dict(snapshot or memory_snapshot())
        sample['phase'] = phase
        resource_samples.append(sample)

    if pilot:
        config.output_dir.mkdir(parents=True, exist_ok=False)
        _mark_manifest(config, identity, 'incomplete', started_at=time.time(),
                       stop_reason='run_in_progress', requested_outer_users=False, **audit)
    try:
        _emit_memory_event('worker-before-data-load', config.phase, config.run_id,
                           max_rss_bytes=caps['max_rss_bytes'],
                           min_available_ram_bytes=caps['min_available_ram_bytes'])
        record_resource(phase='before_data_load')
        loaded = (_load_phase_inputs(config, output_reserved=True) if pilot
                  else _load_phase_inputs(config))
        identity, split, train_data, val_data = loaded[:4]
        load_observations = loaded[4] if len(loaded) > 4 else {
            'selected_train_learners': len(train_data),
            'selected_validation_learners': len(val_data),
            'loaded_train_learners': len(train_data),
            'loaded_validation_learners': len(val_data),
            'selected_train_targets': sum(len(user.events) for user in train_data),
            'selected_validation_targets': sum(len(user.events) for user in val_data),
        }
        record_resource(phase='after_data_load')
        if not pilot:
            config.output_dir.mkdir(parents=True, exist_ok=False)
        cohort = {'train_users': len(train_data), 'validation_users': len(val_data),
                  'train_targets_selected': sum(len(user.events) for user in train_data),
                  'validation_targets_selected': sum(len(user.events) for user in val_data),
                  'train_user_hashes': [hashlib.sha256(user.user_id.encode()).hexdigest() for user in train_data],
                  'validation_user_hashes': [hashlib.sha256(user.user_id.encode()).hexdigest() for user in val_data],
                  **load_observations}
        audit['gate_records']['gate1']['runtime_report_sha256'] = identity['runtime_report_sha256']
        _mark_manifest(config, identity, 'incomplete', started_at=time.time(), cohort=cohort,
                       requested_outer_users=False, **audit)

        def record_training_progress(progress: dict) -> None:
            nonlocal latest_progress
            latest_progress = progress
            record_resource(phase='training_progress')
            if pilot:
                _write_json(config.output_dir / 'pilot-progress.json', {
                    'status': 'incomplete', 'phase': 'pilot', 'run_id': config.run_id,
                    'complete_epoch': progress['complete_epoch'],
                    'stop_reason': progress['stop_reason'],
                    'progress': progress,
                    'worker_resources': _resource_summary(resource_samples),
                })

        selection = select_checkpoint(
            config, inner_split=split, train_learners_factory=lambda: iter(train_data),
            val_learners_factory=lambda: iter(val_data), identity=identity,
            budget={'max_steps': caps.get('max_steps'), 'max_seconds': caps.get('max_seconds'),
                    'max_targets': caps.get('max_targets_per_side') or caps.get('max_total_targets'),
                    'max_rss_bytes': caps.get('max_rss_bytes'),
                    'min_available_ram_bytes': caps.get('min_available_ram_bytes'),
                    'phase': config.phase, 'run_id': config.run_id},
            **({'progress_callback': record_training_progress,
                'resource_callback': lambda snapshot: record_resource(snapshot, phase='resource_guard')}
               if pilot else {}))
        record_resource(phase='after_selection_and_validation')
        if time.perf_counter() - started > caps['max_wall_seconds']:
            raise TimeoutError('phase wall-clock cap exceeded')
        if pilot and selection.status == 'bounded':
            training = selection.history[-1]['training'] if selection.history else latest_progress
            summary = {
                'complete_epoch': False,
                'stop_reason': selection.stop_reason,
                'selected_epoch': selection.selected_epoch,
                'cohort': load_observations,
                'training': training,
                'validation': None,
                'checkpoint_reload_state_exact': None,
                'prediction_export': None,
                'elapsed_seconds': time.perf_counter() - started,
                'worker_resources': _resource_summary(resource_samples),
                'outer_users_requested': False,
                'holdout_requested': False,
            }
            _write_json(config.output_dir / 'pilot.json', {
                'status': 'bounded', 'phase': 'pilot', 'run_id': config.run_id,
                'source_commit': identity['source']['commit'], 'summary': summary})
            if latest_progress is not None:
                _write_json(config.output_dir / 'pilot-progress.json', {
                    'status': 'bounded', 'phase': 'pilot', 'run_id': config.run_id,
                    'complete_epoch': False, 'stop_reason': selection.stop_reason,
                    'progress': latest_progress,
                    'worker_resources': _resource_summary(resource_samples),
                })
            _mark_manifest(config, identity, 'bounded', summary=summary, **audit)
            return RunResult(expected_phase, config.run_id, 'bounded', config.output_dir, summary)
        if pilot and (selection.status != 'completed' or not selection.complete_epoch
                      or selection.checkpoint is None):
            raise ValueError('pilot selection did not produce a complete-epoch checkpoint')
        if pilot:
            encoding_started = time.perf_counter()
            fitted_encoding = fit_vocabulary(train_data)
            expected_checkpoint_identity = {**identity, 'split_hash': split.split_hash,
                                            'encoding_hash': _encoding_hash(fitted_encoding)}
            encoding_build_seconds = time.perf_counter() - encoding_started
            checkpoint_load_started = time.perf_counter()
            payload = load_checkpoint(selection.checkpoint, expected_identity=expected_checkpoint_identity,
                                      device=config.device)
            checkpoint_load_seconds = time.perf_counter() - checkpoint_load_started
            encoding = ExerciseEncoding(StableVocabulary(tuple(payload['encoding']['values'])),
                                        payload['encoding']['train_support_students'])
            model_initialization_started = time.perf_counter()
            fitted = AKTAdapter(config, encoding)
            optimizer = torch.optim.Adam(fitted.native.parameters(), lr=config.lr, betas=config.betas,
                                         eps=config.eps, weight_decay=config.weight_decay)
            model_initialization_seconds = time.perf_counter() - model_initialization_started
            checkpoint_restore_started = time.perf_counter()
            restore_checkpoint(fitted, optimizer, payload)
            if not _checkpoint_state_matches(fitted, payload):
                raise ValueError('checkpoint reload model state mismatch')
            checkpoint_restore_seconds = time.perf_counter() - checkpoint_restore_started
            checkpoint_reload_seconds = checkpoint_load_seconds + checkpoint_restore_seconds
            record_resource(phase='after_checkpoint_reload')
            fitted.run_identity = identity
            fitted.checkpoint_id = sha256_file(selection.checkpoint)
            prediction_dir = config.output_dir / 'predictions'
            export_started = time.perf_counter()
            records = iter_predictions(fitted, order_prediction_learners(val_data))
            export = export_predictions(
                records, prediction_dir,
                expected_learners_factory=lambda: iter(val_data),
                identity={'run': config.run_id,
                          'checkpoint_sha256': sha256_file(selection.checkpoint)},
                shard_rows=50000)
            prediction_export_seconds = time.perf_counter() - export_started
            _check_resource_budget({'max_rss_bytes': caps['max_rss_bytes'],
                                    'min_available_ram_bytes': caps['min_available_ram_bytes'],
                                    'phase': config.phase, 'run_id': config.run_id})
            record_resource(phase='after_prediction_export')
            prediction_distribution = _prediction_distribution(prediction_dir)
            if export['status'] != 'complete' or export['expected_rows'] != export['prediction_rows']:
                raise ValueError('pilot prediction export is incomplete')
            if prediction_distribution['fitted_count'] != export['fitted_rows']:
                raise ValueError('pilot fitted prediction distribution coverage mismatch')
            training = selection.history[-1]['training']
            training_wall = float(training['resource']['wall_seconds'])
            windows = int(training['windows_processed'])
            optimized = int(training['optimized_target_rows'])
            validation = selection.history[-1]['validation']
            summary = {
                'complete_epoch': True,
                'selected_epoch': selection.selected_epoch,
                'training': training,
                'validation_loss': selection.history[-1]['validation_loss'],
                'validation': validation,
                'checkpoint_reload_state_exact': True,
                'checkpoint_sha256': sha256_file(selection.checkpoint),
                'checkpoint_save_seconds': selection.history[-1].get('checkpoint_save_seconds'),
                'checkpoint_reload_seconds': checkpoint_reload_seconds,
                'checkpoint_load_seconds': checkpoint_load_seconds,
                'checkpoint_restore_seconds': checkpoint_restore_seconds,
                'encoding_build_seconds': encoding_build_seconds,
                'model_initialization_seconds': model_initialization_seconds,
                'coverage': export,
                'prediction_distribution': prediction_distribution,
                'prediction_export_seconds': prediction_export_seconds,
                'cohort': load_observations,
                'timing': {
                    'data_loading_seconds': load_observations.get('data_loading_seconds'),
                    'chronological_query_sort_and_materialize_seconds':
                        load_observations.get('chronological_query_sort_and_materialize_seconds'),
                    'training_wall_seconds': training_wall,
                    'forward_seconds': training.get('forward_seconds', 0.0),
                    'backward_seconds': training.get('backward_seconds', 0.0),
                    'gradient_clip_seconds': training.get('gradient_clip_seconds', 0.0),
                    'optimizer_seconds': training.get('optimizer_seconds', 0.0),
                    'validation_seconds': validation.get('elapsed_seconds'),
                    'checkpoint_save_seconds': selection.history[-1].get('checkpoint_save_seconds'),
                    'encoding_build_seconds': encoding_build_seconds,
                    'checkpoint_load_seconds': checkpoint_load_seconds,
                    'model_initialization_seconds': model_initialization_seconds,
                    'checkpoint_restore_seconds': checkpoint_restore_seconds,
                    'checkpoint_reload_seconds': checkpoint_reload_seconds,
                    'prediction_export_seconds': prediction_export_seconds,
                    'windows_per_second': windows / training_wall if training_wall > 0 else None,
                    'scored_targets_per_second': optimized / training_wall if training_wall > 0 else None,
                },
                'worker_resources': _resource_summary(resource_samples),
                'outer_users_requested': False,
                'holdout_requested': False,
                'source_commit': identity['source']['commit'],
            }
        else:
            fitted_encoding = fit_vocabulary(train_data)
            expected_checkpoint_identity = {**identity, 'split_hash': split.split_hash,
                                            'encoding_hash': _encoding_hash(fitted_encoding)}
            payload = load_checkpoint(selection.checkpoint, expected_identity=expected_checkpoint_identity,
                                      device=config.device)
            # Selection already persisted the fitted vocabulary in the checkpoint; rebuild its adapter.
            encoding = ExerciseEncoding(StableVocabulary(tuple(payload['encoding']['values'])),
                                        payload['encoding']['train_support_students'])
            prediction_dir = config.output_dir / 'predictions'
            fitted = AKTAdapter(config, encoding)
            optimizer = torch.optim.Adam(fitted.native.parameters(), lr=config.lr, betas=config.betas,
                                         eps=config.eps, weight_decay=config.weight_decay)
            restore_checkpoint(fitted, optimizer, payload)
            if not _checkpoint_state_matches(fitted, payload):
                raise ValueError('checkpoint reload model state mismatch')
            fitted.run_identity = identity
            fitted.checkpoint_id = sha256_file(selection.checkpoint)
            records = iter_predictions(fitted, order_prediction_learners(val_data))
            export = export_predictions(records, prediction_dir,
                                        expected_learners_factory=lambda: iter(val_data),
                                        identity={'run': config.run_id,
                                                  'checkpoint_sha256': sha256_file(selection.checkpoint)},
                                        shard_rows=50000)
            summary = {'selected_epoch': selection.selected_epoch,
                       'validation_loss': selection.history[-1]['validation_loss'],
                       'training': selection.history[-1]['training'],
                       'checkpoint_reload_state_exact': True,
                       'checkpoint_sha256': sha256_file(selection.checkpoint),
                       'coverage': export, 'metrics': score_akt_shards(str(prediction_dir / 'part-*.parquet'))}
        elapsed = time.perf_counter() - started
        resource_samples.append(memory_snapshot())
        peak_rss = _check_resource_budget({'max_rss_bytes': caps['max_rss_bytes'],
                                           'min_available_ram_bytes': caps['min_available_ram_bytes'],
                                           'phase': config.phase, 'run_id': config.run_id})
        if elapsed > caps['max_wall_seconds']:
            raise RuntimeError('phase resource cap exceeded')
        summary.update({'elapsed_seconds': elapsed, 'peak_rss_bytes': peak_rss,
                       'outer_users_requested': False, 'holdout_requested': False,
                       'selection_checkpoint': str(selection.checkpoint.name),
                       'source_commit': identity['source']['commit']})
        if pilot:
            summary['worker_resources'] = _resource_summary(resource_samples)
            if latest_progress is not None:
                _write_json(config.output_dir / 'pilot-progress.json', {
                    'status': 'completed', 'phase': 'pilot', 'run_id': config.run_id,
                    'complete_epoch': True, 'stop_reason': 'epoch_complete',
                    'progress': latest_progress,
                    'worker_resources': summary['worker_resources'],
                })
        if pilot:
            _write_json(config.output_dir / 'pilot.json', {'status': 'complete', 'phase': 'pilot',
                                                            'run_id': config.run_id,
                                                            'source_commit': identity['source']['commit'],
                                                            'summary': summary})
        _mark_manifest(config, identity, 'completed', summary=summary, **audit)
        return RunResult(expected_phase, config.run_id, 'completed', config.output_dir, summary)
    except Exception as exc:
        status = ('incomplete' if isinstance(exc, (TimeoutError, MemoryError)) else 'failed') if pilot else 'incomplete'
        if pilot:
            failure = {'status': status, 'phase': 'pilot', 'run_id': config.run_id,
                       'error_type': type(exc).__name__, 'error': str(exc),
                       'stop_reason': 'resource_or_timeout' if status == 'incomplete' else 'implementation_or_numerical_failure',
                       'complete_epoch': bool(latest_progress and latest_progress.get('complete_epoch')),
                       'partial_progress': latest_progress,
                       'worker_resources': _resource_summary(resource_samples)}
            _write_json(config.output_dir / 'pilot.json', failure)
        _mark_manifest(config, identity, status, error_type=type(exc).__name__, error=str(exc),
                       stop_reason=('resource_or_timeout' if status == 'incomplete' else 'implementation_or_numerical_failure'),
                       partial_progress=latest_progress, **audit)
        raise


def run_smoke(config: AKTConfig, *, authorization: dict | None = None,
              _invocation: dict | None = None) -> RunResult:
    return _run_phase(config, authorization, pilot=False, invocation=_invocation)


def run_pilot(config: AKTConfig, *, authorization: dict | None = None,
              _invocation: dict | None = None) -> RunResult:
    return _run_phase(config, authorization, pilot=True, invocation=_invocation)


def prepare_fold_readiness(config: AKTConfig, *, pilot_result: Path) -> dict:
    validate_config(config)
    if config.phase != 'fold-readiness' or not pilot_result.is_file():
        raise ValueError('fold readiness requires fold-readiness config and a pilot result file')
    result = json.loads(pilot_result.read_text(encoding='utf-8'))
    if result.get('status') not in {'completed', 'complete'} or result.get('source_commit') != SOURCE_COMMIT:
        raise ValueError('pilot result is incomplete or uses another source')
    summary = result.get('summary')
    validation = summary.get('validation') if isinstance(summary, dict) else None
    coverage = summary.get('coverage') if isinstance(summary, dict) else None
    if (not isinstance(summary, dict) or summary.get('complete_epoch') is not True
            or not isinstance(summary.get('validation_loss'), (int, float))
            or not math.isfinite(float(summary['validation_loss']))
            or not isinstance(validation, dict) or validation.get('predicted_rows', 0) <= 0
            or summary.get('checkpoint_reload_state_exact') is not True
            or not summary.get('checkpoint_sha256')
            or not isinstance(coverage, dict) or coverage.get('status') != 'complete'
            or not isinstance(coverage.get('expected_rows'), int) or coverage['expected_rows'] <= 0
            or coverage.get('prediction_rows') != coverage.get('expected_rows')):
        raise ValueError('pilot result lacks complete validation/checkpoint/export evidence')
    return {
        'status': 'pending-explicit-approval', 'run_id': config.run_id,
        'pilot_result_sha256': sha256_file(pilot_result),
        'source_commit': config.source_commit,
        'authorization': {'full_fold': False, 'five_fold': False},
    }


def _orchestrate_full_fold(config: AKTConfig, *, authorization: dict | None, inner_split: InnerSplit,
                           outer_train_users: tuple[str, ...], inner_train_factory, inner_val_factory,
                           outer_train_factory, outer_eval_factory, identity: dict, budget: dict) -> dict:
    """Private workflow; the public full-fold entry remains disabled at this milestone."""
    if (config.phase != 'fold' or config.execution_enabled is not True
            or not isinstance(authorization, dict) or authorization.get('full_fold') is not True
            or authorization.get('scope') != 'development-fold'
            or authorization.get('run_id') != config.run_id
            or authorization.get('source_commit') != config.source_commit
            or authorization.get('config_sha256') != _config_hash(config)
            or not isinstance(authorization.get('approval_reference'), str)
            or not authorization['approval_reference'].strip()):
        raise PermissionError('full-fold execution requires future explicit authorization')
    allowed_budget = {'max_steps', 'max_targets', 'max_seconds', 'max_rss_bytes', 'min_available_ram_bytes'}
    if (not isinstance(budget, dict) or not budget or authorization.get('budget') != budget
            or not set(budget) <= allowed_budget
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(value) or value <= 0
                   or (key != 'max_seconds' and not isinstance(value, int))
                   for key, value in budget.items())):
        raise PermissionError('full-fold budget must match the explicit authorization')
    validate_config(config)
    _require_gate2_evidence(config)
    if authorization.get('identity') != identity or _identity(config, preflight(config)) != identity:
        raise PermissionError('full-fold identity does not match authorization or current inputs')
    assignments = read_development_assignments(_data_paths())
    if (assignments.empty or assignments.user_id.isna().any()
            or assignments.user_id.astype(str).duplicated().any()
            or not assignments.fold.isin(range(5)).all()):
        raise ValueError('invalid Development assignments')
    expected_train = set(assignments.loc[assignments.fold != config.outer_fold, 'user_id'].astype(str))
    expected_eval = set(assignments.loc[assignments.fold == config.outer_fold, 'user_id'].astype(str))
    assigned_folds = dict(zip(assignments.user_id.astype(str), assignments.fold.astype(int)))
    inner_train = set(inner_split.inner_train_users)
    inner_val = set(inner_split.inner_val_users)
    if (inner_split != make_inner_split(assignments, outer_fold=config.outer_fold, seed=config.seed)
            or inner_split.outer_fold != config.outer_fold or inner_train & inner_val
            or len(set(outer_train_users)) != len(outer_train_users)
            or not expected_eval or set(outer_train_users) != expected_train
            or set(outer_train_users) != inner_train | inner_val):
        raise ValueError('full-fold training scope does not match the inner split')

    def checked_training(factory, allowed):
        for learner in factory():
            if learner.user_id not in allowed or assigned_folds.get(learner.user_id) != learner.fold:
                raise ValueError('full-fold training learner assignment mismatch')
            yield learner

    def outer_evaluation():
        seen = set()
        for learner in outer_eval_factory():
            if (learner.fold != config.outer_fold or learner.user_id not in expected_eval or learner.user_id in seen
                    or learner.user_id in inner_train or learner.user_id in inner_val):
                raise ValueError('full-fold evaluation scope violation')
            seen.add(learner.user_id)
            yield learner
        if seen != expected_eval:
            raise ValueError('full-fold evaluation scope is incomplete')

    selection = select_checkpoint(config, inner_split=inner_split,
                                  train_learners_factory=lambda: checked_training(inner_train_factory, inner_train),
                                  val_learners_factory=lambda: checked_training(inner_val_factory, inner_val),
                                  identity=identity, budget=budget)
    fitted = refit_outer_train(config, outer_train_users=outer_train_users,
                               train_learners_factory=lambda: checked_training(outer_train_factory, expected_train),
                               selected_epochs=selection.selected_epoch,
                               identity=identity, budget=budget)
    checkpoint = config.output_dir / f'refit-epoch-{selection.selected_epoch}.pt'
    save_checkpoint(checkpoint, fitted, fitted.optimizer, identity=fitted.run_identity,
                    progress={'epoch': selection.selected_epoch, 'complete': True,
                              'sampler_seed': config.seed + selection.selected_epoch,
                              'history': fitted.training_history})
    fitted.checkpoint_id = sha256_file(checkpoint)
    records = iter_predictions(fitted, outer_evaluation())
    coverage = export_predictions(records, config.output_dir / 'predictions',
                                  expected_learners_factory=outer_evaluation,
                                  identity={'run': config.run_id, 'checkpoint_sha256': fitted.checkpoint_id})
    return {'selected_epoch': selection.selected_epoch, 'checkpoint': str(checkpoint), 'coverage': coverage}


def run_full_fold(config: AKTConfig, *, authorization: dict | None) -> None:
    if not authorization or authorization.get('full_fold') is not True:
        raise PermissionError('full-fold execution requires future explicit authorization')
    raise PermissionError('full-fold execution is disabled in the Tasks 1–12 milestone')


def main(argv: list[str] | None = None) -> int:
    """Compatibility wrapper; the public CLI is implemented by the lightweight watchdog."""
    from .watchdog import main as watchdog_main
    return watchdog_main(argv)


def _worker_main(argv: list[str]) -> int:
    if not argv or argv[0] not in {'smoke', 'pilot'}:
        raise ValueError('invalid internal AKT worker phase')
    phase, *rest = argv
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args(rest)
    config = load_config(args.config)
    _emit_memory_event('worker-after-runtime-import', phase, config.run_id)
    authorization = json.loads(args.authorization.read_text(encoding='utf-8')) if args.authorization else None
    invocation = {'kind': 'cli', 'argv': [sys.executable, '-m', 'knowledge_tracing.akt.cli', *sys.argv[1:]]}
    result = (run_smoke(config, authorization=authorization, _invocation=invocation) if phase == 'smoke'
              else run_pilot(config, authorization=authorization, _invocation=invocation))
    print(json.dumps(asdict(result), indent=2, default=str))
    return 0
