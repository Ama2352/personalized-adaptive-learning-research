"""AKT native coverage, matched rows, and paired learner sufficient statistics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import psutil

from knowledge_tracing.gam_kt.evaluation import score_frame
from knowledge_tracing.paired_bootstrap import PairedFoldSufficientStats


_MODEL_COLUMNS = {'akt': 'akt_prediction', 'bkt': 'bkt_prediction', 'gam': 'gam_prediction'}
_IDENTITY = ('user_id', 'exercise', 'correct', 'suggested')
_ECE_BINS = 15


@dataclass(frozen=True)
class NamedPairedFoldStats(PairedFoldSufficientStats):
    """Legacy `_bkt` fields store reference; `_gam` fields store candidate."""

    reference_name: str
    candidate_name: str


def _path_literal(path: str) -> str:
    return "'" + str(Path(path).resolve()).replace("'", "''") + "'"


def _columns(con, relation: str) -> set[str]:
    return {row[0] for row in con.execute(f'DESCRIBE SELECT * FROM {relation}').fetchall()}


def _create_view(con, name: str, path: str) -> None:
    if name not in {'akt_source', 'bkt_source', 'gam_source'}:
        raise ValueError('unapproved source relation')
    con.execute(f'CREATE VIEW {name} AS SELECT * FROM read_parquet({_path_literal(path)})')


def _require_columns(con, relation: str, required: set[str]) -> set[str]:
    available = _columns(con, relation)
    missing = required - available
    if missing:
        raise ValueError(f'{relation} is missing required fields: {sorted(missing)}')
    return available


def _validate_common_schema(con, relation: str, *, akt: bool) -> dict:
    required = {'source_row', *_IDENTITY}
    if akt:
        required |= {'fold', 'prediction', 'prediction_kind', 'is_fallback', 'train_support_students'}
    else:
        required |= {'prediction', 'train_support_students' if relation == 'gam_source' else 'train_skill_students'}
        if relation == 'gam_source':
            required.add('is_fallback')
    fields = _require_columns(con, relation, required)
    if con.execute(f'SELECT count(*) FROM {relation}').fetchone()[0] == 0:
        raise ValueError(f'{relation} is empty')
    rows, unique_rows = con.execute(
        f'SELECT count(*), count(DISTINCT source_row) FROM {relation}').fetchone()
    if rows != unique_rows:
        raise ValueError(f'duplicate source_row in {relation}')
    nulls = con.execute(f'SELECT count(*) FROM {relation} WHERE source_row IS NULL OR '
                        'user_id IS NULL OR exercise IS NULL OR correct IS NULL OR suggested IS NULL').fetchone()[0]
    if nulls:
        raise ValueError(f'null identity in {relation}')
    invalid_binary = con.execute(
        f'SELECT count(*) FROM {relation} WHERE correct NOT IN (0,1) OR suggested NOT IN (0,1)').fetchone()[0]
    if invalid_binary:
        raise ValueError(f'invalid target identity in {relation}')
    invalid_source = con.execute(f'SELECT count(*) FROM {relation} WHERE source_row<=0').fetchone()[0]
    if invalid_source:
        raise ValueError(f'invalid source_row in {relation}')
    if 'time_done' in fields:
        invalid_time = con.execute(f'SELECT count(*) FROM {relation} WHERE time_done IS NULL').fetchone()[0]
        if invalid_time:
            raise ValueError(f'null time identity in {relation}')
    return {'rows': int(rows), 'fields': fields}


def _validate_akt(con, relation: str = 'akt_source') -> dict:
    summary = _validate_common_schema(con, relation, akt=True)
    invalid_fold = con.execute(
        f'SELECT count(*) FROM {relation} WHERE fold IS NULL OR fold NOT BETWEEN 0 AND 4').fetchone()[0]
    if invalid_fold:
        raise ValueError('AKT fold identity is invalid')
    counts = con.execute(
        f"SELECT count(*) FILTER(WHERE prediction_kind='fitted'), "
        f"count(*) FILTER(WHERE prediction_kind='unseen'), "
        f"count(*) FILTER(WHERE is_fallback), "
        f"count(*) FILTER(WHERE prediction_kind NOT IN ('fitted','unseen') OR prediction_kind IS NULL), "
        f"count(*) FILTER(WHERE prediction_kind='fitted' AND "
        f"(prediction IS NULL OR NOT isfinite(prediction) OR prediction<0 OR prediction>1 "
        f"OR train_support_students IS NULL OR train_support_students<=0)), "
        f"count(*) FILTER(WHERE prediction_kind='unseen' AND "
        f"(prediction IS NOT NULL OR train_support_students IS NULL OR train_support_students<>0)), "
        f"count(*) FILTER(WHERE is_fallback IS NULL OR train_support_students IS NULL OR train_support_students<0) "
        f"FROM {relation}").fetchone()
    fitted, unseen, fallback, unknown, bad_fitted, bad_unseen, bad_meta = map(int, counts)
    if fallback or unknown or bad_fitted or bad_unseen or bad_meta or fitted + unseen != summary['rows']:
        raise ValueError(f'invalid AKT prediction coverage: fitted={fitted}, unseen={unseen}, fallback={fallback}')
    summary.update({'fitted_rows': fitted, 'unseen_rows': unseen, 'is_fallback_rows': fallback})
    return summary


def _score_relation(con, relation: str, *, prediction_column: str = 'prediction') -> dict:
    count = int(con.execute(f'SELECT count(*) FROM {relation}').fetchone()[0])
    if not count:
        raise ValueError('no finite fitted rows to score')
    # Exact AUC requires materializing numeric vectors. Refuse before allocation without headroom.
    estimated = count * 512
    if estimated > psutil.virtual_memory().available * 0.6:
        raise MemoryError('exact AUC scoring blocked: insufficient memory for exact metric vectors')
    frame = con.execute(
        f'SELECT correct,prediction AS prediction,suggested,exercise,is_fallback,train_support_students '
        f'FROM {relation}').fetchdf()
    if prediction_column != 'prediction':
        frame = frame.rename(columns={prediction_column: 'prediction'})
    return score_frame(frame)


def score_akt_shards(prediction_glob: str) -> dict:
    with duckdb.connect(config={'memory_limit': '512MB', 'threads': '2'}) as con:
        _create_view(con, 'akt_source', prediction_glob)
        summary = _validate_akt(con)
        con.execute("CREATE VIEW akt_fitted AS SELECT * FROM akt_source WHERE prediction_kind='fitted'")
        metrics = _score_relation(con, 'akt_fitted')
        expected = summary['rows']
        return {
            'native': metrics['native'], 'supported': metrics['supported'],
            'coverage': {
                'expected_rows': expected, 'prediction_rows': expected,
                'fitted_rows': summary['fitted_rows'], 'unseen_rows': summary['unseen_rows'],
                'is_fallback_rows': summary['is_fallback_rows'],
                'output_coverage': 1.0,
                'fitted_coverage': summary['fitted_rows'] / expected,
            },
            'definitions': metrics['definitions'],
        }


def _check_side_identity(con, relation: str, reference: str, *, include_time: bool) -> int:
    keys = list(_IDENTITY) + (['time_done'] if include_time else [])
    conditions = ' OR '.join(f'{relation}.{key} IS DISTINCT FROM {reference}.{key}' for key in keys)
    mismatches = con.execute(
        f'SELECT count(*) FROM {reference} JOIN {relation} USING(source_row) WHERE {conditions}').fetchone()[0]
    if mismatches:
        raise ValueError(f'identity mismatch between {reference} and {relation}')
    missing = con.execute(
        f'SELECT count(*) FROM {reference} LEFT JOIN {relation} USING(source_row) WHERE {relation}.source_row IS NULL').fetchone()[0]
    extra = con.execute(
        f'SELECT count(*) FROM {relation} LEFT JOIN {reference} USING(source_row) WHERE {reference}.source_row IS NULL').fetchone()[0]
    if missing or extra:
        raise ValueError(f'row population mismatch between {reference} and {relation}: missing={missing}, extra={extra}')
    return int(mismatches)


def compare_common_rows(akt_glob: str, bkt_glob: str, gam_glob: str) -> dict:
    with duckdb.connect(config={'memory_limit': '512MB', 'threads': '2'}) as con:
        _create_view(con, 'akt_source', akt_glob)
        _create_view(con, 'bkt_source', bkt_glob)
        _create_view(con, 'gam_source', gam_glob)
        akt = _validate_akt(con)
        bkt = _validate_common_schema(con, 'bkt_source', akt=False)
        gam = _validate_common_schema(con, 'gam_source', akt=False)
        if bkt['fields'] and 'train_skill_students' in bkt['fields']:
            bkt_support = 'train_skill_students'
        else:
            raise ValueError('BKT support column missing')
        if 'is_fallback' not in gam['fields'] or 'train_support_students' not in gam['fields']:
            raise ValueError('GAM fallback/support fields missing')
        if len({akt['rows'], bkt['rows'], gam['rows']}) != 1:
            raise ValueError('model row populations differ')
        all_times = all('time_done' in value['fields'] for value in (akt, bkt, gam))
        _check_side_identity(con, 'bkt_source', 'akt_source', include_time=all_times)
        _check_side_identity(con, 'gam_source', 'akt_source', include_time=all_times)
        for relation, support, is_gam in (('bkt_source', bkt_support, False),
                                          ('gam_source', 'train_support_students', True)):
            fallback = 'is_fallback' if is_gam else 'FALSE'
            unsupported_invalid = (f'({support}=0 AND NOT ({fallback}))' if is_gam
                                   else f'({support}=0 AND prediction IS NOT NULL)')
            fallback_invalid = f'{fallback} IS NULL OR ' if is_gam else ''
            bad = con.execute(
                f'SELECT count(*) FROM {relation} WHERE '
                f'({fallback_invalid}{support} IS NULL OR {support}<0) OR '
                f'(NOT ({fallback}) AND {support}>0 AND (prediction IS NULL OR NOT isfinite(prediction) '
                f'OR prediction<0 OR prediction>1)) OR '
                f'{unsupported_invalid}').fetchone()[0]
            if bad:
                raise ValueError(f'invalid fitted/support predictions in {relation}')
        con.execute(
            "CREATE VIEW common_rows AS SELECT a.source_row,a.user_id,a.exercise,a.correct,a.suggested,a.fold, "
            "a.prediction AS akt_prediction,b.prediction AS bkt_prediction,g.prediction AS gam_prediction, "
            "a.train_support_students AS akt_support,b.train_skill_students AS bkt_support, "
            "g.train_support_students AS gam_support FROM akt_source a "
            "JOIN bkt_source b USING(source_row) JOIN gam_source g USING(source_row) "
            "WHERE a.prediction_kind='fitted' AND a.prediction IS NOT NULL AND NOT a.is_fallback "
            "AND b.train_skill_students>0 AND b.prediction IS NOT NULL AND isfinite(b.prediction) "
            "AND NOT g.is_fallback AND g.train_support_students>0 AND g.prediction IS NOT NULL "
            "AND isfinite(g.prediction)")
        common = int(con.execute('SELECT count(*) FROM common_rows').fetchone()[0])
        if common == 0:
            raise ValueError('no common fitted rows')
        for model in ('akt', 'bkt', 'gam'):
            column = _MODEL_COLUMNS[model]
            con.execute(f'CREATE VIEW score_{model} AS SELECT correct,{column} AS prediction,suggested,exercise,FALSE AS is_fallback, '
                        f'{model}_support AS train_support_students FROM common_rows')
        metrics = {model: _score_relation(con, f'score_{model}')['native'] for model in ('akt', 'bkt', 'gam')}
        akt_fit = akt['fitted_rows']
        bkt_fit = int(con.execute('SELECT count(*) FROM bkt_source WHERE train_skill_students>0 AND prediction IS NOT NULL AND isfinite(prediction)').fetchone()[0])
        gam_fit = int(con.execute('SELECT count(*) FROM gam_source WHERE NOT is_fallback AND train_support_students>0 AND prediction IS NOT NULL AND isfinite(prediction)').fetchone()[0])
        pairs = {}
        pair_metrics = {}
        pair_predicate = {
            'akt': "a.prediction_kind='fitted' AND a.prediction IS NOT NULL AND NOT a.is_fallback",
            'bkt': 'b.train_skill_students>0 AND b.prediction IS NOT NULL AND isfinite(b.prediction)',
            'gam': 'NOT g.is_fallback AND g.train_support_students>0 AND g.prediction IS NOT NULL AND isfinite(g.prediction)',
        }
        pair_column = {'akt': 'a.prediction', 'bkt': 'b.prediction', 'gam': 'g.prediction'}
        pair_support = {'akt': 'a.train_support_students', 'bkt': 'b.train_skill_students',
                        'gam': 'g.train_support_students'}
        for left, right in (('akt', 'bkt'), ('akt', 'gam'), ('bkt', 'gam')):
            available = pair_predicate
            pair_count = con.execute(
                f'SELECT count(*) FROM akt_source a JOIN bkt_source b USING(source_row) '
                f'JOIN gam_source g USING(source_row) WHERE {available[left]} AND {available[right]}').fetchone()[0]
            pair_name = f'{left}_vs_{right}'
            pairs[pair_name] = int(pair_count)
            model_scores = {}
            for model in (left, right):
                view = f'pair_{left}_{right}_{model}'
                con.execute(
                    f'CREATE VIEW {view} AS SELECT a.correct,a.suggested,a.exercise,'
                    f'{pair_column[model]} AS prediction,FALSE AS is_fallback,'
                    f'{pair_support[model]} AS train_support_students '
                    'FROM akt_source a JOIN bkt_source b USING(source_row) '
                    'JOIN gam_source g USING(source_row) '
                    f'WHERE {available[left]} AND {available[right]}')
                model_scores[model] = _score_relation(con, view)['native']
            pair_metrics[pair_name] = {'rows': int(pair_count), 'models': model_scores}
        folds = con.execute('SELECT count(DISTINCT fold), min(fold), max(fold) FROM akt_source').fetchone()
        if int(folds[0]) != 1:
            raise ValueError('compare_common_rows accepts one fold at a time')
        return {
            'fold': int(folds[1]), 'expected_rows': akt['rows'], 'common_rows': common,
            'attrition': {'akt_fitted': akt_fit, 'bkt_fitted': bkt_fit, 'gam_fitted': gam_fit},
            'pair_rows': pairs, 'pair_metrics': pair_metrics, 'models': metrics,
        }


def paired_stats_for_comparison(connection: duckdb.DuckDBPyConnection, common_view: str, *,
                                reference: str, candidate: str) -> PairedFoldSufficientStats:
    if (common_view != 'common_rows' or reference not in _MODEL_COLUMNS or candidate not in _MODEL_COLUMNS
            or reference == candidate):
        raise ValueError('unapproved common view or model names')
    reference_col = _MODEL_COLUMNS[reference]
    candidate_col = _MODEL_COLUMNS[candidate]
    available = _columns(connection, common_view)
    if not {'user_id', 'correct', reference_col, candidate_col} <= available:
        raise ValueError('common view is missing paired metric columns')
    # Aggregate only user and user-by-bin sufficient statistics; never fetch interaction rows.
    con = connection
    con.execute('DROP TABLE IF EXISTS _paired_source')
    con.execute('CREATE TEMP TABLE _paired_source AS SELECT user_id,correct,'
                f'{reference_col} AS reference_p,{candidate_col} AS candidate_p FROM {common_view} '
                f'WHERE {reference_col} IS NOT NULL AND {candidate_col} IS NOT NULL '
                f'AND isfinite({reference_col}) AND isfinite({candidate_col})')
    bad = con.execute('SELECT count(*) FROM _paired_source WHERE correct NOT IN (0,1) '
                      'OR reference_p<0 OR reference_p>1 OR candidate_p<0 OR candidate_p>1').fetchone()[0]
    if bad:
        con.execute('DROP TABLE _paired_source')
        raise ValueError('invalid paired target or probability')
    eps = np.finfo(np.float64).eps
    base = con.execute(
        'SELECT user_id,count(*) AS n, '
        'sum(-(correct*ln(greatest(reference_p,?))+(1-correct)*ln(greatest(1-reference_p,?)))) AS ll_ref, '
        'sum(-(correct*ln(greatest(candidate_p,?))+(1-correct)*ln(greatest(1-candidate_p,?)))) AS ll_cand, '
        'sum(pow(reference_p-correct,2)) AS brier_ref,sum(pow(candidate_p-correct,2)) AS brier_cand, '
        'sum(CASE WHEN (reference_p>=0.5)= (correct=1) THEN 1 ELSE 0 END) AS correct_ref, '
        'sum(CASE WHEN (candidate_p>=0.5)= (correct=1) THEN 1 ELSE 0 END) AS correct_cand '
        'FROM _paired_source GROUP BY user_id ORDER BY user_id', [eps, eps, eps, eps]).fetchall()
    ref_bins = con.execute(
        'SELECT user_id,floor(least(reference_p*15,14))::INTEGER AS bin,count(*) AS n,'
        'sum(correct-reference_p) AS residual FROM _paired_source GROUP BY user_id,bin').fetchall()
    cand_bins = con.execute(
        'SELECT user_id,floor(least(candidate_p*15,14))::INTEGER AS bin,count(*) AS n,'
        'sum(correct-candidate_p) AS residual FROM _paired_source GROUP BY user_id,bin').fetchall()
    con.execute('DROP TABLE _paired_source')
    if not base:
        raise ValueError('common comparison has no finite paired rows')
    users = [row[0] for row in base]
    index = {user: i for i, user in enumerate(users)}
    n_users = len(users)
    row_count = np.zeros(n_users, dtype=np.int64)
    ll_ref = np.zeros(n_users); ll_cand = np.zeros(n_users)
    brier_ref = np.zeros(n_users); brier_cand = np.zeros(n_users)
    correct_ref = np.zeros(n_users); correct_cand = np.zeros(n_users)
    residual_ref = np.zeros((n_users, _ECE_BINS)); residual_cand = np.zeros_like(residual_ref)
    bins_ref = np.zeros_like(residual_ref, dtype=np.int64); bins_cand = np.zeros_like(bins_ref)
    for user, n, llr, llc, br, bc, cr, cc in base:
        position = index[user]
        row_count[position] = int(n)
        ll_ref[position] = float(llr); ll_cand[position] = float(llc)
        brier_ref[position] = float(br); brier_cand[position] = float(bc)
        correct_ref[position] = float(cr); correct_cand[position] = float(cc)
    for user, bin_id, n, residual in ref_bins:
        position = index[user]; bin_id = int(bin_id)
        residual_ref[position, bin_id] = float(residual); bins_ref[position, bin_id] = int(n)
    for user, bin_id, n, residual in cand_bins:
        position = index[user]; bin_id = int(bin_id)
        residual_cand[position, bin_id] = float(residual); bins_cand[position, bin_id] = int(n)
    return NamedPairedFoldStats(
        user_ids=np.asarray(users), row_count=row_count,
        log_loss_bkt=ll_ref, log_loss_gam=ll_cand,
        brier_bkt=brier_ref, brier_gam=brier_cand,
        correct_bkt=correct_ref, correct_gam=correct_cand,
        ece_residual_bkt=residual_ref, ece_residual_gam=residual_cand,
        ece_count_bkt=bins_ref, ece_count_gam=bins_cand,
        reference_name=reference, candidate_name=candidate)
