"""Revision02 SOURCE PREPARATION ONLY; root must approve exact pins before dispatch.

Native whole-policy available-history intervention, not teacher/learning outcome.
Full-prefix exact controls complete FIRST; failed/partial runs never interpretable.
"""
import time
START=time.perf_counter()
from pathlib import Path
from collections import Counter,deque
from dataclasses import is_dataclass
import argparse,copy,gzip,hashlib,json,math,os,struct,sys,traceback
ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def exact(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,float):return struct.pack('>d',a)==struct.pack('>d',b)
 if isinstance(a,dict):return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 return a==b
def write(path,value):
 with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def read_rows(path,limit):
 assert path.stat().st_size<=2*1024**2
 with gzip.open(path,'rb') as f:content=f.read(limit+1)
 assert len(content)<=limit
 lines=content.splitlines();assert len(lines)==3240
 result={}
 for line in lines:
  assert len(line)<=65536
  row=json.loads(line);key=(row['variant'],row['learner_id'],row['event_id'])
  assert key not in result;result[key]=row
 return result
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
 parser.add_argument('--remaining-seconds',type=float,required=True);args=parser.parse_args()
 assert Path(sys.prefix).resolve()==ROOT/'.venv'
 assert math.isfinite(args.remaining_seconds) and 0<args.remaining_seconds<=60
 PLAN=PREP/'history_availability_plan02.json';assert sha(PLAN)==args.plan_sha256
 plan=json.loads(PLAN.read_bytes());OUT=PREP/plan['output_directory']
 dispatch=json.loads((OUT/'dispatch.json').read_bytes())
 assert dispatch['status']=='RESERVED_ONE_ATTEMPT_NO_RETRY' and dispatch['plan_sha256']==args.plan_sha256
 assert dispatch['approval_reference'].strip()
 expected={**plan['inputs_sha256'],**plan['source_sha256'],PLAN.relative_to(ROOT).as_posix():args.plan_sha256}
 assert all(sha(ROOT/name)==d for name,d in expected.items())
 assert dispatch['prior_charged_seconds']==plan['cumulative_prior_seconds']
 sys.path.insert(0,str(ROOT/'scripts/research'))
 from windows_owned_worker import worker_gate
 owner=worker_gate()  # Source/plan pinned first; still BEFORE knowledge_tracing/NumPy/pandas.
 assert owner['status']=='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE'
 assert owner['worker']['pid']==os.getpid() and owner['parent_owner']['pid']==dispatch['worker_parent_pid']
 sys.path.insert(0,str(ROOT/'src'))
 from knowledge_tracing.akt.resources import memory_snapshot
 limits=plan['resource_limits'];memory_events=[]
 deadline=START+args.remaining_seconds
 def clock():
  if time.perf_counter()>=deadline:raise TimeoutError('native replay cooperative deadline')
 def guard(stage):
  clock();sample=memory_snapshot()
  for k in ('process_rss_bytes','system_available_ram_bytes'):
   assert type(sample[k]) is int and sample[k]>=0,'unknown memory telemetry'
  peak=sample['process_peak_rss_bytes'];assert peak is None or type(peak) is int and peak>=0
  if max(sample['process_rss_bytes'],peak or 0)>limits['max_rss_bytes']:raise MemoryError('process RSS ceiling')
  if sample['system_available_ram_bytes']<limits['min_available_ram_bytes']:raise MemoryError('free RAM floor')
  clock();memory_events.append({'stage':stage,'elapsed_seconds':time.perf_counter()-START,**sample})
 guard('before_numpy_pandas_native_import')
 import numpy as np
 import pandas as pd
 from knowledge_tracing.paper2_reference import load_reference
 guard('after_native_import_before_loader')
 assert 'torch' not in sys.modules
 counts=Counter();returns=Counter();reservations=Counter();results=[];error=None;control_passed=False
 phase='preflight';active=None;initial_fingerprint=None
 def state_data(v):
  if isinstance(v,np.ndarray):return {'array_shape':list(v.shape),'dtype':str(v.dtype),'bytes_sha256':hashlib.sha256(v.tobytes()).hexdigest()}
  if isinstance(v,np.generic):return state_data(v.item())
  if isinstance(v,pd.Timestamp):return {'timestamp_iso':v.isoformat(),'timestamp_ns':int(v.value)}
  if isinstance(v,float):return {'float_hex':v.hex()}
  if isinstance(v,dict):return {str(k):state_data(x) for k,x in v.items()}
  if isinstance(v,deque):return {'deque_maxlen':v.maxlen,'items':[state_data(x) for x in v]}
  if isinstance(v,(list,tuple)):return [state_data(x) for x in v]
  if is_dataclass(v):return state_data(vars(v))
  if v is None or type(v) in (str,int,bool):return v
  raise TypeError('unknown native state field '+str(type(v)))
 def fingerprint(policy):return digest(state_data(vars(policy)))
 def graph_identity(scope):
  graph=scope['graph'];nodes=list(scope['nodes'])
  edges=sorted((p,c) for p in graph.nodes for c in graph.successors(p))
  return digest({'nodes':nodes,'edges':edges})
 def call(kind,method,*values):
  clock()
  if counts[kind]>=plan['direct_call_caps'][kind]:raise RuntimeError('global direct-call cap '+kind)
  counts[kind]+=1
  value=method(*values);returns[kind]+=1;clock();return value
 try:
  BASE=ROOT/plan['cached_bundle'];manifest=json.loads((BASE/'manifest.json').read_bytes())
  assert manifest['status']=='completed'
  assert all(sha(BASE/n)==d for n,d in manifest['outputs_sha256'].items())
  legacy=read_rows(BASE/'observed_legacy.jsonl.gz',16*1024**2)
  side=read_rows(BASE/'observed_query_sidecar.jsonl.gz',8*1024**2);assert set(legacy)==set(side)
  seedset=(20000,20001,20002);profiles=('PG','PY','PYH');variants=('graph_package','empty_graph_package')
  expected_keys={(v,f'{s}-{p}',str(t)) for v in ('graph_free',*variants) for s in seedset for p in profiles for t in range(120)}
  assert set(legacy)==expected_keys
  for key,row in side.items():
   assert row['legacy_row_sha256']==digest(legacy[key]) and row['update_pairing_verified'] is True
   assert row['query_capture_phase']=='before_delegate_predict' and row['preview_is_served'] is False
   assert row['preview_timestamp_argument'] is None and row['preview_capture_phase']=='after_native_preview_select'
   assert exact(row['correct'],legacy[key]['correct']) and exact(row['probability'],legacy[key]['probability'])
  for s in seedset:
   for p in profiles:
    for t in range(120):
     a,b=(side[(v,f'{s}-{p}',str(t))] for v in variants)
     assert exact(a['query'],b['query']) and exact(a['correct'],b['correct'])
  full=load_reference();empty=load_reference(estimator_edges=[])
  assert all(sha(ROOT/n)==d for n,d in expected.items())
  parity=json.loads((BASE/'parity.json').read_bytes());header=parity['observed']['policy_headers'][0]
  assert graph_identity(full['estimator'])==header['estimator_graph']['sha256']
  assert graph_identity(empty['estimator'])==header['empty_estimator_graph']['sha256']
  assert all(graph_identity(r['controller'])==header['controller_graph']['sha256'] for r in (full,empty))
  assert list(full['estimator']['nodes'])==list(empty['estimator']['nodes'])==header['estimator_graph']['nodes']
  expected_initial=header['initial_policy_state_sha256']['graph_package']
  assert expected_initial==header['initial_policy_state_sha256']['empty_graph_package']
  scopes={'graph_package':full['estimator'],'empty_graph_package':empty['estimator']}
  guard('after_loader_and_inputs')
  with (OUT/'case_ledger.jsonl').open('x',encoding='utf-8') as ledger,(OUT/'endpoint_records.jsonl').open('x',encoding='utf-8') as endpoints:
   for case in plan['cases']:
    if phase!=case['phase']:
     if case['phase']=='truncated':
      assert len(results)==54 and all(r['exact_full_prefix_legacy_parity'] for r in results)
      assert sum(c['phase']=='control' for c in plan['cases'])==54
      control_passed=True
      write(OUT/'control_parity.json',{'status':'PASS_ALL54_EXACT_BEFORE_TRUNCATED_PHASE','arms':54,'compared_fields':['P','S28','M','R','full_preview_tuple'],'endpoint_records_sha256':sha(OUT/'endpoint_records.jsonl'),'direct_attempts':dict(counts)})
      ledger.flush();os.fsync(ledger.fileno());endpoints.flush();os.fsync(endpoints.fileno())
     phase=case['phase']
    active=case['case_id'];guard('before_case:'+active)
    assert phase=='control' or control_passed
    for k,n in case['direct_call_reservations'].items():
     assert reservations[k]+n<=plan['direct_call_caps'][k];reservations[k]+=n
    ledger.write(canonical({'event':'RESERVED_BEFORE_NATIVE_CONSTRUCTOR','case':case,'elapsed_seconds':time.perf_counter()-START,'cumulative_reservations':dict(reservations)})+'\n');ledger.flush()
    before=counts.copy();scope=scopes[case['variant']]
    policy=call('policy_constructor',scope['GAMKTPolicy'],True)
    initial=fingerprint(policy);assert initial==expected_initial
    if initial_fingerprint is None:initial_fingerprint=initial
    assert initial==initial_fingerprint
    learner=f"{case['seed']}-{case['profile']}";H,L=case['Hpast'],case['available_length']
    for t in range(H-L,H):
     row=side[(case['variant'],learner,str(t))];q=row['query']
     timestamp=pd.Timestamp(q['timestamp_iso']);assert int(timestamp.value)==q['timestamp_ns']
     probability=call('prior_predict',policy.predict,q['concept'],q['question'],q['difficulty'],timestamp)
     call('update',policy.update,q['concept'],q['question'],q['difficulty'],timestamp,row['correct'],probability)
     # Literal source fixed-runner bookkeeping; no native select in history.
     policy.selection_counts[q['concept']]+=1
     policy.question_counts[q['question']]+=1
     policy.recent_concepts.append(q['concept'])
     policy.current_chapter=scope['chapter_map'][q['concept']]
     if (t-(H-L))%10==9:guard('history_progress:'+active+':'+str(t))
    key=(case['variant'],learner,str(H));q=side[key]['query']
    timestamp=pd.Timestamp(q['timestamp_iso']);assert int(timestamp.value)==q['timestamp_ns']
    before_probe=fingerprint(policy)
    probability=call('target_predict',policy.predict,q['concept'],q['question'],q['difficulty'],timestamp)
    preview=call('preview_select',copy.deepcopy(policy).select)
    preview={'concept':preview[0],'question':preview[1],'difficulty':float(preview[2])}
    observation={'probability':float(probability),'full_preview':preview}
    matched=None
    if phase=='control':
     ready=sorted(call('control_ready_set',policy.ready_set))
     scores={n:float(call('control_mastery_score',policy.mastery_score,n)) for n in scope['nodes']}
     mastered=sorted(n for n in scope['nodes'] if call('control_is_mastered',policy.is_mastered,n))
     observation.update(mastery=scores,mastered=mastered,ready=ready)
     actual={'probability':observation['probability'],'mastery':scores,'mastered':mastered,'ready':ready,'action':preview['concept']}
     stored={n:legacy[key][n] for n in actual}
     matched=exact(actual,stored) and exact(preview,side[key]['preview'])
     if not matched:
      write(OUT/'control_mismatch.json',{'case':case,'actual':actual,'stored':stored,'preview':preview,'stored_preview':side[key]['preview']})
      raise ValueError('full prefix legacy endpoint mismatch; STOP before truncated phase')
    assert fingerprint(policy)==before_probe,'target probes changed real policy state'
    assert counts-before==Counter(case['direct_call_reservations'])
    assert all(counts[k]==returns[k] for k in counts)
    record={**case,'query':q,'cached_target_y_for_evaluation_only':legacy[key]['correct'],
     'observation':observation,'exact_full_prefix_legacy_parity':matched,'initial_state_sha256':initial,
     'state_before_and_after_target_probes_sha256':before_probe,'elapsed_seconds':time.perf_counter()-START}
    results.append(record);endpoints.write(canonical(record)+'\n');endpoints.flush()
    ledger.write(canonical({'event':'COMPLETED_CASE','case_id':active,'attempts':dict(counts),'returns':dict(returns),'elapsed_seconds':time.perf_counter()-START})+'\n');ledger.flush()
    guard('after_case:'+active)
   ledger.flush();os.fsync(ledger.fileno());endpoints.flush();os.fsync(endpoints.fileno())
  assert control_passed and len(results)==108
  assert counts==returns==reservations==Counter(plan['direct_call_caps'])
  assert graph_identity(full['estimator'])==header['estimator_graph']['sha256']
  assert graph_identity(empty['estimator'])==header['empty_estimator_graph']['sha256']
  assert all(graph_identity(r['controller'])==header['controller_graph']['sha256'] for r in (full,empty))
  assert all(sha(ROOT/n)==d for n,d in expected.items())
  assert 'torch' not in sys.modules
  guard('final_postcheck')
 except Exception as exc:
  error={'type':type(exc).__name__,'message':str(exc),'active_case':active,'phase':phase}
  with (OUT/'failure.log').open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
 finally:
  after={n:sha(ROOT/n) for n in expected}
  if after!=expected:error=error or {'type':'SourceDrift','message':'source/input posthash mismatch'}
  elapsed=time.perf_counter()-START
  if elapsed>args.remaining_seconds:error=error or {'type':'ResourceBound','message':'postelapsed over worker allowance'}
  # Parent-owned stdout/stderr remain open until child exit; bind them in outer receipt.
  outputs={f.name:sha(f) for f in OUT.iterdir() if f.is_file() and f.name not in ('worker_run.json','stdout.log','stderr.log')}
  result={'status':'ACCEPTED_ALGORITHMIC_HISTORY_REPLAY_ALL_CONTROLS_EXACT' if error is None else 'REJECTED_RETAIN_NO_RETRY_NO_PARTIAL_CLAIM',
   'error':error,'plan_sha256':args.plan_sha256,'source_input_before_sha256':expected,'source_input_after_sha256':after,
   'direct_attempts':dict(counts),'direct_returns':dict(returns),'case_reservations':dict(reservations),
   'completed_cases':len(results),'full_control_phase_passed':control_passed,'worker_elapsed_seconds':elapsed,
   'worker_allowance_seconds':args.remaining_seconds,'owned_gate':owner,'prior_charged_seconds':plan['cumulative_prior_seconds'],'new_independent_N':0,'explicit_teacher_environment_rng_draw_nn_optimizer_calls':0,
   'scope':'whole native policy available-history intervention, controller bookkeeping included; preview not served, no learning benefit',
   'resource_scope':'cooperative telemetry plus outer process timeout; no OS hard RSS quota or peak allocation attestation',
   'memory_events':memory_events,'outputs_sha256':outputs}
  write(OUT/'worker_run.json',result)
  print(canonical({'status':result['status'],'completed_cases':len(results),'elapsed_seconds':elapsed,'error':error}),flush=True)
 return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
