"""Parent kiểm source/raw receipts, không chạy lại inference/model."""
import hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path.cwd();prep=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((prep/'acceptance.json').read_bytes())
for name,digest in a['source_sha256'].items():assert sha(root/name)==digest
base=prep.parent
for label,key in [('unit01','unit'),('integration01','actual_integration')]:
    directory=base/('parallel-gkt-adapter-20261108-'+label)
    run=json.loads((directory/'run.json').read_bytes())
    assert sha(directory/'run.json')==a[key]['run_sha256']
    assert run['returncode']==0 and run['timeout'] is False and run['resource_accepted'] is True
    assert run['source_before']==run['source_after'] and len(run['source_before'])==10
    for name,digest in run['source_before'].items():
        assert sha(root/name)==digest
        for suffix in ['.before','.after']:
            assert sha(directory/(name.replace('/','__')+suffix))==digest
unit=base/'parallel-gkt-adapter-20261108-unit01'
assert sha(unit/'pytest.xml')==a['unit']['junit_sha256']
suites=list(ET.parse(unit/'pytest.xml').iter('testsuite'))
counts={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
assert counts==a['unit']['tests']==dict(tests=32,failures=0,errors=0,skipped=0)
actual=base/'parallel-gkt-adapter-20261108-integration01/result.json'
assert sha(actual)==a['actual_integration']['result_sha256']
r=json.loads(actual.read_bytes())
assert r['actual_torch_loads']==1 and r['mock_loads']==r['optimizer_steps']==0
for name,digest in r['input_sha256'].items():assert sha(root/name)==digest
assert r['source_before']==r['source_after']
scores=r['scores'];p=r['target_population']
assert len(scores)==p['expected_targets']==6
assert sum(s['probability'] is not None for s in scores)==p['scored_targets']==2
assert p['unsupported_targets']==4 and p['research_fitted_targets']==0
assert [s['global_rank'] for s in scores]==list(range(6))
assert [s['source_row'] for s in scores]==list(range(101,107))
assert not any(s['research_fitted'] for s in scores)
assert {s['weight_role'] for s in scores}=={'synthetic_trained_engineering_only'}
assert r['inference_binding']['mapping_provenance']=='caller_declared_inference_mapping_NOT_training_attested'
assert all(r[k] is True for k in ['offline_query_parity','same_node_alias_parity','immutable_probe','fitted_online_promotion_rejected'])
assert a['cumulative_conservative_seconds']<=a['cap_seconds']==60
result=dict(status='PASS_PARENT_SOURCE_AND_RAW_GKT05_REVIEW',
    acceptance_sha256=sha(prep/'acceptance.json'),unit_cases=32,actual_stored_loads_in_original_run=1,
    target_population=p,root_review_model_or_optimizer_calls=0,
    scope='Đã đọc code/tests/controller và kiểm XML/40snapshots/currentSHA/actualstoredresult/inputSHA; không chạy lại model. Không fitted baseline, train-attested mapping hoặc OnlineSession promotion.')
with (prep/'parent-review.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
