"""RQ2 từ aggregates đã lưu: không query rows, chạy model/simulator hay sinh graph."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TOL = 1e-12
CATEGORIES = ('observed_prior_fraction', 'observed_later_fraction',
              'timestamp_tie_fraction', 'unobserved_parent_fraction')
ALLOWED_OUTPUTS = {
    'cpu-factorial-20261107-01': {'contrasts.json', 'summary.json'},
    'cpu-junyi-controls-20261107-02-expanded':
        {'corrected_graph.json', 'matched_controls.json', 'order_summary.json'},
    'cpu-junyi-common-20261107-01': {'common_population.json'},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('expected finite number, not boolean')
    return float(value)


def count(value):
    if type(value) is not int or value < 0:
        raise ValueError('expected nonnegative integer count')
    return value


def close(actual, expected):
    if not math.isclose(number(actual), number(expected), rel_tol=0, abs_tol=TOL):
        raise ValueError('stored aggregate arithmetic mismatch')


def mean(values):
    return math.fsum(values) / len(values)


def signs(values):
    return {'positive': sum(v > TOL for v in values), 'negative': sum(v < -TOL for v in values),
            'arithmetic_zero': sum(abs(v) <= TOL for v in values)}


def factorial_conditions(rows, summary, followup, *, seeds, profiles):
    if (len(seeds) < 2 or any(type(seed) is not int for seed in seeds)
            or any(not isinstance(profile, str) or not profile for profile in profiles)
            or len(set(seeds)) != len(seeds) or len(set(profiles)) != len(profiles)
            or set(summary) != set(profiles)):
        raise ValueError('invalid seed/profile grid')
    expected = {(seed, profile) for seed in seeds for profile in profiles}
    indexed = {}
    for row in rows:
        key = (row['seed'], row['profile'])
        if type(row['seed']) is not int or type(row['profile']) is not str or key not in expected or key in indexed:
            raise ValueError('missing, duplicate or foreign seed/profile')
        on = number(row['graph_effect_mechanism_on'])
        off = number(row['graph_effect_mechanism_off'])
        interaction = number(row['interaction_contrast'])
        close(interaction, on - off)
        indexed[key] = (on, off, interaction)
    if set(indexed) != expected:
        raise ValueError('incomplete paired seed/profile grid')
    conditions = []
    for profile in profiles:
        values = [indexed[seed, profile] for seed in seeds]
        exposure = followup['mechanism_coverage'][profile]
        events, exposed = count(exposure['events']), count(exposure['positive_deficit'])
        if events == 0 or exposed > events or summary[profile]['paired_seeds'] != len(seeds):
            raise ValueError('invalid mechanism coverage or source sample size')
        average = mean([value[2] for value in values])
        close(average, summary[profile]['mean_interaction'])
        conditions.append({'profile': profile, 'seed_blocks': len(seeds),
            'initial_min_ability': number(followup['initial_min_ability_in_pilot'][profile]),
            'mechanism_exposed_events': exposed, 'mechanism_event_denominator': events,
            'pooled_mechanism_exposure_fraction': exposed / events,
            'graph_effect_lambda055': mean([value[0] for value in values]),
            'graph_effect_lambda0': mean([value[1] for value in values]),
            'mean_lambda_edge_interaction': average,
            'interaction_signs': signs([value[2] for value in values]),
            'mechanism_exposure_joined_to_seed_effects': False})
    pairs = []
    for low, high in combinations(profiles, 2):
        values = [indexed[seed, high][2] - indexed[seed, low][2] for seed in seeds]
        loo = [{'omitted_seed': seed, 'mean': mean(values[:index] + values[index + 1:])}
               for index, seed in enumerate(seeds)]
        pairs.append({'contrast': f'I({high})-I({low})', 'seed_blocks': len(seeds),
            'mean': mean(values), 'seed_min': min(values), 'seed_max': max(values),
            'signs': signs(values), 'seed_values': [dict(seed=seed, value=value) for seed, value in zip(seeds, values)],
            'leave_one_seed_out': loo, 'loo_min': min(v['mean'] for v in loo),
            'loo_max': max(v['mean'] for v in loo),
            'scope_vi': 'Descriptive profile moderation; không causal ability effect hoặc formal CI.'})
    return {'profiles': conditions, 'paired_profile_contrasts': pairs,
            'unit_vi': 'Seed block; không pooled events hoặc 30 profile-seed rows độc lập.',
            'estimand': 'I=(edge_on-edge_off)|lambda055-(edge_on-edge_off)|lambda0',
            'seed_exposure_conditioning_available': False}


def edge_table(order):
    learners = count(order['learners'])
    table = {}
    for row in order['edges']:
        edge = (row['parent'], row['child'])
        if (edge in table or any(not isinstance(v, str) or not v for v in edge) or edge[0] == edge[1]):
            raise ValueError('invalid or duplicate stored edge')
        n, before, after = (count(row[key]) for key in
                            ('coobserved_learners', 'parent_first_count', 'child_first_count'))
        if n > learners or before + after != n:
            raise ValueError('invalid edge-learner pair denominator')
        if n:
            close(row['parent_first_fraction'], before / n)
        elif row['parent_first_fraction'] is not None:
            raise ValueError('unsupported edge must not have a finite alignment rate')
        table[edge] = (n, before, after)
    return table


def edge_summary(table, selected):
    if not set(selected).issubset(table):
        raise ValueError('stored order is missing requested frozen edges')
    values = [table[edge] for edge in selected]
    n = sum(value[0] for value in values)
    prior = sum(value[1] for value in values)
    supported = [value for value in values if value[0] > 0]
    return {'edges': len(values), 'supported_edges': len(supported),
            'edge_coverage': len(supported) / len(values) if values else None,
            'coobserved_edge_learner_pairs': n, 'parent_first_pairs': prior,
            'pair_weighted_parent_first_fraction': prior / n if n else None,
            'equal_weight_supported_edge_fraction': mean([v[1] / v[0] for v in supported]) if supported else None}


def compare_graph_edges(base_table, control_order, base_edges, control_edges):
    base_edges, control_edges = set(base_edges), set(control_edges)
    control_table = edge_table(control_order)
    if (set(control_table) != control_edges
            or Counter(a for a, b in base_edges) != Counter(a for a, b in control_edges)
            or Counter(b for a, b in base_edges) != Counter(b for a, b in control_edges)):
        raise ValueError('frozen controls must preserve edge identity and in/out degree')
    shared, removed, added = base_edges & control_edges, base_edges - control_edges, control_edges - base_edges
    if any(base_table[edge] != control_table[edge] for edge in shared):
        raise ValueError('same edge has different stored cohort/order counts')
    base, control = edge_summary(base_table, base_edges), edge_summary(control_table, control_edges)
    remove, add = edge_summary(base_table, removed), edge_summary(control_table, added)
    pair_delta = control['coobserved_edge_learner_pairs'] - base['coobserved_edge_learner_pairs']
    prior_delta = control['parent_first_pairs'] - base['parent_first_pairs']
    if (pair_delta != add['coobserved_edge_learner_pairs'] - remove['coobserved_edge_learner_pairs']
            or prior_delta != add['parent_first_pairs'] - remove['parent_first_pairs']):
        raise ValueError('removed/added decomposition mismatch')
    support = control_order['exercise_learner_support']
    changed = removed | added
    child_observed = sum(support.get(b, 0) > 0 for a, b in changed)
    endpoints_global = sum(support.get(a, 0) > 0 and support.get(b, 0) > 0 for a, b in changed)
    same_learner = remove['supported_edges'] + add['supported_edges']
    return {'base': base, 'control': control, 'shared': edge_summary(base_table, shared),
            'removed': remove, 'added': add, 'symmetric_difference_entries': len(changed),
            'removed_edge_fraction': len(removed) / len(base_edges),
            'changed_entries_with_observed_child': child_observed,
            'changed_entries_with_globally_observed_endpoints': endpoints_global,
            'changed_entries_coobserved_same_learner': same_learner,
            'changed_entry_coobserved_fraction': same_learner / len(changed) if changed else None,
            'delta_parent_first_pairs': prior_delta, 'delta_pair_denominator': pair_delta,
            'delta_pair_weighted_fraction': (control['pair_weighted_parent_first_fraction'] -
                base['pair_weighted_parent_first_fraction']) if base['coobserved_edge_learner_pairs'] and
                control['coobserved_edge_learner_pairs'] else None}


def population_rates(group):
    learners = count(group['learners'])
    if not learners:
        raise ValueError('empty common population has no estimand')
    for side in ('base', 'control'):
        values = [number(group[side][key]) for key in CATEGORIES]
        if any(not 0 <= value <= 1 for value in values):
            raise ValueError('invalid category fraction')
        close(math.fsum(values), 1)
    result = {}
    for key in CATEGORIES:
        stored = group['paired_control_minus_base'][key]
        contrast = number(group['control'][key]) - number(group['base'][key])
        close(stored['mean'], contrast)
        if sum(count(stored[name]) for name in ('positive_learners', 'negative_learners', 'unchanged_learners')) != learners:
            raise ValueError('learner sign counts do not match population')
        if not number(stored['min']) - TOL <= contrast <= number(stored['max']) + TOL:
            raise ValueError('paired mean outside stored range')
        result[key] = {'base': group['base'][key], 'control': group['control'][key],
                       'delta_control_minus_base': contrast,
                       'changed_learners': stored['positive_learners'] + stored['negative_learners']}
    return {'learners': learners, 'categories': result}


def common_population_sensitivity(source):
    outputs = []
    for row in source['comparisons']:
        if row['status'] != 'analyzed':
            raise ValueError('all frozen control seeds must remain in the analysis')
        value = row['contrast']
        fixed, common = (population_rates(value[name]) for name in
                         ('all_fixed_opportunities', 'common_coobserved_opportunities'))
        total = count(value['cohort_learners'])
        eligible, opportunities = count(value['eligible_learners']), count(value['fixed_child_opportunities'])
        common_opportunities = count(value['common_coobserved_child_opportunities'])
        changed = count(value['changed_parent_child_opportunities'])
        if (fixed['learners'] != eligible or eligible + count(value['excluded_no_incoming_child']) != total
                or not 0 < common['learners'] <= eligible <= opportunities
                or not common['learners'] <= common_opportunities <= opportunities or changed > opportunities):
            raise ValueError('invalid common-population denominators')
        close(value['common_opportunity_retained_fraction'], common_opportunities / opportunities)
        outputs.append({'seed': row['seed'], 'graph_sha256': row['graph_sha256'],
            'cohort_learners': total, 'eligible_learners': eligible,
            'eligible_cohort_fraction': eligible / total,
            'fixed_child_opportunities': opportunities, 'changed_parent_child_opportunities': changed,
            'changed_opportunity_fraction': changed / opportunities,
            'common_child_opportunities': common_opportunities,
            'common_opportunity_retained_fraction': common_opportunities / opportunities,
            'common_learner_retained_fraction': common['learners'] / eligible,
            'all_fixed': fixed, 'common_coobserved': common,
            'learner_loo_available': False,
            'limit_vi': 'Chỉ aggregate means/sign counts, không có learner rows để resampling hoặc learner LOO.'})
    identity = source['identity_negative_control']
    if count(identity['changed_parent_child_opportunities']) != 0:
        raise ValueError('identity negative control changes parents')
    for name in ('all_fixed_opportunities', 'common_coobserved_opportunities'):
        checked = population_rates(identity[name])
        if any(abs(row['delta_control_minus_base']) > TOL or row['changed_learners'] for row in checked['categories'].values()):
            raise ValueError('identity negative control is not zero')
    return outputs


def load_inputs(root):
    """Allowlist cố định; chỉ đọc selected outputs/hash manifests, không đọc raw rows."""
    data, inventory, manifests = {}, {}, {}
    def read(relative, *, parse_json=True):
        path = root / relative
        content = path.read_bytes()
        inventory[relative] = hashlib.sha256(content).hexdigest()
        return json.loads(content) if parse_json else content.decode('utf-8')
    for run, names in ALLOWED_OUTPUTS.items():
        prefix = f'research_tracking/runs/{run}'
        manifest = read(prefix + '/manifest.json')
        if manifest['status'] != 'completed':
            raise ValueError('incomplete source bundle')
        manifests[run] = manifest
        for name in sorted(names):
            relative = prefix + '/' + name
            value = read(relative)
            if inventory[relative] != manifest['outputs_sha256'].get(name):
                raise ValueError('selected input SHA-256 mismatch: ' + relative)
            data[run + '/' + name] = value
    readme = 'research_tracking/runs/cpu-factorial-20261107-01/README.md'
    read(readme, parse_json=False)
    if inventory[readme] != manifests['cpu-factorial-20261107-01']['outputs_sha256'].get('README.md'):
        raise ValueError('factorial context README SHA-256 mismatch')
    order_code = 'src/knowledge_tracing/gam_kt/practice_order.py'
    read(order_code, parse_json=False)
    if inventory[order_code] != manifests['cpu-junyi-common-20261107-01']['sources_sha256'].get(order_code):
        raise ValueError('stored order estimand code SHA-256 mismatch')
    archive = read('research_tracking/runs/parallel-graph-diagnostics-20261107-01/manifest.json')
    followup_path = 'research_tracking/reports/cpu_pilot_followup_20261107.json'
    data['followup'] = read(followup_path)
    if (archive['status'] != 'completed' or inventory[followup_path] !=
            archive['outputs_sha256'].get('input_mechanism_followup.json')):
        raise ValueError('mechanism followup no longer matches archived bytes')
    return data, manifests, inventory


def analyze_loaded(data, manifests):
    factorial_run = 'cpu-factorial-20261107-01'
    order_run = 'cpu-junyi-controls-20261107-02-expanded'
    common_run = 'cpu-junyi-common-20261107-01'
    factorial = manifests[factorial_run]
    pilot = manifests[order_run]
    if (factorial['kind'] != 'approved_cpu_factorial_pilot' or factorial['cells'] != 4
            or factorial['mechanism_strength'] != [0, 0.55]
            or factorial['edge_treatment'] != 'S=P=on versus S=P=off, L=off in both'
            or factorial['steps'] != 120 or factorial['environment_controller_graph'] != 'historical advanced, fixed'
            or factorial['seeds'] != list(range(21000, 21010)) or factorial['profiles'] != ['PG', 'PY', 'PYH']
            or pilot['uses_correct_labels'] is not False or pilot['scope'] != 'inner-train learners only'
            or pilot['control_spec']['seeds'] != [0, 1, 2]):
        raise ValueError('source estimand or scope differs from approved historical pilot')
    graph = data[order_run + '/corrected_graph.json']
    original_order = data[order_run + '/order_summary.json']
    controls = data[order_run + '/matched_controls.json']
    common = data[common_run + '/common_population.json']
    if ([row['seed'] for row in controls] != [0, 1, 2] or [row['seed'] for row in common['comparisons']] != [0, 1, 2]
            or common['cohort_sha256'] != pilot['cohort_sha256']
            or common['learners'] != original_order['learners'] or common['events'] != original_order['events']
            or common['original_control_summaries_reproduced'] is not True):
        raise ValueError('cohort, control seed or source version mismatch')
    base_edges = {tuple(edge) for edge in graph['corrected_edges']}
    raw_edges = {tuple(edge) for edge in graph['raw_edges_without_self_loops']}
    base_table = edge_table(original_order)
    if (len(base_edges) != 976 or len(raw_edges) != 979 or set(base_table) != raw_edges
            or not base_edges.issubset(raw_edges)):
        raise ValueError('unexpected corrected/raw graph denominator')
    comparisons = []
    populations = common_population_sensitivity(common)
    for control, population in zip(controls, populations):
        if (control['status'] != 'constructed' or control['applied_swaps'] != 10
                or control['original_sha256'] != common['base_graph_sha256']
                or control['result_sha256'] != population['graph_sha256']
                or control['order']['learners'] != common['learners'] or control['order']['events'] != common['events']):
            raise ValueError('control status/hash/cohort mismatch')
        result = compare_graph_edges(base_table, control['order'], base_edges, {tuple(edge) for edge in control['edges']})
        if (result['symmetric_difference_entries'] != control['changed_edge_entries']
                or result['changed_entries_with_observed_child'] != control['changed_entries_with_observed_child']
                or result['changed_entries_with_globally_observed_endpoints'] != control['changed_entries_with_both_endpoints_observed']):
            raise ValueError('stored perturbation exposure counts mismatch')
        comparisons.append({'seed': control['seed'], **result})
    return {'schema_version': 1, 'evidence_level': 'EXPLORATORY_STORED_AGGREGATE_REANALYSIS',
        'factorial': factorial_conditions(data[factorial_run + '/contrasts.json'], data[factorial_run + '/summary.json'],
                                         data['followup'], seeds=factorial['seeds'], profiles=factorial['profiles']),
        'junyi': {'raw_reference': edge_summary(base_table, raw_edges),
                  'corrected_base': edge_summary(base_table, base_edges),
                  'controls': comparisons, 'common_population_sensitivity': populations,
                  'cohort_sha256': common['cohort_sha256'], 'prefix_rows_sha256': common['prefix_rows_sha256'],
                  'order_unit_vi': 'Pooled edge-learner pairs; tuple(time,source_row) first-exposure order.',
                  'common_unit_vi': 'Equal learner weight, child mean trong learner; timestamp ties riêng, incoming edges denominator.'},
        'limits_vi': ['Không causal ability effect, final efficacy, equivalence, p-value hoặc formal CI.',
                     'Không pooling đơn vị seed, event, edge hoặc learner giữa hai hệ.',
                     'Không per-seed mechanism exposure hoặc per-learner contrasts trong selected inputs.',
                     'Profile dynamics/initialization và graph correlation của nguồn được giữ; không giả ability-only intervention.']}


def run(root, run_id):
    if Path(sys.prefix).resolve() != (root / '.venv').resolve():
        raise ValueError('use project .venv only')
    started = time.perf_counter()
    data, manifests, inventory = load_inputs(root)
    sys.path.insert(0, str(root / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = [root / name for name in inventory]
    sources += [Path(__file__).resolve(), root / 'tests/shared_kt/test_rq2_controls.py',
                root / 'src/knowledge_tracing/evidence.py', root / 'src/knowledge_tracing/gam_kt/practice_order.py']
    note = '''# RQ2: conditions từ aggregates bất biến — 08/11/2026

Đọc selected stored aggregates và đối chiếu SHA theo manifest; không mở raw outcomes/traces,
Junyi interactions/correctness/Holdout, không chạy model/simulator hoặc sinh graph mới.
Giữ cả3profiles,10seed blocks và3control seeds. Phân tích mới gồm paired profile moderation
LOO, graph removed/added/shared decomposition và fixed/common population attrition.
Không causal ability effect, equivalence, final efficacy hoặc formal uncertainty.
Source snapshots và input SHA cho phép tái lập trong repository; không tự là standalone kit.
'''
    with record_evidence_run(root, run_id, metadata={'kind': 'RQ2_STORED_AGGREGATE_CONDITIONS_ANALYSIS',
            'rq': ['RQ2'], 'max_seconds': 60, 'raw_queries': 0, 'model_or_simulator_runs': 0,
            'graph_generation_runs': 0, 'statistical_inference': 'descriptive only'}, sources=sources, note=note) as directory:
        result = analyze_loaded(data, manifests)
        result['input_sha256'] = inventory
        if time.perf_counter() - started > 60:
            raise TimeoutError('aggregate analysis cap60s exceeded')
        (directory / 'conditions.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        copies = []
        for source, name in ((Path(__file__).resolve(), 'analysis_source.py'),
                             (root / 'tests/shared_kt/test_rq2_controls.py', 'test_source.py')):
            before = sha(source)
            target = directory / name
            target.write_bytes(source.read_bytes())
            if sha(target) != before or sha(source) != before:
                raise ValueError('source snapshot hash drift')
            copies.append({'source': source.relative_to(root).as_posix(), 'snapshot': name,
                           'sha256_before': before, 'sha256_after': sha(target)})
        (directory / 'copy_inventory.json').write_text(json.dumps(copies, indent=2)+'\n', encoding='utf-8')
    return {'run_id': run_id, 'integrity': verify_evidence_bundle(directory),
            'elapsed_seconds': time.perf_counter()-started,
            'conditions_sha256': sha(directory / 'conditions.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    print(json.dumps(run(ROOT, args.run_id), ensure_ascii=False))
