"""SOURCE PREPARATION ONLY; ROOT alone dispatches this reviewed objective once.

NewRQ2 allocation60s, distinct from and never resetting oldavailability ledger.
Owned cleanup and complete scientific controls/population BOTH required.
"""
import time
START=time.perf_counter();WALL=time.time()
from pathlib import Path
import argparse,hashlib,json,math,os,sys,traceback
ROOT=Path(__file__).resolve().parents[4];PREP=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def elapsed():return max(time.perf_counter()-START,time.time()-WALL)
def require(ok,message):
 if not ok:raise ValueError(message)
def write(path,value):
 raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 require(len(raw)<=4*1024**2,'receipt byte cap')
 with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
 parser.add_argument('--approval-reference',required=True);args=parser.parse_args()
 require(Path.cwd().resolve()==ROOT and Path(sys.prefix).resolve()==ROOT/'.venv','fixedROOT/venv required')
 require(args.approval_reference.strip(),'root dispatch reference required, not scientific authority inferred from code')
 PLAN=PREP/'plan.json';require(sha(PLAN)==args.plan_sha256,'plan bytes mismatch')
 plan=json.loads(PLAN.read_bytes());require(plan['resource_limits']['max_cumulative_seconds']==60,'unchanged cap60')
 expected={**plan['source_sha256'],**plan['inputs_sha256'],PLAN.relative_to(ROOT).as_posix():args.plan_sha256}
 require(all(sha(ROOT/n)==d for n,d in expected.items()),'source/input drift')
 OUT=PREP/'attempt01';require(not OUT.exists(),'ONE exclusive attempt; no repair/resume/retry');OUT.mkdir(exist_ok=False)
 error=None;owned=None;worker=None;memory=None
 try:
  sys.path.insert(0,str(ROOT/'scripts/research'))
  from windows_owned_worker import run_owned
  sys.path.insert(0,str(ROOT/'src'))
  from knowledge_tracing.akt.resources import memory_snapshot
  memory=memory_snapshot();limits=plan['resource_limits']
  require(type(memory['system_available_ram_bytes']) is int and memory['system_available_ram_bytes']>=limits['min_available_ram_bytes'],'preflight freeRAM')
  require(type(memory['process_rss_bytes']) is int and memory['process_rss_bytes']<=limits['max_rss_bytes'],'preflight parentRSS')
  allowance=60-elapsed()-plan['finalization_reserve_seconds']
  native_allowance=allowance-plan['cleanup_reserve_seconds']-.1
  require(math.isfinite(native_allowance) and native_allowance>0,'positive remaining allocation')
  worker_args=['--plan-sha256',args.plan_sha256,'--remaining-seconds',str(native_allowance)]
  write(OUT/'dispatch.json',{'status':'RESERVED_ROOT_APPROVED_ONE_ATTEMPT','approval_reference':args.approval_reference,
   'plan_sha256':args.plan_sha256,'parent_pid':os.getpid(),'source_input_before_sha256':expected,'preflight_memory':memory,
   'limits':limits,'helper_allowance_seconds':allowance,'worker_allowance_seconds':native_allowance,
   'cell_count':36,'max_interact_reservations':4320,'reserve120_before_each_cell_world_work':True,
   'hardkill_actual_counts':'UNKNOWN<=durable reserved; never inferzero/reclaim/retry',
   'no_other_objective_budget_reset':True,'worker_args':worker_args})
  owned=run_owned(PREP/'worker.py',worker_args,OUT/'owned-launch',expected_worker_sha256=sha(PREP/'worker.py'),
   approval_reference=args.approval_reference,max_seconds=allowance,
   cleanup_reserve_seconds=plan['cleanup_reserve_seconds'],max_output_bytes=65536)
  write(OUT/'owned_launch_receipt.json',owned)
  if (OUT/'worker_run.json').is_file():worker=json.loads((OUT/'worker_run.json').read_bytes())
  require(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0,'ownedlaunch/cleanup notaccepted')
  require(owned['actual_worker_in_job_before_GO'] is True and owned['GO_released'] and owned['popen_handle_closed'],'actualworker ownership/handles')
  require(owned['worker_returncode_before_cleanup']==0,'worker nonzero exit')
  require(worker is not None and worker['status']=='WORKER_COMPLETE_36CELL_FACTORIAL_PENDING_OUTER_ACCEPTANCE','scientific worker incomplete')
  require(worker['completed_cells']==36 and worker['reserved_interact_attempts']==4320 and worker['high_negative_pairs']==6,'scientific population/negative checks incomplete')
  require(worker['direct_attempts']==worker['direct_returns']==plan['direct_call_caps'],'directattempt/return caps')
  require(worker['source_input_before_sha256']==worker['source_input_after_sha256']==expected,'native source/input mismatch')
  require(all(sha(OUT/n)==d for n,d in worker['outputs_sha256'].items()),'native output hash mismatch')
  require(not (OUT/'failure.log').exists(),'worker failure marker')
  for name,n in [('outcomes.json',36),('interactions.json',9),('graph_deltas.json',18),('ability_moderation.json',6)]:
   require(len(json.loads((OUT/name).read_bytes()))==n,'result population '+name)
 except Exception as exc:
  error={'type':type(exc).__name__,'message':str(exc)}
  with (OUT/'outer_failure.log').open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
 after={n:sha(ROOT/n) for n in expected}
 if after!=expected:error=error or {'type':'SourceDrift','message':'final source/input mismatch'}
 files=[p for p in OUT.rglob('*') if p.is_file()]
 if len(files)>40 or any(p.is_symlink() or p.stat().st_size>8*1024**2 for p in files) or sum(p.stat().st_size for p in files)>32*1024**2:
  error=error or {'type':'OutputBound','message':'artifact file/population/byte cap'}
 outputs={p.relative_to(OUT).as_posix():sha(p) for p in files}
 observed=elapsed()
 if not math.isfinite(observed) or observed>60:error=error or {'type':'ResourceBound','message':'postelapsed wholeoperation60 exceeded'}
 receipt={'status':'ACCEPTED_FINITE_CONTROLLED_ABILITY_PREREQUISITE_EXPERIMENT' if error is None else 'REJECTED_RETAIN_NO_RETRY_NO_PARTIAL_CLAIM',
  'error':error,'approval_reference':args.approval_reference,'plan_sha256':args.plan_sha256,'source_input_before_sha256':expected,
  'source_input_after_sha256':after,'elapsed_seconds':observed,'max_cumulative_seconds':60,
  'owned_launch_status':None if owned is None else owned['status'],'owned_cleanup_accepted':None if owned is None else owned['cleanup_accepted'],
  'worker_status':None if worker is None else worker['status'],'actual_counts_if_missing_worker_receipt':'UNKNOWN<=durable reserved, neverzero/retry/reset',
  'direct_attempts':None if worker is None else worker['direct_attempts'],'preflight_memory':memory,'outputs_sha256':outputs,
  'new_independent_seed_blocks':0,'native_GAM_state_updates_are_model_calls':True,'nn_optimizer_calls':0,
  'limits':'Finite source-versioned simulatorworld intervention, no p/CI/population ability/learning generalization or model-training claim',
  'no_automatic_retry_resume_or_partial_acceptance':True}
 write(OUT/'run.json',receipt)
 print(json.dumps({'status':receipt['status'],'elapsed_seconds':observed,'error':error,'run_sha256':sha(OUT/'run.json')},ensure_ascii=False,indent=2))
 return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
