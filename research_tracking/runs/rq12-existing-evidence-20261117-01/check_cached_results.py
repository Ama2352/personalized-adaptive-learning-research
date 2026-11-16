"""Kiểm phụ bằng digest canonical toàn chuỗi và đếm từ CSV nguồn."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PARENT = ROOT/'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02'
CHILD = ROOT/'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    primary = load(HERE/'LAMBDA_OBSERVABLES.json')
    for path, expected in primary['inputs_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected
    complete_parent = set(load(CHILD/'parent_reference.json')['complete_cells'])
    metadata = {r['cell']['cell_id']:r['cell'] for source in (PARENT,CHILD)
                for r in lines(source/'cell_ledger.jsonl') if r['event']=='RESERVED_BEFORE_WORLD'}
    grouped = {}
    for source in (PARENT,CHILD):
        for row in lines(source/'observables.jsonl'):
            if source == PARENT and row['cell_id'] not in complete_parent:
                continue
            cell = metadata[row['cell_id']]
            key = (cell['block'],cell['ability'],cell['graph'],cell['mechanism_strength'])
            grouped.setdefault(key,{})[row['step']] = {k:v for k,v in row.items() if k!='cell_id'}
    assert len(grouped)==120
    digests = {key:digest([rows[i] for i in range(120)]) for key,rows in grouped.items()}
    per_ability = []
    for ability in (1000,1150,1300):
        equal = sum(digests[(b,ability,g,0.)] == digests[(b,ability,g,.55)]
                    for b in range(21010,21020) for g in ('full','learned'))
        per_ability.append(dict(ability=ability,pairs=20,exact_observable_sequences=equal))
    assert [row['exact_observable_sequences'] for row in per_ability] == [18,20,20]
    outcome_path = ROOT/('research_tracking/runs/rq2-fresh-graph-recovery-20261110-01/'
                         'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03/outcomes.json')
    assert hashlib.sha256(outcome_path.read_bytes()).hexdigest() == '35f6603726f21d717e1da8e75ada8369584fcdcbbacbf3d170981e027dd662fa'
    outcome_rows = load(outcome_path)
    full_outcomes = {(r['block'],r['ability'],r['graph_source'],r['mechanism_strength']):r for r in outcome_rows}
    outcomes = {key:row['outcome'] for key,row in full_outcomes.items()}
    for block in range(21010,21020):
        for ability in (1000,1150,1300):
            for graph in ('expert','learned'):
                off=full_outcomes[(block,ability,graph,0.)]
                on=full_outcomes[(block,ability,graph,.55)]
                assert off['latent_identity']==on['latent_identity']
                assert off['uniform_identity']==on['uniform_identity']
    for result in per_ability:
        ability = result['ability']
        delta = [outcomes[(b,ability,g,.55)] - outcomes[(b,ability,g,0.)]
                 for b in range(21010,21020) for g in ('expert','learned')]
        result.update(latent_delta_on_minus_off_minimum=min(delta),latent_delta_on_minus_off_maximum=max(delta),
                      latent_delta_negative=sum(v<0 for v in delta),latent_delta_zero=sum(v==0 for v in delta))
    assert per_ability[0]['latent_delta_negative']==per_ability[1]['latent_delta_negative']==20
    assert per_ability[2]['latent_delta_zero']==20
    with (ROOT/'research_tracking/runs/cpu-rq1-transitions-20261108-01/paired_snapshot_flags.csv').open(newline='') as stream:
        rows=[r for r in csv.DictReader(stream) if r['candidate']=='graph_package']
    cross=Counter((r['r_changed']=='True',r['a_changed']=='True') for r in rows)
    assert dict(cross)=={(True,True):5,(True,False):55,(False,True):17,(False,False):1003}
    result=dict(status='PASS_SECONDARY_CANONICAL_SEQUENCE_CHECK',
                total_exact_observable_sequence_pairs=58,paired_conditions=60,per_ability=per_ability,
                paired_lambda_latent_and_uniform_identities=True,
                rq1_ready_preview_cross_table={str(k):v for k,v in cross.items()},
                method_vi='Digest canonical toàn bộ query/correct/probability/step của 120 dòng, bỏ cell_id; đối chiếu cùng block/ability/graph giữa lambda0 và0,55.',
                new_model_or_simulator_calls=0)
    (HERE/'SECONDARY_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
