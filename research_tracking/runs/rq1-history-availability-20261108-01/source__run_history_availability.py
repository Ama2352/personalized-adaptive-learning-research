"""Prepare-only outer single-attempt cap60; dispatch needs root exact-source review."""
import time
START=time.perf_counter()
from pathlib import Path
import argparse,hashlib,json,math,os,subprocess,sys,traceback
ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,value):
 with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
 parser.add_argument('--approval-reference',required=True);args=parser.parse_args()
 assert Path(sys.prefix).resolve()==ROOT/'.venv' and args.approval_reference.strip()
 PLAN=PREP/'history_availability_plan.json';assert sha(PLAN)==args.plan_sha256
 plan=json.loads(PLAN.read_bytes());assert plan['resource_limits']['max_cumulative_seconds']==60
 expected={**plan['source_sha256'],**plan['inputs_sha256'],PLAN.relative_to(ROOT).as_posix():args.plan_sha256}
 assert all(sha(ROOT/n)==d for n,d in expected.items())
 OUT=PREP/plan['output_directory'];assert OUT.parent==PREP and not OUT.exists()
 OUT.mkdir(exist_ok=False)
 sys.path.insert(0,str(ROOT/'src'))
 from knowledge_tracing.akt.resources import memory_snapshot
 preflight=memory_snapshot();limits=plan['resource_limits']
 error=None;rc=None;timed_out=False;command=None;child=None
 try:
  assert type(preflight['system_available_ram_bytes']) is int and preflight['system_available_ram_bytes']>=limits['min_available_ram_bytes']
  assert type(preflight['process_rss_bytes']) is int and preflight['process_rss_bytes']<=limits['max_rss_bytes']
  remaining=60-(time.perf_counter()-START)-.5
  assert math.isfinite(remaining) and remaining>0
  worker=PREP/'history_availability_worker.py'
  command=[sys.executable,'-B',str(worker),'--plan-sha256',args.plan_sha256,'--remaining-seconds',str(remaining)]
  dispatch={'status':'RESERVED_ONE_ATTEMPT_NO_RETRY','command':command,'approval_reference':args.approval_reference,
   'worker_parent_pid':os.getpid(),'plan_sha256':args.plan_sha256,'source_input_before_sha256':expected,
   'preflight_memory':preflight,'limits':limits,'case_count':108,'planned_direct_call_caps':plan['direct_call_caps'],
   'clock':'perf_counter monotonic cumulative outer start before imports','window_timestamps':'unchanged stored absolute UTC'}
  write(OUT/'dispatch.json',dispatch)
  env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',OMP_NUM_THREADS='2',
   MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
  with (OUT/'stdout.log').open('xb') as stdout,(OUT/'stderr.log').open('xb') as stderr:
   try:
    child=subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,
     timeout=max(.001,60-(time.perf_counter()-START)-.3),check=False)
    rc=child.returncode
   except subprocess.TimeoutExpired:
    timed_out=True;raise TimeoutError('outer60s timeout killed/waited owned subprocess; no retry')
  assert rc==0,'native child nonzero exit'
  receipt=json.loads((OUT/'worker_run.json').read_bytes())
  assert receipt['status']=='ACCEPTED_ALGORITHMIC_HISTORY_REPLAY_ALL_CONTROLS_EXACT'
  assert receipt['completed_cases']==108 and receipt['full_control_phase_passed'] is True
  assert receipt['source_input_before_sha256']==receipt['source_input_after_sha256']==expected
  assert all(receipt[k]==plan['direct_call_caps'] for k in ('direct_attempts','direct_returns','case_reservations'))
  assert all(sha(OUT/n)==d for n,d in receipt['outputs_sha256'].items())
 except Exception as exc:
  error={'type':type(exc).__name__,'message':str(exc)}
  with (OUT/'outer_failure.log').open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
 after={n:sha(ROOT/n) for n in expected}
 if after!=expected:error=error or {'type':'SourceDrift','message':'post source/input mismatch'}
 elapsed=time.perf_counter()-START
 if not math.isfinite(elapsed) or elapsed>60:error=error or {'type':'ResourceBound','message':'postelapsed exceeded cumulative60s'}
 outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}
 result={'status':'ACCEPTED_ONE_NATIVE_HISTORY_AVAILABILITY_REPLAY' if error is None else 'REJECTED_RETAIN_NO_RETRY_NO_PARTIAL_CLAIM',
  'error':error,'command':command,'approval_reference':args.approval_reference,'returncode':rc,'timed_out':timed_out,
  'plan_sha256':args.plan_sha256,'source_input_before_sha256':expected,'source_input_after_sha256':after,
  'elapsed_seconds':elapsed,'max_cumulative_seconds':60,'preflight_memory':preflight,'outputs_sha256':outputs,
  'native_state_updates_are_model_calls':True,'new_independent_N':0,
  'teacher_environment_rng_draw_nn_optimizer_calls':0,'no_automatic_retry_resume_or_partial_claim':True}
 write(OUT/'run.json',result)
 print(json.dumps({'status':result['status'],'elapsed_seconds':elapsed,'returncode':rc,'error':error,
  'receipt_sha256':sha(OUT/'run.json')},ensure_ascii=False,indent=2))
 return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
