"""Phân tích thứ cấp trace CPU09 đã lưu, dùng stdlib và owned worker."""

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONTRACT = PREP / 'rq2_cache_mechanism_contract01.json'
TRACE_FIELDS = frozenset(('seed', 'profile', 'graph_on', 'mechanism_on', 'step',
                         'concept', 'question', 'prediction', 'y', 'p_true',
                         'theta_before', 'learning_gain', 'challenge_match',
                         'prereq_violation', 'prerequisite_deficit', 'gap_days'))
SEMANTIC_FIELDS = TRACE_FIELDS - {'mechanism_on'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def decode(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value, 'duplicate JSON key')
            value[key] = item
        return value

    def invalid(value):
        raise ValueError('nonfinite JSON token')

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def sha(path, cap):
    need(path.is_file() and not path.is_symlink(), 'bounded regular file required')
    result = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            size += len(block)
            need(size <= cap, 'input byte cap')
            result.update(block)
    return result.hexdigest(), size


def trace_rows(path, *, max_compressed, max_uncompressed, max_line, max_rows, guard):
    need(path.stat().st_size <= max_compressed, 'compressed byte cap')
    total = count = 0
    with gzip.open(path, 'rb') as stream:
        while True:
            guard()
            raw = stream.readline(max_line + 1)
            if not raw:
                break
            total += len(raw)
            count += 1
            need(len(raw) <= max_line and total <= max_uncompressed and count <= max_rows,
                 'decompressed line/byte/record cap')
            need(raw.endswith(b'\n'), 'trace line must terminate')
            yield decode(raw)
    guard()


def validate_manifest(manifest, contract):
    grid = contract['grid']
    need(manifest.get('kind') == 'approved_cpu_factorial_pilot'
         and manifest.get('status') == 'completed'
         and manifest.get('seeds') == grid['seeds'] and manifest.get('profiles') == grid['profiles']
         and type(manifest.get('steps')) is int and manifest['steps'] == grid['steps']
         and type(manifest.get('cells')) is int and manifest['cells'] == 4
         and manifest.get('edge_treatment') == 'S=P=on versus S=P=off, L=off in both',
         'historical study identity')
    for role in ('outcomes', 'contrasts', 'summary', 'provenance', 'traces'):
        name = contract['paths'][role]
        need(manifest['outputs_sha256'].get(Path(name).name) == contract['inputs'][name]['sha256'],
             'closed manifest/output hash binding')


def validate_trace(rows, *, seeds, profiles, steps, questions, roots):
    buckets = {(s, p, g, m): {} for s in seeds for p in profiles
               for g in (False, True) for m in (False, True)}
    for row in rows:
        need(type(row) is dict and set(row) == TRACE_FIELDS, 'exact trace schema')
        need(type(row['seed']) is int and row['seed'] in seeds
             and type(row['profile']) is str and row['profile'] in profiles
             and type(row['graph_on']) is bool and type(row['mechanism_on']) is bool,
             'trace condition identity')
        need(type(row['step']) is int and 0 <= row['step'] < steps, 'trace step')
        need(type(row['question']) is str and row['question'] in questions
             and row['concept'] == questions[row['question']]['concept'], 'trace query identity')
        need(type(row['y']) is int and row['y'] in (0, 1)
             and type(row['prereq_violation']) is int and row['prereq_violation'] in (0, 1),
             'trace binary values')
        for field in ('prediction', 'p_true', 'theta_before', 'learning_gain',
                      'challenge_match', 'prerequisite_deficit', 'gap_days'):
            need(finite(row[field]), 'trace numeric finite')
        need(all(0 <= row[k] <= 1 for k in ('prediction', 'p_true', 'challenge_match',
                                            'prerequisite_deficit'))
             and row['learning_gain'] >= 0 and row['gap_days'] >= 0, 'trace numeric range')
        if row['concept'] in roots:
            need(row['prerequisite_deficit'] == 0 and row['prereq_violation'] == 0,
                 'root cannot have prerequisite deficit')
        key = (row['seed'], row['profile'], row['graph_on'], row['mechanism_on'])
        need(row['step'] not in buckets[key], 'duplicate trace key')
        buckets[key][row['step']] = row
    need(all(set(rows) == set(range(steps)) for rows in buckets.values()), 'incomplete trace grid')
    return {key: tuple(rows[t] for t in range(steps)) for key, rows in buckets.items()}


def endpoint_table(rows, *, seeds, profiles):
    expected = {(s, p, g, m) for s in seeds for p in profiles
                for g in (False, True) for m in (False, True)}
    result = {}
    for row in rows:
        need(type(row) is dict and set(row) == {'seed', 'profile', 'graph_on',
             'prerequisite_mechanism_on', 'latent_identity', 'random_stream_identity', 'outcome'},
             'endpoint schema')
        need(type(row['seed']) is int and type(row['profile']) is str
             and type(row['graph_on']) is bool and type(row['prerequisite_mechanism_on']) is bool,
             'endpoint condition types')
        key = row['seed'], row['profile'], row['graph_on'], row['prerequisite_mechanism_on']
        need(key in expected and key not in result and finite(row['outcome']), 'endpoint grid/value')
        for field in ('latent_identity', 'random_stream_identity'):
            value = row[field]
            need(type(value) is str and len(value) == 64
                 and all(c in '0123456789abcdef' for c in value), 'endpoint SHA shape')
        result[key] = row
    need(set(result) == expected, 'incomplete endpoint grid')
    for seed in seeds:
        all_rows = [r for k, r in result.items() if k[0] == seed]
        need(len({r['random_stream_identity'] for r in all_rows}) == 1, 'cross-profile U binding')
        latent_ids = []
        for profile in profiles:
            group = [r for k, r in result.items() if k[:2] == (seed, profile)]
            need(len({r['latent_identity'] for r in group}) == 1, 'four-cell latent binding')
            latent_ids.append(group[0]['latent_identity'])
        need(len(set(latent_ids)) == len(profiles), 'persona latent vectors must remain distinct')
    return result


def arm_summary(key, rows, roots):
    deficits = [r['prerequisite_deficit'] for r in rows]
    root_count = sum(r['concept'] in roots for r in rows)
    return dict(seed=key[0], profile=key[1], graph_on=key[2], mechanism_on=key[3],
                events=len(rows), positive_true_deficit_events=sum(d > 0 for d in deficits),
                mean_true_deficit=sum(deficits) / len(rows), max_true_deficit=max(deficits),
                root_events=root_count, nonroot_events=len(rows) - root_count,
                served_concepts=len({r['concept'] for r in rows}))


def pair_summary(seed, profile, axis, fixed, left, right):
    query_diffs = [i for i, (a, b) in enumerate(zip(left, right))
                   if (a['concept'], a['question']) != (b['concept'], b['question'])]
    label_diffs = [i for i, (a, b) in enumerate(zip(left, right)) if a['y'] != b['y']]
    first_query = query_diffs[0] if query_diffs else None
    first_label = label_diffs[0] if label_diffs else None
    first_history = min((v for v in (first_query, first_label) if v is not None), default=None)
    return dict(seed=seed, profile=profile, axis=axis, fixed_other_flag=fixed,
                orientation='false_vs_true', paired_steps=len(left),
                first_query_difference_step=first_query, first_label_difference_step=first_label,
                common_query_prefix_steps=len(left) if first_query is None else first_query,
                common_observable_prefix_steps=len(left) if first_history is None else first_history,
                same_query_steps=len(left) - len(query_diffs), different_query_steps=len(query_diffs),
                different_label_steps=len(label_diffs))


def analyze(buckets, endpoints, contrasts, summary, *, seeds, profiles, roots):
    declared = {}
    for row in contrasts:
        need(type(row) is dict and set(row) == {'seed', 'profile', 'graph_effect_mechanism_on',
             'graph_effect_mechanism_off', 'interaction_contrast'}, 'contrast schema')
        key = row['seed'], row['profile']
        need(type(key[0]) is int and type(key[1]) is str and key not in declared
             and key[0] in seeds and key[1] in profiles, 'contrast key')
        need(all(finite(row[k]) for k in row if k not in ('seed', 'profile')), 'finite contrasts')
        declared[key] = row
    need(set(declared) == {(s, p) for s in seeds for p in profiles}, 'contrast completeness')
    arms, pairs, joined = [], [], []
    for seed in seeds:
        for profile in profiles:
            group_arms = [arm_summary((seed, profile, g, m), buckets[seed, profile, g, m], roots)
                          for g in (False, True) for m in (False, True)]
            group_pairs = []
            for g in (False, True):
                left, right = buckets[seed, profile, g, False], buckets[seed, profile, g, True]
                group_pairs.append(pair_summary(seed, profile, 'mechanism', g, left, right))
                if profile == 'PG':
                    need(all(r['prerequisite_deficit'] == 0 for r in (*left, *right)), 'PG deficit negative')
                    need(all(all(a[k] == b[k] for k in SEMANTIC_FIELDS)
                             for a, b in zip(left, right)), 'PG mechanism semantic negative')
                    need(endpoints[seed, profile, g, False]['outcome']
                         == endpoints[seed, profile, g, True]['outcome'], 'PG endpoint negative')
            for m in (False, True):
                group_pairs.append(pair_summary(seed, profile, 'policy', m,
                    buckets[seed, profile, False, m], buckets[seed, profile, True, m]))
            outcomes = [dict(graph_on=g, mechanism_on=m, outcome=endpoints[seed, profile, g, m]['outcome'])
                        for g in (False, True) for m in (False, True)]
            delta = {m: endpoints[seed, profile, True, m]['outcome']
                        - endpoints[seed, profile, False, m]['outcome'] for m in (False, True)}
            expected = declared[seed, profile]
            values = {'graph_effect_mechanism_on': delta[True],
                      'graph_effect_mechanism_off': delta[False],
                      'interaction_contrast': delta[True] - delta[False]}
            need(all(abs(expected[k] - v) <= 1e-12 for k, v in values.items()), 'endpoint contrast arithmetic')
            joined.append(dict(seed=seed, profile=profile, **values, outcomes=outcomes,
                               arm_exposures=group_arms, paired_trajectories=group_pairs))
            arms.extend(group_arms)
            pairs.extend(group_pairs)
    need(type(summary) is dict and set(summary) == set(profiles), 'source summary profiles')
    for profile in profiles:
        expected = summary[profile]
        need(type(expected) is dict and set(expected) == {'paired_seeds', 'mean_interaction'}
             and type(expected['paired_seeds']) is int and expected['paired_seeds'] == len(seeds)
             and finite(expected['mean_interaction']), 'source summary schema')
        mean = sum(declared[s, profile]['interaction_contrast'] for s in seeds) / len(seeds)
        need(abs(mean - expected['mean_interaction']) <= 1e-12, 'source mean reconciliation')
    return dict(arm_exposures=arms, paired_trajectories=pairs, joined_contrasts=joined)


def topology(raw):
    nodes = [r['concept_id'] for r in csv.DictReader(io.StringIO(raw['nodes'].decode('utf-8-sig')))]
    edges = [(r['source'], r['target']) for r in csv.DictReader(io.StringIO(raw['edges'].decode('utf-8-sig')))]
    need(len(nodes) == len(set(nodes)) == 28 and len(edges) == len(set(edges)) == 31, 'historical topology size')
    need(all(a in nodes and b in nodes and a != b for a, b in edges), 'historical edge endpoints')
    degree = {n: 0 for n in nodes}
    for a, b in edges:
        degree[b] += 1
    pending = [n for n in nodes if degree[n] == 0]
    visited = []
    while pending:
        node = pending.pop()
        visited.append(node)
        for a, b in edges:
            if a == node:
                degree[b] -= 1
                if degree[b] == 0:
                    pending.append(b)
    need(len(visited) == len(nodes), 'historical DAG')
    rows = list(csv.DictReader(io.StringIO(raw['questions'].decode('utf-8-sig'))))
    need(len(rows) == 84 and len({r['question_id'] for r in rows}) == 84
         and all(r['concept_id'] in nodes and finite(float(r['elo_difficulty'])) for r in rows), 'historical question bank')
    questions = {r['question_id']: dict(concept=r['concept_id'], difficulty=float(r['elo_difficulty'])) for r in rows}
    return questions, set(nodes) - {b for a, b in edges}


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--output-name', required=True)
    args = parser.parse_args()
    need(Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT / '.venv', 'fixed repository/venv')
    need(sha(Path(__file__), 65536)[0] == args.source_sha256
         and sha(CONTRACT, 65536)[0] == args.contract_sha256, 'source/contract pins')
    contract = decode(CONTRACT.read_bytes())
    need(contract['analysis_source_sha256'] == args.source_sha256, 'contract source binding')
    need(args.output_name == contract['output_name'] and Path(args.output_name).name == args.output_name
         and args.output_name not in ('.', '..'), 'exclusive planned output')
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    limits = contract['limits']

    def guard():
        need(time.monotonic() - started <= limits['worker_seconds'], 'worker elapsed cap')

    def write(path, value):
        raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
        need(len(raw) <= limits['output_file_bytes'], 'output file cap')
        with path.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())

    before = {}
    for name, expected in contract['inputs'].items():
        path = ROOT / name
        need(path.resolve().is_relative_to(ROOT), 'input root')
        actual, size = sha(path, expected['bytes'])
        need(actual == expected['sha256'] and size == expected['bytes'], 'input pin')
        before[name] = actual
        guard()
    out = PREP / args.output_name
    out.mkdir(exist_ok=False)
    write(out / 'reservation.json', dict(scope=contract['scope'], owner=owner,
          source_sha256=args.source_sha256, contract_sha256=args.contract_sha256,
          model_calls=0, world_transitions=0, input_hashes=before))
    try:
        roles = contract['paths']
        validate_manifest(decode((ROOT / roles['manifest']).read_bytes()), contract)
        raw = {name: (ROOT / roles[name]).read_bytes() for name in ('nodes', 'edges', 'questions')}
        questions, roots = topology(raw)
        grid = contract['grid']
        rows = trace_rows(ROOT / roles['traces'], max_compressed=limits['compressed_bytes'],
                          max_uncompressed=limits['uncompressed_bytes'], max_line=limits['line_bytes'],
                          max_rows=limits['trace_rows'], guard=guard)
        buckets = validate_trace(rows, seeds=grid['seeds'], profiles=grid['profiles'],
                                 steps=grid['steps'], questions=questions, roots=roots)
        endpoints = endpoint_table(decode((ROOT / roles['outcomes']).read_bytes()),
                                   seeds=grid['seeds'], profiles=grid['profiles'])
        result = analyze(buckets, endpoints, decode((ROOT / roles['contrasts']).read_bytes()),
                         decode((ROOT / roles['summary']).read_bytes()),
                         seeds=grid['seeds'], profiles=grid['profiles'], roots=roots)
        for name, values in result.items():
            guard()
            write(out / (name + '.json'), values)
        after = {name: sha(ROOT / name, contract['inputs'][name]['bytes'])[0] for name in before}
        need(before == after, 'input drift after analysis')
        guard()
        write(out / 'result.json', dict(status='COMPLETE_CACHED_SECONDARY_ANALYSIS_PENDING_OUTER_ACCEPTANCE',
              elapsed_seconds=time.monotonic()-started, source_sha256=args.source_sha256,
              contract_sha256=args.contract_sha256, inputs_before=before, inputs_after=after,
              arms=len(result['arm_exposures']), pairs=len(result['paired_trajectories']),
              contrasts=len(result['joined_contrasts']), seed_clusters=len(grid['seeds']),
              new_independent_seed_families=0, model_calls=0, world_transitions=0,
              scope=contract['scope']))
        outputs = {p.name: dict(sha256=sha(p, limits['output_file_bytes'])[0], bytes=p.stat().st_size)
                   for p in sorted(out.iterdir()) if p.is_file()}
        guard()
        write(out / 'output-manifest.json', dict(outputs=outputs))
        guard()
        return 0
    except BaseException as error:
        write(out / 'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
              elapsed_seconds=time.monotonic()-started, source_sha256=args.source_sha256,
              contract_sha256=args.contract_sha256, whole_analysis_accepted=False))
        raise


if __name__ == '__main__':
    raise SystemExit(main())
