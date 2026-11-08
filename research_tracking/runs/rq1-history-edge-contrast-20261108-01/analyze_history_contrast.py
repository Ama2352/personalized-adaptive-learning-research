"""Frozen-bin cached arithmetic; no native classes/model/teacher/RNG execution."""
from pathlib import Path
from collections import Counter
import argparse,gzip,hashlib,json,math,struct,sys,time
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
START=time.perf_counter();PREP=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
args=parser.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PLAN=PREP/'history_contrast_plan.json';assert sha(PLAN)==args.plan_sha256
plan=json.loads(PLAN.read_bytes());OUT=PREP/'history-contrast-analysis01';assert not OUT.exists()
assert sha(Path(__file__).resolve())==plan['analyzer_sha256']
for name,digest in plan['inputs_sha256'].items():assert sha(ROOT/name)==digest,name
BASE=ROOT/plan['bundle'];manifest=json.loads((BASE/'manifest.json').read_bytes())
assert manifest['status']=='completed'
assert all(sha(BASE/name)==digest for name,digest in manifest['outputs_sha256'].items())
old=json.loads((BASE/'summary.json').read_bytes());receipt=json.loads((BASE/'run.json').read_bytes())
assert old['population_keys']==1080 and len(old['groups'])==16 and len(old['historical_metric_checks'])==36
assert receipt['status']=='PASS_CACHED_ANALYSIS' and receipt['before_sha256']==receipt['after_sha256']
flags=json.loads((BASE/'event_flags.json').read_bytes());assert len(flags)==1080
SEEDS=(20000,20001,20002);PROFILES=('PG','PY','PYH');VARIANTS=('graph_free','graph_package','empty_graph_package')
expected={(s,p,t) for s in SEEDS for p in PROFILES for t in range(120)}
def exact(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,float):return struct.pack('>d',a)==struct.pack('>d',b)
 if isinstance(a,dict):return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 return a==b
def rowsha(row):return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def readrows(name,limit):
 path=BASE/name;assert path.stat().st_size<=2*1024**2
 with gzip.open(path,'rb') as stream:data=stream.read(limit+1)
 assert len(data)<=limit
 lines=data.splitlines();assert len(lines)==3240
 result={}
 for line in lines:
  assert len(line)<=65536
  row=json.loads(line);key=(row['variant'],row['learner_id'],row['event_id'])
  assert key[0] in VARIANTS and key not in result
  result[key]=row
 return result
legacy=readrows('observed_legacy.jsonl.gz',16*1024**2)
sidecar=readrows('observed_query_sidecar.jsonl.gz',8*1024**2);assert set(legacy)==set(sidecar)
queries={}
for key,row in sidecar.items():
 assert row['learner_id']==f"{row['seed']}-{row['profile']}"
 assert type(row['event_id']) is str and str(int(row['event_id']))==row['event_id']
 logical=(row['seed'],row['profile'],int(row['event_id']));assert logical in expected
 assert row['legacy_row_sha256']==rowsha(legacy[key])
 assert row['query_capture_phase']=='before_delegate_predict' and row['update_pairing_verified'] is True
 assert row['preview_capture_phase']=='after_native_preview_select' and row['preview_is_served'] is False
 assert row['preview_timestamp_argument'] is None
 assert set(row['query'])=={'concept','question','difficulty','timestamp_iso','timestamp_ns'}
 assert set(row['preview'])=={'concept','question','difficulty'}
 assert exact(row['correct'],legacy[key]['correct']) and exact(row['probability'],legacy[key]['probability'])
 queries.setdefault(logical,{})[row['variant']]=row
assert set(queries)==expected
for key,arms in queries.items():
 assert set(arms)==set(VARIANTS)
 full=arms['graph_package']
 assert all(exact(a['query'],full['query']) and exact(a['correct'],full['correct']) for a in arms.values())
index={}
for f in flags:
 key=(f['seed'],f['profile'],int(f['event_id']))
 assert key in expected and key not in index and f['learner_id']==f"{key[0]}-{key[1]}"
 assert str(key[2])==f['event_id']
 assert all(type(f[name]) is float and math.isfinite(f[name]) for name in ('LL_full_minus_empty','Brier_full_minus_empty'))
 assert type(f['full_preview_tuple_changed']) is bool
 arms=queries[key]
 assert f['full_preview_tuple_changed']==(not exact(arms['graph_package']['preview'],arms['empty_graph_package']['preview']))
 index[key]=f
assert set(index)==expected
H=('0','1-10','11-50','>50');C=('0','1-5','>=6')
def hbin(n):return '0' if n==0 else '1-10' if n<=10 else '11-50' if n<=50 else '>50'
def cbin(n):return '0' if n==0 else '1-5' if n<=5 else '>=6'
events=[]
for seed in SEEDS:
 for profile in PROFILES:
  counts=Counter();prefix=[]
  for t in range(120):
   key=(seed,profile,t);q=queries[key]['graph_package']['query'];cid=q['concept']
   assert type(cid) is str and cid
   prior=counts[cid];assert prior==sum(p==cid for p in prefix)
   f=index[key]
   events.append({'seed':seed,'profile':profile,'event_id':str(t),'learner_id':f'{seed}-{profile}',
    'query_concept':cid,'Hpast':t,'concept_prior_count':prior,'history_bin':hbin(t),'concept_bin':cbin(prior),
    'LL_full_minus_empty':f['LL_full_minus_empty'],'Brier_full_minus_empty':f['Brier_full_minus_empty'],
    'full_preview_tuple_changed':f['full_preview_tuple_changed']})
   counts[cid]+=1;prefix.append(cid)
  assert len(prefix)==sum(counts.values())==120
assert len(events)==1080
geometry={str(seed):all(exact(queries[(seed,p,t)]['graph_package']['query'],
 queries[(seed,'PG',t)]['graph_package']['query']) for p in PROFILES for t in range(120)) for seed in SEEDS}
contexts=[('pooled',events)]
contexts += [('profile:'+p,[r for r in events if r['profile']==p]) for p in PROFILES]
contexts += [('seed:'+str(s),[r for r in events if r['seed']==s]) for s in SEEDS]
contexts += [(f'trajectory:{s}:{p}',[r for r in events if r['seed']==s and r['profile']==p]) for s in SEEDS for p in PROFILES]
oldgroups={g['group']:g for g in old['groups']};assert set(oldgroups)==set(n for n,_ in contexts)
def cell(rows,axis,h=None,c=None):
 n=len(rows);change=sum(r['full_preview_tuple_changed'] for r in rows)
 return {'axis':axis,'history_bin':h,'concept_bin':c,'paired_targets':n,
  'LL_full_minus_empty':math.fsum(r['LL_full_minus_empty'] for r in rows)/n if n else None,
  'Brier_full_minus_empty':math.fsum(r['Brier_full_minus_empty'] for r in rows)/n if n else None,
  'full_preview_changes':change,'full_preview_change_rate':change/n if n else None,
  'nonempty_seed_families':len({r['seed'] for r in rows}),
  'nonempty_seed_profile_trajectories':len({(r['seed'],r['profile']) for r in rows})}
groups=[];checks=[]
for name,rows in contexts:
 prior=oldgroups[name];assert len(rows)==prior['paired_snapshot_targets']
 cells=[cell([r for r in rows if r['history_bin']==h],'history',h=h) for h in H]
 cells += [cell([r for r in rows if r['concept_bin']==c],'concept',c=c) for c in C]
 cells += [cell([r for r in rows if r['history_bin']==h and r['concept_bin']==c],'joint',h,c) for h in H for c in C]
 assert len(cells)==19
 for axis in ('history','concept','joint'):
  part=[v for v in cells if v['axis']==axis];assert sum(v['paired_targets'] for v in part)==len(rows)
  assert sum(v['full_preview_changes'] for v in part)==prior['full_preview_tuple_changed']
  for metric in ('LL_full_minus_empty','Brier_full_minus_empty'):
   restored=math.fsum(v[metric]*v['paired_targets'] for v in part if v['paired_targets'])/len(rows)
   residual=restored-prior[metric];assert abs(residual)<=1e-12
   checks.append({'context':name,'partition':axis,'metric':metric,'residual':residual})
 groups.append({'context':name,'paired_targets':len(rows),'cells':cells})
assert len(groups)==16 and sum(len(g['cells']) for g in groups)==304 and len(checks)==96
pooled=groups[0]['cells'];assert [v['paired_targets'] for v in pooled if v['axis']=='history']==[9,90,360,621]
result={'status':'CACHED_DESCRIPTIVE_HISTORY_STRATIFICATION','candidate':'graph_package','reference':'empty_graph_package',
 'paired_targets':1080,'contexts':16,'summary_cells':304,'history_bin_order':H,'concept_bin_order':C,
 'groups':groups,'weighted_metric_reconstruction_checks':checks,
 'query_geometry_exact_across_profiles_within_seed':geometry,
 'full_empty_same_query_label_history_overlap':1080,'source_inputs_sha256':plan['inputs_sha256'],
 'new_independent_N':0,'native_teacher_model_rng_replay_calls':0,
 'limits':['Hpast confounded exactly with sequence time/order, not randomized history intervention',
 'Concept prior is within-learner target-concept exposure, NOT training support/vocab or parent evidence',
 'Package-conditional estimator edges; preview NOT served; no causal ability/history/learning effect, no p/CI']}
assert time.perf_counter()-START<9.5
for name,digest in plan['inputs_sha256'].items():assert sha(ROOT/name)==digest,name
OUT.mkdir(exist_ok=False)
for name,value in [('summary.json',result),('event_bins.json',events)]:
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'paired_targets':1080,'contexts':16,'cells':304,'pooled_cells':pooled},ensure_ascii=False,indent=2))
