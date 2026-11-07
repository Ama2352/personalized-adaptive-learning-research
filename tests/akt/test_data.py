from dataclasses import replace
from pathlib import Path

import duckdb
import pytest

from knowledge_tracing.akt.config import DataPaths
import knowledge_tracing.akt.data as data_module
from knowledge_tracing.akt.data import iter_development_learners


@pytest.fixture
def frozen_fixture(tmp_path):
    canonical = tmp_path / 'canonical'
    canonical.mkdir()
    assignments = tmp_path / 'assignments.parquet'
    con = duckdb.connect()
    try:
        con.execute('CREATE TABLE a(user_id VARCHAR, partition VARCHAR, fold INTEGER)')
        con.executemany('INSERT INTO a VALUES (?, ?, ?)',
                        [('a', 'development', 0), ('b', 'development', 1), ('hold', 'test', -1)])
        con.execute('COPY a TO ? (FORMAT PARQUET)', [str(assignments)])
        con.execute('CREATE TABLE e(user_id VARCHAR, exercise VARCHAR, time_done BIGINT, '
                    'source_row BIGINT, correct INTEGER, suggested INTEGER)')
        con.executemany('INSERT INTO e VALUES (?, ?, ?, ?, ?, ?)',
                        [('a', 'B', 20, 3, 0, 0), ('a', 'A', 10, 2, 1, 0),
                         ('a', 'C', 20, 1, 1, 1), ('b', 'A', 10, 4, 0, 0),
                         ('hold', 'X', 10, 5, 1, 0)])
        con.execute('COPY e TO ? (FORMAT PARQUET)', [str(canonical / 'events.parquet')])
    finally:
        con.close()
    return DataPaths(canonical, assignments, tmp_path / 'canonical.json', tmp_path / 'split.json')


def test_loader_keeps_user_history_across_fetch_batches_and_orders_ties(frozen_fixture):
    learners = list(iter_development_learners(frozen_fixture, user_ids=['b', 'a'],
                                             allowed_folds=(0, 1), fetch_rows=2))
    assert [u.user_id for u in learners] == ['a', 'b']
    assert [e.source_row for e in learners[0].events] == [2, 1, 3]
    assert [e.exercise for e in learners[0].events] == ['A', 'C', 'B']
    assert [e.source_row for e in learners[1].events] == [4]


def test_loader_can_preserve_requested_cohort_order(frozen_fixture):
    stats = {}
    learners = list(iter_development_learners(frozen_fixture, user_ids=['b', 'a'],
                                             allowed_folds=(0, 1), fetch_rows=2,
                                             preserve_user_order=True, stats=stats))
    assert [learner.user_id for learner in learners] == ['b', 'a']
    assert [event.source_row for event in learners[1].events] == [2, 1, 3]
    assert stats['peak_fetch_rows'] == 2
    assert stats['peak_learner_events'] == 3
    assert stats['query_rows_returned'] == 4
    assert stats['chronological_query_sort_and_materialize_seconds'] >= 0


def test_non_development_user_fails_before_interactions_query(frozen_fixture, tmp_path):
    paths = replace(frozen_fixture, canonical=tmp_path / 'absent')
    with pytest.raises(ValueError, match='development'):
        list(iter_development_learners(paths, user_ids=['hold'], allowed_folds=(0,)))


def test_loader_rejects_wrong_scope_and_duplicate_user_request(frozen_fixture):
    with pytest.raises(ValueError, match='fold'):
        list(iter_development_learners(frozen_fixture, user_ids=['b'], allowed_folds=(0,)))
    with pytest.raises(ValueError, match='duplicate'):
        list(iter_development_learners(frozen_fixture, user_ids=['a', 'a'], allowed_folds=(0,)))


def test_loader_rejects_empty_cohort(frozen_fixture):
    with pytest.raises(ValueError, match='empty'):
        list(iter_development_learners(frozen_fixture, user_ids=[], allowed_folds=(0,)))


def test_loader_rejects_spill_directory_in_protected_tree(frozen_fixture, tmp_path, monkeypatch):
    monkeypatch.setattr(data_module, 'PROJECT_ROOT', tmp_path)
    with pytest.raises(ValueError, match='temporary directory'):
        list(iter_development_learners(frozen_fixture, user_ids=['a'], allowed_folds=(0,),
                                     temp_dir=tmp_path / 'artifacts/bkt_baseline/tmp'))


def test_loader_rejects_duplicate_source_rows_across_learners(frozen_fixture):
    con = duckdb.connect()
    try:
        con.execute("COPY (SELECT 'b' user_id, 'D' exercise, 15::BIGINT time_done, "
                    "1::BIGINT source_row, 1 correct, 0 suggested) TO ? (FORMAT PARQUET)",
                    [str(frozen_fixture.canonical / 'duplicate.parquet')])
    finally:
        con.close()
    with pytest.raises(ValueError, match='duplicate source_row'):
        list(iter_development_learners(frozen_fixture, user_ids=['a', 'b'], allowed_folds=(0, 1)))


def test_loader_matches_shared_sequence_contract(frozen_fixture):
    from knowledge_tracing.shared_kt import build_causal_sequence_inputs

    users = list(iter_development_learners(frozen_fixture, user_ids=['a', 'b'], allowed_folds=(0, 1)))
    rows = [vars(event) for user in users for event in user.events]
    inputs, targets = build_causal_sequence_inputs(rows, item_key='exercise')
    assert inputs.source_rows.tolist() == [2, 1, 3, 4]
    assert inputs.prior_responses.tolist() == [-1, 1, 1, -1]
    assert targets.tolist() == [1, 1, 0, 0]
