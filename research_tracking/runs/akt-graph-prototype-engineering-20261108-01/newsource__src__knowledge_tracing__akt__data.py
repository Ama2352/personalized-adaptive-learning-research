"""Đọc learner Development theo timeline xuyên exercise."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
import time

import duckdb
import pandas as pd

from .config import DataPaths, PROJECT_ROOT
from .types import KTEvent, LearnerEvents


def read_development_assignments(paths: DataPaths) -> pd.DataFrame:
    con = duckdb.connect(config={'memory_limit': '512MB', 'threads': '2', 'temp_directory': ''})
    try:
        frame = con.execute(
            "SELECT user_id, fold FROM read_parquet(?) WHERE partition='development'",
            [str(paths.assignments)],
        ).df()
    finally:
        con.close()
    if (frame.empty or frame.user_id.isna().any() or frame.user_id.astype(str).eq('').any()
            or frame.user_id.astype(str).duplicated().any() or not frame.fold.isin(range(5)).all()):
        raise ValueError('invalid development assignments')
    frame['user_id'] = frame.user_id.astype(str)
    return frame


def iter_development_learners(paths: DataPaths, *, user_ids: Sequence[str],
                              allowed_folds: tuple[int, ...], fetch_rows: int = 50000,
                              temp_dir: Path | None = None,
                              preserve_user_order: bool = False,
                              stats: dict | None = None) -> Iterator[LearnerEvents]:
    users = [str(user) for user in user_ids]
    if stats is not None:
        stats.update({'peak_fetch_rows': 0, 'peak_learner_events': 0})
    if not users:
        raise ValueError('empty cohort')
    if len(users) != len(set(users)):
        raise ValueError('duplicate user request')
    if fetch_rows <= 0 or not allowed_folds or not set(allowed_folds) <= set(range(5)):
        raise ValueError('invalid fetch size or fold')
    assignments = read_development_assignments(paths)
    selected = assignments[assignments.user_id.isin(users)].copy()
    if set(selected.user_id) != set(users):
        raise ValueError('requested user is not in development')
    if not selected.fold.isin(allowed_folds).all():
        raise ValueError('requested user belongs to a disallowed fold')
    selected['cohort_order'] = selected.user_id.map({user: i for i, user in enumerate(users)})
    if temp_dir is not None:
        temp_dir = temp_dir.resolve()
        base = (PROJECT_ROOT / 'artifacts/akt/tmp').resolve()
        protected = (PROJECT_ROOT / 'dataset', PROJECT_ROOT / 'artifacts/bkt_baseline',
                     PROJECT_ROOT / 'venv', PROJECT_ROOT / '.wsl')
        if (not temp_dir.is_relative_to(base) or temp_dir == base
                or any(temp_dir.is_relative_to(path.resolve()) for path in protected)):
            raise ValueError('invalid temporary directory')
        temp_dir.mkdir(parents=True, exist_ok=True)
    settings = {'memory_limit': '512MB', 'threads': '2',
                'temp_directory': str(temp_dir) if temp_dir is not None else ''}
    con = duckdb.connect(config=settings)
    query_started = time.perf_counter()
    query_rows_returned = 0
    try:
        con.register('selected_development_users', selected)
        pattern = str(paths.canonical / '**' / '*.parquet') if paths.canonical.is_dir() else str(paths.canonical)
        order = 'u.cohort_order' if preserve_user_order else 'c.user_id'
        cursor = con.execute(
            "SELECT c.user_id,c.exercise,c.time_done,c.source_row,c.correct,c.suggested,u.fold, "
            "COUNT(*) OVER (PARTITION BY c.source_row) AS row_count "
            "FROM read_parquet(?, hive_partitioning=true) c "
            "JOIN selected_development_users u ON c.user_id=u.user_id "
            f"ORDER BY {order},c.time_done,c.source_row", [pattern])
        current_user = None
        current_fold = None
        events: list[KTEvent] = []
        encountered: set[str] = set()
        while True:
            rows = cursor.fetchmany(fetch_rows)
            if not rows:
                break
            query_rows_returned += len(rows)
            if stats is not None:
                stats['peak_fetch_rows'] = max(stats['peak_fetch_rows'], len(rows))
            for user, exercise, time_done, source_row, correct, suggested, fold, count in rows:
                if (not user or not exercise or not isinstance(time_done, int) or time_done < 0
                        or not isinstance(source_row, int) or source_row <= 0 or correct not in (0, 1)
                        or suggested not in (0, 1) or count != 1):
                    raise ValueError('invalid event or duplicate source_row')
                if current_user is not None and current_user != user:
                    yield LearnerEvents(current_user, current_fold, tuple(events))
                    events = []
                current_user, current_fold = user, int(fold)
                encountered.add(user)
                events.append(KTEvent(user, exercise, time_done, source_row, int(correct), int(suggested), int(fold)))
                if stats is not None:
                    stats['peak_learner_events'] = max(stats['peak_learner_events'], len(events))
        if current_user is not None:
            yield LearnerEvents(current_user, current_fold, tuple(events))
        if encountered != set(users):
            raise ValueError('requested development learner has no interactions')
    finally:
        con.close()
        if stats is not None:
            stats['chronological_query_sort_and_materialize_seconds'] = time.perf_counter() - query_started
            stats['query_rows_returned'] = query_rows_returned
