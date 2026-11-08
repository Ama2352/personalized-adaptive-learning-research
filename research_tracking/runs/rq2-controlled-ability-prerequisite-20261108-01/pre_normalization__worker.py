"""PREPARE ONLY until ROOT dispatch: controlled ability/prerequisite diagnostic.

Native source equations/builders unchanged. Oracle is evaluator-only. Fresh
whole cells reserve120 durable before world work; no retries/partial acceptance.
"""
import time
START=time.perf_counter()
from pathlib import Path
from collections import Counter,deque
from dataclasses import asdict,is_dataclass
import argparse,gzip,hashlib,json,math,os,sys,traceback
ROOT=Path(__file__).resolve().parents[4];PREP=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def identity(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def write(path,value):
 raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 if len(raw)>4*1024**2:raise ValueError('metadata output byte cap')
 with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def require(ok,message):
 if not ok:raise ValueError(message)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
 parser.add_argument('--remaining-seconds',type=float,required=True);args=parser.parse_args()
 require(Path.cwd().resolve()==ROOT and Path(sys.prefix).resolve()==ROOT/'.venv','fixed repository/venv required')
 require(math.isfinite(args.remaining_seconds) and 0<args.remaining_seconds<=60,'bounded worker allowance')
 PLAN=PREP/'plan.json';require(sha(PLAN)==args.plan_sha256,'plan bytes mismatch')
 plan=json.loads(PLAN.read_bytes());OUT=PREP/'attempt01';dispatch=json.loads((OUT/'dispatch.json').read_bytes())
 require(dispatch['status']=='RESERVED_ROOT_APPROVED_ONE_ATTEMPT' and dispatch['plan_sha256']==args.plan_sha256
  and dispatch['approval_reference'].strip(),'parent dispatch binding')
 expected={**plan['source_sha256'],**plan['inputs_sha256'],PLAN.relative_to(ROOT).as_posix():args.plan_sha256}
 require(all(sha(ROOT/n)==d for n,d in expected.items()),'source/input drift before gate')
 sys.path.insert(0,str(ROOT/'scripts/research'))
 from windows_owned_worker import worker_gate
 owner=worker_gate()  # BEFORE knowledge_tracing/NumPy/pandas/model/world imports.
 require(owner['worker']['pid']==os.getpid() and owner['parent_owner']['pid']==dispatch['parent_pid'],'owned worker/logical parent mismatch')
 write(OUT/'operation_reservation.json',{'status':'RESERVED4320_NOT_ACTUAL_COUNTS','max_interact_attempts':4320,
  'actual_attempts':None,'plan_sha256':args.plan_sha256,'owner':owner,'retry_or_resume':False})
 counts=Counter();returns=Counter();reserved=0;completed=0;active=None;error=None;outcomes=[];high_checks=[]
 phase='admission';memory_events=[];results={};high_expected={};stream_sizes=Counter()
 try:
  sys.path.insert(0,str(ROOT/'src'))
  from knowledge_tracing.akt.resources import memory_snapshot
  deadline=START+args.remaining_seconds;limits=plan['resource_limits']
  def clock():require(time.perf_counter()<deadline,'worker cooperative deadline')
  def guard(stage):
   clock();sample=memory_snapshot();rss=sample['process_rss_bytes'];peak=sample['process_peak_rss_bytes'];available=sample['system_available_ram_bytes']
   require(type(rss) is int and rss>=0 and type(available) is int and available>=0
    and (peak is None or type(peak) is int and peak>=0),'unknown memory telemetry')
   require(max(rss,peak or 0)<=limits['max_rss_bytes'],'RSS/peak cap');require(available>=limits['min_available_ram_bytes'],'free RAM floor')
   clock();memory_events.append({'stage':stage,'elapsed_seconds':time.perf_counter()-START,**sample})
  def call(kind,method,*a,**kw):
   clock();require(counts[kind]<plan['direct_call_caps'][kind],'global direct-call cap '+kind)
   counts[kind]+=1;value=method(*a,**kw);returns[kind]+=1;clock();return value
  guard('before_heavy_imports')
  import numpy as np
  import pandas as pd
  from knowledge_tracing.paper2_reference import load_reference
  from knowledge_tracing.gam_kt.simulator_mechanisms import build_mechanism_environment
  from knowledge_tracing.gam_kt.simulator_pathways import build_pathway_policy
  from knowledge_tracing.experimental_controls import FactorialOutcome,paired_mechanism_contrasts
  require('torch' not in sys.modules,'unexpected Torch import')
  guard('after_heavy_imports')
  def state_data(v):
   if isinstance(v,np.ndarray):return {'shape':list(v.shape),'dtype':str(v.dtype),'sha256':hashlib.sha256(v.tobytes()).hexdigest()}
   if isinstance(v,np.generic):return state_data(v.item())
   if isinstance(v,pd.Timestamp):return {'iso':v.isoformat(),'ns':int(v.value)}
   if isinstance(v,float):return {'float_hex':v.hex()}
   if isinstance(v,dict):return {str(k):state_data(x) for k,x in v.items()}
   if isinstance(v,deque):return {'maxlen':v.maxlen,'items':[state_data(x) for x in v]}
   if isinstance(v,(list,tuple)):return [state_data(x) for x in v]
   if is_dataclass(v):return state_data(vars(v))
   if v is None or type(v) in (str,int,bool):return v
   raise TypeError('unsupported native state '+str(type(v)))
  def fingerprint(v):return identity(state_data(v))
  def graph_id(scope):
   g=scope['graph'];return identity({'nodes':list(scope['nodes']),'edges':sorted((p,c) for p in g.nodes for c in g.successors(p))})
  def static_id(ref):
   scope=ref['estimator'];questions={cid:frame.to_dict('records') for cid,frame in scope['questions_by_concept'].items()}
   return fingerprint({'graphs':{k:graph_id(ref[k]) for k in ('environment','controller','estimator')},
    'nodes':scope['nodes'],'chapters':scope['chapter_map'],'questions':questions,
    'question_features':scope['question_features'],'concept_features':scope['concept_features']})
  full=load_reference();empty=load_reference(estimator_edges=[]);scope=full['environment']
  refs={'full':full,'empty':empty};nodes=list(scope['nodes']);require(len(nodes)==28 and len(full['estimator']['question_features'])==84,'native geometry changed')
  require(graph_id(full['environment'])==graph_id(full['controller'])==graph_id(full['estimator'])==plan['graphs']['full'],'source graph mismatch')
  require(graph_id(empty['environment'])==graph_id(empty['controller'])==plan['graphs']['full'] and graph_id(empty['estimator'])==plan['graphs']['empty'],'world/controller must remain full')
  require(full['estimator']['nodes']==empty['estimator']['nodes'],'node order mismatch')
  require(fingerprint(full['estimator']['question_features'])==fingerprint(empty['estimator']['question_features'])
   and fingerprint(full['estimator']['concept_features'])==fingerprint(empty['estimator']['concept_features']),'feature geometry differs across graph arms')
  static={g:static_id(ref) for g,ref in refs.items()}
  classes={m:build_mechanism_environment(full,prerequisite_strength=m) for m in (0.,.55)}
  old=json.loads((ROOT/plan['historical_outcomes']).read_bytes());blocks={};serialized=[]
  for block in plan['blocks']:
   guard('before_shared_inputs:'+str(block))
   anchor=call('anchor_generation',scope['persona_base_abilities'],'PY',block)
   anchor_old=hashlib.sha256(json.dumps(anchor,sort_keys=True).encode()).hexdigest()
   historical=[r for r in old if r['seed']==block and r['profile']=='PY']
   require(len(historical)==4 and {r['latent_identity'] for r in historical}=={anchor_old},'anchor differs from historical PY seed realization')
   mean=float(np.mean([anchor[c] for c in nodes]));centered={c:float(anchor[c]-mean) for c in nodes}
   scale=max(1.,max(abs(z) for z in centered.values()));residual={c:float(60.*centered[c]/scale) for c in nodes}
   require(abs(float(np.mean(list(residual.values()))))<=1e-10 and max(abs(z) for z in residual.values())<=60.,'residual centering/bound')
   bases={a:{c:float(a+residual[c]) for c in nodes} for a in plan['ability_levels']}
   require(all(850<=x<=1500 for base in bases.values() for x in base.values()),'no-clipping base domain')
   uniforms=call('uniform_array_generation',lambda seed:np.random.default_rng(seed).random((120,2)),block)
   uniform_sha=hashlib.sha256(uniforms.tobytes()).hexdigest();require(uniforms.shape==(120,2) and np.isfinite(uniforms).all(),'uniform geometry')
   require({r['random_stream_identity'] for r in historical}=={uniform_sha},'uniforms differ from reused historical block')
   uniforms.setflags(write=False)
   info={'block':block,'anchor':anchor,'source_anchor_sha256':anchor_old,'anchor_mean':mean,
    'centered_before_scaling':centered,'centering_denominator':scale,'centered_residual':residual,'residual_sha256':identity(residual),
    'bases':bases,'base_sha256':{a:identity(b) for a,b in bases.items()},'uniforms':uniforms.tolist(),
    'uniform_sha256':uniform_sha,'uniform_dtype':str(uniforms.dtype),'uniform_shape':[120,2],'uniform_sha_encoding':'numpy native float64 C-order bytes; matches historical ID'}
   blocks[block]={'info':info,'U':uniforms,'bases':bases};serialized.append(info)
  # All3realizations/alpha bases/U identities durable BEFORE first environment.
  write(OUT/'shared_inputs.json',{'recipe_version':plan['initializer_version'],'node_order':nodes,'blocks':serialized,
   'graphs':plan['graphs'],'model_initial_elo':scope['MODEL_INITIAL_ELO'],'new_independent_seed_blocks':0,
   'numpy_version':np.__version__,'pandas_version':pd.__version__,'python_version':sys.version})
  write(OUT/'admission.json',{'status':'ADMITTED_SOURCE_GEOMETRY_SHARED_INPUTS_BEFORE_WORLD','plan_sha256':args.plan_sha256,
   'source_input_before_sha256':expected,'static_namespace_sha256':static,'owner':owner,'initialization_is_new_recipe_not_source_persona_reproduction':True})
  initial_policy_sha=None
  def append(stream,name,value):
   raw=(canonical(value)+'\n').encode();require(len(raw)<=16384,'bounded trace line')
   require(stream_sizes[name]+len(raw)<=plan['max_trace_file_bytes'],'trace file cap')
   require(sum(stream_sizes.values())+len(raw)<=plan['max_total_trace_bytes'],'total trace cap')
   stream.write(raw);stream_sizes[name]+=len(raw)
  with (OUT/'cell_ledger.jsonl').open('xb') as ledger,(OUT/'observables.jsonl').open('xb') as obslog,(OUT/'oracle.jsonl').open('xb') as oraclelog,(OUT/'oracle_endpoints.jsonl').open('xb') as endpointlog:
   for cell in plan['cells']:
    active=cell['cell_id'];block,a,g,m=cell['block'],cell['ability'],cell['graph'],cell['mechanism_strength']
    if phase!=cell['phase']:
     if cell['phase']=='main':
      require(len(high_checks)==6 and all(x['semantic_trace_exact'] for x in high_checks),'all high negatives must pass first')
      write(OUT/'high_controls.json',{'status':'PASS_ALL6_HIGH_LAMBDA_PAIRS_BEFORE_MAIN','pairs':high_checks,'design_known_not_discovery':True})
     phase=cell['phase']
    guard('before_reserve:'+active)
    require(reserved+120<=4320,'global reserved interact cap');reserved+=120
    info=blocks[block]['info'];base=blocks[block]['bases'][a];U=blocks[block]['U']
    append(ledger,'cell_ledger.jsonl',{'event':'RESERVED_BEFORE_CELL_WORLD_WORK','cell':cell,'interact_reservation':120,
     'cumulative_reserved':reserved,'actual_attempts':None,'base_sha256':info['base_sha256'][a],
     'residual_sha256':info['residual_sha256'],'uniform_sha256':info['uniform_sha256'],'plan_sha256':args.plan_sha256})
    ledger.flush();os.fsync(ledger.fileno())
    before=counts.copy()
    environment=call('environment_constructor',classes[m],base)
    policy=call('policy_builder',build_pathway_policy,refs[g],signal=True,parent_adaptation=True,local_adaptation=False)
    require(environment.base==base==environment.theta and all(x is None for x in environment.last_seen.values()),'fresh environment mismatch')
    initial=fingerprint(vars(policy))
    if initial_policy_sha is None:initial_policy_sha=initial
    require(initial==initial_policy_sha and all(s.theta==1200. for s in policy.states.values()),'model initialization differs by world condition')
    timestamp=pd.Timestamp('2026-01-01',tz='UTC');semantics=[];positive_deficit=ceiling_hits=0
    for step in range(120):
     clock();timestamp+=pd.Timedelta(hours=72 if step>0 and step%28==0 else 6)
     cid,qid,difficulty=call('select',policy.select)
     prediction=call('predict',policy.predict,cid,qid,difficulty,timestamp)
     require(type(prediction) is float and math.isfinite(prediction) and 0<=prediction<=1,'invalid policy prediction')
     # Evaluator-only probe, NEVER passed to policy predict/select/update.
     env_before=fingerprint(vars(environment))
     theta=call('oracle_theta_probe',environment.theta_at,cid,timestamp)
     p_oracle=call('oracle_probability_probe',scope['elo_probability'],theta,difficulty)
     require(fingerprint(vars(environment))==env_before,'oracle readout mutated environment')
     uo,ul=float(U[step,0]),float(U[step,1])
     result=call('interact',environment.interact,cid,difficulty,timestamp,uo,ul)
     require(type(result) is dict and type(result.get('y')) is int and result['y'] in (0,1),'invalid world response')
     require(result['p_true']==p_oracle and result['theta_before']==theta and result['y']==int(uo<p_oracle),'oracle response/label equation mismatch')
     expected_challenge=math.exp(-.5*((p_oracle-.65)/.22)**2)
     expected_gain=(scope['TRUE_GAIN_SCALE']*expected_challenge*(1.15 if result['y']==0 else .85)
      *(1.+.20*min(result['gap_days'],7.)/7.)*(1.-m*result['prerequisite_deficit'])*(.85+.30*ul))
     require(result['challenge_match']==expected_challenge and result['learning_gain']==expected_gain,'native learning equation mismatch')
     require(environment.theta[cid]==min(1600.,theta+result['learning_gain']),'cap/transition mismatch')
     if a==1300:require(result['prerequisite_deficit']==0. and result['prereq_violation']==0,'high-ability inactive mechanism violated')
     positive_deficit+=int(result['prerequisite_deficit']>0);ceiling_hits+=int(theta+result['learning_gain']>=1600.)
     call('update',policy.update,cid,qid,difficulty,timestamp,result['y'],prediction)
     # Native select already updates visits/questions/recent/chapter; no double bookkeeping.
     query={'concept':str(cid),'question':str(qid),'difficulty':float(difficulty),'timestamp_iso':timestamp.isoformat(),'timestamp_ns':int(timestamp.value)}
     observable={'cell_id':active,'step':step,'query':query,'probability':prediction,'correct':result['y']}
     oracle={'cell_id':active,'step':step,'oracle_probability':p_oracle,'oracle_theta_before':theta,
      'environment_readonly_probe_sha256':env_before,'outcome_uniform':uo,'learning_uniform':ul,'result':result,
      'ceiling_hit':theta+result['learning_gain']>=1600.}
     append(obslog,'observables.jsonl',observable);append(oraclelog,'oracle.jsonl',oracle)
     if a==1300:
      semantic=canonical({'step':step,'query':query,'probability':prediction,'correct':result['y'],
       'oracle_probability':p_oracle,'theta_before':theta,'U':[uo,ul],'result':result,'readonly_state_sha256':env_before})
      if m==0.:semantics.append(semantic)
      else:require(semantic==high_expected[(block,g)]['trace'][step],'high lambda semantic trace mismatch')
     if step%10==9:guard('progress:'+active+':'+str(step))
    snapshot=call('snapshot',environment.snapshot,timestamp)
    outcome=float(np.mean([snapshot[c]-base[c] for c in nodes]));require(math.isfinite(outcome),'nonfinite endpoint')
    final={'environment_state':state_data(vars(environment)),'policy_state':state_data(vars(policy)),'snapshot':snapshot,'outcome':outcome}
    if a==1300:
     if m==0.:high_expected[(block,g)]={'trace':semantics,'final':canonical(final),'cell_id':active}
     else:
      require(canonical(final)==high_expected[(block,g)]['final'],'high lambda final-state mismatch')
      high_checks.append({'block':block,'graph':g,'events':120,'semantic_trace_exact':True,'final_state_exact':True,
       'lambda0_cell':high_expected[(block,g)]['cell_id'],'lambda55_cell':active,
       'trace_sha256':hashlib.sha256(('\n'.join(high_expected[(block,g)]['trace'])).encode()).hexdigest()})
    row=FactorialOutcome(block,'A'+str(a),g=='full',m==.55,info['base_sha256'][a],info['uniform_sha256'],outcome)
    expected_delta=Counter(environment_constructor=1,policy_builder=1,select=120,predict=120,interact=120,update=120,
     oracle_theta_probe=120,oracle_probability_probe=120,snapshot=1)
    require(counts-before==expected_delta,'cell direct-call count mismatch')
    require(hashlib.sha256(U.tobytes()).hexdigest()==info['uniform_sha256'] and identity(base)==info['base_sha256'][a],'shared inputs mutated')
    require({key:static_id(ref) for key,ref in refs.items()}==static,'static namespace mutated/cross-cell leakage')
    append(endpointlog,'oracle_endpoints.jsonl',{'cell_id':active,'timestamp_iso':timestamp.isoformat(),'timestamp_ns':int(timestamp.value),
     'final_snapshot':snapshot,'final_environment_state':final['environment_state'],'final_policy_state_sha256':identity(final['policy_state']),
     'base_sha256':info['base_sha256'][a],'net_mean_theta_gain':outcome,'scope':'oracle/evaluator only, never policy input'})
    obslog.flush();oraclelog.flush();endpointlog.flush();os.fsync(obslog.fileno());os.fsync(oraclelog.fileno());os.fsync(endpointlog.fileno())
    append(ledger,'cell_ledger.jsonl',{'event':'COMPLETED_CELL','cell_id':active,'actual_interact_attempts':120,'actual_interact_returns':120,
     'cumulative_direct_attempts':dict(counts),'cumulative_direct_returns':dict(returns),'cumulative_reserved':reserved,
     'outcome':asdict(row),'positive_deficit_events':positive_deficit,'ceiling_hit_events':ceiling_hits,
     'final_environment_sha256':identity(final['environment_state']),'final_policy_sha256':identity(final['policy_state'])})
    ledger.flush();os.fsync(ledger.fileno());outcomes.append(row);completed+=1;guard('after_cell:'+active)
  require(completed==36 and reserved==4320 and counts==returns==Counter(plan['direct_call_caps']),'batch population/call caps incomplete')
  require(len(high_checks)==6,'high negative control coverage')
  write(OUT/'outcomes.json',[asdict(x) for x in outcomes])
  interactions=paired_mechanism_contrasts(outcomes);require(len(interactions)==9,'all9interactions required')
  keyed={(x['seed'],int(x['profile'][1:])):x for x in interactions}
  require(set(keyed)=={(b,a) for b in plan['blocks'] for a in plan['ability_levels']},'interaction population mismatch')
  require(all(keyed[(b,1300)]['interaction_contrast']==0. for b in plan['blocks']),'high known-null interaction not exact0')
  deltas=[{'block':x['seed'],'ability':int(x['profile'][1:]),'mechanism_strength':m,'graph_delta':x[field]}
   for x in interactions for m,field in ((0.,'graph_effect_mechanism_off'),(.55,'graph_effect_mechanism_on'))]
  moderation=[{'block':b,'ability_low':a1,'ability_high':a2,'interaction_difference':keyed[(b,a2)]['interaction_contrast']-keyed[(b,a1)]['interaction_contrast']}
   for b in plan['blocks'] for a1,a2 in ((1000,1150),(1150,1300))]
  require(len(deltas)==18 and len(moderation)==6,'contrast population missing')
  write(OUT/'interactions.json',interactions);write(OUT/'graph_deltas.json',deltas);write(OUT/'ability_moderation.json',moderation)
  write(OUT/'summary.json',{'kind':'FINITE_CONTROLLED_ABILITY_PREREQUISITE_FACTORIAL_NO_INFERENCE','blocks':plan['blocks'],
   'abilities':{str(a):{'blocks':3,'mean_interaction':float(np.mean([keyed[(b,a)]['interaction_contrast'] for b in plan['blocks']]))} for a in plan['ability_levels']},
   'all36outcomes_9interactions_18deltas_6moderations':True,'new_independent_seed_blocks':0,
   'no_p_CI_ability_generalization_or_required_model_waiver':True})
  guard('final_source_and_input_check');require(all(sha(ROOT/n)==d for n,d in expected.items()),'source/input drift')
  require('torch' not in sys.modules,'unexpected Torch import')
 except Exception as exc:
  error={'type':type(exc).__name__,'message':str(exc),'active_cell':active,'phase':phase}
  with (OUT/'failure.log').open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
 finally:
  after={n:sha(ROOT/n) for n in expected}
  if after!=expected:error=error or {'type':'SourceDrift','message':'posthash mismatch'}
  elapsed=time.perf_counter()-START
  if not math.isfinite(elapsed) or elapsed>args.remaining_seconds:error=error or {'type':'ResourceBound','message':'postelapsed exceeded allowance'}
  outputs={x.name:sha(x) for x in OUT.iterdir() if x.is_file() and x.name!='worker_run.json'}
  receipt={'status':'WORKER_COMPLETE_36CELL_FACTORIAL_PENDING_OUTER_ACCEPTANCE' if error is None else 'REJECTED_RETAIN_NO_RETRY_NO_PARTIAL_CLAIM',
   'error':error,'source_input_before_sha256':expected,'source_input_after_sha256':after,'owner':owner,
   'completed_cells':completed,'reserved_interact_attempts':reserved,'direct_attempts':dict(counts),'direct_returns':dict(returns),
   'high_negative_pairs':len(high_checks),'worker_elapsed_seconds':elapsed,'worker_allowance_seconds':args.remaining_seconds,
   'hardkill_scope':'Without cell terminal actual counts UNKNOWN<=reserved120 for activecell; conservative charge, never0/reset/retry',
   'model_state_updates_are_actual_model_calls':True,'nn_optimizer_calls':0,'new_independent_seed_blocks':0,
   'scientific_scope':'versioned native world/whole-policy conditional factorial, no learning/ability population generalization',
   'memory_events':memory_events,'outputs_sha256':outputs}
  write(OUT/'worker_run.json',receipt)
  print(canonical({'status':receipt['status'],'completed_cells':completed,'reserved':reserved,'elapsed_seconds':elapsed,'error':error}),flush=True)
 return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
