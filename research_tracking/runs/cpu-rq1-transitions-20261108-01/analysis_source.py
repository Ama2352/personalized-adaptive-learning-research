"""Đọc lại stored synthetic traces; không simulator, model hoặc realdata query.

Default chỉ in JSON. Chỉ --run-id mới tạo evidence run exclusive dưới runs/.
Các bảng conditional là đồng biến cùng pre-update snapshot, không mediation.
"""

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
if __name__ == '__main__':
    sys.dont_write_bytecode = True  # CLI mặc định không tạo repo bytecode cache.
from knowledge_tracing.diagnostics import DecisionTrace, compare_decision_traces
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

FIXED = 'research_tracking/runs/cpu-rq12-20261107-03'
CLOSED = 'research_tracking/runs/cpu-closedloop-20261107-01'
VARIANTS = ('graph_free', 'graph_package', 'empty_graph_package')
CANDIDATES = VARIANTS[1:]
FLAGS = ('p_changed', 'm_changed', 'r_changed', 'a_changed')
EDGES = (('p_changed', 'm_changed'), ('m_changed', 'r_changed'),
         ('r_changed', 'a_changed'), ('p_changed', 'a_changed'))
FIXED_FIELDS = {'variant', 'event_id', 'learner_id', 'correct', 'probability',
                'mastery', 'mastered', 'ready', 'action'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_time(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError('analysis CPU/wall budget60s exceeded')


def read_gzip_json(path, deadline):
    rows, size = [], 0
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            size += len(line)
            if len(line) > 65536 or size > 32 * 1024**2 or len(rows) >= 12000:
                raise ValueError('stored trace exceeds bounded analysis cap')
            rows.append(json.loads(line))
            if len(rows) % 128 == 0:
                check_time(deadline)
    return rows


def _probability(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and 0 <= value <= 1)


def fixed_index(rows, candidates=CANDIDATES):
    """Join identity bằng key, không zip theo thứ tự vật lý trong gzip."""
    variants = ('graph_free', *candidates)
    index = {v: {} for v in variants}
    for row in rows:
        if set(row) != FIXED_FIELDS or row['variant'] not in variants:
            raise ValueError('fixed-stream schema/variant mismatch; không nhận oracle fields')
        if (not isinstance(row['learner_id'], str)
                or not re.fullmatch(r'[0-9]+-[A-Za-z0-9_]+', row['learner_id'])
                or not isinstance(row['event_id'], str) or not row['event_id'].isdigit()
                or str(int(row['event_id'])) != row['event_id']
                or type(row['correct']) is not int or row['correct'] not in (0, 1)):
            raise ValueError('invalid fixed event/cluster identity or outcome')
        mastery = row['mastery']
        if (not isinstance(mastery, dict) or not mastery
                or any(not isinstance(k, str) or not k or not _probability(v) for k, v in mastery.items())
                or (row['probability'] is not None and not _probability(row['probability']))):
            raise ValueError('invalid stored probability/mastery score')
        for field in ('ready', 'mastered'):
            values = row[field]
            if (not isinstance(values, list) or any(not isinstance(v, str) for v in values)
                    or len(set(values)) != len(values) or not set(values) <= set(mastery)):
                raise ValueError('explicit mastered/ready decisions required; no score threshold replacement')
        if row['action'] is not None and row['action'] not in row['ready']:
            raise ValueError('action outside recorded ready set')
        key = (row['learner_id'], row['event_id'])
        bucket = index[row['variant']]
        if key in bucket:
            raise ValueError('duplicate fixed event identity')
        bucket[key] = row
    reference = set(index['graph_free'])
    if not reference or any(set(index[v]) != reference for v in candidates):
        raise ValueError('fixed event join coverage mismatch')
    return index


def paired_flags(rows, candidates=CANDIDATES):
    index = fixed_index(rows, candidates)
    events = []
    universe = None
    for candidate in candidates:
        for key in sorted(index['graph_free'], key=lambda k: (int(k[0].split('-', 1)[0]), k[0], int(k[1]))):
            left, right = index['graph_free'][key], index[candidate][key]
            if left['correct'] != right['correct'] or set(left['mastery']) != set(right['mastery']):
                raise ValueError('paired label/concept identity mismatch')
            if universe is None:
                universe = set(left['mastery'])
            if set(left['mastery']) != universe:
                raise ValueError('concept universe changes across snapshots')
            crossed = sorted(set(left['mastered']) ^ set(right['mastered']))
            p = (left['probability'] != right['probability']
                 if left['probability'] is not None and right['probability'] is not None else None)
            seed, profile = key[0].split('-', 1)
            events.append({'candidate': candidate, 'seed': int(seed), 'profile': profile,
                           'cluster': key[0], 'event_id': key[1], 'correct': left['correct'],
                           'p_changed': p, 'm_changed': bool(crossed),
                           'r_changed': set(left['ready']) != set(right['ready']),
                           'a_changed': left['action'] != right['action'],
                           'mastery_concept_crossings': len(crossed), 'concepts': len(universe),
                           'reference_probability': left['probability'], 'candidate_probability': right['probability'],
                           'reference_action': left['action'], 'candidate_action': right['action'],
                           'crossed_concepts': crossed,
                           'ready_added': sorted(set(right['ready']) - set(left['ready'])),
                           'ready_removed': sorted(set(left['ready']) - set(right['ready']))})
    return index, events


def conditional_table(events, first, second):
    eligible = [e for e in events if e[first] is not None and e[second] is not None]
    result = []
    for a, b in itertools.product((False, True), repeat=2):
        denominator = sum(e[first] == a for e in eligible)
        count = sum(e[first] == a and e[second] == b for e in eligible)
        result.append({'first': first, 'second': second, 'first_changed': a, 'second_changed': b,
                       'count': count, 'conditional_denominator': denominator,
                       'conditional_fraction': count / denominator if denominator else None,
                       'eligible_event_pairs': len(eligible),
                       'unknown_pairs_excluded': len(events) - len(eligible)})
    return result


def group_summary(events):
    supported = [e for e in events if e['p_changed'] is not None]
    patterns = Counter(''.join(str(int(e[k])) for k in FLAGS) for e in supported)
    return {'event_pairs': len(events), 'supported_probability_pairs': len(supported),
            'unsupported_probability_pairs': len(events) - len(supported),
            'changed_probability_events': sum(e['p_changed'] for e in supported),
            'changed_mastery_events_any_concept': sum(e['m_changed'] for e in events),
            'mastery_concept_crossings': sum(e['mastery_concept_crossings'] for e in events),
            'concept_decision_pairs': sum(e['concepts'] for e in events),
            'changed_ready_events': sum(e['r_changed'] for e in events),
            'changed_action_preview_events': sum(e['a_changed'] for e in events),
            'joint_patterns_PMRA': {''.join(map(str, p)): patterns[''.join(map(str, p))]
                                   for p in itertools.product((0, 1), repeat=4)},
            'conditional_tables': [r for edge in EDGES for r in conditional_table(events, *edge)]}


def analyze_fixed(rows, comparisons, manifest):
    index, events = paired_flags(rows)
    profiles = sorted({r['profile'] for r in comparisons})
    expected = {(f'{seed}-{profile}', str(step)) for seed in manifest['seeds']
                for profile in profiles for step in range(manifest['steps_per_profile'])}
    if set(index['graph_free']) != expected:
        raise ValueError('fixed seed/profile/step coverage differs from source manifest')
    published = {(r['seed'], r['profile'], r['candidate']): r for r in comparisons}
    if len(published) != len(comparisons) or set(published) != {
            (s, p, c) for s in manifest['seeds'] for p in profiles for c in CANDIDATES}:
        raise ValueError('published aggregate coverage mismatch')
    legacy_checks = []
    groups = []
    for candidate in CANDIDATES:
        subset = [e for e in events if e['candidate'] == candidate]
        scopes = [('pooled', None, None, subset)]
        scopes += [('profile', None, p, [e for e in subset if e['profile'] == p]) for p in profiles]
        scopes += [('cluster', s, p, [e for e in subset if e['seed'] == s and e['profile'] == p])
                   for s in manifest['seeds'] for p in profiles]
        for scope, seed, profile, selected in scopes:
            groups.append({'candidate': candidate, 'scope': scope, 'seed': seed, 'profile': profile,
                           **group_summary(selected)})
        for seed in manifest['seeds']:
            for profile in profiles:
                keys = sorted((k for k in index['graph_free'] if k[0] == f'{seed}-{profile}'), key=lambda k: int(k[1]))
                def trace(variant, key):
                    r = index[variant][key]
                    return DecisionTrace(r['event_id'], r['learner_id'], r['correct'], r['probability'],
                                         r['mastery'], frozenset(r['ready']), r['action'], frozenset(r['mastered']))
                computed = compare_decision_traces([trace('graph_free', k) for k in keys],
                                                   [trace(candidate, k) for k in keys], threshold=.5)
                source = published[seed, profile, candidate]
                for field in ('paired_events', 'paired_supported_probability_rows', 'unsupported_probability_pairs',
                              'changed_probability_rows', 'concept_decisions', 'mastery_crossings',
                              'changed_ready_sets', 'changed_actions'):
                    if computed[field] != source[field]:
                        raise ValueError(f'legacy aggregate reconciliation failed: {field}')
                legacy_checks.append({'seed': seed, 'profile': profile, 'candidate': candidate, 'counts_exact': True})
    examples = {}
    for candidate in CANDIDATES:
        selected = [e for e in events if e['candidate'] == candidate]
        examples[candidate] = {
            'probability_changed_action_unchanged': [e for e in selected if e['p_changed'] is True and not e['a_changed']][:3],
            'action_changed': [e for e in selected if e['a_changed']][:3]}
    return {'groups': groups, 'examples': examples, 'legacy_reconciliation': legacy_checks,
            'seed_blocks': manifest['seeds'], 'profiles': profiles,
            'trajectory_clusters': len(manifest['seeds']) * len(profiles)}, events


def analyze_closed(rows, outcomes, manifest):
    """Chỉ observable projection; không lấy theta/p_true làm mastery thay thế."""
    index = {v: {} for v in VARIANTS}
    required = {'seed', 'profile', 'variant', 'step', 'concept', 'question', 'prediction', 'timestamp', 'y'}
    ignored = set()
    for raw in rows:
        if not required <= set(raw) or raw['variant'] not in index:
            raise ValueError('closed-loop observable identity schema mismatch')
        row = {k: raw[k] for k in required}
        ignored.update(set(raw) - required)
        if (type(row['seed']) is not int or type(row['step']) is not int or row['step'] < 0
                or not isinstance(row['profile'], str) or not row['profile']
                or any(not isinstance(row[k], str) or not row[k] for k in ('concept', 'question', 'timestamp'))
                or type(row['y']) is not int or row['y'] not in (0, 1)
                or not _probability(row['prediction'])):
            raise ValueError('invalid closed-loop observable record')
        key = row['seed'], row['profile'], row['step']
        if key in index[row['variant']]:
            raise ValueError('duplicate closed-loop step identity')
        index[row['variant']][key] = row
    profiles = sorted({r['profile'] for r in outcomes})
    expected = {(s, p, t) for s in manifest['seeds'] for p in profiles
                for t in range(manifest['steps_per_profile'])}
    if any(set(bucket) != expected for bucket in index.values()):
        raise ValueError('closed-loop manifest step coverage mismatch')
    published = {(r['seed'], r['profile'], r['variant']): r for r in outcomes}
    if (len(published) != len(outcomes) or set(published) != {
            (s, p, v) for s in manifest['seeds'] for p in profiles for v in VARIANTS}):
        raise ValueError('closed-loop outcome cluster coverage mismatch')
    result = []
    for candidate in CANDIDATES:
        for seed in manifest['seeds']:
            for profile in profiles:
                keys = [(seed, profile, t) for t in range(manifest['steps_per_profile'])]
                left = [index['graph_free'][k] for k in keys]
                right = [index[candidate][k] for k in keys]
                if any(a['timestamp'] != b['timestamp'] for a, b in zip(left, right)):
                    raise ValueError('closed-loop step clock mismatch')
                for variant, records in (('graph_free', left), (candidate, right)):
                    if [r['concept'] for r in records] != published[seed, profile, variant]['actions']:
                        raise ValueError('closed-loop action sequence differs from stored outcomes')
                action_steps = [a['step'] for a, b in zip(left, right) if a['concept'] != b['concept']]
                query_steps = [a['step'] for a, b in zip(left, right)
                               if (a['concept'], a['question']) != (b['concept'], b['question'])]
                result.append({'candidate': candidate, 'seed': seed, 'profile': profile,
                               'paired_step_indices': len(keys), 'actual_concept_action_disagreements': len(action_steps),
                               'question_identity_disagreements': len(query_steps),
                               'first_concept_action_divergence_step': action_steps[0] if action_steps else None,
                               'first_question_divergence_step': query_steps[0] if query_steps else None})
    return {'cluster_rows': result, 'full_transition_chain_available': False,
            'missing_stored_fields': ['explicit mastered concept decisions', 'ready set'],
            'ignored_oracle_diagnostic_fields': sorted(ignored),
            'prediction_contrasts_computed': False,
            'reason_vi': 'Closed-loop actions/questions và histories có thể khác; không ghép Δp như same-target fixed-stream hoặc suy mastery/ready từ oracle.'}


def load_analysis(deadline):
    used = []
    manifests = {}
    for folder in (FIXED, CLOSED):
        verify_evidence_bundle(ROOT / folder)
        manifests[folder] = json.loads((ROOT / folder / 'manifest.json').read_text(encoding='utf-8'))
        used.extend(ROOT / folder / n for n in ('manifest.json', 'README.md', 'source_provenance.json', 'traces.jsonl.gz'))
    fixed_manifest, closed_manifest = manifests[FIXED], manifests[CLOSED]
    if fixed_manifest.get('mode', 'fixed-stream') != 'fixed-stream' or closed_manifest['mode'] != 'closed-loop':
        raise ValueError('source run mode mismatch')
    helper_name = 'src/knowledge_tracing/diagnostics.py'
    helper_expected = {k.replace('\\', '/'): v for k, v in fixed_manifest['implementation_sha256'].items()}[helper_name]
    if sha(ROOT / helper_name) != helper_expected:
        raise ValueError('legacy comparator source drift; do not silently change source arithmetic')
    used += [ROOT / FIXED / 'comparisons.json', ROOT / CLOSED / 'closed_loop_outcomes.json']
    fixed, events = analyze_fixed(read_gzip_json(ROOT / FIXED / 'traces.jsonl.gz', deadline),
                                  json.loads((ROOT / FIXED / 'comparisons.json').read_text()), fixed_manifest)
    check_time(deadline)
    closed = analyze_closed(read_gzip_json(ROOT / CLOSED / 'traces.jsonl.gz', deadline),
                            json.loads((ROOT / CLOSED / 'closed_loop_outcomes.json').read_text()), closed_manifest)
    check_time(deadline)
    summary = {'schema_version': 1, 'evidence_class': 'Stored synthetic descriptive post-hoc diagnostic; không inference/causal efficacy',
               'fixed_stream': fixed, 'closed_loop': closed,
               'legacy_comparator_sha256': helper_expected,
               'definitions': {'PMRA': 'P=scalar p(correct) của current logged query differs, không toàn concept prediction vector; M=any explicit mastered concept differs; R=ready set differs; A=concept action preview differs',
                               'probability_change': 'Exact Python float inequality, giữ đúng comparator nguồn; không chọn tolerance mới.',
                               'mastery': 'Dùng explicit is_mastered decisions đã lưu, không threshold mastery score hoặc p(correct).',
                               'conditional_unit': 'Paired pre-update event snapshots; mastery_concept_crossings có denominator concept×event riêng.',
                               'clustering': 'Seed-profile trajectory IDs; profiles cùng seed có thể phụ thuộc. Không xem events hoặc9trajectories là independent inferential samples.'},
               'limits_vi': ['Bảng conditional là đồng biến cùng snapshot, không temporal transition/causal mediation.',
                             'P giữ/A đổi không là causality violation hoặc hidden-path bug; action có thể phụ thuộc scores/ranking khác ngoài scalar current-query p.',
                             'Fixed traces thiếu current item/question/timestamp: cùng stream do hồ sơ nguồn khai báo; không independently audit query identity từ trace.',
                             'Fixed action là preview trên bản sao, không served action; closed-loop served action không có đủ mastery/ready.',
                             'Package bật nhiều pathways; empty graph package vẫn local adaptation, không isolate edges.',
                             'Không pvalues/CI, không efficacy/causal benefit trên Junyi hoặc người học thật; seeds pilot đã công khai.'],
               'input_inventory': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in used]}
    return summary, events, used


def write_csv(path, rows):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(directory, summary, events, plot):
    (directory / 'analysis.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    scalars = [{k: e[k] for k in ('candidate', 'seed', 'profile', 'cluster', 'event_id', *FLAGS, 'mastery_concept_crossings')}
               for e in events]
    write_csv(directory / 'paired_snapshot_flags.csv', scalars)
    tables = []
    groups = []
    for g in summary['fixed_stream']['groups']:
        identity = {k: g[k] for k in ('candidate', 'scope', 'seed', 'profile')}
        tables += [{**identity, **r} for r in g['conditional_tables']]
        groups.append({**identity, **{k: v for k, v in g.items() if isinstance(v, int)}})
    write_csv(directory / 'conditional_tables.csv', tables)
    write_csv(directory / 'cluster_denominators.csv', groups)
    write_csv(directory / 'closed_loop_action_audit.csv', summary['closed_loop']['cluster_rows'])
    lines = ['# Bảng đồng biến fixed-stream đã lưu', '',
             'Đơn vị event snapshot trước update; không causal/temporal funnel. Action là preview.', '',
             '| Package | N event pairs | P đổi | M event(any concept) | M concept crossings / concept pairs | R đổi | A preview đổi |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for g in summary['fixed_stream']['groups']:
        if g['scope'] == 'pooled':
            lines.append(f"|{g['candidate']}|{g['event_pairs']}|{g['changed_probability_events']}|{g['changed_mastery_events_any_concept']}|{g['mastery_concept_crossings']}/{g['concept_decision_pairs']}|{g['changed_ready_events']}|{g['changed_action_preview_events']}|")
    lines += ['', 'Các denominator conditional cụ thể trong conditional_tables.csv; không lấy R/M concept crossings làm tỷ lệ chuyển tiếp.',
              'Closed-loop thiếu mastered/ready, không dựng full chain từ oracle. Xem analysis.json cho missing fields, clusters và examples.']
    (directory / 'tables.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), constrained_layout=True)
        for ax, candidate in zip(axes, CANDIDATES):
            g = next(g for g in summary['fixed_stream']['groups'] if g['scope'] == 'pooled' and g['candidate'] == candidate)
            cells = [r for r in g['conditional_tables'] if (r['first'], r['second']) == ('p_changed', 'a_changed')]
            matrix = [[next(r['count'] for r in cells if r['first_changed'] == p and r['second_changed'] == a)
                       for a in (False, True)] for p in (False, True)]
            ax.imshow(matrix, cmap='Blues')
            for i, j in itertools.product(range(2), repeat=2):
                ax.text(j, i, str(matrix[i][j]), ha='center', va='center', color='black')
            ax.set(xticks=[0, 1], xticklabels=['Action giữ', 'Action đổi'], yticks=[0, 1],
                   yticklabels=['p giữ', 'p đổi'], title=candidate)
        fig.suptitle('Số paired snapshots: đồng biến, không causal funnel')
        fig.savefig(directory / 'probability_action_counts.png', dpi=150)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', help='Tạo run mới exclusive; mặc định chỉ đọc/in JSON.')
    parser.add_argument('--plot', action='store_true', help='Matplotlib đã có sẵn; không cài dependency.')
    parser.add_argument('--test-evidence-dir', type=Path)
    args = parser.parse_args()
    if Path(sys.prefix).resolve() != ROOT / '.venv':
        raise ValueError('chỉ project .venv')
    deadline = time.monotonic() + 60
    if not args.run_id:
        summary, _, _ = load_analysis(deadline)
        print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
        return
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', args.run_id):
        raise ValueError('invalid exclusive run ID')
    test_files = []
    if args.test_evidence_dir:
        folder = args.test_evidence_dir.resolve()
        if not folder.is_relative_to((ROOT / 'artifacts/akt/local-tests').resolve()):
            raise ValueError('test evidence must stay in local-tests')
        test_files = [folder / 'pytest.log', folder / 'pytest.xml']
        if not all(p.is_file() for p in test_files):
            raise ValueError('missing targeted test evidence')
    sources = [Path(__file__), ROOT / 'tests/shared_kt/test_rq1_transitions.py',
               ROOT / 'src/knowledge_tracing/diagnostics.py', ROOT / 'src/knowledge_tracing/evidence.py', *test_files]
    sources += [ROOT / folder / n for folder in (FIXED, CLOSED)
                for n in ('manifest.json', 'README.md', 'source_provenance.json', 'traces.jsonl.gz')]
    sources += [ROOT / FIXED / 'comparisons.json', ROOT / CLOSED / 'closed_loop_outcomes.json']
    note = ('# Stored synthetic RQ1 transition diagnostic\n\n'
            'Chỉ đọc traces đã lưu; không simulator/train/realdata/Holdout/GPU. Conditional tables là đồng biến cùng pre-update snapshot, '
            'không temporal/causal funnel. Mastery event(any concept) tách concept crossings; preview fixed stream tách served closed loop. '
            'Closed loop thiếu mastery/ready nên full chain unavailable; không dùng oracle thay thế. '
            'analysis.json/CSV/tables.md lưu denominator/seed-profile clusters/examples và limitations. Source/test snapshots và logs được giữ nguyên bytes.\n')
    with record_evidence_run(ROOT, args.run_id,
                             metadata={'kind': 'STORED_SYNTHETIC_RQ1_CONDITIONAL_SNAPSHOT_ANALYSIS',
                                       'new_training_or_simulator_events': 0, 'max_seconds': 60,
                                       'inference': 'descriptive only; no pvalues/causal inference'},
                             sources=sources, note=note) as directory:
        for source, name in ((Path(__file__), 'analysis_source.py'),
                             (ROOT / 'tests/shared_kt/test_rq1_transitions.py', 'test_source.py')):
            before = sha(source)
            (directory / name).write_bytes(source.read_bytes())
            if sha(directory / name) != before:
                raise ValueError('source snapshot copy mismatch')
        for p in test_files:
            (directory / ('targeted-' + p.name)).write_bytes(p.read_bytes())
        summary, events, _ = load_analysis(deadline)
        write_outputs(directory, summary, events, args.plot)
        check_time(deadline)
    print(json.dumps({'run': str(directory.relative_to(ROOT)), **verify_evidence_bundle(directory)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
