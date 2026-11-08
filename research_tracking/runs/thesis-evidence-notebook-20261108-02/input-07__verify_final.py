"""Đối chiếu bytes/outputs sau regenerate; không thực thi lại notebook."""
import hashlib
import json
from pathlib import Path
from run_integrity import FILES, PREP, ROOT, dump, inventory, sha, snapshot

before=json.loads((PREP/'before/inventory.json').read_bytes())
after=snapshot(PREP/'after')
assert after[FILES[0]]['sha256']=='5f49bb44138087ebd2d783fa6d8bca7d1ec028bcc970ebde2cfd3e0500b94952'
assert after[FILES[1]]['sha256']=='ed1b7cad329d453d535a233ac8effdf4abf7a22d030a011962f9f04486ef090c'
assert all(before[p]==after[p] for p in FILES[2:])
original=ROOT/'research_tracking/runs/thesis-evidence-notebook-20261108-01'
manifest=json.loads((original/'manifest.json').read_bytes())
assert sha(original/'manifest.json')=='2100a70da6b8da2547bfeba958187b478a53f5e195e8987b1cdb1f5109eee410'
for name,digest in manifest['outputs_sha256'].items(): assert sha(original/name)==digest
assert len(manifest['outputs_sha256'])==7
old=json.loads((original/'thesis_evidence_report.ipynb').read_bytes())
new=json.loads((ROOT/FILES[1]).read_bytes())
assert [c.get('outputs') for c in old['cells']]==[c.get('outputs') for c in new['cells']]
assert len(new['cells'])==14 and len({c['id'] for c in new['cells']})==14
assert [c['execution_count'] for c in new['cells'] if c['cell_type']=='code']==list(range(1,8))
first=''.join(new['cells'][1]['source'])
assert 'exec(compile(builder_payload' in first and 'runpy.run_path' not in first
assert after[FILES[0]]['sha256'] in first
replacement=json.loads((PREP/'replacement-before.json').read_bytes())
assert sha(PREP/'notebook-before.ipynb')==before[FILES[1]]['sha256']==replacement['backup_sha256']
records=[]
for trial,rc,changes in [('trial01-red',1,[]),('trial02-green',0,[]),('trial03-regenerate',0,[FILES[1]])]:
    row=json.loads((PREP/trial/'run.json').read_bytes())
    assert row['returncode']==rc and not row['timed_out'] and row['changed_paths']==changes
    for name,metadata in row['before'].items():
        assert sha(PREP/trial/'source-before'/name.replace('/','__'))==metadata['sha256']
    records.append(dict(trial=trial,returncode=rc,controller_seconds=row['controller_seconds'],changed_paths=changes))
assert 'Ran 3 tests' in (PREP/'trial01-red/execution.log').read_text() and 'FAILED (failures=3)' in (PREP/'trial01-red/execution.log').read_text()
assert 'Ran 12 tests' in (PREP/'trial02-green/execution.log').read_text() and '\nOK\n' in (PREP/'trial02-green/execution.log').read_text()
build=json.loads((PREP/'trial03-regenerate/execution.log').read_text())
assert (build['inputs'],build['claims'],build['pointers'])==(28,14,104)
cumulative=sum(r['controller_seconds'] for r in records)
assert cumulative<=30
receipt=dict(status='VERIFIED_SINGLE_PAYLOAD_REPORT_INTEGRITY_NOT_KERNEL_QA',
             before=before,after=after,trials=records,cumulative_controller_seconds=cumulative,budget_seconds=30,
             regression_red=dict(tests=3,failures=3),regression_green=dict(tests=12,failures=0),
             old_bundle_outputs_preserved=7,new_executed_code_cells=7,cached_outputs_identical_to_v1=True,
             verified_inputs=28,verified_claims=14,verified_pointers=104,
             model_or_simulator_runs=0,kernels=0,remote_calls=0,
             limitations_vi='Stdlib execution/JSON subset only; chưa Jupyter kernel/nbformat library/visual QA. Không thêm nghiên cứu hoặc independent N.')
dump(PREP/'final-verification.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k not in ('before','after','trials')}))
