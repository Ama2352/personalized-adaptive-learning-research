"""Raw endpoint/control verification only; no native execution or effect estimates."""
from pathlib import Path
from collections import Counter
import ast,gzip,hashlib,json,struct,time
START=time.perf_counter();ROOT=Path.cwd();PREP=Path(__file__).resolve().parent
OUT=PREP/'availability-replay-attempt02';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
outer=read(OUT/'run.json');worker=read(OUT/'worker_run.json');owned=read(OUT/'owned_launch_receipt.json')
control=read(OUT/'control_parity.json');plan=read(PREP/'history_availability_plan02.json')
assert sha(OUT/'run.json')=='972f329c0adf4921383590fcc139bdf79ee51a4e8f19782df8392431adf39ef8'
assert outer['status']=='ACCEPTED_ONE_NATIVE_HISTORY_AVAILABILITY_REPLAY' and outer['error'] is None
assert worker['status']=='ACCEPTED_ALGORITHMIC_HISTORY_REPLAY_ALL_CONTROLS_EXACT' and worker['error'] is None
assert outer['source_input_before_sha256']==outer['source_input_after_sha256']==worker['source_input_before_sha256']==worker['source_input_after_sha256']
assert len(outer['source_input_after_sha256'])==25
assert all(sha(ROOT/n)==d for n,d in outer['source_input_after_sha256'].items())
assert all(sha(OUT/n)==d for n,d in outer['outputs_sha256'].items())
assert all(sha(OUT/n)==d for n,d in worker['outputs_sha256'].items())
assert {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}==set(outer['outputs_sha256'])|{'run.json'}
assert owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0
assert owned['actual_worker_in_job_before_GO'] and owned['GO_released'] and owned['popen_handle_closed']
assert owned['worker_returncode_before_cleanup']==0
assert all(sha(OUT/'owned-launch'/n)==d for n,d in owned['output_sha256'].items())
assert worker['completed_cases']==108 and worker['full_control_phase_passed'] is True
assert all(worker[k]==plan['direct_call_caps'] for k in ('direct_attempts','direct_returns','case_reservations'))
assert outer['cumulative_seconds']==outer['prior_charged_seconds']+outer['revision_elapsed_seconds']<=60
def exact(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,float):return struct.pack('>d',a)==struct.pack('>d',b)
 if isinstance(a,dict):return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 return a==b
def rows(path):
 with gzip.open(path,'rt',encoding='utf-8') as f:return [json.loads(line) for line in f]
base=ROOT/plan['cached_bundle'];legacy={(r['variant'],r['learner_id'],r['event_id']):r for r in rows(base/'observed_legacy.jsonl.gz')}
side={(r['variant'],r['learner_id'],r['event_id']):r for r in rows(base/'observed_query_sidecar.jsonl.gz')}
raw=(OUT/'endpoint_records.jsonl').read_bytes();lines=raw.splitlines(keepends=True);endpoints=[json.loads(line) for line in lines]
assert len(endpoints)==108 and len({r['case_id'] for r in endpoints})==108
assert hashlib.sha256(b''.join(lines[:54])).hexdigest()==control['endpoint_records_sha256']
assert control['status']=='PASS_ALL54_EXACT_BEFORE_TRUNCATED_PHASE' and control['arms']==54
ledger=[json.loads(line) for line in (OUT/'case_ledger.jsonl').read_bytes().splitlines()];assert len(ledger)==216
counts=Counter();control_counts=Counter();controls_checked=0
for i,(actual,case) in enumerate(zip(endpoints,plan['cases'])):
 assert {k:actual[k] for k in case}==case
 assert actual['phase']==('control' if i<54 else 'truncated')
 key=(case['variant'],f"{case['seed']}-{case['profile']}",str(case['Hpast']))
 assert exact(actual['query'],side[key]['query']) and actual['cached_target_y_for_evaluation_only']==legacy[key]['correct']
 for field in ('initial_state_sha256','state_before_and_after_target_probes_sha256'):
  assert type(actual[field]) is str and len(actual[field])==64 and all(c in '0123456789abcdef' for c in actual[field])
 assert actual['initial_state_sha256']==endpoints[0]['initial_state_sha256']
 reserved,completed=ledger[2*i:2*i+2];assert reserved['event']=='RESERVED_BEFORE_NATIVE_CONSTRUCTOR' and reserved['case']==case
 counts.update(case['direct_call_reservations'])
 assert reserved['cumulative_reservations']==dict(counts)
 assert completed['event']=='COMPLETED_CASE' and completed['case_id']==case['case_id']
 assert completed['attempts']==completed['returns']==dict(counts)
 if i<54:
  control_counts.update(case['direct_call_reservations']);observation=actual['observation']
  projection={'probability':observation['probability'],'mastery':observation['mastery'],
   'mastered':observation['mastered'],'ready':observation['ready'],'action':observation['full_preview']['concept']}
  assert exact(projection,{k:legacy[key][k] for k in projection})
  assert exact(observation['full_preview'],side[key]['preview']) and actual['exact_full_prefix_legacy_parity'] is True
  controls_checked+=1
 else:assert actual['exact_full_prefix_legacy_parity'] is None
assert dict(counts)==worker['direct_attempts'] and dict(control_counts)==control['direct_attempts'] and controls_checked==54
source=(PREP/'history_availability_worker02.py').read_text(encoding='utf-8')
ast.parse(source);assert "assert fingerprint(policy)==before_probe,'target probes changed real policy state'" in source
result={'status':'PASS_RAW_ENDPOINT_AND_CONTROL_VERIFICATION_NO_EFFECT_ESTIMATES','outer_receipt_sha256':sha(OUT/'run.json'),
 'source_input_pins_verified':25,'raw_output_sha_verified':len(outer['outputs_sha256']),
 'unique_native_endpoint_arms':108,'direct_reservations_attempts_returns_exact':worker['direct_attempts'],
 'full_prefix_arm_P_S_M_R_fulltuple_exact_checks':54,'control_phase_precedes_truncated_phase':True,
 'control_stream_prefix_sha_verified':True,'case_reservation_terminal_pairs_verified':108,
 'read_only_target_probes_source_assert_passed_108':True,
 'read_only_probe_limit':'Each endpoint stores one shared before/after fingerprint; equality was asserted in pinned executed source. No independent pair of raw hidden-state dumps exists; no hidden-state reconstruction claimed.',
 'owned_actual_worker_before_GO_and_cleanup_accepted':True,'prior_charged_seconds':outer['prior_charged_seconds'],
 'revision_seconds':outer['revision_elapsed_seconds'],'cumulative_seconds':outer['cumulative_seconds'],
 'new_native_replay_model_or_effect_calculation':False,'elapsed_verification_seconds':time.perf_counter()-START}
with (PREP/'availability_raw_verification02.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
