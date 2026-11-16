"""Kiểm chéo đồng biến RQ1 và factorial RQ2 từ CSV/JSON đã có."""
from collections import Counter
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import math
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TRANSITIONS = ROOT / 'research_tracking/runs/cpu-rq1-transitions-20261108-01'
FRESH = ROOT / ('research_tracking/runs/rq2-fresh-graph-recovery-20261110-01/'
                'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03')
PUBLISH = ROOT / 'research_tracking/runs/rq2-fresh-graph-source-analysis-20261110-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def write_csv(name, rows):
    with (HERE / name).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixed_rows(rows):
    columns = ('p_changed', 'm_changed', 'r_changed', 'a_changed')
    return Counter(''.join(str(int(row[column] == 'True')) for column in columns) for row in rows)


def main():
    started = time.perf_counter()
    transition_manifest = read(TRANSITIONS / 'manifest.json')
    fresh_manifest = read(PUBLISH / 'inventory_before_copy.json')
    input_pins = {}
    for name in ('analysis.json', 'paired_snapshot_flags.csv'):
        path = TRANSITIONS / name
        input_pins[path.relative_to(ROOT).as_posix()] = transition_manifest['outputs_sha256'][name]
    for name in ('outcomes.json', 'graph_source_contrasts.json', 'conditional_lambda_contrasts.json',
                 'trajectory_pairs.json', 'high_controls.json'):
        path = FRESH / name
        if name == 'outcomes.json':
            expected = '35f6603726f21d717e1da8e75ada8369584fcdcbbacbf3d170981e027dd662fa'
        else:
            original = 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03/' + name
            expected = fresh_manifest[original]
        input_pins[path.relative_to(ROOT).as_posix()] = expected
    for name, digest in input_pins.items():
        assert sha(ROOT / name) == digest, name
    save('INPUTS.json', dict(sha256=input_pins, bytes_read=sum((ROOT / p).stat().st_size for p in input_pins)))

    # Hai phép đếm độc lập: từng dòng CSV và joint PMRA đã lưu.
    with (TRANSITIONS / 'paired_snapshot_flags.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = [row for row in csv.DictReader(stream) if row['candidate'] == 'graph_package']
    assert len(rows) == 1080 and len({row['cluster'] for row in rows}) == 9
    assert all(row[key] in ('True','False') for row in rows
               for key in ('p_changed','m_changed','r_changed','a_changed'))
    assert all(sum(r['cluster']==cluster for r in rows)==120 for cluster in {r['cluster'] for r in rows})
    assert len({(r['seed'], r['profile'], r['event_id']) for r in rows}) == 1080
    counts = fixed_rows(rows)
    pooled = next(g for g in read(TRANSITIONS / 'analysis.json')['fixed_stream']['groups']
                  if g['candidate'] == 'graph_package' and g['scope'] == 'pooled')
    assert {p: counts[p] for p in pooled['joint_patterns_PMRA']} == pooled['joint_patterns_PMRA']
    assert sum(counts.values()) == 1080
    conditionals = []
    for column, name in enumerate(('served_probability', 'mastery_any_concept', 'ready_set')):
        for changed in (True, False):
            denominator = sum(n for pattern, n in counts.items() if (pattern[column] == '1') == changed)
            changed_action = sum(n for pattern, n in counts.items()
                                 if (pattern[column] == '1') == changed and pattern[3] == '1')
            direct = sum(row['a_changed'] == 'True' for row in rows
                         if (row[('p_changed', 'm_changed', 'r_changed')[column]] == 'True') == changed)
            assert direct == changed_action
            conditionals.append(dict(variable=name, changed=changed, snapshots=denominator,
                                     preview_changed=changed_action, preview_unchanged=denominator-changed_action,
                                     changed_fraction=changed_action/denominator))
    assert sum(c['preview_changed'] for c in conditionals if c['variable'] == 'ready_set') == 22
    assert next(c for c in conditionals if c['variable'] == 'ready_set' and c['changed'])['preview_changed'] == 5
    assert next(c for c in conditionals if c['variable'] == 'ready_set' and not c['changed'])['preview_changed'] == 17
    write_csv('rq1_conditionals.csv', conditionals)

    # Q được kiểm từ outcomes, rồi K từ các Q trong cùng block.
    outcomes = read(FRESH / 'outcomes.json')
    contrasts = read(FRESH / 'graph_source_contrasts.json')
    interactions = read(FRESH / 'conditional_lambda_contrasts.json')
    pairs = read(FRESH / 'trajectory_pairs.json')
    assert len(outcomes) == 120 and len(contrasts) == len(pairs) == 60 and len(interactions) == 30
    keys = {(r['block'], r['ability'], r['mechanism_strength'], r['graph_source']) for r in outcomes}
    expected = {(b, a, strength, graph) for b in range(21010,21020) for a in (1000,1150,1300)
                for strength in (0., .55) for graph in ('expert', 'learned')}
    assert keys == expected
    lookup = {(r['block'], r['ability'], r['mechanism_strength'], r['graph_source']):r for r in outcomes}
    qlookup = {(r['block'], r['ability'], r['mechanism_strength']):r for r in contrasts}
    assert set(qlookup) == {(b,a,strength) for b in range(21010,21020)
                            for a in (1000,1150,1300) for strength in (0.,.55)}
    assert {(r['block'],r['ability'],r['mechanism_strength']) for r in pairs} == set(qlookup)
    maximum_decimal_error = Decimal(0)
    block_rows = []
    with localcontext() as context:
        context.prec = 60
        for block in range(21010,21020):
            for ability in (1000,1150,1300):
                qs = {}
                for strength in (0., .55):
                    expert = lookup[(block, ability, strength, 'expert')]
                    learned = lookup[(block, ability, strength, 'learned')]
                    assert expert['latent_identity'] == learned['latent_identity']
                    assert expert['uniform_identity'] == learned['uniform_identity']
                    q = qlookup[(block, ability, strength)]
                    assert q['expert_minus_learned'] == expert['outcome'] - learned['outcome']
                    exact = Decimal(str(expert['outcome'])) - Decimal(str(learned['outcome']))
                    maximum_decimal_error = max(maximum_decimal_error, abs(exact-Decimal(str(q['expert_minus_learned']))))
                    qs[strength] = q['expert_minus_learned']
                k = qs[.55] - qs[0.]
                original = next(r for r in interactions if r['block'] == block and r['ability'] == ability)
                assert k == original['lambda_difference']
                if ability == 1300:
                    assert k == 0 and qs[0.] != 0
                block_rows.append(dict(block=block, ability=ability, q_penalty_off=qs[0.],
                                       q_penalty_on=qs[.55], k_difference=k))
    write_csv('rq2_block_contrasts.csv', block_rows)
    groups = []
    for ability in (1000,1150,1300):
        selected = [row for row in block_rows if row['ability'] == ability]
        group = dict(ability=ability, independent_blocks=10)
        for name in ('q_penalty_off','q_penalty_on','k_difference'):
            values = [row[name] for row in selected]
            mean = math.fsum(values)/10
            with localcontext() as context:
                context.prec = 60
                exact = sum(Decimal(str(v)) for v in values)/10
                maximum_decimal_error = max(maximum_decimal_error, abs(exact-Decimal(str(mean))))
            group.update({name+'_mean': mean, name+'_positive': sum(v>0 for v in values),
                          name+'_negative': sum(v<0 for v in values), name+'_zero': sum(v==0 for v in values)})
        for strength in (0., .55):
            chosen = [r for r in pairs if r['ability'] == ability and r['mechanism_strength'] == strength]
            assert len(chosen) == 10 and all(r['ordinal_rows'] == 120 for r in chosen)
            assert all(r['labels_equal_before_first_question_difference'] for r in chosen)
            prefix = 'penalty_off' if strength == 0 else 'penalty_on'
            group[prefix+'_question_differences'] = sum(r['question_id_differences'] for r in chosen)
            group[prefix+'_positions'] = 1200
        groups.append(group)
    assert sum(r['question_id_differences'] for r in pairs) == 4936
    assert maximum_decimal_error < Decimal('1e-12')
    write_csv('rq2_ability_summary.csv', groups)
    save('RESULTS.json', dict(status='CACHED_DESCRIPTIVE_REFINEMENT',
         rq1=dict(snapshots=1080, clusters=9, joint_pmra=dict(counts), conditionals=conditionals),
         rq2=dict(independent_blocks=10, trajectory_pairs=60, question_differences=4936,
                  positions=7200, ability_groups=groups),
         scientific_limits_vi=['Phân tích hậu nghiệm từ kết quả đã có, không sinh mẫu độc lập mới.',
            'Các snapshot/vị trí thời gian có tương quan, tỷ lệ là mô tả.',
            'Joint PMRA là đồng biến cùng snapshot, chưa nhận dạng đường trung gian nhân quả.',
            'Q đo đổi estimator graph expert/learned cố định; world/controller cùng expert.',
            'Sau trajectory divergence, ordinal không bảo đảm cùng target/history.'],
         calls=dict(simulator=0, model=0, gpu=0, junyi=0, holdout=0)))
    save('NUMERIC_ACCEPTANCE.json', dict(status='PASS', csv_aggregate_pmra_exact=True,
         all_120_outcome_keys_exact=True, paired_latent_uniform_identities=True,
         q_from_outcomes_60_exact=True, k_from_q_30_exact=True,
         decimal_maximum_absolute_error=str(maximum_decimal_error), absolute_tolerance='1e-12',
         source_sha_before_after_equal=all(sha(ROOT/p)==h for p,h in input_pins.items()),
         elapsed_seconds=time.perf_counter()-started))
    print(json.dumps(dict(conditionals=conditionals, ability_summary=groups,
                         max_decimal_error=str(maximum_decimal_error)), ensure_ascii=False))


if __name__ == '__main__':
    main()
