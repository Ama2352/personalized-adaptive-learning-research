"""Prepared stdlib cached endpoint analysis; no native model/teacher/RNG calls."""
import time
START=time.perf_counter()
from pathlib import Path
import argparse,hashlib,json,math,struct,sys
ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
assert Path(sys.prefix).resolve()==ROOT/'.venv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True);args=parser.parse_args()
PLAN=PREP/'availability_analysis_plan02.json';assert sha(PLAN)==args.plan_sha256
plan=json.loads(PLAN.read_bytes());assert sha(Path(__file__).resolve())==plan['analyzer_sha256']
for n,d in plan['inputs_sha256'].items():assert sha(ROOT/n)==d,n
OUT=PREP/'availability-cached-analysis01';assert not OUT.exists()
raw=PREP/'availability-replay-attempt02'
outer=json.loads((raw/'run.json').read_bytes());worker=json.loads((raw/'worker_run.json').read_bytes())
verification=json.loads((PREP/'availability_raw_verification02.json').read_bytes())
assert verification['status']=='PASS_RAW_ENDPOINT_AND_CONTROL_VERIFICATION_NO_EFFECT_ESTIMATES'
assert verification['full_prefix_arm_P_S_M_R_fulltuple_exact_checks']==54
assert outer['status']=='ACCEPTED_ONE_NATIVE_HISTORY_AVAILABILITY_REPLAY'
assert worker['completed_cases']==108 and worker['full_control_phase_passed'] is True
native_plan=json.loads((PREP/'history_availability_plan02.json').read_bytes())
lines=(raw/'endpoint_records.jsonl').read_bytes().splitlines();assert len(lines)==108
rows=[json.loads(line) for line in lines];arms={}
def exact(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,float):return struct.pack('>d',a)==struct.pack('>d',b)
 if isinstance(a,dict):return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
 return a==b
for row,case in zip(rows,native_plan['cases']):
 assert {k:row[k] for k in case}==case
 key=(row['seed'],row['profile'],row['Hpast'],row['available_length'],row['variant'])
 assert key not in arms;arms[key]=row
 p=row['observation']['probability'];assert type(p) is float and math.isfinite(p) and 0<=p<=1
 assert type(row['cached_target_y_for_evaluation_only']) is int and row['cached_target_y_for_evaluation_only'] in (0,1)
 assert set(row['observation']['full_preview'])=={'concept','question','difficulty'}
 assert row['exact_full_prefix_legacy_parity'] is (True if row['phase']=='control' else None)
SEEDS=(20000,20001,20002);PROFILES=('PG','PY','PYH');VARIANTS=('graph_package','empty_graph_package')
LENGTHS={10:(10,),50:(10,50),100:(10,50,100)};LABELS=('10','50','full')
expected={(s,p,H,L,v) for s in SEEDS for p in PROFILES for H in LENGTHS for L in LENGTHS[H] for v in VARIANTS}
assert len(arms)==108 and set(arms)==expected
def loss(p,y):
 q=min(1-1e-15,max(1e-15,p));return -y*math.log(q)-(1-y)*math.log(1-q)
def value(row):
 p=row['observation']['probability'];y=row['cached_target_y_for_evaluation_only']
 return {'p':p,'LL':loss(p,y),'Brier':(p-y)**2}
pairs=[]
for s in SEEDS:
 for profile in PROFILES:
  for H,lengths in LENGTHS.items():
   full_history={v:arms[(s,profile,H,H,v)] for v in VARIANTS}
   target=full_history['graph_package']
   assert exact(full_history['empty_graph_package']['query'],target['query'])
   for L in lengths:
    selected={v:arms[(s,profile,H,L,v)] for v in VARIANTS}
    assert all(exact(r['query'],target['query']) and exact(r['cached_target_y_for_evaluation_only'],target['cached_target_y_for_evaluation_only']) for r in [*selected.values(),*full_history.values()])
    aliases=[label for label in LABELS if (H if label=='full' else min(int(label),H))==L]
    assert all(r['requested_window_aliases']==aliases for r in selected.values())
    x={v:value(selected[v]) for v in VARIANTS};ref={v:value(full_history[v]) for v in VARIANTS}
    numbers={};checks={}
    for metric in ('p','LL','Brier'):
     delta=x['graph_package'][metric]-x['empty_graph_package'][metric]
     changes={v:x[v][metric]-ref[v][metric] for v in VARIANTS}
     interaction=delta-(ref['graph_package'][metric]-ref['empty_graph_package'][metric])
     residual=interaction-(changes['graph_package']-changes['empty_graph_package'])
     assert abs(residual)<=1e-12;checks[metric]=residual
     numbers['graph_delta_'+metric]=delta
     numbers['full_arm_window_minus_full_history_'+metric]=changes['graph_package']
     numbers['empty_arm_window_minus_full_history_'+metric]=changes['empty_graph_package']
     numbers['availability_interaction_'+metric]=interaction
    numbers['absolute_graph_delta_p']=abs(numbers['graph_delta_p'])
    changed={v:not exact(selected[v]['observation']['full_preview'],full_history[v]['observation']['full_preview']) for v in VARIANTS}
    if L==H:
     assert all(numbers['availability_interaction_'+m]==numbers['full_arm_window_minus_full_history_'+m]==numbers['empty_arm_window_minus_full_history_'+m]==0 for m in ('p','LL','Brier'))
     assert not any(changed.values())
    pairs.append({'native_pair_id':f'{s}:{profile}:H{H}:L{L}','seed':s,'profile':profile,'Hpast':H,
     'available_length':L,'requested_aliases':aliases,'target_query':target['query'],
     'graph_P_changed':not exact(x['graph_package']['p'],x['empty_graph_package']['p']),
     'graph_full_preview_changed':not exact(selected['graph_package']['observation']['full_preview'],selected['empty_graph_package']['observation']['full_preview']),
     'full_arm_preview_vs_full_history_changed':changed['graph_package'],
     'empty_arm_preview_vs_full_history_changed':changed['empty_graph_package'],
     'arithmetic_interaction_residuals':checks,**numbers})
assert len(pairs)==54 and len({r['native_pair_id'] for r in pairs})==54
expanded=[{**r,'nominal_window':label,'alias_of_full_history_native_case':r['available_length']==r['Hpast'] and label!='full'} for r in pairs for label in r['requested_aliases']]
assert len(expanded)==81
numeric=[n for n in pairs[0] if n.startswith(('graph_delta_','full_arm_window_minus_','empty_arm_window_minus_','availability_interaction_'))]+['absolute_graph_delta_p']
assert len(numeric)==13
contexts=[('pooled',lambda r:True)]
contexts += [('profile:'+p,lambda r,p=p:r['profile']==p) for p in PROFILES]
contexts += [('seed:'+str(s),lambda r,s=s:r['seed']==s) for s in SEEDS]
contexts += [(f'trajectory:{s}:{p}',lambda r,s=s,p=p:r['seed']==s and r['profile']==p) for s in SEEDS for p in PROFILES]
summary=[]
for context,predicate in contexts:
 for H in LENGTHS:
  for label in LABELS:
   selected=[r for r in expanded if predicate(r) and r['Hpast']==H and r['nominal_window']==label]
   n=len(selected);assert n==(9 if context=='pooled' else 1 if context.startswith('trajectory:') else 3)
   summary.append({'context':context,'Hpast':H,'nominal_window':label,'available_length':selected[0]['available_length'],
    'alias_of_full_history_native_case':selected[0]['alias_of_full_history_native_case'],'same_target_pairs':n,
    **{'mean_'+name:math.fsum(r[name] for r in selected)/n for name in numeric},
    **{name:sum(r[name] for r in selected) for name in ('graph_P_changed','graph_full_preview_changed','full_arm_preview_vs_full_history_changed','empty_arm_preview_vs_full_history_changed')}})
assert len(summary)==144
aliases=[{'Hpast':H,'nominal_window':label,'available_length':H if label=='full' else min(int(label),H),
 'alias_of_full_history_native_case':label!='full' and int(label)>=H} for H in LENGTHS for label in LABELS]
result={'status':'CACHED_CONTROLLED_ALGORITHMIC_AVAILABLE_HISTORY_CONTRAST','unique_targets':27,
 'unique_native_target_window_pairs':54,'native_endpoint_arms':108,'expanded_nominal_pairs_including_aliases':81,
 'summary_rows':144,'contexts':16,'aliases':aliases,'groups':summary,'source_inputs_sha256':plan['inputs_sha256'],
 'new_independent_N':0,'new_native_model_teacher_world_rng_optimizer_calls':0,
 'limits':['Whole native policy INCLUDING controller bookkeeping; not KT-only or actual learner-practice intervention',
 'Same cached query/label/time, reset retained-record state; preview NOT served, no learning benefit',
 'Three reused seed families/profiles/targets/windows dependent; no p/CI/calibrator, no grandmean acrossaliases',
 'P/S/M/R full-controls exact; readonly state equality asserted in native source, no independent dual raw state dumps']}
assert time.perf_counter()-START<9.5
for n,d in plan['inputs_sha256'].items():assert sha(ROOT/n)==d,n
OUT.mkdir(exist_ok=False)
for name,v in [('summary.json',result),('unique_pairs.json',pairs),('nominal_aliases.json',expanded)]:
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'targets':27,'unique_pairs':54,'nominal_pairs':81,'summary_rows':144,
 'pooled':[g for g in summary if g['context']=='pooled']},ensure_ascii=False,indent=2))
