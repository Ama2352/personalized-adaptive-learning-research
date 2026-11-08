"""Kiểm raw accepted reconstruction, không replay/metric/causal inference mới."""
import csv,gzip,hashlib,json,re,runpy
from pathlib import Path
root=Path.cwd();prep=Path(__file__).resolve().parent;out=prep/'closed-loop-fast-model-attempt01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((prep/'closed_loop_fast_model_attempt01_frozen.json').read_bytes())
assert frozen['run_status']=='PASS_CURRENT_SOURCE_RECONSTRUCTION_EXACT_STORED_LEGACY_PARITY'
assert frozen['new_revision_controller_seconds_including_conservative5spy']<=300
assert frozen['overall_seconds_including_prior_failure_and_diagnostic']<=430
for name,row in frozen['actual_raw_files'].items():
    assert sha(out/name)==row['sha256'] and (out/name).stat().st_size==row['bytes']
inventory=json.loads((prep/'closed_loop_fast_source_inventory.json').read_bytes())
for name,digest in inventory['files_sha256'].items():assert sha(root/name)==digest
parity=json.loads((out/'parity.json').read_bytes());control,observed=parity['passes']
assert control['native_state_fingerprints']==observed['native_state_fingerprints']
assert control['uniform_fingerprints']==observed['uniform_fingerprints']
assert len(control['native_state_fingerprints'])==27 and len(control['uniform_fingerprints'])==9
exact=runpy.run_path(str(prep/'closed_loop_observer.py'))['exact']
def load(path):
    with gzip.open(path,'rt',encoding='utf-8') as stream:return [json.loads(line) for line in stream]
history=load(root/'research_tracking/runs/cpu-closedloop-20261107-01/traces.jsonl.gz')
for name in ['control_legacy.jsonl.gz','observed_legacy.jsonl.gz']:
    rows=load(out/name);assert len(rows)==3240 and all(exact(a,b) for a,b in zip(rows,history))
assert load(out/'control_metadata.jsonl.gz')==[]
metadata=load(out/'observed_metadata.jsonl.gz');assert len(metadata)==3240
key=lambda r:(r['seed'],r['profile'],r['variant'],r['step'])
lookup={key(r):r for r in history};assert len(lookup)==3240
nodes_path=root/'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/nodes.csv'
with nodes_path.open(encoding='utf-8-sig',newline='') as stream:nodes={r['concept_id'] for r in csv.DictReader(stream)}
assert len(nodes)==28
seen=set()
for r in metadata:
    k=key(r);assert k not in seen;seen.add(k);old=lookup[k]
    assert set(r['mastered_decisions'])==nodes and all(type(v) is bool for v in r['mastered_decisions'].values())
    assert set(r['balanced_candidates'])<=set(r['eligible_candidates'])<=nodes
    assert r['served_tuple']['concept'] in r['balanced_candidates']
    assert r['served_tuple']=={k:r['query'][k] for k in ['concept','question','difficulty']}
    assert (old['concept'],old['question'],old['timestamp'])==(r['query']['concept'],r['query']['question'],r['query']['timestamp_iso'])
    assert exact(old['prediction'],r['prediction']) and exact(old['y'],r['correct'])
    assert r['is_served_in_simulator'] is True and r['full_mastery_score_vector_available'] is False
    assert r['mastery_ready_capture_phase']=='during_selection_before_bookkeeping'
    assert r['prediction_capture_phase']=='after_selection_bookkeeping_before_environment_interact'
    assert r['phases'][-1]=='after_update'
    for name in ['state_before_selection_sha256','state_after_selection_sha256','state_after_update_sha256']:
        assert re.fullmatch('[a-f0-9]{64}',r[name])
assert seen==set(lookup)
assert parity['original_a585_whole_source_recovered'] is False and parity['new_independent_N']==0
result=dict(status='PASS_PARENT_RAW_RECONSTRUCTION_REVIEW_NO_NEW_METRICS',
    raw_files_verified=10,source_bindings_verified=len(inventory['files_sha256']),
    legacy_rows_exact_each_pass=3240,metadata_rows_verified=3240,mastery_decisions_per_row=28,
    final_state_pairs_verified=27,uniform_pairs_verified=9,model_or_optimizer_calls=0,
    scope='Tái dựng từ nguồn hiện có; chưa tìm được runner lịch sử đầy đủ. Không tính predictive metrics giữa các quỹ đạo khác nhau, CI, suy luận nhân quả hoặc bổ sung ngược metadata lịch sử.',
    supersedes='parent-closed-loop-fast-review.json: chỉ sửa diễn đạt scope; các giá trị kiểm chứng giữ nguyên.')
with (prep/'parent-closed-loop-fast-review02.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
