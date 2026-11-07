"""Kiểm aggregates tổng hợp; không loader, simulator, model hoặc dataset thật."""

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

import pytest

from scripts.research import analyze_rq2_controls as analysis


def factorial_fixture():
    seeds, profiles = [1, 2, 3], ['PG', 'PY', 'PYH']
    effects = {'PG': [0, 0, 0], 'PY': [.1, .2, -.3], 'PYH': [.2, -.1, .5]}
    rows = []
    for index, seed in enumerate(seeds):
        for profile in profiles:
            off = [.2, .3, -.2][index]
            rows.append({'seed': seed, 'profile': profile, 'graph_effect_mechanism_on': off + effects[profile][index],
                         'graph_effect_mechanism_off': off, 'interaction_contrast': effects[profile][index]})
    summary = {profile: {'paired_seeds': 3, 'mean_interaction': math.fsum(effects[profile]) / 3}
               for profile in profiles}
    followup = {'initial_min_ability_in_pilot': {'PG': 1200., 'PY': 900., 'PYH': 950.},
                'mechanism_coverage': {profile: {'events': 100, 'positive_deficit': exposed}
                                       for profile, exposed in zip(profiles, [0, 80, 50])}}
    return rows, summary, followup, seeds, profiles


def factorial(rows=None, summary=None, followup=None):
    original, original_summary, original_followup, seeds, profiles = factorial_fixture()
    return analysis.factorial_conditions(rows if rows is not None else original,
        summary if summary is not None else original_summary,
        followup if followup is not None else original_followup, seeds=seeds, profiles=profiles)


def test_profile_moderation_uses_seed_pairs_and_all_leave_one_out_blocks():
    result = factorial()
    assert len(result['paired_profile_contrasts']) == 3
    contrast = next(row for row in result['paired_profile_contrasts'] if row['contrast'] == 'I(PYH)-I(PY)')
    assert contrast['mean'] == pytest.approx(.2)
    assert [row['value'] for row in contrast['seed_values']] == pytest.approx([.1, -.3, .8])
    assert [row['omitted_seed'] for row in contrast['leave_one_seed_out']] == [1, 2, 3]
    assert [row['mean'] for row in contrast['leave_one_seed_out']] == pytest.approx([.25, .45, -.1])
    assert contrast['loo_min'] < 0 < contrast['loo_max']
    assert contrast['signs'] == {'positive': 2, 'negative': 1, 'arithmetic_zero': 0}


def test_zero_interaction_and_zero_exposure_do_not_zero_graph_effect_components():
    pg = factorial()['profiles'][0]
    assert pg['mean_lambda_edge_interaction'] == 0
    assert pg['graph_effect_lambda0'] == pytest.approx(.1)
    assert pg['graph_effect_lambda055'] == pytest.approx(.1)
    assert pg['pooled_mechanism_exposure_fraction'] == 0
    assert pg['seed_blocks'] == 3 and pg['mechanism_event_denominator'] == 100
    assert pg['mechanism_exposure_joined_to_seed_effects'] is False


@pytest.mark.parametrize('change', ['duplicate', 'missing', 'foreign', 'interaction', 'nan', 'boolean_seed'])
def test_factorial_rejects_unpaired_or_invalid_aggregate_grid(change):
    rows, summary, followup, _, _ = factorial_fixture()
    if change == 'duplicate':
        rows[-1] = deepcopy(rows[0])
    elif change == 'missing':
        rows.pop()
    elif change == 'foreign':
        rows[0]['seed'] = 4
    elif change == 'interaction':
        rows[0]['interaction_contrast'] = 1
    elif change == 'nan':
        rows[0]['graph_effect_mechanism_on'] = float('nan')
    else:
        rows[0]['seed'] = True
    with pytest.raises(ValueError):
        factorial(rows, summary, followup)


@pytest.mark.parametrize('change', ['summary', 'events', 'exposed', 'count_bool'])
def test_factorial_rejects_bad_sample_size_or_exposure_denominator(change):
    rows, summary, followup, _, _ = factorial_fixture()
    if change == 'summary':
        summary['PY']['paired_seeds'] = 30
    else:
        followup['mechanism_coverage']['PY'][{'events': 'events', 'exposed': 'positive_deficit',
                                             'count_bool': 'events'}[change]] = {'events': 0, 'exposed': 101,
                                                                                'count_bool': True}[change]
    with pytest.raises(ValueError):
        factorial(rows, summary, followup)


def order_fixture(edges):
    return {'learners': 4, 'events': 20, 'exercise_learner_support': dict.fromkeys('abcd', 4),
            'edges': [{'parent': a, 'child': b, 'coobserved_learners': n,
                       'parent_first_count': before, 'child_first_count': n - before,
                       'parent_first_fraction': before / n if n else None}
                      for a, b, n, before in edges]}


def test_pair_denominator_can_reverse_numerator_only_interpretation():
    base = order_fixture([('a', 'c', 2, 2), ('b', 'd', 0, 0)])
    control = order_fixture([('a', 'd', 1, 0), ('b', 'c', 3, 3)])
    value = analysis.compare_graph_edges(analysis.edge_table(base), control,
                                         {('a', 'c'), ('b', 'd')}, {('a', 'd'), ('b', 'c')})
    assert value['delta_parent_first_pairs'] == 1
    assert value['delta_pair_denominator'] == 2
    assert value['delta_pair_weighted_fraction'] == pytest.approx(-.25)
    assert value['shared']['pair_weighted_parent_first_fraction'] is None
    assert value['removed']['coobserved_edge_learner_pairs'] == 2
    assert value['added']['coobserved_edge_learner_pairs'] == 4
    assert value['changed_entries_with_globally_observed_endpoints'] == 4
    assert value['changed_entries_coobserved_same_learner'] == 3


def test_unsupported_edge_remains_none_and_same_edge_counts_are_checked():
    order = order_fixture([('a', 'c', 0, 0), ('b', 'd', 1, 1)])
    table = analysis.edge_table(order)
    output = analysis.compare_graph_edges(table, order, set(table), set(table))
    assert output['delta_pair_weighted_fraction'] == 0
    assert output['removed']['edges'] == 0
    assert analysis.edge_summary(table, {('a', 'c')})['pair_weighted_parent_first_fraction'] is None
    changed = deepcopy(order)
    changed['edges'][1]['parent_first_count'] = 0
    changed['edges'][1]['child_first_count'] = 1
    changed['edges'][1]['parent_first_fraction'] = 0
    with pytest.raises(ValueError, match='same edge'):
        analysis.compare_graph_edges(table, changed, set(table), set(table))


@pytest.mark.parametrize('change', ['duplicate', 'counts', 'unsupported_fraction', 'degree'])
def test_edge_summary_rejects_invalid_counts_or_unmatched_controls(change):
    order = order_fixture([('a', 'c', 0, 0), ('b', 'd', 1, 1)])
    if change == 'duplicate':
        order['edges'].append(deepcopy(order['edges'][0]))
    elif change == 'counts':
        order['edges'][1]['child_first_count'] = 1
    elif change == 'unsupported_fraction':
        order['edges'][0]['parent_first_fraction'] = 0
    else:
        with pytest.raises(ValueError, match='degree'):
            analysis.compare_graph_edges(analysis.edge_table(order), order,
                                         {('a', 'd'), ('c', 'b')}, {('a', 'c'), ('b', 'd')})
        return
    with pytest.raises(ValueError):
        analysis.edge_table(order)


def population(learners, before, after):
    sides = [{'observed_prior_fraction': prior, 'observed_later_fraction': .1,
              'timestamp_tie_fraction': 0., 'unobserved_parent_fraction': .9 - prior}
             for prior in (before, after)]
    changes = {}
    for key in analysis.CATEGORIES:
        delta = sides[1][key] - sides[0][key]
        changes[key] = {'mean': delta, 'min': delta, 'max': delta,
                        'positive_learners': learners if delta > 1e-15 else 0,
                        'negative_learners': learners if delta < -1e-15 else 0,
                        'unchanged_learners': learners if abs(delta) <= 1e-15 else 0}
    return {'learners': learners, 'base': sides[0], 'control': sides[1], 'paired_control_minus_base': changes}


def common_fixture():
    contrast = {'cohort_learners': 3, 'eligible_learners': 2, 'excluded_no_incoming_child': 1,
                'fixed_child_opportunities': 4, 'common_coobserved_child_opportunities': 1,
                'changed_parent_child_opportunities': 2, 'common_opportunity_retained_fraction': .25,
                'all_fixed_opportunities': population(2, .2, .3),
                'common_coobserved_opportunities': population(1, .8, .75)}
    identity = deepcopy(contrast)
    identity.update(changed_parent_child_opportunities=0,
                    all_fixed_opportunities=population(2, .2, .2),
                    common_coobserved_opportunities=population(1, .8, .8))
    return {'comparisons': [{'seed': 0, 'status': 'analyzed', 'graph_sha256': 'fixture', 'contrast': contrast}],
            'identity_negative_control': identity}


def test_common_population_retains_its_denominator_and_can_change_sign():
    value = analysis.common_population_sensitivity(common_fixture())[0]
    assert value['common_opportunity_retained_fraction'] == .25
    assert value['common_learner_retained_fraction'] == .5
    assert value['eligible_cohort_fraction'] == pytest.approx(2 / 3)
    assert value['all_fixed']['categories']['observed_prior_fraction']['delta_control_minus_base'] == pytest.approx(.1)
    assert value['common_coobserved']['categories']['observed_prior_fraction']['delta_control_minus_base'] == pytest.approx(-.05)
    assert value['learner_loo_available'] is False


@pytest.mark.parametrize('change', ['attrition', 'category_mass', 'paired_mean', 'sign_count', 'identity'])
def test_common_population_rejects_bad_denominators_or_nonzero_identity(change):
    source = common_fixture()
    contrast = source['comparisons'][0]['contrast']
    if change == 'attrition':
        contrast['common_opportunity_retained_fraction'] = .5
    elif change == 'category_mass':
        contrast['all_fixed_opportunities']['base']['observed_prior_fraction'] = .8
    elif change == 'paired_mean':
        contrast['all_fixed_opportunities']['paired_control_minus_base']['observed_prior_fraction']['mean'] = 0
    elif change == 'sign_count':
        contrast['all_fixed_opportunities']['paired_control_minus_base']['observed_prior_fraction']['positive_learners'] = 20
    else:
        source['identity_negative_control']['all_fixed_opportunities'] = population(2, .2, .3)
    with pytest.raises(ValueError):
        analysis.common_population_sensitivity(source)


def source_repository(tmp_path):
    for run, files in analysis.ALLOWED_OUTPUTS.items():
        directory = tmp_path / 'research_tracking/runs' / run
        directory.mkdir(parents=True)
        outputs = {}
        for name in files:
            path = directory / name
            path.write_text('{}', encoding='utf-8')
            outputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if run.startswith('cpu-factorial'):
            path = directory / 'README.md'
            path.write_text('Synthetic metadata', encoding='utf-8')
            outputs['README.md'] = hashlib.sha256(path.read_bytes()).hexdigest()
        order = tmp_path / 'src/knowledge_tracing/gam_kt/practice_order.py'
        order.parent.mkdir(parents=True, exist_ok=True)
        order.write_text('# synthetic definitions', encoding='utf-8')
        (directory / 'manifest.json').write_text(json.dumps({'status': 'completed', 'outputs_sha256': outputs,
            'sources_sha256': {'src/knowledge_tracing/gam_kt/practice_order.py': hashlib.sha256(order.read_bytes()).hexdigest()}}), encoding='utf-8')
    followup = tmp_path / 'research_tracking/reports/cpu_pilot_followup_20261107.json'
    followup.parent.mkdir(parents=True)
    followup.write_text('{}', encoding='utf-8')
    archive = tmp_path / 'research_tracking/runs/parallel-graph-diagnostics-20261107-01'
    archive.mkdir()
    (archive / 'manifest.json').write_text(json.dumps({'status': 'completed', 'outputs_sha256':
        {'input_mechanism_followup.json': hashlib.sha256(followup.read_bytes()).hexdigest()}}), encoding='utf-8')
    return followup


def test_source_reader_only_opens_selected_aggregate_and_metadata_paths(tmp_path, monkeypatch):
    source_repository(tmp_path)
    opened = []
    real_read = Path.read_bytes
    def tracked(path):
        opened.append(path.relative_to(tmp_path).as_posix())
        assert not any(word in str(path) for word in ('outcomes.json', 'traces.jsonl', 'dataset', 'parquet'))
        return real_read(path)
    monkeypatch.setattr(Path, 'read_bytes', tracked)
    _, _, inventory = analysis.load_inputs(tmp_path)
    assert set(inventory) == set(opened)
    assert len(inventory) == 13


@pytest.mark.parametrize('which', ['aggregate', 'followup'])
def test_source_reader_fails_closed_on_selected_hash_mismatch(tmp_path, which):
    followup = source_repository(tmp_path)
    target = followup if which == 'followup' else tmp_path / 'research_tracking/runs/cpu-factorial-20261107-01/contrasts.json'
    target.write_text('{"changed":true}', encoding='utf-8')
    with pytest.raises(ValueError, match='SHA|bytes'):
        analysis.load_inputs(tmp_path)
