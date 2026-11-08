"""Kiểm độc lập artifact CPU dummy đã nhận; không load/train model hoặc dữ liệu thật."""
import hashlib,json,math
from pathlib import Path
w=Path(__file__).resolve().parent;b=w/'received-cpu-worker-evidence01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((b/name).read_bytes())
e_name='linux-cpu-dummy-execution-20261108-01/result.json'
e=read(e_name);actual=json.loads((w/'cpu-dummy-execute02-actual-rpc-summary.json').read_bytes())['summary']
assert sha(b/e_name)==actual['result_sha256']
assert e['status']=='ACCEPTED_NATIVE_CPU_DUMMY_ENGINEERING_ONLY' and e['child_cleanup_accepted'] is True
assert all(math.isfinite(e[k]) and 0<=e[k]<=330 for k in ('elapsed_seconds','elapsed_wall_seconds'))
out='experiments/akt/results/ctx-linux-20261108-01/'
m=read(out+'manifest.json');r=read(out+'watchdog-resources.json');s=m['summary'];t=s['training'];coverage=s['coverage']
assert sha(b/(out+'manifest.json'))==e['native_manifest_sha256']
assert sha(b/(out+'watchdog-resources.json'))==e['watchdog_resources_sha256']
assert m['status']=='completed' and m['phase']=='smoke' and m['run_id']=='ctx-linux-20261108-01'
assert m['approved_caps']==e['bindings']['caps']
assert m['approved_caps']['max_steps']==2 and m['approved_caps']['max_seconds']==120 and m['approved_caps']['max_wall_seconds']==300
assert m['approved_caps']['max_rss_bytes']==2*1024**3
assert t['optimizer_steps']==t['nonzero_gradient_steps']==t['parameter_update_steps']==2
assert t['valid_targets']==t['optimized_target_rows']==t['processed_target_rows']==48
assert t['windows_processed']==6 and t['complete_epoch'] is True
assert t['resource']['peak_rss_bytes']<=2*1024**3
assert coverage['status']=='complete' and coverage['prediction_rows']==coverage['expected_rows']==8 and coverage['unseen_rows']==0
assert sum(row['rows'] for row in coverage['shards'])==8 and coverage['unique_users']==1
assert s['checkpoint_reload_state_exact'] is True and s['outer_users_requested'] is False and s['holdout_requested'] is False
assert r['status']=='completed' and r['worker_returncode']==0 and r['worker_pid']>1
assert all(row['pid']==r['worker_pid'] for row in t['resource']['samples'])
public=next(row for row in e['children'] if row['name']=='native-smoke')
assert any(row['event']=='watchdog-after-worker-spawn' and row['pid']==public['pid'] and row['worker_pid']==r['worker_pid'] for row in r['parent_events'])
config=read('linux-cpu-dummy-preparation-20261108-01/execution-config.json')
proposal=read('linux-cpu-dummy-preparation-20261108-01/proposed-authorization.json')
auth=read('linux-cpu-dummy-execution-20261108-01/authorization.json')
assert config['execution_enabled'] is True and config['n_pid']==0 and config['device']=='cpu'
assert proposal['approved'] is False and auth['approved'] is True and proposal['identity']==auth['identity']
assert auth['caps']==m['approved_caps'] and m['authorized_config_sha256']==auth['config_sha256']
assert m['identity']['worker_context_sha256']==auth['identity']['worker_context_sha256']==e['bindings']['context_sha256']
for key,field in {'gate2_report_sha256':'report_sha256','gate2_test_log_sha256':'test_log_sha256','gate2_pointer_sha256':'pointer_sha256'}.items():
 assert m['gate_records']['gate2'][field]==auth['identity'][key]
marker=read('artifacts/akt/synthetic/ctx-linux-20261108-01/SYNTHETIC_ONLY.json')
assert marker['synthetic_only'] is True and marker['real_data_authorized'] is False
transport=read('acceptance.json');assert transport['files']==32
for row in transport['copies']:
 assert row['sha256_before_copy']==row['sha256_after_copy']==sha(b/row['path'])
for row in transport['binary_omissions']:
 assert row['expected_sha256']==row['sha256_before']==row['sha256_after'] and row['body_exported'] is False
checkpoint=next(row for row in transport['binary_omissions'] if row['path'].endswith('.pt'))
assert checkpoint['expected_sha256']==s['checkpoint_sha256'] and checkpoint['path']==out+s['selection_checkpoint']
result={'status':'PASS_PARENT_INDEPENDENT_NATIVE_CPU_DUMMY_ARTIFACT_REVIEW','phase_result_sha256':sha(b/e_name),'native_manifest_sha256':sha(b/(out+'manifest.json')),'text_artifacts_verified':32,'genuine_optimizer_updates':2,'trained_targets':48,'training_windows':6,'validation_predictions':8,'checkpoint_reload_state_exact':True,'checkpoint_sha256':s['checkpoint_sha256'],'native_worker_returncode':0,'elapsed_seconds':e['elapsed_seconds'],'binary_payloads_local_pending':4,'scope_vi':'CPU dummy pipeline; không hiệu quả nghiên cứu/CUDA/resume/refit. Binary hiện mới hash-verified remote, durability local đang làm riêng.'}
with (w/'parent-cpu-worker-review01.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
