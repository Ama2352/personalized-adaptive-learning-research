"""Prepared cached full-minus-empty analysis; no model/RNG/source execution.

Do not dispatch before root reviews the exact source/plan SHA. Strict fixed-stream
identity, package-conditional interpretation; no calibration fit or inference.
"""
from pathlib import Path
from collections import Counter
import argparse,gzip,hashlib,json,math,sys,time
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
START=time.perf_counter();PREP=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
args=parser.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PLAN=PREP/'full_empty_plan.json';assert sha(PLAN)==args.plan_sha256
plan=json.loads(PLAN.read_bytes());OUT=PREP/'full-empty-analysis01';assert not OUT.exists()
for path,digest in plan['inputs_sha256'].items():assert sha(ROOT/path)==digest,path
BASE=ROOT/plan['bundle']
manifest=json.loads((BASE/'manifest.json').read_bytes());assert manifest['status']=='completed'
assert all(sha(BASE/name)==digest for name,digest in manifest['outputs_sha256'].items())
sys.path.insert(0,str(BASE))
from observer import exact,row_sha  # Archived pure-stdlib equality helper, not a policy.
parity=json.loads((BASE/'parity.json').read_bytes())
assert parity['status']=='PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY'
assert parity['logical_event_keys']==1080 and parity['new_independent_N']==0
for pass_name in ('control','observed'):
 for header in parity[pass_name]['policy_headers']:
  assert header['parameter_flags']['graph_package'] is True
  assert header['parameter_flags']['empty_graph_package'] is True
  assert header['initial_policy_state_sha256']['graph_package']==header['initial_policy_state_sha256']['empty_graph_package']
  assert header['environment_graph']['sha256']==header['controller_graph']['sha256']==header['estimator_graph']['sha256']
  assert header['estimator_graph']['nodes']==header['empty_estimator_graph']['nodes']
  assert header['empty_estimator_graph']['edges']==[]

VARIANTS=('graph_free','graph_package','empty_graph_package')
SEEDS=(20000,20001,20002);PROFILES=('PG','PY','PYH')
expected={(seed,profile,step) for seed in SEEDS for profile in PROFILES for step in range(120)}
def read_gzip(name,max_bytes):
 path=BASE/name;assert path.stat().st_size<=2*1024**2
 with gzip.open(path,'rb') as stream:data=stream.read(max_bytes+1)
 assert len(data)<=max_bytes,'expanded input cap'
 lines=data.splitlines();assert len(lines)==3240
 result={}
 for line in lines:
  assert len(line)<=65536
  row=json.loads(line);key=(row['variant'],row['learner_id'],row['event_id'])
  assert key[0] in VARIANTS and key not in result
  result[key]=row
 return result
legacy=read_gzip('observed_legacy.jsonl.gz',16*1024**2)
sidecar=read_gzip('observed_query_sidecar.jsonl.gz',8*1024**2)
control=read_gzip('control_legacy.jsonl.gz',16*1024**2)
historical=read_gzip('historical__traces.jsonl.gz',16*1024**2)
assert set(legacy)==set(sidecar)==set(control)==set(historical)
assert all(exact(legacy[k],control[k]) and exact(legacy[k],historical[k]) for k in legacy)
bykey={};concepts=None
for key,row in sidecar.items():
 assert row['variant']==key[0] and row['learner_id']==f"{row['seed']}-{row['profile']}"
 assert type(row['event_id']) is str and str(int(row['event_id']))==row['event_id']
 logical=(row['seed'],row['profile'],int(row['event_id']));assert logical in expected
 assert row['legacy_row_sha256']==row_sha(legacy[key])
 assert row['preview_is_served'] is False and row['preview_timestamp_argument'] is None
 assert row['preview_capture_phase']=='after_native_preview_select'
 assert row['query_capture_phase']=='before_delegate_predict' and row['update_pairing_verified'] is True
 assert row['phases']==['before_predict','after_predict','preview_deepcopy','after_preview_select',
                       'legacy_pre_update','before_update_pairing_verified','after_update']
 assert exact(row['probability'],legacy[key]['probability']) and exact(row['correct'],legacy[key]['correct'])
 assert row['preview']['concept']==legacy[key]['action']
 assert set(row['query'])=={'concept','question','difficulty','timestamp_iso','timestamp_ns'}
 assert set(row['preview'])=={'concept','question','difficulty'}
 scores=legacy[key]['mastery'];assert len(scores)==28 and all(type(x) is float and math.isfinite(x) and 0<=x<=1 for x in scores.values())
 if concepts is None:concepts=set(scores)
 assert set(scores)==concepts
 assert set(legacy[key]['mastered'])<=concepts and set(legacy[key]['ready'])<=concepts
 assert legacy[key]['action'] in legacy[key]['ready']
 bykey.setdefault(logical,{})[key[0]]={'legacy':legacy[key],'sidecar':row}
assert set(bykey)==expected
gf_valid=True;gf_reasons=[]
for logical,arms in bykey.items():
 assert set(arms)==set(VARIANTS)
 full,empty=arms['graph_package'],arms['empty_graph_package']
 assert exact(full['sidecar']['query'],empty['sidecar']['query']) and exact(full['legacy']['correct'],empty['legacy']['correct'])
 for arm in (full,empty):
  assert type(arm['legacy']['correct']) is int and arm['legacy']['correct'] in (0,1)
  p=arm['legacy']['probability'];assert type(p) is float and math.isfinite(p) and 0<=p<=1
 gf=arms['graph_free']
 if (not exact(gf['sidecar']['query'],full['sidecar']['query'])
      or not exact(gf['legacy']['correct'],full['legacy']['correct'])
      or type(gf['legacy']['probability']) is not float or not math.isfinite(gf['legacy']['probability'])
      or not 0<=gf['legacy']['probability']<=1):
  gf_valid=False;gf_reasons.append(logical)

# Same equation/clip as diagnostics.compare_decision_traces; no arbitrary score threshold.
def ll(p,y):
 clipped=min(1-1e-15,max(1e-15,p))
 return -y*math.log(clipped)-(1-y)*math.log(1-clipped)
flags=[]
for key in sorted(expected):
 arms=bykey[key];f,e=(arms[v]['legacy'] for v in ('graph_package','empty_graph_package'))
 fs,es=(arms[v]['sidecar'] for v in ('graph_package','empty_graph_package'))
 pf,pe,y=f['probability'],e['probability'],f['correct']
 s_changed=[c for c in sorted(concepts) if not exact(f['mastery'][c],e['mastery'][c])]
 crossing=set(f['mastered'])^set(e['mastered']);r_diff=set(f['ready'])^set(e['ready'])
 union=set(f['ready'])|set(e['ready'])
 row={'seed':key[0],'profile':key[1],'event_id':str(key[2]),'learner_id':f'{key[0]}-{key[1]}',
  'P_changed':not exact(pf,pe),'absolute_delta_P':abs(pf-pe),
  'LL_full_minus_empty':ll(pf,y)-ll(pe,y),'Brier_full_minus_empty':(pf-y)**2-(pe-y)**2,
  'S_event_changed':bool(s_changed),'S_concept_pairs_changed':len(s_changed),
  'S_absolute_delta_sum':math.fsum(abs(f['mastery'][c]-e['mastery'][c]) for c in concepts),
  'M_event_changed':bool(crossing),'M_concept_crossings':len(crossing),
  'R_event_changed':bool(r_diff),'R_membership_symmetric_difference':len(r_diff),
  'R_jaccard':len(set(f['ready'])&set(e['ready']))/len(union) if union else 1.,
  'preview_concept_changed':fs['preview']['concept']!=es['preview']['concept'],
  'preview_question_changed':fs['preview']['question']!=es['preview']['question'],
  'preview_difficulty_changed':not exact(fs['preview']['difficulty'],es['preview']['difficulty']),
  'full_preview_tuple_changed':not exact(fs['preview'],es['preview'])}
 if gf_valid:
  pg=arms['graph_free']['legacy']['probability']
  row.update(LL_full_minus_GF=ll(pf,y)-ll(pg,y),LL_empty_minus_GF=ll(pe,y)-ll(pg,y),
             Brier_full_minus_GF=(pf-y)**2-(pg-y)**2,Brier_empty_minus_GF=(pe-y)**2-(pg-y)**2)
 flags.append(row)

def summarize(rows,label):
 n=len(rows);assert n
 counts={name:sum(r[name] for r in rows) for name in ('P_changed','S_event_changed','S_concept_pairs_changed',
  'M_event_changed','M_concept_crossings','R_event_changed','R_membership_symmetric_difference',
  'preview_concept_changed','preview_question_changed','preview_difficulty_changed','full_preview_tuple_changed')}
 result={'group':label,'paired_snapshot_targets':n,'paired_supported_prediction_targets':n,
  'concept_score_pairs':28*n,'concept_mastery_decisions':28*n,'preview_tuples':n,**counts,
  'mean_absolute_delta_P':math.fsum(r['absolute_delta_P'] for r in rows)/n,
  'mean_absolute_delta_S':math.fsum(r['S_absolute_delta_sum'] for r in rows)/(28*n),
  'mean_R_jaccard':math.fsum(r['R_jaccard'] for r in rows)/n,
  'LL_full_minus_empty':math.fsum(r['LL_full_minus_empty'] for r in rows)/n,
  'Brier_full_minus_empty':math.fsum(r['Brier_full_minus_empty'] for r in rows)/n,
  'P_preview_table':[{'P_changed':p,'full_preview_changed':a,
      'count':sum(r['P_changed']==p and r['full_preview_tuple_changed']==a for r in rows),
      'conditional_denominator':sum(r['P_changed']==p for r in rows)}
       for p in (False,True) for a in (False,True)]}
 if gf_valid:
  decomposition={name:math.fsum(r[name] for r in rows)/n for name in
   ('LL_full_minus_GF','LL_empty_minus_GF','Brier_full_minus_GF','Brier_empty_minus_GF')}
  decomposition['LL_residual']=decomposition['LL_full_minus_GF']-(result['LL_full_minus_empty']+decomposition['LL_empty_minus_GF'])
  decomposition['Brier_residual']=decomposition['Brier_full_minus_GF']-(result['Brier_full_minus_empty']+decomposition['Brier_empty_minus_GF'])
  assert abs(decomposition['LL_residual'])<=1e-12 and abs(decomposition['Brier_residual'])<=1e-12
  result['baseline_cancellation']=decomposition
 return result
groups=[summarize(flags,'pooled')]
groups += [summarize([r for r in flags if r['profile']==p],'profile:'+p) for p in PROFILES]
groups += [summarize([r for r in flags if r['seed']==s],'seed:'+str(s)) for s in SEEDS]
groups += [summarize([r for r in flags if r['seed']==s and r['profile']==p],f'trajectory:{s}:{p}') for s in SEEDS for p in PROFILES]
legacy_checks=[]
if gf_valid:
 old=json.loads((BASE/'historical__comparisons.json').read_bytes())
 for comparison in old:
  selected=next(g for g in groups if g['group']==f"trajectory:{comparison['seed']}:{comparison['profile']}")
  suffix='full' if comparison['candidate']=='graph_package' else 'empty'
  for metric,old_field in [('LL','candidate_minus_reference_log_loss'),('Brier','candidate_minus_reference_brier')]:
   value=selected['baseline_cancellation'][f'{metric}_{suffix}_minus_GF']
   residual=value-comparison[old_field];assert abs(residual)<=1e-12
   legacy_checks.append({'seed':comparison['seed'],'profile':comparison['profile'],'candidate':comparison['candidate'],
                        'metric':metric,'residual':residual})
result={'status':'CACHED_FIXED_STREAM_CONDITIONAL_EDGE_SET_CONTRAST','reference':'empty_graph_package',
 'candidate':'graph_package','population_keys':1080,'groups':groups,'GF_decomposition_eligible':gf_valid,
 'GF_decomposition_skip_reasons':gf_reasons,'historical_metric_checks':legacy_checks,
 'metric_definition':'LL clip1e-15 and raw Brier as diagnostics.py; M uses stored booleans, no S>=threshold',
 'interpretation':'estimator edge-set contribution within enabled package, including graph-dependent updates/local downstream states',
 'limitations':['P is logged query scalar; S not calibrated mastery; A is copied preview, not served action',
  'Not direct-logit-only, individual edge quality, causal mediation or closed-loop learning benefit',
  'Three reused seed families with profiles nested; no p/CI/calibrator or new independent N'],
 'new_independent_N':0,'model_teacher_rng_reproduction_calls':0,'source_inputs_sha256':plan['inputs_sha256']}
assert time.perf_counter()-START<9.5
OUT.mkdir(exist_ok=False)
for name,value in [('summary.json',result),('event_flags.json',flags)]:
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
for path,digest in plan['inputs_sha256'].items():assert sha(ROOT/path)==digest
print(json.dumps({'status':result['status'],'population':1080,'groups':len(groups),'GF_decomposition_eligible':gf_valid,
                 'pooled':groups[0]},ensure_ascii=False,indent=2))
