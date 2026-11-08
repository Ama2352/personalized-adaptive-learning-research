"""ROOT-only bounded pure14 capture; reuse owned helper, never duplicate Kernel."""
import time
START,WALL=time.perf_counter(),time.time()
from pathlib import Path
import argparse
import hashlib
import json
import re
import runpy
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
SELF=Path(__file__).resolve()
TEST=PREP/'test_fixed_controller_candidates01.py'
CAP=10.
HELPER='scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
PINS={
    'analyze_fixed_controller_candidates01.py':'e6275c7a57a7fc35276fb6536b13ff111138d8bb0bf31c8243aa0d7bf6877fe1',
    'test_fixed_controller_candidates01.py':'711b8eb9153553e5acd5db29715098df8805b87d28df86134b15b9299a3e1383',
    'rq1_fixed_controller_candidates_contract_20261109.md':'eddde48afb910685de5d5f9ab4650f381bf04a1cae832fdc97b9012153fe19d3',
}
OUT=PREP/'fixed-controller-pure14-capture01'
OWNED=PREP/'fixed-controller-pure14-owned01'


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    need(path.is_file() and not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'physical source/log')
    need(path.stat().st_size<=128*1024,'bounded pure source/log')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush()


def worker():
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    worker_gate()
    need(all(sha(PREP/n)==h for n,h in PINS.items()),'exact pure sources before tests')
    def guard(event,values):
        if event=='subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            raise RuntimeError('pure fixtures cannot launch children/network')
        if event=='import' and str(values[0]).split('.')[0] in {'knowledge_tracing','numpy','pandas','torch','sklearn','scipy'}:
            raise RuntimeError('pure fixtures cannot import native/scientific code')
        if event=='open' and isinstance(values[0],(str,bytes)):
            name=str(values[0]).replace('\\','/').lower()
            if any(x in name for x in ('/research_tracking/runs/','/artifacts/simulator/corpora/','/dataset/','/experiments/')):
                raise RuntimeError('pure fixtures cannot open actual cached/corpus/model data')
    sys.addaudithook(guard)
    need(not any(n in sys.modules for n in ('knowledge_tracing','numpy','pandas','torch','sklearn','scipy')),'fresh stdlib-only worker')
    sys.argv=[str(TEST)]
    runpy.run_path(str(TEST),run_name='__main__')  # unittest.main exits; all outputs captured by owned helper.


def root(approval):
    need(approval and approval.strip(),'explicit ROOT approval reference')
    need(not OUT.exists() and not OWNED.exists(),'fresh exclusive capture, no retry')
    OUT.mkdir()
    errors=[];receipt=None;counts=None;before={};after={};self_sha=sha(SELF)
    try:
        before={n:sha(PREP/n) for n in PINS}
        need(before==PINS and sha(ROOT/HELPER)==HELPER_SHA,'source/helper preflight')
        write(OUT/'before.json',dict(source_sha256=before,controller_sha256=self_sha,helper_sha256=HELPER_SHA,
            expected_unittest_methods=14,cap_seconds=CAP,model_or_cache_work_allowed=False,approval_reference=approval))
        allowance=CAP-elapsed()-.4
        need(allowance>2,'not enough remaining time for owned cleanup; STOP before dispatch')
        sys.path.insert(0,str(ROOT/'scripts/research'))
        from windows_owned_worker import run_owned
        receipt=run_owned(SELF,['--worker'],OWNED,expected_worker_sha256=self_sha,approval_reference=approval,
            max_seconds=allowance,cleanup_reserve_seconds=2,max_output_bytes=32768)
        write(OWNED/'receipt.json',receipt)
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] is True and receipt['returncode']==0
             and receipt['actual_worker_in_job_before_GO'] is True and not receipt['errors'],'owned pure execution/cleanup')
        for name,pin in receipt['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(OWNED/name)==pin,'owned original output hash')
        stderr=(OWNED/'stderr.log').read_text(encoding='utf-8',errors='replace')
        matches=re.findall(r'(?m)^Ran (\d+) tests? in ([0-9.]+)s\s*$',stderr)
        need(len(matches)==1 and int(matches[0][0])==14 and re.search(r'(?m)^OK\s*$',stderr)
             and '(skipped=' not in stderr,'actual14 unittest cases, no skip/partial promotion')
        counts=dict(tests=14,failures=0,errors=0,skipped=0)
        after={n:sha(PREP/n) for n in PINS}
        need(after==PINS and sha(SELF)==self_sha and sha(ROOT/HELPER)==HELPER_SHA,
             'source/helper post-test drift')
        need(elapsed()<CAP,'whole10s resource budget')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
    final=dict(status='ACCEPTED_14_PURE_CONTROLLER_RULE_FIXTURES' if not errors else 'REJECTED_KEEP_PARTIAL_PURE_FIXTURES',
        errors=errors,counts=counts,elapsed_before_receipt_seconds=elapsed(),cap_seconds=CAP,
        source_before=before,source_after=after,source_expected=PINS,controller_sha256=self_sha,
        owned_receipt_sha256=sha(OWNED/'receipt.json') if (OWNED/'receipt.json').exists() else None,
        output_sha256=None if receipt is None else receipt.get('output_sha256'),
        scope='Hand-made rule fixtures only; no gzip/cache/solver/model/native/scientific imports; not research samples',
        automatic_retry=False)
    write(OUT/'final.json',final)
    ok=not errors and elapsed()<CAP
    if not ok and elapsed()>=CAP:
        write(OUT/'postwrite_rejection.json',dict(status='REJECTED_WHOLE10S_POSTWRITE',elapsed_seconds=elapsed()))
    print(json.dumps(dict(status=final['status'] if ok else 'REJECTED_KEEP_PARTIAL_PURE_FIXTURES',elapsed_seconds=elapsed(),cap_seconds=CAP)))
    raise SystemExit(0 if ok else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--approval-reference')
    args=parser.parse_args()
    if args.worker:worker()
    else:root(args.approval_reference)
