"""Parent kiểm source và raw epoch artifacts; không train/load model lại."""
import csv,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path.cwd();prep=Path(__file__).resolve().parent;base=prep.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((prep/'acceptance.json').read_bytes())
for name,digest in a['source_sha256'].items():assert sha(root/name)==digest
for name,digest in a['raw_hashes'].items():assert sha(root/name)==digest
for row in a['checkpoint_binaries_referenced_not_copied']:
    p=root/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
for phase in ['pure01','model01']:
    directory=base/('parallel-gkt-pipeline-20261108-'+phase)
    run=json.loads((directory/'run.json').read_bytes())
    assert run['returncode']==0 and run['timeout'] is False and run['resource_accepted'] is True
    assert run['source_before']==run['source_after'] and len(run['source_before'])==13
    for name,digest in run['source_before'].items():
        assert sha(root/name)==digest
        for suffix in ['.before','.after']:assert sha(directory/(name.replace('/','__')+suffix))==digest
suites=list(ET.parse(base/'parallel-gkt-pipeline-20261108-pure01/pytest.xml').iter('testsuite'))
assert {k:sum(int(s.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}==dict(tests=38,failures=0,errors=0,skipped=0)
out=base/'parallel-gkt-pipeline-20261108-model01/output'
m=json.loads((out/'run.json').read_bytes());marker=json.loads((out/'COMPLETE.json').read_bytes())
assert marker['run_manifest_sha256']==sha(out/'run.json') and not (out/'failure.json').exists()
assert m['optimizer_counters']==dict(started_steps=2,returned_steps=2,started_targets=12,returned_targets=12)
assert len(m['epochs'])==2 and m['selected_epoch']==2 and m['fitted_research_model'] is False
events=[json.loads(line) for line in (out/'optimizer_events.jsonl').read_text().splitlines()]
assert [x['event'] for x in events]==['step_started','step_returned','step_started','step_returned']
for epoch in m['epochs']:
    n=epoch['epoch'];p=out/f'epoch-{n:03d}'
    assert epoch['complete_epoch'] is True and len(set(epoch['optimized_source_rows']))==6
    assert epoch['selection']['population']==dict(expected_targets=4,scored_targets=2,unsupported_targets=2,research_fitted_targets=0)
    assert sha(p/'selection.csv')==epoch['selection_csv_sha256']
    cp=p/'weights';assert sha(cp/'COMPLETE.json')==epoch['checkpoint_manifest_sha256']
    cm=json.loads((cp/'COMPLETE.json').read_bytes())
    for name,row in cm['files'].items():assert sha(cp/name)==row['sha256'] and (cp/name).stat().st_size==row['bytes']
    with (p/'selection.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    assert [int(r['source_row']) for r in rows]==[101,102,103,104]
    assert [int(r['global_rank']) for r in rows]==[0,1,2,3]
    assert sum(r['probability']!='' for r in rows)==2
assert (out/'selected_predictions.csv').read_bytes()==(out/'epoch-002/selection.csv').read_bytes()
for used in m['mapping_usage']:
    proof=used['prepared'];assert len(proof['source_rows'])==len(proof['mapped_node_indices'])==6
    assert proof['mapping_sha256']==m['training_encoding']['mapping_sha256'] and used['completed']['optimizer_steps']==1
assert a['cumulative_conservative_seconds']<=a['cap_seconds']==60
result=dict(status='PASS_PARENT_SOURCE_AND_RAW_GKT06_REVIEW',pure_tests=38,source_snapshots_verified=52,
    completed_epochs=2,optimizer_reservations=2,optimizer_body_returns=2,complete_batches=2,
    train_targets_each_epoch=6,selection_population=m['epochs'][0]['selection']['population'],
    selected_epoch=2,root_model_or_optimizer_calls=0,acceptance_sha256=sha(prep/'acceptance.json'),
    scope='Kiểm source, XML, CSV, checkpoints SHA và actual mapping-use receipts; không train/load lại. Mapping chỉ chứng minh cách dùng khai báo, chưa semantics đúng hoặc fitted nghiên cứu/selected refit/resume.')
with (prep/'parent-review.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
