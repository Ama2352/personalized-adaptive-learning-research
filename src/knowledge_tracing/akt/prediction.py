"""Inference and source-row-safe AKT Parquet export."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
from typing import TYPE_CHECKING
import uuid

import duckdb
import numpy as np
import pandas as pd

from knowledge_tracing.shared_kt import check_prediction_alignment
from .config import PROJECT_ROOT
from .filesystem import publish_new_file
if TYPE_CHECKING:
    from .model import AKTAdapter
from .types import LearnerEvents, PredictionRecord, UnseenTarget
from .windows import iter_windows


_COLUMNS = tuple(PredictionRecord.__dataclass_fields__)
_IDENTITY_KEYS = ('user_id', 'exercise', 'time_done', 'correct', 'suggested', 'fold')


def order_prediction_learners(learners: tuple[LearnerEvents, ...]) -> tuple[LearnerEvents, ...]:
    """Sort a bounded cohort at the prediction boundary without changing learner events."""
    return tuple(sorted(learners, key=lambda learner: learner.user_id))


def _checkpoint_id(adapter: AKTAdapter) -> str:
    pinned = getattr(adapter, 'checkpoint_id', None)
    if isinstance(pinned, str) and pinned:
        return pinned
    identity = getattr(adapter, 'run_identity', None)
    if not isinstance(identity, dict) or not identity:
        raise ValueError('adapter has no checkpoint identity')
    payload = json.dumps(identity, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def iter_predictions(adapter: AKTAdapter, learners: Iterable[LearnerEvents]) -> Iterator[PredictionRecord]:
    """Predict every requested row once; current OOV rows remain explicit nulls."""
    checkpoint_id = _checkpoint_id(adapter)
    support = adapter.encoding.train_support_students
    previous_user = None
    for learner in learners:
        if (not learner.user_id or not learner.events or learner.user_id == previous_user
                or any(event.user_id != learner.user_id or event.fold != learner.fold
                       or event.correct not in (0, 1) or event.suggested not in (0, 1)
                       for event in learner.events)):
            raise ValueError('invalid or repeated prediction learner')
        if previous_user is not None and learner.user_id < previous_user:
            raise ValueError('prediction learners must be sorted by user_id')
        rows = [event.source_row for event in learner.events]
        if any(row <= 0 for row in rows) or len(rows) != len(set(rows)):
            raise ValueError('source_row must be positive and unique per learner')
        if any((left.time_done, left.source_row) > (right.time_done, right.source_row)
               for left, right in zip(learner.events, learner.events[1:])):
            raise ValueError('learner events are not in canonical chronological order')
        event_by_row = {event.source_row: event for event in learner.events}
        for entry in iter_windows(learner, adapter.encoding, context=adapter.config.context,
                                  target_block=adapter.config.target_block, training=False):
            if isinstance(entry, UnseenTarget):
                event = entry.event
                block_start = (entry.global_rank // adapter.config.target_block) * adapter.config.target_block
                base = max(0, block_start - adapter.config.context)
                yield PredictionRecord(
                    event.source_row, event.user_id, event.exercise, event.time_done,
                    event.correct, event.suggested, event.fold, None, 'unseen', False, 0,
                    entry.global_rank - base, 0, True,
                    hashlib.sha256(f'{event.user_id}\0{entry.global_rank}\0unseen'.encode()).hexdigest(),
                    checkpoint_id)
                continue
            probabilities = np.asarray(adapter.predict_window(entry), dtype=np.float64)
            if probabilities.shape != entry.target_mask.shape:
                raise ValueError('adapter prediction shape does not align with window')
            for index in np.flatnonzero(entry.target_mask):
                event = event_by_row.get(int(entry.inputs.source_rows[index]))
                value = float(probabilities[index])
                if event is None or not math.isfinite(value) or not 0.0 <= value <= 1.0:
                    raise ValueError('known target has missing identity or invalid probability')
                item_support = support.get(event.exercise, 0)
                if item_support <= 0:
                    raise ValueError('known prediction has no train support')
                yield PredictionRecord(
                    event.source_row, event.user_id, event.exercise, event.time_done,
                    event.correct, event.suggested, event.fold, value, 'fitted', False,
                    int(item_support), int(entry.history_available[index]), int(entry.history_used[index]),
                    bool(entry.context_reset[index]), entry.window_id, checkpoint_id)
        previous_user = learner.user_id


def _validate_record(record: PredictionRecord) -> None:
    if not isinstance(record, PredictionRecord):
        raise ValueError('invalid prediction record type')
    if (record.source_row <= 0 or not record.user_id or not record.exercise
            or record.time_done < 0 or record.correct not in (0, 1)
            or record.suggested not in (0, 1) or record.fold not in range(5)
            or not isinstance(record.is_fallback, bool) or record.is_fallback
            or min(record.train_support_students, record.history_available,
                   record.history_used) < 0 or record.history_used > record.history_available
            or not record.window_id or not record.checkpoint_id):
        raise ValueError('invalid prediction metadata')
    if record.prediction_kind == 'fitted':
        if (record.prediction is None or not math.isfinite(float(record.prediction))
                or not 0.0 <= float(record.prediction) <= 1.0
                or record.train_support_students <= 0):
            raise ValueError('invalid fitted probability or support')
    elif record.prediction_kind == 'unseen':
        if record.prediction is not None or record.train_support_students != 0:
            raise ValueError('unseen predictions must be null and unsupported')
    else:
        raise ValueError('invalid prediction kind')


def _write_json_atomic(path: Path, payload: dict) -> None:
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(payload, stream, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _prepare_output(output_dir: Path) -> tuple[Path, Path]:
    root = PROJECT_ROOT.resolve()
    output = output_dir.resolve()
    allowed = root / 'experiments/akt/results'
    protected = (root / 'dataset', root / 'artifacts/bkt_baseline', root / 'venv', root / '.wsl')
    if (not output.is_relative_to(allowed.resolve()) or output == allowed.resolve()
            or any(output.is_relative_to(path.resolve()) for path in protected)):
        raise ValueError('unsafe AKT prediction output')
    manifest = output / 'manifest.json'
    if output.exists():
        if not manifest.is_file():
            raise FileExistsError('output directory exists without a resumable manifest')
        return output, manifest
    output.mkdir(parents=True, exist_ok=False)
    (output / '.pending').mkdir()
    return output, manifest


def _sql_path(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def _record_rows(path: Path, records: list[PredictionRecord]) -> None:
    frame = pd.DataFrame([asdict(record) for record in records], columns=_COLUMNS)
    frame['prediction'] = pd.array(frame['prediction'], dtype='Float64')
    with duckdb.connect() as con:
        con.register('prediction_batch', frame)
        con.execute(f'COPY prediction_batch TO {_sql_path(path)} (FORMAT PARQUET, COMPRESSION ZSTD)')
        con.unregister('prediction_batch')


def _promote_pending(output: Path, pending: list[tuple[Path, int]], manifest: dict,
                     user_id: str) -> None:
    shard_entries = []
    next_index = len(manifest['shards'])
    for offset, (temp_path, rows) in enumerate(pending):
        name = f'part-{next_index + offset:05d}.parquet'
        destination = output / name
        publish_new_file(temp_path, destination)
        shard_entries.append({'path': name, 'rows': rows, 'user_id': user_id})
    manifest['shards'].extend(shard_entries)
    manifest['completed_users'].append(user_id)
    manifest['prediction_rows'] += sum(shard['rows'] for shard in shard_entries)
    _write_json_atomic(output / 'manifest.json', manifest)


def _expected_insert(con, factory: Callable[[], Iterator[LearnerEvents]]) -> int:
    con.execute('CREATE TABLE expected (source_row BIGINT PRIMARY KEY, user_id VARCHAR, exercise VARCHAR, '
                'time_done BIGINT, correct INTEGER, suggested INTEGER, fold INTEGER)')
    count = 0
    seen_users: set[str] = set()
    for learner in factory():
        if (not learner.user_id or learner.user_id in seen_users or not learner.events
                or any(event.user_id != learner.user_id or event.fold != learner.fold
                       for event in learner.events)):
            raise ValueError('invalid expected learner identity')
        seen_users.add(learner.user_id)
        rows = [(event.source_row, event.user_id, event.exercise, event.time_done,
                 event.correct, event.suggested, event.fold) for event in learner.events]
        if any(row <= 0 or not user or not exercise or not isinstance(time_done, int) or time_done < 0
               or correct not in (0, 1)
               or suggested not in (0, 1) or fold not in range(5)
               for row, user, exercise, time_done, correct, suggested, fold in rows):
            raise ValueError('invalid expected row')
        con.executemany('INSERT INTO expected VALUES (?, ?, ?, ?, ?, ?, ?)', rows)
        count += len(rows)
    if count == 0:
        raise ValueError('empty expected prediction cohort')
    return count


def export_predictions(records: Iterable[PredictionRecord], output_dir: Path, *,
                       expected_learners_factory: Callable[[], Iterator[LearnerEvents]],
                       identity: dict, shard_rows: int = 50000) -> dict:
    """Write complete learner-atomic shards, resume exact identities, then audit all rows."""
    if shard_rows <= 0 or not isinstance(identity, dict) or not identity:
        raise ValueError('invalid prediction export configuration')
    output, manifest_path = _prepare_output(Path(output_dir))
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest.get('identity') != identity:
            raise ValueError('prediction export identity mismatch')
        if manifest.get('status') == 'complete':
            return manifest
        for shard in output.glob('part-*.parquet'):
            if shard.name not in {entry['path'] for entry in manifest.get('shards', [])}:
                shard.unlink()
    else:
        manifest = {'schema_version': 1, 'status': 'incomplete', 'identity': identity,
                    'shards': [], 'completed_users': [], 'prediction_rows': 0}
        _write_json_atomic(manifest_path, manifest)
    pending_dir = output / '.pending'
    pending_dir.mkdir(exist_ok=True)
    for stale in pending_dir.glob('*.parquet.tmp'):
        stale.unlink()
    completed = set(manifest['completed_users'])
    current_user: str | None = None
    current_buffer: list[PredictionRecord] = []
    pending_files: list[tuple[Path, int]] = []
    pending_index = 0
    seen_new_users: set[str] = set()

    def write_pending() -> None:
        nonlocal current_buffer, pending_index
        if not current_buffer:
            return
        temp = pending_dir / f'{uuid.uuid4().hex}-{pending_index:05d}.parquet.tmp'
        _record_rows(temp, current_buffer)
        pending_files.append((temp, len(current_buffer)))
        pending_index += 1
        current_buffer = []

    def finish_user() -> None:
        nonlocal pending_files, current_user
        if current_user is None or current_user in completed:
            return
        write_pending()
        _promote_pending(output, pending_files, manifest, current_user)
        completed.add(current_user)
        pending_files = []
        current_user = None

    try:
        for record in records:
            _validate_record(record)
            if record.user_id in completed:
                if current_user is not None:
                    finish_user()
                continue
            if current_user is None:
                if record.user_id in seen_new_users:
                    raise ValueError('prediction learner rows are not contiguous')
                current_user = record.user_id
                seen_new_users.add(current_user)
            elif record.user_id != current_user:
                finish_user()
                if record.user_id in completed or record.user_id in seen_new_users:
                    raise ValueError('prediction learner rows are not contiguous')
                current_user = record.user_id
                seen_new_users.add(current_user)
            current_buffer.append(record)
            if len(current_buffer) >= shard_rows:
                write_pending()
        finish_user()

        audit_path = output / '.audit.tmp.duckdb'
        if audit_path.exists():
            audit_path.unlink()
        con = duckdb.connect(str(audit_path), config={'memory_limit': '512MB', 'threads': '2'})
        try:
            expected_count = _expected_insert(con, expected_learners_factory)
            shard_paths = [str(output / shard['path']) for shard in manifest['shards']]
            if not shard_paths:
                raise ValueError('prediction export produced no shards')
            parquet_list = '[' + ','.join(_sql_path(Path(path)) for path in shard_paths) + ']'
            con.execute(f'CREATE VIEW predictions AS SELECT * FROM read_parquet({parquet_list})')
            output_count = int(con.execute('SELECT count(*) FROM predictions').fetchone()[0])
            duplicate_count = output_count - int(con.execute(
                'SELECT count(DISTINCT source_row) FROM predictions').fetchone()[0])
            if duplicate_count:
                raise ValueError('duplicate source_row in predictions')
            missing = int(con.execute('SELECT count(*) FROM expected e LEFT JOIN predictions p USING(source_row) '
                                      'WHERE p.source_row IS NULL').fetchone()[0])
            extra = int(con.execute('SELECT count(*) FROM predictions p LEFT JOIN expected e USING(source_row) '
                                    'WHERE e.source_row IS NULL').fetchone()[0])
            mismatched = int(con.execute(
                'SELECT count(*) FROM expected e JOIN predictions p USING(source_row) WHERE '
                'p.user_id IS DISTINCT FROM e.user_id OR p.exercise IS DISTINCT FROM e.exercise OR '
                'p.time_done IS DISTINCT FROM e.time_done OR p.correct IS DISTINCT FROM e.correct OR '
                'p.suggested IS DISTINCT FROM e.suggested OR p.fold IS DISTINCT FROM e.fold').fetchone()[0])
            if (expected_count != output_count or missing or extra or mismatched
                    or output_count != int(manifest['prediction_rows'])):
                raise ValueError(f'prediction alignment failed: missing={missing}, extra={extra}, identity={mismatched}')
            sample_expected = con.execute(
                'SELECT e.source_row,e.user_id,e.exercise,e.time_done,e.correct,e.suggested,e.fold '
                'FROM expected e JOIN predictions p USING(source_row) ORDER BY e.source_row LIMIT 256').fetchdf().to_dict('records')
            sample_predictions = con.execute(
                'SELECT source_row,user_id,exercise,time_done,correct,suggested,fold FROM predictions '
                'ORDER BY source_row LIMIT 256').fetchdf().to_dict('records')
            sample_alignment = check_prediction_alignment(
                sample_expected, sample_predictions,
                identity_keys=('user_id', 'exercise', 'time_done', 'correct', 'suggested', 'fold'))
            counts = con.execute(
                "SELECT count(*) FILTER (WHERE prediction_kind='fitted'), "
                "count(*) FILTER (WHERE prediction_kind='unseen'), "
                "count(DISTINCT user_id), count(DISTINCT exercise), "
                "count(*) FILTER (WHERE context_reset), "
                "count(*) FILTER (WHERE prediction_kind='fitted' AND history_used<history_available), "
                "count(*) FILTER (WHERE context_reset AND history_used=0), "
                "count(*) FILTER (WHERE history_used=0) FROM predictions").fetchone()
            fitted, unseen, users, exercises, barriers, reduced, zero_after_barrier, zero_history = map(int, counts)
            manifest.update({
                'status': 'complete', 'expected_rows': expected_count, 'prediction_rows': output_count,
                'fitted_rows': fitted, 'unseen_rows': unseen,
                'output_coverage': output_count / expected_count,
                'fitted_coverage': fitted / expected_count,
                'unique_users': users, 'unique_exercises': exercises,
                'context_barrier_rows': barriers, 'known_reduced_history_rows': reduced,
                'known_zero_history_after_oov_rows': zero_after_barrier,
                'zero_history_rows': zero_history, 'alignment_sample_rows': sample_alignment.aligned_rows,
            })
        finally:
            con.close()
        if audit_path.exists():
            audit_path.unlink()
        _write_json_atomic(manifest_path, manifest)
        return manifest
    except Exception:
        manifest['status'] = 'incomplete'
        _write_json_atomic(manifest_path, manifest)
        raise
