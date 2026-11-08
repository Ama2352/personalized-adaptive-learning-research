"""Giữ report cũ nguyên vẹn; current pointer chuyển sang resource rejection audit."""
import hashlib
import json
from pathlib import Path
import sys
root=Path.cwd();sys.path.insert(0,str(root/'src'))
from knowledge_tracing.akt.authorization import require_gate2_evidence
from knowledge_tracing.akt.config import AKTConfig
directory=root/'artifacts/akt/preflight'
report=directory/'gate2-evidence-20261108-graph-prototype-20.json'
pointer=directory/'gate2-current.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='9d86b215bd936f04880bcd9bc775f2016784f279572109c39c017d46375fe351'
assert sha(report)==expected
original=json.loads(report.read_text(encoding='utf-8'))
assert original['status']=='PASS' and original['elapsed_seconds']>original['timeout_seconds']
before=require_gate2_evidence(AKTConfig())
assert before['report_sha256']==expected
pointer_before=pointer.read_bytes();pointer_sha=sha(pointer)
backup=directory/'gate2-pointer-before-resource-audit-20261108-20.json'
with backup.open('xb') as stream:stream.write(pointer_before)
assert sha(backup)==pointer_sha
audit=directory/'gate2-resource-audit-20261108-graph-prototype-20.json'
value={key:original[key] for key in ('schema_version','source_commit','suite','lock_sha256','build_hashes',
    'test_result','test_log_sha256','elapsed_seconds','timeout_seconds')}
value.update(status='REJECTED_RESOURCE_BOUND',functional_status='ALL_724_TESTS_PASSED',
    execution_authorization=False,original_evidence=report.name,original_evidence_sha256=expected,
    reason='Observed elapsed1083.995s exceeds approved540s; old refresh script failed to reject after process exit.',
    cause='UNRESOLVED; do not infer model regression or host suspend from this audit alone.',
    scope='Operational gate rejection only; historical test/report bytes preserved, no model/data/GPU run.')
with audit.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)
old_pointer=json.loads(pointer_before)
new_pointer={'schema_version':1,'evidence_file':audit.name,'evidence_sha256':sha(audit),
    'test_log_file':old_pointer['test_log_file'],'test_log_sha256':old_pointer['test_log_sha256']}
temp=directory/'gate2-current-resource-audit-20261108-20.tmp'
with temp.open('x',encoding='utf-8',newline='\n') as stream:json.dump(new_pointer,stream,sort_keys=True)
temp.replace(pointer)
try:require_gate2_evidence(AKTConfig())
except ValueError:rejected=True
else:raise AssertionError('operational gate was not revoked')
assert sha(report)==expected and sha(backup)==pointer_sha
result={'status':'REVOKED_FOR_EXECUTION','audit_sha256':sha(audit),'original_report_unchanged_sha256':sha(report),
    'pointer_before_sha256':pointer_sha,'pointer_backup_sha256':sha(backup),'pointer_after_sha256':sha(pointer),
    'validator_rejects':rejected,'functional_tests_passed':724,'resource_gate_accepted':False}
with (directory/'gate2-resource-audit-20261108-20-verification.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
state_path=root/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
state['current_software_gate']={'status':'REJECTED_RESOURCE_BOUND','functional_passed':724,
    'observed_elapsed_seconds':original['elapsed_seconds'],'allowed_timeout_seconds':original['timeout_seconds'],
    'original_report_sha256':expected,'current_pointer_rejects':True,
    'next':'Diagnose isolated refit anomaly; postelapsed acceptance guard + regression tests; new source-bound gate required.'}
state['autonomous_engineering_loop']['new_blocker']='Gate20 functional tests pass but operational time contract violated; no training/paid execution may use it.'
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
