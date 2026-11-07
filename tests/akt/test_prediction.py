from dataclasses import replace
import json
from types import SimpleNamespace

import duckdb
import numpy as np
import pytest

from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.prediction import PredictionRecord, export_predictions, iter_predictions
import knowledge_tracing.akt.prediction as prediction_module


def learner(user='u', *, n=201, oov=(100,), fold=0, offset=0):
    return LearnerEvents(user, fold, tuple(
        KTEvent(user, 'X' if i in oov else 'A', 1_000+i, offset+i+1, i % 2, (i+1) % 2, fold)
        for i in range(n)))


class FakeAdapter:
    def __init__(self):
        train = LearnerEvents('train', 1, (KTEvent('train', 'A', 1, 1, 1, 0, 1),))
        self.encoding = fit_vocabulary([train])
        self.config = SimpleNamespace(context=100, target_block=100)
        self.run_identity = {'source': 'pinned', 'checkpoint': 'synthetic'}

    def predict(self, inputs):
        return np.full(len(inputs.item_ids), 0.6, dtype=np.float64)


def ready_records(user=None):
    user = user or learner()
    return list(iter_predictions(FakeAdapter(), [user]))


def prediction_root(tmp_path, monkeypatch):
    monkeypatch.setattr(prediction_module, 'PROJECT_ROOT', tmp_path)
    return tmp_path / 'experiments/akt/results/run-001'


def test_iter_predictions_preserves_each_source_row_and_oov_null():
    source = learner()
    records = ready_records(source)
    assert len(records) == 201
    assert [row.source_row for row in records] == [event.source_row for event in source.events]
    assert len({row.source_row for row in records}) == 201
    unseen = records[100]
    assert unseen.prediction is None
    assert unseen.prediction_kind == 'unseen'
    assert unseen.is_fallback is False
    assert unseen.train_support_students == 0
    known = records[101]
    assert known.prediction == pytest.approx(0.6)
    assert known.prediction_kind == 'fitted'
    assert known.train_support_students == 1
    assert known.history_used == 0
    assert known.context_reset is True
    assert (known.user_id, known.exercise, known.time_done, known.correct, known.suggested) == (
        'u', 'A', source.events[101].time_done, source.events[101].correct, source.events[101].suggested)


def test_export_writes_complete_parquet_with_accounted_coverage(tmp_path, monkeypatch):
    source = learner()
    records = ready_records(source)
    output = prediction_root(tmp_path, monkeypatch)
    result = export_predictions(records, output, expected_learners_factory=lambda: iter([source]),
                                identity={'run': 'synthetic'}, shard_rows=50)
    assert result['status'] == 'complete'
    assert result['expected_rows'] == result['prediction_rows'] == 201
    assert result['fitted_rows'] == 200
    assert result['unseen_rows'] == 1
    assert result['output_coverage'] == 1.0
    assert result['fitted_coverage'] == pytest.approx(200 / 201)
    assert len(list(output.glob('part-*.parquet'))) == 5
    with duckdb.connect() as con:
        frame = con.execute('SELECT source_row,prediction,prediction_kind,is_fallback FROM read_parquet(?) ORDER BY source_row',
                             [str(output / 'part-*.parquet')]).fetchdf()
    assert len(frame) == 201 and frame.source_row.is_unique
    assert frame.loc[frame.source_row == 101, 'prediction'].isna().all()
    assert not frame.is_fallback.any()


@pytest.mark.parametrize('mutation', ['duplicate', 'missing', 'extra', 'identity', 'nan'])
def test_export_rejects_row_or_identity_mismatch_without_complete_manifest(tmp_path, monkeypatch, mutation):
    source = learner(n=3, oov=())
    rows = ready_records(source)
    if mutation == 'duplicate':
        rows[1] = rows[0]
    elif mutation == 'missing':
        rows.pop()
    elif mutation == 'extra':
        rows.append(replace(rows[-1], source_row=999))
    elif mutation == 'identity':
        rows[1] = replace(rows[1], exercise='wrong')
    elif mutation == 'nan':
        rows[1] = replace(rows[1], prediction=float('nan'))
    output = prediction_root(tmp_path, monkeypatch)
    with pytest.raises((ValueError, RuntimeError)):
        export_predictions(rows, output, expected_learners_factory=lambda: iter([source]),
                           identity={'run': 'invalid'}, shard_rows=2)
    manifest = output / 'manifest.json'
    assert not manifest.exists() or json.loads(manifest.read_text(encoding='utf-8'))['status'] != 'complete'


def test_export_resumes_completed_users_once_and_rejects_changed_identity(tmp_path, monkeypatch):
    first = learner('a', n=3, oov=(), offset=10)
    second = learner('b', n=3, oov=(), offset=20)
    full = ready_records(first) + ready_records(second)
    output = prediction_root(tmp_path, monkeypatch)

    def interrupted():
        yield from full[:4]
        raise RuntimeError('synthetic interruption')

    with pytest.raises(RuntimeError, match='interruption'):
        export_predictions(interrupted(), output,
                           expected_learners_factory=lambda: iter([first, second]),
                           identity={'run': 'resume'}, shard_rows=2)
    result = export_predictions(full, output,
                               expected_learners_factory=lambda: iter([first, second]),
                               identity={'run': 'resume'}, shard_rows=2)
    assert result['status'] == 'complete' and result['prediction_rows'] == 6
    with duckdb.connect() as con:
        count, distinct_count = con.execute(
            'SELECT count(*), count(DISTINCT source_row) FROM read_parquet(?)',
            [str(output / 'part-*.parquet')]).fetchone()
    assert count == distinct_count == 6

    with pytest.raises(ValueError, match='identity'):
        export_predictions(full, output, expected_learners_factory=lambda: iter([first, second]),
                           identity={'run': 'changed'}, shard_rows=2)


def test_hash_order_prediction_adapter_preserves_membership_and_chronology():
    cohort = (
        learner('a', n=201, oov=(100, 150), fold=1, offset=0),
        learner('c', n=3, oov=(), fold=2, offset=1000),
        learner('b', n=3, oov=(1,), fold=3, offset=2000),
    )

    def reopened_cohort():
        return iter(cohort)

    first_open = tuple(reopened_cohort())
    second_open = tuple(reopened_cohort())
    assert first_open == second_open
    ordered = prediction_module.order_prediction_learners(first_open)
    assert [user.user_id for user in first_open] == ['a', 'c', 'b']
    assert [user.user_id for user in ordered] == ['a', 'b', 'c']
    assert {user.user_id for user in ordered} == {user.user_id for user in first_open}
    assert all(after.events is before.events for before, after in zip(
        sorted(first_open, key=lambda user: user.user_id), ordered))
    assert all([(event.time_done, event.source_row) for event in user.events] == sorted(
        (event.time_done, event.source_row) for event in user.events) for user in ordered)


def test_ordered_hash_prediction_export_aligns_different_expected_order_and_oov(tmp_path, monkeypatch):
    hash_cohort = (
        learner('a', n=201, oov=(100, 150), fold=1, offset=0),
        learner('c', n=3, oov=(), fold=2, offset=1000),
        learner('b', n=3, oov=(1,), fold=3, offset=2000),
    )
    prediction_users = prediction_module.order_prediction_learners(hash_cohort)
    assert [user.user_id for user in prediction_users] == ['a', 'b', 'c']
    assert [user.user_id for user in hash_cohort] == ['a', 'c', 'b']
    output = prediction_root(tmp_path, monkeypatch)
    result = export_predictions(
        iter_predictions(FakeAdapter(), prediction_users), output,
        expected_learners_factory=lambda: iter(hash_cohort),
        identity={'run': 'hash-cohort-adapter'}, shard_rows=50)
    assert result['status'] == 'complete'
    assert result['expected_rows'] == result['prediction_rows'] == 207
    assert result['fitted_rows'] == 204 and result['unseen_rows'] == 3
    assert result['output_coverage'] == 1.0
    assert sum(shard['user_id'] == 'a' for shard in result['shards']) == 5
    expected = {event.source_row: (event.user_id, event.exercise, event.time_done,
                                   event.correct, event.suggested, event.fold)
                for user in hash_cohort for event in user.events}
    with duckdb.connect() as con:
        rows = con.execute('SELECT source_row,user_id,exercise,time_done,correct,suggested,fold, '
                           'prediction_kind,prediction FROM read_parquet(?) ORDER BY source_row',
                           [str(output / 'part-*.parquet')]).fetchall()
    assert len(rows) == len(expected) and len({row[0] for row in rows}) == len(expected)
    assert {row[0] for row in rows} == set(expected)
    assert all(tuple(row[1:7]) == expected[row[0]] for row in rows)
    assert sum(row[7] == 'unseen' and row[8] is None for row in rows) == 3


def test_unsorted_hash_export_keeps_partial_manifest_incomplete(tmp_path, monkeypatch):
    hash_cohort = (
        learner('a', n=201, oov=(100,), fold=1, offset=0),
        learner('c', n=3, oov=(), fold=2, offset=1000),
        learner('b', n=3, oov=(), fold=3, offset=2000),
    )
    output = prediction_root(tmp_path, monkeypatch)
    identity = {'run': 'partial-order-failure'}
    with pytest.raises(ValueError, match='sorted by user_id'):
        export_predictions(iter_predictions(FakeAdapter(), hash_cohort), output,
                           expected_learners_factory=lambda: iter(hash_cohort),
                           identity=identity, shard_rows=50)
    manifest_path = output / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert manifest['status'] == 'incomplete'
    assert manifest['prediction_rows'] == 201
    assert 'expected_rows' not in manifest
    with pytest.raises(ValueError, match='alignment failed'):
        export_predictions(iter(()), output,
                           expected_learners_factory=lambda: iter(hash_cohort),
                           identity=identity, shard_rows=50)
    assert json.loads(manifest_path.read_text(encoding='utf-8'))['status'] == 'incomplete'
