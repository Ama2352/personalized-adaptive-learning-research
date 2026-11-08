import duckdb
import numpy as np
import pandas as pd
import pytest

from knowledge_tracing.akt.evaluation import (compare_common_rows, paired_stats_for_comparison,
                                               score_akt_shards)
from knowledge_tracing.paired_bootstrap import fold_differences


def parquet(path, rows):
    frame = pd.DataFrame(rows)
    with duckdb.connect() as con:
        con.register('frame', frame)
        con.execute(f"COPY frame TO '{str(path).replace(chr(39), chr(39)*2)}' (FORMAT PARQUET)")


def akt_rows():
    return [
        {'source_row': 1, 'user_id': 'u1', 'exercise': 'A', 'time_done': 1, 'correct': 0, 'suggested': 0,
         'fold': 0, 'prediction': 0.0, 'prediction_kind': 'fitted', 'is_fallback': False, 'train_support_students': 2},
        {'source_row': 2, 'user_id': 'u1', 'exercise': 'A', 'time_done': 2, 'correct': 1, 'suggested': 1,
         'fold': 0, 'prediction': 0.5, 'prediction_kind': 'fitted', 'is_fallback': False, 'train_support_students': 2},
        {'source_row': 3, 'user_id': 'u2', 'exercise': 'B', 'time_done': 3, 'correct': 1, 'suggested': 0,
         'fold': 0, 'prediction': 1.0, 'prediction_kind': 'fitted', 'is_fallback': False, 'train_support_students': 1},
        {'source_row': 4, 'user_id': 'u2', 'exercise': 'X', 'time_done': 4, 'correct': 0, 'suggested': 0,
         'fold': 0, 'prediction': None, 'prediction_kind': 'unseen', 'is_fallback': False, 'train_support_students': 0},
    ]


def test_akt_metrics_keep_unseen_out_of_fitted_denominator_and_handle_auc_one_class(tmp_path):
    path = tmp_path / 'akt.parquet'
    parquet(path, akt_rows())
    result = score_akt_shards(str(path))
    assert result['native']['rows'] == 3
    assert result['native']['metrics']['accuracy'] == pytest.approx(1.0)
    assert result['native']['metrics']['auc'] == pytest.approx(1.0)
    assert result['coverage']['expected_rows'] == 4
    assert result['coverage']['fitted_rows'] == 3
    assert result['coverage']['unseen_rows'] == 1
    assert result['coverage']['is_fallback_rows'] == 0


def test_auc_is_null_for_one_class_and_accuracy_uses_probability_half_threshold(tmp_path):
    rows = akt_rows()[:3]
    rows[1]['correct'] = rows[2]['correct'] = 0
    path = tmp_path / 'one-class.parquet'
    parquet(path, rows)
    result = score_akt_shards(str(path))
    assert result['native']['metrics']['auc'] is None
    assert result['native']['metrics']['accuracy'] == pytest.approx(1 / 3)
    assert result['native']['metrics']['ece'] == pytest.approx(0.5)


@pytest.mark.parametrize('bad', [None, float('nan'), float('inf'), -0.01, 1.01])
def test_known_missing_or_invalid_probability_fails(tmp_path, bad):
    rows = akt_rows()
    rows[0]['prediction'] = bad
    path = tmp_path / 'bad.parquet'
    parquet(path, rows)
    with pytest.raises(ValueError):
        score_akt_shards(str(path))


def benchmark_sides():
    akt = akt_rows()
    bkt = []
    gam = []
    for row in akt:
        bkt.append({key: row[key] for key in ('source_row', 'user_id', 'exercise', 'correct', 'suggested')} | {
            'prediction': [0.1, 0.8, None, None][row['source_row']-1],
            'train_skill_students': 2 if row['source_row'] <= 2 else 0})
        gam.append({key: row[key] for key in ('source_row', 'user_id', 'exercise', 'correct', 'suggested')} | {
            'prediction': [0.2, 0.7, 0.9, 0.3][row['source_row']-1],
            'train_support_students': 2 if row['source_row'] <= 3 else 0,
            'is_fallback': row['source_row'] == 4})
    return akt, bkt, gam


def test_intersection_recomputes_every_model_on_exact_common_rows(tmp_path):
    akt, bkt, gam = benchmark_sides()
    paths = [tmp_path / f'{name}.parquet' for name in ('akt', 'bkt', 'gam')]
    for path, rows in zip(paths, (akt, bkt, gam)):
        parquet(path, rows)
    result = compare_common_rows(*(str(path) for path in paths))
    assert result['expected_rows'] == 4
    assert result['common_rows'] == 2
    assert result['attrition'] == {'akt_fitted': 3, 'bkt_fitted': 2, 'gam_fitted': 3}
    assert result['pair_rows'] == {'akt_vs_bkt': 2, 'akt_vs_gam': 3, 'bkt_vs_gam': 2}
    assert result['pair_metrics']['akt_vs_gam']['rows'] == 3
    assert set(result['pair_metrics']['akt_vs_gam']['models']) == {'akt', 'gam'}
    assert result['models']['akt']['rows'] == result['models']['bkt']['rows'] == result['models']['gam']['rows'] == 2
    assert result['models']['akt']['metrics']['log_loss'] == pytest.approx(
        -np.log(0.5) / 2)


@pytest.mark.parametrize('mutation', ['duplicate', 'identity'])
def test_common_comparison_rejects_duplicates_or_identity_mismatch_before_join(tmp_path, mutation):
    akt, bkt, gam = benchmark_sides()
    if mutation == 'duplicate':
        bkt.append(dict(bkt[0]))
    else:
        gam[0]['exercise'] = 'other'
    paths = [tmp_path / f'{name}.parquet' for name in ('akt', 'bkt', 'gam')]
    for path, rows in zip(paths, (akt, bkt, gam)):
        parquet(path, rows)
    with pytest.raises(ValueError):
        compare_common_rows(*(str(path) for path in paths))


def test_paired_sufficient_stats_map_candidate_minus_reference_and_match_direct_resampling():
    rows = [
        ('u1', 0, 0.1, 0.2), ('u1', 1, 0.8, 0.7),
        ('u2', 0, 0.4, 0.3), ('u2', 1, 0.6, 0.9),
    ]
    with duckdb.connect() as con:
        con.execute('CREATE TABLE common_rows(user_id VARCHAR, correct INTEGER, bkt_prediction DOUBLE, akt_prediction DOUBLE, gam_prediction DOUBLE)')
        con.executemany('INSERT INTO common_rows VALUES (?, ?, ?, ?, ?)',
                        [(user, y, reference, candidate, candidate) for user, y, reference, candidate in rows])
        stats = paired_stats_for_comparison(con, 'common_rows', reference='bkt', candidate='akt')
    assert stats.reference_name == 'bkt'
    assert stats.candidate_name == 'akt'
    multiplicities = np.array([2, 1])
    paired = fold_differences(stats, multiplicities)
    expanded = [row for row in rows for count in [multiplicities[int(row[0][-1])-1]] for _ in range(count)]
    labels = np.asarray([row[1] for row in expanded])
    reference = np.asarray([row[2] for row in expanded])
    candidate = np.asarray([row[3] for row in expanded])
    def ece(probability):
        bins = np.minimum((probability * 15).astype(int), 14)
        return sum(np.mean(bins == b) * abs(labels[bins == b].mean() - probability[bins == b].mean())
                   for b in range(15) if np.any(bins == b))
    direct = {
        'log_loss': np.mean(-(labels*np.log(candidate)+(1-labels)*np.log(1-candidate)))
                     - np.mean(-(labels*np.log(reference)+(1-labels)*np.log(1-reference))),
        'brier': np.mean((candidate-labels)**2) - np.mean((reference-labels)**2),
        'ece': ece(candidate) - ece(reference),
        'accuracy': np.mean((candidate >= .5) == labels) - np.mean((reference >= .5) == labels),
    }
    for metric in direct:
        assert paired[metric] == pytest.approx(direct[metric])


def test_paired_stats_rejects_unapproved_identifiers():
    with duckdb.connect() as con, pytest.raises(ValueError):
        paired_stats_for_comparison(con, 'common_rows; DROP TABLE x', reference='bkt', candidate='akt')
