"""ROOT-only GRAPH18 pure14; whole30/cleanup2, no scientific import/model/data."""
import time
START,WALL=time.perf_counter(),time.time()
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import math
import os
import sys

R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
SELF=Path(__file__).resolve()
PACKET=P/'research_main_stage_pure_packet01.json'
OUT=P/'research-main-stage-pure-capture01'
OWNED=P/'research-main-stage-pure-owned01'
CAP=30.
HELPER='scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
SCIENTIFIC={'numpy','pandas','torch','sklearn','scipy','pyBKT','joblib','modal','boto3'}
DOMAIN_MODULES={'knowledge_tracing.research_selection','knowledge_tracing.research_admission',
                'knowledge_tracing.akt','knowledge_tracing.akt.research_main_stage'}


def need(ok,message):
    if not ok: raise ValueError(message)


def elapsed(): return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    need(path.is_file() and not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(), 'physical file')
    with path.open('rb') as stream: raw=stream.read(256*1024+1)
    need(len(raw)<=256*1024,'small source/runtime/log cap')
    return hashlib.sha256(raw).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def packet(digest):
    need(type(digest) is str and len(digest)==64 and sha(PACKET)==digest,'ROOT-reviewed packet SHA required')
    result=json.loads(PACKET.read_bytes())
    need(result['expected_tests']==14 and result['whole_seconds']==30 and result['cleanup_seconds']==2
         and result['model_or_data_execution_authorized'] is False,'exact pure14 allocation')
    return result


def source_snapshot(allocation):
    return {name:sha(R/name) for name in allocation['source_pins']}


def runtime_snapshot(allocation):
    return {name:sha(Path(name)) for name in allocation['runtime_pins']}


def worker(digest):
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner=worker_gate()  # No knowledge_tracing/NumPy/Torch before actual owned GO.
    allocation=packet(digest)
    before=source_snapshot(allocation);runtime_before=runtime_snapshot(allocation)
    need(before==allocation['source_pins'] and runtime_before==allocation['runtime_pins'],'pure preflight pins')
    need(not any(n.split('.')[0] in SCIENTIFIC or n=='knowledge_tracing' for n in sys.modules),'cold stdlib worker')
    denied=[]
    def guard(event,args):
        if event=='subprocess.Popen' or event.startswith('socket.') or event=='os.system' or event.startswith('os.spawn'):
            denied.append(event);raise RuntimeError('no child/network/Windows metadata subprocess in pure14')
        if event=='import':
            name=str(args[0])
            if name.split('.')[0] in SCIENTIFIC or name.startswith('knowledge_tracing.') and name not in DOMAIN_MODULES:
                denied.append('import:'+name);raise RuntimeError('only real stdlib stage/admission/selection modules')
        if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
            path=Path(os.path.abspath(os.fsdecode(args[0])))
            for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl','research_tracking/runs'):
                if path==R/relative or path.is_relative_to(R/relative):
                    denied.append('actual_or_protected_data');raise RuntimeError('no actual artifact/corpus access')
            if event=='open' and path.suffix in ('.pt','.pth','.ckpt','.safetensors'):
                denied.append('checkpoint');raise RuntimeError('no checkpoint bytes')
    sys.addaudithook(guard)
    env_keys=('PYTHONDONTWRITEBYTECODE','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES')
    env_before={key:os.environ.get(key) for key in env_keys}
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
    counts=None;error=None;canary=None;after={};runtime_after={};cached_identity=False
    try:
        sys.path.insert(0,str(R/'src'))
        module=importlib.import_module('knowledge_tracing.akt.research_main_stage')
        admission=importlib.import_module('knowledge_tracing.research_admission')
        need(Path(module.__file__).resolve()==R/'src/knowledge_tracing/akt/research_main_stage.py'
             and Path(admission.__file__).resolve()==R/'src/knowledge_tracing/research_admission.py','real module origins')
        need(not any(n.split('.')[0] in SCIENTIFIC for n in sys.modules),'cold module imported scientific dependency')
        canary=dict(status='STDLIB_MAIN_STAGE_COLD_IMPORT_ONLY',module_file=str(module.__file__),
            module_sha256=sha(Path(module.__file__)),admission_file=str(admission.__file__),
            prefix=sys.prefix,executable=sys.executable,scientific_modules_present=[],
            required_candidates=list(admission.REQUIRED_CANDIDATE_IDS),status_label=module.STATUS,
            artifact_bytes_verified=False,external_freeze_authority=False)
        write(OUT/'cold-canary.json',canary)
        import unittest
        sys.path.insert(0,str(R/'tests/akt'))
        fixtures=importlib.import_module('test_research_main_stage')
        need(Path(fixtures.__file__).resolve()==R/'tests/akt/test_research_main_stage.py','real test module path')
        cached_identity=fixtures.stage is module and fixtures.admission is admission and module.admission is admission
        need(cached_identity,'real cached admission/stage identity; no aliases/reload')
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(fixtures.MainSelectedStageTests)
        need(suite.countTestCases()==14,'exact14 collected unittest methods')
        actual=unittest.TextTestRunner(verbosity=2).run(suite)
        counts=dict(tests=actual.testsRun,failures=len(actual.failures),errors=len(actual.errors),skipped=len(actual.skipped))
        need(actual.wasSuccessful() and counts==dict(tests=14,failures=0,errors=0,skipped=0),'actual14 complete noFES')
    except BaseException as original:
        error=dict(type=type(original).__name__,message=str(original))
    finally:
        try:
            after=source_snapshot(allocation);runtime_after=runtime_snapshot(allocation)
            need(after==before==allocation['source_pins'] and runtime_after==runtime_before==allocation['runtime_pins']
                 and sha(PACKET)==digest,'post source/runtime/packet pins')
        except BaseException as original:
            if error is None:error=dict(type=type(original).__name__,message=str(original))
        for key,value in env_before.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
        forbidden_modules=sorted(n for n in sys.modules if n.split('.')[0] in SCIENTIFIC)
        accepted=error is None and not denied and not forbidden_modules and cached_identity and elapsed()<27.
        result=dict(status='ACCEPTED_14_PURE_MAIN_STAGE_PENDING_OUTER' if accepted else 'REJECTED_KEEP_ALL',
            counts=counts,original_error=error,source_before=before,source_after=after,
            runtime_before=runtime_before,runtime_after=runtime_after,allocation_sha256=digest,
            cold_import=canary,cached_real_class_identity=cached_identity,denied_attempts=denied,
            scientific_modules_present=forbidden_modules,ownership=owner,
            environment_restored=all(os.environ.get(k)==v for k,v in env_before.items()),
            elapsed_worker_seconds=elapsed(),active_budget_seconds=27,
            scope_vi='14manufactured unittest methods; no semantic data/model/selector/fileverifier authority. No Windows metadata child. No neural call instrument claimed.')
        write(OUT/'worker-result.json',result)
        if elapsed()>=27.:
            write(OUT/'postwrite_rejection.json',dict(status='REJECTED_WORKER_POSTWRITE_TIME',elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_ALL',counts=counts,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


def root(digest,approval):
    need(type(approval) is str and bool(approval.strip()),'explicit ROOT approval reference')
    need(not OUT.exists() and not OWNED.exists(),'exclusive one attempt; no retry')
    allocation=packet(digest);before=source_snapshot(allocation);runtime_before=runtime_snapshot(allocation)
    need(before==allocation['source_pins'] and runtime_before==allocation['runtime_pins'] and sha(R/HELPER)==HELPER_SHA,'root preflight pins')
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import run_owned,entry,safe
    entry();safe(SELF);safe(OUT);safe(OWNED)
    OUT.mkdir();errors=[];receipt=None;worker_result=None;counts=None;after={};runtime_after={}
    write(OUT/'before.json',dict(source_sha256=before,runtime_sha256=runtime_before,allocation_sha256=digest,
        expected_unittest_methods=14,cap_seconds=CAP,approval_reference=approval,
        scope_vi='Stdlib-only actual real imports; parent owned helper uses pinned installed psutil, no native/data.'))
    try:
        allowance=min(29.,CAP-elapsed()-1.)
        need(allowance>3,'insufficient remaining whole30 including cleanup2/final1')
        receipt=run_owned(SELF,['--worker','--packet-sha256',digest],OWNED,expected_worker_sha256=before[SELF.relative_to(R).as_posix()],
            approval_reference=approval,max_seconds=allowance,cleanup_reserve_seconds=2,max_output_bytes=32768)
        write(OWNED/'receipt.json',receipt)
        need(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] and receipt['actual_worker_in_job_before_GO']
             and receipt['returncode']==0 and receipt['errors']==[],'owned Job/cleanup completion')
        for name,digest_value in receipt['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(OWNED/name)==digest_value,'owned raw log hash')
        worker_result=json.loads((OUT/'worker-result.json').read_bytes());counts=worker_result['counts']
        need(worker_result['status']=='ACCEPTED_14_PURE_MAIN_STAGE_PENDING_OUTER'
             and counts==dict(tests=14,failures=0,errors=0,skipped=0)
             and worker_result['original_error'] is None and worker_result['denied_attempts']==[]
             and worker_result['scientific_modules_present']==[] and worker_result['cached_real_class_identity']
             and worker_result['environment_restored'] and worker_result['elapsed_worker_seconds']<27.,'actual14 pure result')
        need(worker_result['source_before']==worker_result['source_after']==before
             and worker_result['runtime_before']==worker_result['runtime_after']==runtime_before
             and worker_result['allocation_sha256']==digest,'worker exact pins')
        need(worker_result['cold_import']==json.loads((OUT/'cold-canary.json').read_bytes())
             and worker_result['cold_import']['status_label']=='NO_EXECUTION_AUTHORITY'
             and worker_result['cold_import']['external_freeze_authority'] is False
             and not (OUT/'postwrite_rejection.json').exists(),'real cold module and no late failure')
    except BaseException as error:errors.append(dict(type=type(error).__name__,message=str(error)))
    try:
        after=source_snapshot(allocation);runtime_after=runtime_snapshot(allocation)
        need(after==before and runtime_after==runtime_before and sha(PACKET)==digest,'root postflight pins')
    except BaseException as error:errors.append(dict(type=type(error).__name__,message=str(error)))
    outputs={name:sha(OUT/name) for name in ('before.json','cold-canary.json','worker-result.json') if (OUT/name).is_file()}
    accepted=not errors and math.isfinite(elapsed()) and 0<=elapsed()<CAP
    result=dict(status='ACCEPTED_GRAPH18_14_PURE_STAGE_CONTRACT_CASES_ONLY' if accepted else 'REJECTED_KEEP_PARTIAL_GRAPH18',
        counts=counts,errors=errors,source_before=before,source_after=after,runtime_before=runtime_before,runtime_after=runtime_after,
        allocation_sha256=digest,owned_receipt_sha256=sha(OWNED/'receipt.json') if (OWNED/'receipt.json').is_file() else None,
        output_sha256=outputs,elapsed_before_receipt_seconds=elapsed(),cap_seconds=30,cleanup_reserve_seconds=2,
        automatic_retry=False,scope_vi='Typed phase/claim consistency only; no fileadmission/mainproducer/selectedfit/refit/calibration/Gate proof.')
    write(OUT/'final.json',result)
    if elapsed()>=CAP:
        write(OUT/'postwrite_rejection.json',dict(status='REJECTED_WHOLE30_POSTWRITE',elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_PARTIAL_GRAPH18',counts=counts,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--approval-reference')
    args=parser.parse_args()
    if args.worker:worker(args.packet_sha256)
    else:root(args.packet_sha256,args.approval_reference)
