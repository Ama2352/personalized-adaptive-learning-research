"""Đối chiếu observable tape giữa lambda0/.55 trên các trajectory cached."""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PARENT = ROOT / 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-02'
CHILD = ROOT / 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path):
    with path.open(encoding='utf-8-sig') as stream:
        for line in stream:
            yield json.loads(line)


def main():
    started = time.perf_counter()
    parent_manifest = load(ROOT/'research_tracking/runs/rq2-fresh-graph-source-attempt02-20261109-01/manifest.json')
    child_manifest = load(ROOT/'research_tracking/runs/rq2-fresh-graph-recovery-20261110-01/manifest.json')
    worker_pin = child_manifest['outputs_sha256'][str((CHILD/'worker_run.json').relative_to(ROOT)).replace('\\','/')]
    assert sha(CHILD/'worker_run.json') == worker_pin
    worker = load(CHILD/'worker_run.json')
    pins = {CHILD/'worker_run.json': worker_pin}
    for name in ('cell_ledger.jsonl','observables.jsonl'):
        pins[PARENT/name] = parent_manifest['sources_sha256'][(PARENT/name).relative_to(ROOT).as_posix()]
        pins[CHILD/name] = worker['outputs_sha256'][name]
    reference = load(CHILD/'parent_reference.json')
    pins[CHILD/'parent_reference.json'] = child_manifest['outputs_sha256'][(CHILD/'parent_reference.json').relative_to(ROOT).as_posix()]
    for p, h in pins.items():
        assert sha(p) == h, p.name
    keep_parent = set(reference['complete_cells'])
    assert len(keep_parent) == 61 and reference['excluded_partial_cell'] == 'F062'
    cells = {}
    observations = defaultdict(list)
    for source, parent in ((PARENT, True), (CHILD, False)):
        for row in lines(source/'cell_ledger.jsonl'):
            if row['event'] != 'RESERVED_BEFORE_WORLD':
                continue
            cell = row['cell']
            cell_id = cell['cell_id']
            if parent and cell_id not in keep_parent:
                continue
            assert cell_id not in cells
            cells[cell_id] = cell
        for row in lines(source/'observables.jsonl'):
            if parent and row['cell_id'] not in keep_parent:
                continue
            assert row['cell_id'] in cells
            observations[row['cell_id']].append(row)
    assert len(cells) == len(observations) == 120
    by_condition = {}
    for cell_id, cell in cells.items():
        rows = sorted(observations[cell_id], key=lambda r:r['step'])
        assert len(rows) == 120 and [r['step'] for r in rows] == list(range(120))
        key = (cell['block'],cell['ability'],cell['graph'],cell['mechanism_strength'])
        assert key not in by_condition
        by_condition[key] = rows
    output = []
    for block in range(21010,21020):
        for ability in (1000,1150,1300):
            for graph in ('full','learned'):
                off = by_condition[(block,ability,graph,0.)]
                on = by_condition[(block,ability,graph,.55)]
                compared = list(zip(off,on))
                output.append(dict(block=block,ability=ability,graph=graph,positions=120,
                    changed_question=sum(a['query']['question']!=b['query']['question'] for a,b in compared),
                    changed_query_full=sum(a['query']!=b['query'] for a,b in compared),
                    changed_correct=sum(a['correct']!=b['correct'] for a,b in compared),
                    changed_probability=sum(a['probability']!=b['probability'] for a,b in compared),
                    maximum_probability_difference=max(abs(a['probability']-b['probability']) for a,b in compared)))
    with (HERE/'lambda_observable_pairs.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(output[0]));writer.writeheader();writer.writerows(output)
    summary = dict(status='CACHED_OBSERVABLE_COMPARISON_COMPLETE',paired_conditions=60,positions=7200,
        outcome_cells=120,parent_complete_cells=61,child_complete_cells=59,excluded_parent_partial_rows=30,
        totals={field:sum(row[field] for row in output) for field in ('changed_question','changed_query_full','changed_correct','changed_probability')},
        by_ability=[dict(ability=a,paired_conditions=20,positions=2400,
            **{field:sum(r[field] for r in output if r['ability']==a) for field in ('changed_question','changed_query_full','changed_correct','changed_probability')}) for a in (1000,1150,1300)],
        all_query_label_probability_sequences_equal=all(all(row[f]==0 for f in ('changed_query_full','changed_correct','changed_probability')) for row in output),
        inputs_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        inputs_bytes=sum(p.stat().st_size for p in pins),source_sha_before_after_equal=all(sha(p)==h for p,h in pins.items()),
        new_simulator_or_model_calls=0,elapsed_seconds=time.perf_counter()-started,
        limitations_vi=['Đối chiếu hậu nghiệm trên 10 block và horizon120, một learned graph cố định.',
            'Query, correct và probability là các trường đã lưu, chưa phải toàn bộ trạng thái ẩn của estimator/controller.',
            'Không dùng các vị trí thời gian làm mẫu thống kê độc lập.'])
    (HERE/'LAMBDA_OBSERVABLES.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    main()
