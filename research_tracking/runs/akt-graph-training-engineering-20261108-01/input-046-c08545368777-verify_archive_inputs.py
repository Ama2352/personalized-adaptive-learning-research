"""Kiểm raw/SHA/CSV bằng stdlib; không test/model/checkpoint deserialization."""
from pathlib import Path
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET

ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
ADAPTER=PREP.parent/'graph-training-adapter-20261108-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())

def counts(path):
    suites=list(ET.parse(path).getroot().iter('testsuite'))
    return {k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}

def verify():
    receipts={}
    for base,label in ((ADAPTER,'pure01'),(ADAPTER,'pure02'),(PREP,'callback-pure01'),(PREP,'callback-pure02'),(PREP,'actual01'),(PREP,'actual02')):
        d=base/label;r=read(d/'receipt.json');receipts[label]=r
        if r['counts']['tests']:assert counts(d/'pytest.xml')==r['counts']
        assert r['source_before']==r['source_after'] and r['child_reaped']
    assert receipts['pure02']['counts']==dict(tests=34,failures=0,errors=0,skipped=0)
    assert receipts['callback-pure02']['counts']==dict(tests=8,failures=0,errors=0,skipped=0)
    assert receipts['actual01']['counts']==dict(tests=46,failures=3,errors=11,skipped=0)
    assert receipts['actual02']['counts']==dict(tests=46,failures=1,errors=0,skipped=0)
    a=receipts['actual02'];assert a['status']=='FAILED'
    graphcases=[c for c in ET.parse(PREP/'actual02/pytest.xml').getroot().iter('testcase') if c.get('classname','').endswith('test_graph_lifecycle')]
    assert len(graphcases)==6 and all(not list(c) for c in graphcases)
    assert receipts['actual01']['created_run_dirs']==[] and receipts['actual01']['optimizer_reservations']==0
    assert 'available RAM floor' in (PREP/'actual01/stdout.log').read_text()
    correction=read(PREP/'inventory-correction01/receipt.json')
    assert correction['status']=='PASS_READONLY_CORRECTED_INVENTORY_TEST' and correction['new_optimizer_updates']==0
    elapsed=sum(receipts[x]['controller_seconds'] for x in ('actual01','actual02'))+correction['controller_seconds']
    assert math.isclose(elapsed,correction['cumulative_seconds'],abs_tol=1e-10) and elapsed<=60
    ledger=PREP/'actual_optimizer_events.jsonl';events=[json.loads(s) for s in ledger.read_text().splitlines()]
    assert sha(ledger)==a['ledger_sha256']
    assert sum(e['event']=='optimizer_reservation' for e in events)==sum(e['event']=='optimizer_body_returned' for e in events)==4
    binaries=[];outputs=[]
    for name in a['created_run_dirs']:
        d=ROOT/name;assert d.parent==ROOT/'artifacts/akt/synthetic' and d.is_dir() and not d.is_symlink()
        for p in d.iterdir():
            assert p.is_file() and not p.is_symlink()
            if p.suffix=='.pt':binaries.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
            else:outputs.append(p.relative_to(ROOT).as_posix())
    assert len(binaries)==2
    complete=next(ROOT/n for n in a['created_run_dirs'] if Path(n).name.startswith('grapheng-') and '-complete-' in n)
    partial=next(ROOT/n for n in a['created_run_dirs'] if Path(n).name.startswith('grapheng-') and '-partial-' in n)
    result=read(complete/'result.json');training=read(complete/'training.json');selection=read(complete/'selection.json')
    assert result['optimizer_steps']==1 and result['train_targets']==8 and result['reload_max_abs_delta']==0
    assert result['selection_coverage']['expected_rows']==4 and result['selection_coverage']['known_rows']==3 and result['selection_coverage']['unseen_rows']==1
    assert sha(complete/'epoch1.pt')==result['checkpoint_sha256']
    assert training['complete'] and len(training['target_ledger'])==len({tuple(k) for k in training['target_ledger']})==8
    assert (complete/'COMPLETE').read_text().strip()=='complete_graph_engineering_only' and not (complete/'failure.json').exists()
    local=[json.loads(x) for x in (complete/'optimizer_events.jsonl').read_text().splitlines()]
    assert [x['event'] for x in local]==['optimizer_started','optimizer_body_returned','graph_batch_completed']
    changed=local[-1]['changed_parameters']
    assert all(any(n.startswith(prefix) for n in changed) for prefix in ('native.','message_module.','gate_module.')) and 'readout' in changed
    rows=selection['predictions']
    with (complete/'selection.csv').open(newline='',encoding='utf-8') as f:csvrows=list(csv.DictReader(f))
    with (complete/'selection_targets.csv').open(newline='',encoding='utf-8') as f:truth=list(csv.DictReader(f))
    key=lambda r:(r['learner_id'],int(r['source_row']),int(r['global_rank']))
    assert len(rows)==len(csvrows)==len(truth)==4 and [key(r) for r in rows]==[key(r) for r in csvrows]==[key(r) for r in truth]
    assert len({key(r) for r in rows})==4 and all('correct' not in r for r in rows)
    assert [r['global_rank'] for r in rows if r['probability'] is None]==[1]
    assert any(r['graph_applied'] for r in rows)
    fail=read(partial/'failure.json');partial_stats=read(partial/'training.json')
    assert fail['run_accepted'] is False and fail['graph_optimizer_start_reservations']==fail['graph_optimizer_body_returns']==1
    assert not partial_stats['complete'] and partial_stats['valid_targets']==4 and partial_stats['optimizer_steps']==1
    assert all(not (partial/n).exists() for n in ('COMPLETE','result.json','epoch1.pt','selection.csv'))
    current={n:sha(ROOT/n) for n in ('src/knowledge_tracing/akt/graph_training.py','src/knowledge_tracing/akt/training.py',
        'src/knowledge_tracing/akt/simulator_engineering.py','tests/akt/test_graph_training.py','tests/akt/test_graph_lifecycle.py',
        'tests/akt/test_batch_factory.py','tests/akt/test_simulator_engineering.py')}
    for n,h in a['source_before'].items():
        if n=='tests/akt/test_simulator_engineering.py':assert sha(PREP/'test_simulator_engineering.before_inventory_correction.py')==h
        else:assert sha(ROOT/n)==h
    return dict(status='GRAPH_LIFECYCLE_TOY_VERIFIED_WITH_SEPARATE_FIXTURE_RECHECK_NOT_FULL_GATE',
        actual02_raw_suite_status='FAILED',graph_new_tests=6,actual02_counts=a['counts'],
        actual01_counts=receipts['actual01']['counts'],adapter_pure_counts=receipts['pure02']['counts'],callback_pure_counts=receipts['callback-pure02']['counts'],
        actual_plus_readonly_cumulative_seconds=elapsed,actual_cap_seconds=60,global_optimizer_reservations=4,global_optimizer_body_returns=4,
        graph_happy_optimizer_steps=1,graph_partial_optimizer_steps=1,graph_train_targets=8,graph_selection_counts=dict(expected=4,scored=3,oov=1),
        reload_max_abs_delta=0,graph_checkpoint_sha256=result['checkpoint_sha256'],current_source_sha256=current,
        binary_references_not_copied=binaries,selected_output_paths=sorted(outputs),failure_time_available_ram_bytes=None,
        analysis_method='Stdlib read/hash/XML/CSV only; no model/test/optimizer/deserialization',closure_authorized=False)

if __name__=='__main__':
    facts=verify()
    with (PREP/'archive_facts.json').open('x',encoding='utf-8') as f:json.dump(facts,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=facts['status'],facts_sha256=sha(PREP/'archive_facts.json'),cumulative_seconds=facts['actual_plus_readonly_cumulative_seconds'])))
