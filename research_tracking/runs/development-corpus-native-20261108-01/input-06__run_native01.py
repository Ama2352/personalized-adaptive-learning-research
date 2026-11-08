"""Một lượt corpus native hữu hạn; không train model hoặc chi cloud.

Caller phải review request/worker/helper và kiểm nhận cả scientific+owned job.
Không tự retry, không dùng DONE một mình làm nghiệm thu.
"""
import time
START=time.perf_counter();WALL=time.time()
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import traceback

ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def elapsed():return max(time.perf_counter()-START,time.time()-WALL)
def write(name,value):
 with (PREP/name).open('x',encoding='utf-8') as stream:
  json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
def need(ok,message):
 if not ok:raise ValueError(message)
def hash_stream(path,size):
 need(path.is_file() and not path.is_symlink() and path.stat().st_size==size and 0<=size<=33554432,'bounded regular artifact')
 digest=hashlib.sha256();count=0
 with path.open('rb') as stream:
  while chunk:=stream.read(65536):
   count+=len(chunk);need(count<=size and elapsed()<120,'artifact size/time cap');digest.update(chunk)
 need(count==size and path.stat().st_size==size,'artifact drift')
 return digest.hexdigest()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--request-sha256',required=True);args=parser.parse_args()
 need(Path(sys.executable).absolute()==ROOT/'.venv/Scripts/python.exe' and Path(sys.prefix).resolve()==ROOT/'.venv','repo venv only')
 request_relative='artifacts/akt/local-tests/development-corpus-20261108-01/request01.json'
 worker=ROOT/'scripts/research/collect_development_corpus.py'
 need(sha(worker)=='09c909570e94ecc5bb87fdc7f4e75848fa53b91ea1317ab20a383bac4362e192','reviewed worker only')
 spec=importlib.util.spec_from_file_location('reviewed_corpus_metadata',worker)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 request,config=module.validate_request(request_relative,args.request_sha256)
 sources={**request['collection_sources'],**request['extra_sources']}
 outer_sha=sha(Path(__file__));owned=None;result=None;error=None;artifacts=[]
 need(not (PREP/'dispatch.json').exists() and not (PREP/'owned-launch01').exists(),'exclusive dispatch only')
 sys.path.insert(0,str(ROOT/'scripts/research'));from windows_owned_worker import run_owned
 sys.path.insert(0,str(ROOT/'src'));from knowledge_tracing.akt.resources import memory_snapshot
 try:
  memory=memory_snapshot();g=config['global_limits']
  need(type(memory['system_available_ram_bytes']) is int and memory['system_available_ram_bytes']>=g['min_available_ram_bytes'],'parent free RAM floor')
  need(memory['process_rss_bytes']<=g['max_rss_bytes'],'parent RSS cap')
  allowance=120-elapsed()-1.;need(math.isfinite(allowance) and allowance>3,'remaining whole-operation allowance')
  write('dispatch.json',dict(status='RESERVED_ONE_NATIVE_CORPUS_OPERATION',request_sha256=args.request_sha256,
   planned_teacher_attempts=12600,final_events=0,model_calls=0,source_sha256=sources,outer_sha256=outer_sha,
   max_cumulative_seconds=120,helper_allowance_seconds=allowance,cleanup_reserve_seconds=3,
   finalization_reserve_seconds=1,memory_before=memory,approval_reference=request['approval_reference'],automatic_retry=False))
  owned=run_owned(worker,['--request',request_relative,'--request-sha256',args.request_sha256],PREP/'owned-launch01',
   expected_worker_sha256=sources[module.SELF],approval_reference=request['approval_reference'],max_seconds=allowance,
   cleanup_reserve_seconds=3,max_output_bytes=65536)
  write('owned_launch_receipt.json',owned)
  need(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0
       and owned['popen_handle_closed'] and owned['worker_returncode_before_cleanup']==0,'owned worker/cleanup not accepted')
  output=module.safe_file(request['output_relative'])
  need(not (output/'failure.json').exists() and not (output/'failure.log').exists(),'worker failure override')
  need((output/'worker_result.json').stat().st_size<=1024**2,'bounded worker result')
  result=json.loads((output/'worker_result.json').read_bytes())
  need(result['status']=='WORKER_COMPLETE_PENDING_OUTER_ACCEPTANCE'
       and result['request_sha256']==args.request_sha256 and result['plan_sha256']==module.PLAN_SHA
       and result['interact_attempts']==result['interact_returns']==12600
       and result['final_events']==result['model_calls']==result['modal_spend_usd']==0,'scientific counts/identity')
  need(result['owner']['worker']==owned['actual_worker'] and result['owner']['job_name']==owned['job_name']
       and result['owner']['parent_owner']==owned['parent'],'worker output owned-process identity')
  publication=result['publication'];need(publication['corpus_id']==config['corpus_id'],'corpus destination identity')
  base=module.safe_file(publication['corpus_path'])
  need(base==ROOT/'artifacts/simulator/corpora'/config['corpus_id'],'fixed published destination')
  names={record[0] for record in publication['files']}
  expected_names={'corpus.json','bank.json','plan.json','DONE.json','oracle/publication-inventory.json'}
  for role in ('train','selection','calibration'):
   expected_names.update((role+'.jsonl',role+'.manifest.json','oracle/'+role+'.json','oracle/'+role+'.collection.json'))
  need(len(names)==len(publication['files'])==17 and names==expected_names and not (base/'failure.json').exists()
       and {path.relative_to(base).as_posix() for path in base.rglob('*') if path.is_file()}==names,
       'exact closed publication file inventory; no failure marker')
  total=sum(record[2] for record in publication['files']);need(total<=config['publication_limits']['max_total_bytes'],'total publication bytes')
  for name,expected,size in publication['files']:
   path=module.safe_file(publication['corpus_path']+'/'+name)
   need(hash_stream(path,size)==expected,'published artifact hash mismatch')
   artifacts.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=expected,bytes=size))
  done=json.loads((base/'DONE.json').read_bytes())
  need(sha(base/'DONE.json')==publication['done_sha256'] and done['status']=='COMPLETE_SIMULATOR_CORPUS','DONE identity')
  need(all(result['role_audits'][r]['reference_complete'] for r in ('train','selection','calibration')),'reference coverage')
  need(all(sha(ROOT/name)==digest for name,digest in sources.items()) and sha(Path(__file__))==outer_sha,'source drift')
  need(sha(ROOT/request_relative)==args.request_sha256 and sha(ROOT/module.CONFIG)==module.CONFIG_SHA,'request/config drift')
  need(elapsed()<=120,'post-artifact whole-operation wall cap')
 except Exception as exc:
  error=dict(type=type(exc).__name__,message=str(exc))
  with (PREP/'outer_failure.log').open('x',encoding='utf-8') as stream:traceback.print_exc(file=stream)
 cumulative=elapsed()
 if cumulative>120:error=error or dict(type='BudgetExceeded',message='postelapsed120')
 receipt=dict(status='ACCEPTED_FIRST_DEVELOPMENT_CORPUS_NOT_MODEL_FITTED' if error is None else 'REJECTED_RETAIN_NO_RETRY',
  error=error,cumulative_seconds=cumulative,max_cumulative_seconds=120,request_sha256=args.request_sha256,
  actual_interact_attempts=None if result is None else result['interact_attempts'],
  actual_interact_returns=None if result is None else result['interact_returns'],
  reserved_teacher_attempts=12600,actual_unknown_if_no_worker_result=True,source_sha256=sources,
  outer_sha256=outer_sha,owned_status=None if owned is None else owned['status'],
  owned_cleanup_accepted=None if owned is None else owned['cleanup_accepted'],artifacts=artifacts,
  publication=None if result is None else result['publication'],final_events=0,model_calls=0,modal_spend_usd=0,
  automatic_retry=False,no_holdout_access=True,source_export=False,
  outer_terminal_success_required=True,
  scope='Native oracle-free logging corpus/typed public restart; no fitted model/calibration/RQ efficacy')
 write('run.json',receipt)
 final_summary=dict(status=receipt['status'],cumulative_seconds=elapsed(),error=error,run_sha256=sha(PREP/'run.json'))
 if elapsed()>120:
  write('post_publication_failure.json',dict(status='REJECTED_OUTER_FINAL_ELAPSED',elapsed_seconds=elapsed(),
   max_seconds=120,prior_run_status_is_superseded=True))
  raise RuntimeError('final receipt publication exceeds cap; prior run.json is not accepted')
 print(json.dumps(final_summary,ensure_ascii=False))
 return 0 if error is None else 1

if __name__=='__main__':raise SystemExit(main())
