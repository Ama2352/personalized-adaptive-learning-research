"""Revision02 PREPARE ONLY: owned Job + unchanged whole-policy science/cap60.

Old .845393699943088s and helper toolwall2.6589773s stay charged. Never dispatch
until root reviews this exact source/plan. No retry/resume of either attempt.
"""
import time
START=time.perf_counter();WALL=time.time()
from pathlib import Path
import argparse,hashlib,json,math,os,sys,traceback
ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,value):
 with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def elapsed():return max(time.perf_counter()-START,time.time()-WALL)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
 parser.add_argument('--approval-reference',required=True);args=parser.parse_args()
 assert Path(sys.prefix).resolve()==ROOT/'.venv' and args.approval_reference.strip()
 PLAN=PREP/'history_availability_plan02.json';assert sha(PLAN)==args.plan_sha256
 plan=json.loads(PLAN.read_bytes());assert plan['resource_limits']['max_cumulative_seconds']==60
 prior=plan['cumulative_prior_seconds'];assert prior==3.504370999943088
 budget=json.loads((PREP/'history_availability_budget02.json').read_bytes())
 assert budget['charged_prior_seconds']==prior and budget['original_cumulative_cap_seconds']==60
 expected={**plan['source_sha256'],**plan['inputs_sha256'],PLAN.relative_to(ROOT).as_posix():args.plan_sha256}
 assert all(sha(ROOT/n)==d for n,d in expected.items())
 OUT=PREP/plan['output_directory'];assert OUT.parent==PREP and not OUT.exists()
 OUT.mkdir(exist_ok=False)
 error=None;owned=None;worker_receipt=None;preflight=None
 try:
  sys.path.insert(0,str(ROOT/'scripts/research'))
  from windows_owned_worker import run_owned
  sys.path.insert(0,str(ROOT/'src'))
  from knowledge_tracing.akt.resources import memory_snapshot
  limits=plan['resource_limits'];preflight=memory_snapshot()
  assert type(preflight['system_available_ram_bytes']) is int and preflight['system_available_ram_bytes']>=limits['min_available_ram_bytes']
  assert type(preflight['process_rss_bytes']) is int and preflight['process_rss_bytes']<=limits['max_rss_bytes']
  helper_allowance=60-prior-elapsed()-plan['finalization_reserve_seconds']
  native_allowance=helper_allowance-plan['cleanup_reserve_seconds']-.1
  assert math.isfinite(native_allowance) and native_allowance>0
  worker=PREP/'history_availability_worker02.py'
  worker_args=['--plan-sha256',args.plan_sha256,'--remaining-seconds',str(native_allowance)]
  write(OUT/'dispatch.json',{'status':'RESERVED_ONE_ATTEMPT_NO_RETRY','approval_reference':args.approval_reference,
   'worker_parent_pid':os.getpid(),'plan_sha256':args.plan_sha256,'source_input_before_sha256':expected,
   'preflight_memory':preflight,'limits':limits,'case_count':108,'planned_direct_call_caps':plan['direct_call_caps'],
   'prior_charged_seconds':prior,'helper_allowance_seconds':helper_allowance,'native_allowance_seconds':native_allowance,
   'cleanup_reserve_seconds':plan['cleanup_reserve_seconds'],'finalization_reserve_seconds':plan['finalization_reserve_seconds'],
   'worker_args':worker_args,'clock':'max(perf_counter elapsed, wall elapsed), oldspent retained'})
  # Generic helper owns a nested fresh launch directory, science owns OUT.
  owned=run_owned(worker,worker_args,OUT/'owned-launch',expected_worker_sha256=sha(worker),
   approval_reference=args.approval_reference,max_seconds=helper_allowance,
   cleanup_reserve_seconds=plan['cleanup_reserve_seconds'],max_output_bytes=plan['max_stdout_stderr_bytes'])
  write(OUT/'owned_launch_receipt.json',owned)
  assert owned['status']=='ACCEPTED_OWNED_PROCESS_LAUNCH_NOT_SCIENTIFIC_ACCEPTANCE' and owned['accepted'] is True
  assert owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
  assert owned['actual_worker_in_job_before_GO'] is True and owned['GO_released'] is True
  assert owned['worker_returncode_before_cleanup']==0 and owned['popen_handle_closed'] is True
  worker_receipt=json.loads((OUT/'worker_run.json').read_bytes())
  assert worker_receipt['status']=='ACCEPTED_ALGORITHMIC_HISTORY_REPLAY_ALL_CONTROLS_EXACT'
  assert worker_receipt['completed_cases']==108 and worker_receipt['full_control_phase_passed'] is True
  assert worker_receipt['source_input_before_sha256']==worker_receipt['source_input_after_sha256']==expected
  assert all(worker_receipt[k]==plan['direct_call_caps'] for k in ('direct_attempts','direct_returns','case_reservations'))
  assert all(sha(OUT/n)==d for n,d in worker_receipt['outputs_sha256'].items())
  assert not (OUT/'failure.log').exists()
 except Exception as exc:
  error={'type':type(exc).__name__,'message':str(exc)}
  with (OUT/'outer_failure.log').open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
 after={n:sha(ROOT/n) for n in expected}
 if after!=expected:error=error or {'type':'SourceDrift','message':'post source/input mismatch'}
 files=sorted(p for p in OUT.rglob('*') if p.is_file())
 assert len(files)<=32 and all(not p.is_symlink() and p.stat().st_size<=4*1024**2 for p in files)
 assert sum(p.stat().st_size for p in files)<=8*1024**2
 outputs={p.relative_to(OUT).as_posix():sha(p) for p in files}
 revision_elapsed=elapsed();cumulative=prior+revision_elapsed
 if not math.isfinite(cumulative) or cumulative>60:error=error or {'type':'ResourceBound','message':'postelapsed cumulative60 exceeded'}
 result={'status':'ACCEPTED_ONE_NATIVE_HISTORY_AVAILABILITY_REPLAY' if error is None else 'REJECTED_RETAIN_NO_RETRY_NO_PARTIAL_CLAIM',
  'error':error,'approval_reference':args.approval_reference,'plan_sha256':args.plan_sha256,
  'source_input_before_sha256':expected,'source_input_after_sha256':after,'prior_charged_seconds':prior,
  'revision_elapsed_seconds':revision_elapsed,'cumulative_seconds':cumulative,'max_cumulative_seconds':60,
  'preflight_memory':preflight,'owned_launch_status':None if owned is None else owned['status'],
  'owned_cleanup_accepted':None if owned is None else owned['cleanup_accepted'],
  'scientific_worker_receipt_status':None if worker_receipt is None else worker_receipt['status'],
  'actual_native_calls_if_no_worker_receipt':'UNKNOWN; retain percase reservations, never zero or retry',
  'outputs_sha256':outputs,'native_state_updates_are_model_calls':True,'new_independent_N':0,
  'explicit_teacher_environment_rng_draw_nn_optimizer_calls':0,'no_automatic_retry_resume_or_partial_claim':True}
 write(OUT/'run.json',result)
 print(json.dumps({'status':result['status'],'revision_elapsed_seconds':revision_elapsed,'cumulative_seconds':cumulative,
  'error':error,'receipt_sha256':sha(OUT/'run.json')},ensure_ascii=False,indent=2))
 return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
