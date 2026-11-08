"""Independent arithmetic from raw endpoints; never import/rerun analyzer/native."""
from pathlib import Path
import hashlib,json,math,struct,time
START=time.perf_counter();ROOT=Path.cwd();PREP=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
plan=read(PREP/'availability_analysis_plan02.json');OUT=PREP/'availability-cached-analysis01'
assert sha(PREP/'analyze_history_availability02.py')==plan['analyzer_sha256']
assert all(sha(ROOT/n)==d for n,d in plan['inputs_sha256'].items())
capture=read(PREP/'availability_analysis_root_dispatch01.json')
assert capture['kind']=='ROOT_TOOL_CAPTURE_NOT_RAW_STDOUT_BYTES' and capture['tool']['exit_code']==0
assert capture['outer_observed_milliseconds']<=10000 and capture['tool']['wall_time_seconds']<=10
summary=read(OUT/'summary.json');pairs=read(OUT/'unique_pairs.json');nominal=read(OUT/'nominal_aliases.json')
raw=[json.loads(x) for x in (PREP/'availability-replay-attempt02/endpoint_records.jsonl').read_bytes().splitlines()]
index={(r['seed'],r['profile'],r['Hpast'],r['available_length'],r['variant']):r for r in raw};assert len(index)==108
keys={(r['seed'],r['profile'],r['Hpast'],r['available_length']):r for r in pairs};assert len(keys)==len(pairs)==54
def exact(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,float):return struct.pack('>d',a)==struct.pack('>d',b)
 if isinstance(a,dict):return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
 if isinstance(a,(tuple,list)):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 return a==b
def measurements(r):
 p=r['observation']['probability'];y=r['cached_target_y_for_evaluation_only'];pclip=max(1e-15,min(1-1e-15,p))
 # log1p independently evaluates the same declared LL formula.
 return dict(p=p,LL=-y*math.log(pclip)-(1-y)*math.log1p(-pclip),Brier=(p-y)**2)
expected_values={};unique_numeric_checks=0
for key,row in keys.items():
 seed,profile,H,L=key
 f,e=(index[(*key,v)] for v in ('graph_package','empty_graph_package'))
 ff,ef=(index[(seed,profile,H,H,v)] for v in ('graph_package','empty_graph_package'))
 assert all(exact(r['query'],f['query']) and exact(r['cached_target_y_for_evaluation_only'],f['cached_target_y_for_evaluation_only']) for r in (e,ff,ef))
 a,b,c,d=map(measurements,(f,e,ff,ef));values={}
 for metric in ('p','LL','Brier'):
  graph=a[metric]-b[metric];fw=a[metric]-c[metric];ew=b[metric]-d[metric]
  interaction=fw-ew
  values.update({f'graph_delta_{metric}':graph,f'full_arm_window_minus_full_history_{metric}':fw,
   f'empty_arm_window_minus_full_history_{metric}':ew,f'availability_interaction_{metric}':interaction})
 values['absolute_graph_delta_p']=abs(a['p']-b['p'])
 values.update(graph_P_changed=not exact(a['p'],b['p']),
  graph_full_preview_changed=not exact(f['observation']['full_preview'],e['observation']['full_preview']),
  full_arm_preview_vs_full_history_changed=not exact(f['observation']['full_preview'],ff['observation']['full_preview']),
  empty_arm_preview_vs_full_history_changed=not exact(e['observation']['full_preview'],ef['observation']['full_preview']))
 for n,v in values.items():
  if type(v) is bool:assert row[n] is v
  else:assert abs(row[n]-v)<=1e-12;unique_numeric_checks+=1
 expected_values[key]=values
assert len(nominal)==81 and len(summary['groups'])==144
seen=set();summary_numeric_checks=summary_count_checks=0
for group in summary['groups']:
 context,H,label=group['context'],group['Hpast'],group['nominal_window'];ident=(context,H,label);assert ident not in seen;seen.add(ident)
 L=H if label=='full' else min(int(label),H);assert group['available_length']==L
 assert group['alias_of_full_history_native_case']==(label!='full' and L==H)
 selected=[]
 for key,v in expected_values.items():
  seed,profile,h,l=key
  if (h,l)!=(H,L):continue
  parts=context.split(':')
  if context!='pooled' and ((parts[0]=='profile' and profile!=parts[1]) or (parts[0]=='seed' and seed!=int(parts[1])) or (parts[0]=='trajectory' and (seed,profile)!=(int(parts[1]),parts[2]))):continue
  selected.append(v)
 assert len(selected)==group['same_target_pairs']==(9 if context=='pooled' else 1 if context.startswith('trajectory:') else 3)
 for n,v in selected[0].items():
  if type(v) is bool:assert sum(r[n] for r in selected)==group[n];summary_count_checks+=1
  else:assert abs(math.fsum(r[n] for r in selected)/len(selected)-group['mean_'+n])<=1e-12;summary_numeric_checks+=1
for row in nominal:
 key=(row['seed'],row['profile'],row['Hpast'],row['available_length']);label=row['nominal_window'];H=key[2]
 assert row['native_pair_id']==keys[key]['native_pair_id']
 assert key[3]==(H if label=='full' else min(int(label),H))
 assert all(exact(row[n],v) for n,v in keys[key].items())
assert summary_numeric_checks==144*13 and summary_count_checks==144*4
assert all(sha(ROOT/n)==d for n,d in plan['inputs_sha256'].items())
result={'status':'PASS_INDEPENDENT_ALL_AVAILABILITY_NUMERIC_CELLS','method':'Separate raw-endpoint implementation with log1p, no analyzer/native import or rerun',
 'input_pins_verified':len(plan['inputs_sha256']),'source_and_plan_pins_verified':2,'unique_native_endpoint_arms':108,
 'unique_pairs_verified':54,'unique_pair_numeric_checks':unique_numeric_checks,'nominal_alias_pairs_verified':81,
 'summary_rows_verified':144,'summary_mean_numeric_checks':summary_numeric_checks,'summary_boolean_count_checks':summary_count_checks,
 'target_query_label_identity_preserved':True,'all_aliases_explicit_no_newN':True,'raw_native_receipt_sha256':sha(PREP/'availability-replay-attempt02/run.json'),
 'analysis_capture_kind':capture['kind'],'capture_is_not_raw_stdout_bytes':True,
 'source_input_after_sha256':plan['inputs_sha256'],'output_sha256':{p.name:sha(p) for p in OUT.iterdir()},
 'native_model_teacher_world_RNG_optimizer_or_new_effect_search':False,'elapsed_seconds':time.perf_counter()-START}
with (PREP/'availability_analysis_verification02.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='source_input_after_sha256'},indent=2))
