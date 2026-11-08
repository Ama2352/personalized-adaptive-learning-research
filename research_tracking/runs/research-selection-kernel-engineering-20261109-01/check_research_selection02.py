"""ROOT-only GRAPH13 pure8/cold-canary revision02; no real selection, corpus, model or grant."""
import time
START,WALL=time.perf_counter(),time.time()
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import runpy
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
SELF=Path(__file__).resolve()
TEST=ROOT/'tests/shared_kt/test_research_selection.py'
OUT=PREP/'research-selection-pure-capture02'
OWNED=PREP/'research-selection-pure-owned02'
CAP=30.
PRIOR_CHARGED_SECONDS=.8424742
HELPER='scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
PINS={
    'src/knowledge_tracing/__init__.py':'b84a9a4118d8b3476daae25a7981c97909524ace7ef93860bba7e6ec9e5bccb8',
    'src/knowledge_tracing/research_selection.py':'0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348',
    'tests/shared_kt/test_research_selection.py':'c2b0de6fa3af4a4c50944c3d15a0b686e068f920c5839565aa9149b5022d6ad6',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/MAIN_SELECTOR_CONTRACT01.md':'5cd1973763ff9783781cc756ad57c5544886657ad63ff8f77369fda58cf44c60',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/reporting-loss-parity01.json':'110d998297ac96e37e2c0bba03053085eee52ea3e5e6508b31d824f24d712e5f',
}
SCIENTIFIC={'numpy','pandas','torch','sklearn','scipy','pyBKT'}


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    need(path.is_file() and not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'physical source/log')
    with path.open('rb') as stream:payload=stream.read(128*1024+1)
    need(len(payload)<=128*1024,'bounded pure source/log')
    return hashlib.sha256(payload).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush()


def worker():
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    ownership=worker_gate()  # Before knowledge_tracing/tests; ROOT owns this exact worker.
    need(all(sha(ROOT/name)==pin for name,pin in PINS.items()),'pure source preflight')
    need(not any(n.split('.')[0] in SCIENTIFIC or n=='knowledge_tracing' for n in sys.modules),'cold stdlib worker')
    denied=[]
    def guard(event,args):
        if event=='subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            denied.append(event);raise RuntimeError('pure kernel cannot launch children/network')
        if event=='import':
            name=str(args[0])
            if name.split('.')[0] in SCIENTIFIC or (name.startswith('knowledge_tracing.') and name!='knowledge_tracing.research_selection'):
                denied.append('import:'+name);raise RuntimeError('only stdlib/new statistics module permitted')
        if event=='open' and isinstance(args[0],(str,bytes)):
            name=str(args[0]).replace('\\','/').lower()
            if any(x in name for x in ('/research_tracking/runs/','/artifacts/simulator/corpora/','/dataset/','/experiments/')):
                denied.append('open:research-data');raise RuntimeError('no actual selection/corpus/cache/model data')
    sys.addaudithook(guard)
    sys.path.insert(0,str(ROOT/'src'))
    import knowledge_tracing.research_selection as kernel
    need(Path(kernel.__file__).resolve()==(ROOT/'src/knowledge_tracing/research_selection.py').resolve(),'new kernel exact origin')
    need(not any(n.split('.')[0] in SCIENTIFIC for n in sys.modules),'cold kernel import pulled scientific dependency')
    write(OUT/'cold-canary.json',dict(status='STDLIB_KERNEL_COLD_IMPORT_ONLY',module_file=str(kernel.__file__),
        scientific_modules_present=[],replicates=kernel.REPLICATES,seed=kernel.SEED,
        row_loss_id=kernel.ROW_LOSS_ID,aggregation_id=kernel.AGGREGATION_ID,
        nine_candidate_admission_performed=False,external_freeze_authority=False))
    sys.argv=[str(TEST)];rc=None;raw_exit_type=None;raw_exit_value=None
    try:runpy.run_path(str(TEST),run_name='__main__')
    except SystemExit as error:
        raw_exit_type,raw_exit_value=type(error.code).__name__,error.code
        if error.code is None:rc=0
        elif type(error.code) in (bool,int):rc=int(error.code)
        else:raise ValueError('unittest returned nonnumeric SystemExit')
    need(type(rc) is int,'unittest exact return code')
    after={name:sha(ROOT/name) for name in PINS}
    need(after==PINS and not denied and not any(n.split('.')[0] in SCIENTIFIC for n in sys.modules),
         'pure sources/guard/cold imports after fixtures')
    write(OUT/'worker-result.json',dict(unittest_returncode=rc,
        unittest_raw_exit_type=raw_exit_type,unittest_raw_exit_value=raw_exit_value,
        source_after=after,denied_attempts=denied,
        scientific_modules_present=[],model_calls=0,optimizer_calls=0,real_data_rows_opened=0,
        scope='Manufactured statistics; not real selection/grant, no main refit authority',
        ownership_gate_returned=True,elapsed_worker_seconds=elapsed()))
    raise SystemExit(rc)


def root(approval):
    need(type(approval) is str and approval.strip(),'explicit ROOT approval reference')
    need(not OUT.exists() and not OWNED.exists(),'fresh exclusive outputs; no retry')
    OUT.mkdir();errors=[];receipt=None;counts=None;before={};after={};self_sha=sha(SELF)
    try:
        before={name:sha(ROOT/name) for name in PINS}
        need(before==PINS and sha(ROOT/HELPER)==HELPER_SHA,'source/helper preflight')
        write(OUT/'before.json',dict(source_sha256=before,controller_sha256=self_sha,helper_sha256=HELPER_SHA,
            expected_unittest_methods=8,cap_seconds=CAP,approval_reference=approval,
            prior_charged_seconds=PRIOR_CHARGED_SECONDS,total_allocation_ceiling_seconds=PRIOR_CHARGED_SECONDS+CAP,
            scope='Kernel/tests stdlib only; existing owned launcher infrastructure uses installed psutil in parent'))
        allowance=CAP-elapsed()-1.
        need(allowance>3,'insufficient whole30s/cleanup; no dispatch')
        sys.path.insert(0,str(ROOT/'scripts/research'))
        from windows_owned_worker import run_owned
        receipt=run_owned(SELF,['--worker'],OWNED,expected_worker_sha256=self_sha,approval_reference=approval,
            max_seconds=allowance,cleanup_reserve_seconds=2,max_output_bytes=32768)
        write(OWNED/'receipt.json',receipt)
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] is True and receipt['returncode']==0
             and receipt['actual_worker_in_job_before_GO'] is True and not receipt['errors'],'owned pure completion/cleanup')
        for name,pin in receipt['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(OWNED/name)==pin,'owned stdout/stderr hash')
        stderr=(OWNED/'stderr.log').read_text(encoding='utf-8',errors='replace')
        matches=re.findall(r'(?m)^Ran (\d+) tests? in ([0-9.]+)s\s*$',stderr)
        need(len(matches)==1 and int(matches[0][0])==8 and re.search(r'(?m)^OK\s*$',stderr)
             and '(skipped=' not in stderr,'actual8 unittest cases; no skip/partial acceptance')
        counts=dict(tests=8,failures=0,errors=0,skipped=0)
        worker_result=json.loads((OUT/'worker-result.json').read_text(encoding='utf-8'))
        canary=json.loads((OUT/'cold-canary.json').read_text(encoding='utf-8'))
        need(worker_result['unittest_returncode']==0 and not worker_result['denied_attempts']
             and not worker_result['scientific_modules_present'] and worker_result['source_after']==PINS
             and canary['status']=='STDLIB_KERNEL_COLD_IMPORT_ONLY' and canary['replicates']==2000
             and canary['seed']==42 and canary['external_freeze_authority'] is False,'durable kernel-only canary/result')
        raw_kind,raw_value=worker_result['unittest_raw_exit_type'],worker_result['unittest_raw_exit_value']
        need((raw_kind=='bool' and raw_value is False)
             or (raw_kind=='int' and type(raw_value) is int and raw_value==0)
             or (raw_kind=='NoneType' and raw_value is None),'honest normalized unittest exit provenance')
        after={name:sha(ROOT/name) for name in PINS}
        need(after==PINS and sha(SELF)==self_sha and sha(ROOT/HELPER)==HELPER_SHA,'source/helper postflight')
        need(math.isfinite(elapsed()) and 0<=elapsed()<CAP,'whole30s including cleanup/finalization')
    except BaseException as error:errors.append(dict(type=type(error).__name__,message=str(error)))
    final=dict(status='ACCEPTED_8_MANUFACTURED_SELECTION_KERNEL_FIXTURES' if not errors else 'REJECTED_KEEP_PARTIAL_KERNEL_FIXTURES',
        errors=errors,counts=counts,elapsed_before_receipt_seconds=elapsed(),cap_seconds=CAP,
        prior_charged_seconds=PRIOR_CHARGED_SECONDS,
        cumulative_elapsed_before_receipt_seconds=PRIOR_CHARGED_SECONDS+elapsed(),
        total_allocation_ceiling_seconds=PRIOR_CHARGED_SECONDS+CAP,
        source_before=before,source_after=after,source_expected=PINS,controller_sha256=self_sha,
        owned_receipt_sha256=sha(OWNED/'receipt.json') if (OWNED/'receipt.json').exists() else None,
        output_sha256={name:sha(OUT/name) for name in ('cold-canary.json','worker-result.json') if (OUT/name).exists()},
        automatic_retry=False,scope='Only manufactured statistics; no real exports/all9 admission/externalfreeze/mainrefit/model efficacy')
    write(OUT/'final.json',final)
    ok=not errors and 0<=elapsed()<CAP
    if not ok and elapsed()>=CAP:
        write(OUT/'postwrite_rejection.json',dict(status='REJECTED_WHOLE30S_POSTWRITE',elapsed_seconds=elapsed()))
    print(json.dumps(dict(status=final['status'] if ok else 'REJECTED_KEEP_PARTIAL_KERNEL_FIXTURES',elapsed_seconds=elapsed(),cap_seconds=CAP)))
    raise SystemExit(0 if ok else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--approval-reference')
    args=parser.parse_args()
    if args.worker:worker()
    else:root(args.approval_reference)

