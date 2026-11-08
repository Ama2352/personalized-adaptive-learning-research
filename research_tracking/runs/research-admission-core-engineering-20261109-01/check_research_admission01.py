"""ROOT-only GRAPH12/13 admission pure8/cold-canary01; no real selection, corpus, model or grant."""
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
TEST=ROOT/'tests/shared_kt/test_research_admission.py'
OUT=PREP/'research-admission-pure-capture01'
OWNED=PREP/'research-admission-pure-owned01'
CAP=30.
PRIOR_CHARGED_SECONDS=0.
HELPER='scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
PINS={
    'src/knowledge_tracing/__init__.py':'b84a9a4118d8b3476daae25a7981c97909524ace7ef93860bba7e6ec9e5bccb8',
    'src/knowledge_tracing/research_selection.py':'0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348',
    'src/knowledge_tracing/research_admission.py':'b8601da03a972834cfd2f5596ea6a6b9c5759437796b4f4b65720f7abc1a92f2',
    'tests/shared_kt/test_research_admission.py':'d69dbf755a0f784a26b9eaf7cfc0b411ff035e191a8faecae770b4eb3bb4a2e3',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/MAIN_NINE_ADMISSION_REVIEW01.md':'88a7d5d72c6281537c12a2cb204bbedc9de7400333e6b387146c17efced6615a',
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
    need(Path(sys.prefix).resolve()==ROOT/'.venv','repository isolated Python required')
    need(all(sha(ROOT/name)==pin for name,pin in PINS.items()),'pure source preflight')
    need(not any(n.split('.')[0] in SCIENTIFIC or n=='knowledge_tracing' for n in sys.modules),'cold stdlib worker')
    denied=[]
    def guard(event,args):
        if event=='subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            denied.append(event);raise RuntimeError('pure kernel cannot launch children/network')
        if event=='import':
            name=str(args[0])
            if name.split('.')[0] in SCIENTIFIC or (name.startswith('knowledge_tracing.') and name not in ('knowledge_tracing.research_selection','knowledge_tracing.research_admission')):
                denied.append('import:'+name);raise RuntimeError('only stdlib/new statistics module permitted')
        if event=='open' and isinstance(args[0],(str,bytes)):
            name=str(args[0]).replace('\\','/').lower()
            if any(x in name for x in ('/research_tracking/runs/','/artifacts/simulator/corpora/','/dataset/','/experiments/')):
                denied.append('open:research-data');raise RuntimeError('no actual selection/corpus/cache/model data')
    sys.addaudithook(guard)
    sys.path.insert(0,str(ROOT/'src'))
    import knowledge_tracing.research_admission as kernel
    need(Path(kernel.__file__).resolve()==(ROOT/'src/knowledge_tracing/research_admission.py').resolve(),'new kernel exact origin')
    need(not any(n.split('.')[0] in SCIENTIFIC for n in sys.modules),'cold kernel import pulled scientific dependency')
    write(OUT/'cold-canary.json',dict(status='STDLIB_ADMISSION_COLD_IMPORT_ONLY',module_file=str(kernel.__file__),
        python_implementation=sys.implementation.name,python_version=list(sys.version_info[:3]),
        prefix=str(Path(sys.prefix).resolve()),executable=str(Path(sys.executable).resolve()),
        scientific_modules_present=[],required_candidates=len(kernel.REQUIRED_CANDIDATE_IDS),common_models=len(kernel.COMMON_MODEL_IDS),
        population_scheme=kernel.POPULATION_SCHEME,
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
             and canary['status']=='STDLIB_ADMISSION_COLD_IMPORT_ONLY' and canary['required_candidates']==9
             and canary['common_models']==5 and canary['external_freeze_authority'] is False,'durable admission-only canary/result')
        raw_kind,raw_value=worker_result['unittest_raw_exit_type'],worker_result['unittest_raw_exit_value']
        need((raw_kind=='bool' and raw_value is False)
             or (raw_kind=='int' and type(raw_value) is int and raw_value==0)
             or (raw_kind=='NoneType' and raw_value is None),'honest normalized unittest exit provenance')
        after={name:sha(ROOT/name) for name in PINS}
        need(after==PINS and sha(SELF)==self_sha and sha(ROOT/HELPER)==HELPER_SHA,'source/helper postflight')
        need(math.isfinite(elapsed()) and 0<=elapsed()<CAP,'whole30s including cleanup/finalization')
    except BaseException as error:errors.append(dict(type=type(error).__name__,message=str(error)))
    final=dict(status='ACCEPTED_8_MANUFACTURED_ADMISSION_CORE_FIXTURES' if not errors else 'REJECTED_KEEP_PARTIAL_ADMISSION_FIXTURES',
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
    print(json.dumps(dict(status=final['status'] if ok else 'REJECTED_KEEP_PARTIAL_ADMISSION_FIXTURES',elapsed_seconds=elapsed(),cap_seconds=CAP)))
    raise SystemExit(0 if ok else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--approval-reference')
    args=parser.parse_args()
    if args.worker:worker()
    else:root(args.approval_reference)



