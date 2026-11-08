"""ROOT dispatch only; pure reservation10s + native whole<=50s, cumulative<=60s.

No execution authority from this source. One attempt per phase, no retry/resume.
"""
import time
START, WALL = time.perf_counter(), time.time()
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import runpy
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PLAN = PREP/'prediction_mastery_trace_plan01.json'
WORKER = PREP/'prediction_mastery_trace_worker01.py'
TEST = PREP/'test_prediction_mastery_trace01.py'
HELPER = ROOT/'scripts/research/windows_owned_worker.py'


def need(ok,message):
    if not ok: raise ValueError(message)


def elapsed(): return max(time.perf_counter()-START,time.time()-WALL)


def physical(path):
    path = path.absolute(); need(path.is_relative_to(ROOT), 'workspace only')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(), 'no source/output alias')
    need(path.resolve() == path, 'canonical physical path')
    return path


def sha(path,cap=4*1024**2):
    path = physical(path)
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular source/input/output')
    with path.open('rb') as stream: raw = stream.read(cap+1)
    need(len(raw) <= cap and len(raw) == path.stat().st_size, 'stable byte payload')
    return hashlib.sha256(raw).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def pure_worker(pin):
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    worker_gate()  # Before test/import of any native package.
    need(sha(PLAN) == pin, 'plan pinned')
    plan=json.loads(PLAN.read_bytes())
    need(all(sha(ROOT/n) == h for n,h in plan['source_sha256'].items()), 'all prepared sources exact')
    def audit(event,values):
        if event == 'subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            raise RuntimeError('no pure children/network')
        if event == 'import' and str(values[0]).split('.')[0] in {'knowledge_tracing','numpy','pandas','torch','scipy','sklearn'}:
            raise RuntimeError('no pure native/scientific import')
        if event == 'open' and isinstance(values[0],(str,bytes)):
            name=str(values[0]).replace('\\','/').lower()
            if any(s in name for s in ('/research_tracking/runs/','/artifacts/simulator/','/dataset/','/experiments/')):
                raise RuntimeError('no actual data/cache/oracle/model in pure fixtures')
    sys.addaudithook(audit)
    need(not any(n in sys.modules for n in ('knowledge_tracing','numpy','pandas','torch')), 'fresh stdlib-only pure')
    sys.argv=[str(TEST)];runpy.run_path(str(TEST),run_name='__main__')


def validate_trace(inner,plan):
    need(not any((inner/n).exists() for n in ('failure.log','postwrite_rejection.json')), 'no native failure/late rejection')
    run=json.loads((inner/'worker_run.json').read_bytes())
    need(run['status'] == 'INNER_ALL2160_LEGACY_AND18_FINAL_FINGERPRINTS_EXACT_PENDING_ROOT'
         and run['errors'] == [] and run['profiler_restored'] is True, 'inner parity success only')
    need(run['direct_attempts'] == run['direct_returns'] == plan['direct_call_caps'], 'exact all direct calls')
    need(run['native_attempts'] == run['native_returns'], 'all native returns')
    for k,n in plan['native_call_caps'].items():
        actual=run['native_attempts'].get(k,0)
        need(type(actual) is int and 0 <= actual <= n, 'native all-calls bound '+k)
    for k,n in dict(predict=6480,update=2160,select=2160,ready_set=4320).items():
        need(run['native_attempts'][k] == n, 'exact native call count '+k)
    need(len(run['completed_trajectories']) == 18 and run['legacy_rows_exact'] == 2160
         and run['teacher_calls'] == run['optimizer_steps'] == run['new_independent_N'] == 0, 'whole population/limits')
    need(type(run['node_order']) is list and len(run['node_order']) == len(set(run['node_order'])) == 28, 'explicit28 node order')
    expected_trajectories={(s,p,v) for s in (20000,20001,20002) for p in ('PG','PY','PYH') for v in ('graph_package','empty_graph_package')}
    need({(r['seed'],r['profile'],r['variant']) for r in run['completed_trajectories']} == expected_trajectories
         and all(r['exact_legacy_rows'] == r['full_preview_exact'] == 120 for r in run['completed_trajectories']), 'all18 complete')
    expected_names={'reservation.json','trace.jsonl.gz','dispatch.json','worker_run.json'}|{f'trajectory-{i}.json' for i in range(1,19)}
    need({p.name for p in inner.iterdir() if p.is_file()} == expected_names, 'exact native output set')
    need(set(run['outputs_sha256']) == expected_names-{'dispatch.json','worker_run.json'}, 'closed native hash set')
    for name,pin in run['outputs_sha256'].items():
        need(sha(inner/name,plan['max_output_file_bytes']) == pin, 'native output SHA '+name)
    size=0;keys=set()
    with gzip.open(inner/'trace.jsonl.gz','rb') as stream:
        while True:
            need(10+elapsed() < 60, 'whole60 includes validation/read/cleanup')
            line=stream.readline(32769)
            if not line: break
            size += len(line)
            need(line.endswith(b'\n') and len(line) <= 32768 and size <= plan['max_trace_decompressed_bytes'], 'bounded complete2160 trace')
            row=json.loads(line);key=row['seed'],row['profile'],row['variant'],row['event_id']
            need(key not in keys and row['phase'] == 'PRE_CURRENT_UPDATE_NO_LABEL_IN_CAPTURE', 'one preupdate trace/key')
            need(set(row).isdisjoint({'y','correct','oracle','profile_theta'}), 'no current answer or oracle in trace payload')
            keys.add(key)
            need(len(row['native_state']) == 28 and len(row['raw_references']) == 3, 'all28 states/3refs')
            for theta,pi,a,b,m in row['native_state']:
                need(type(theta) is float and type(pi) is float and math.isfinite(theta) and math.isfinite(pi) and 0 <= pi <= 1,
                     'raw theta/pi fields')
                need(type(a) is type(b) is type(m) is bool and (a,b,m) == (theta>=1250.,pi<=.55,theta>=1250. and pi<=.55), 'native predicates')
            need(type(row['probability']) is float and 0 <= row['probability'] <= 1 and
                 len([r for r in row['raw_references'] if r['question'] == row['query']['question'] and r['difficulty'] == row['query']['difficulty'] and r['probability'] == row['probability']]) == 1, 'exact current P/reference reuse')
            refs=row['raw_references'];need(sorted(r['difficulty'] for r in refs) == [1050.,1200.,1350.]
                and len({r['question'] for r in refs}) == 3 and all(type(r['probability']) is float
                and math.isfinite(r['probability']) and 0 <= r['probability'] <= 1 for r in refs), 'real raw reference identities')
            need(row['raw_reference_mean'] == sum(r['probability'] for r in refs)/3
                 and row['raw_reference_criterion'] == (row['raw_reference_mean'] >= .5637150147511514), 'raw not calibrated criterion')
    need(keys == {(s,p,v,str(t)) for s,p,v in expected_trajectories for t in range(120)}, 'all2160 trace keys/CRC')
    return run


def main(args):
    need(args.approval_reference.strip() and sha(PLAN) == args.plan_sha256, 'ROOT approval/plan exact')
    need(Path(sys.prefix).resolve() == ROOT/'.venv', '.venv only')
    plan=json.loads(PLAN.read_bytes()); phase=args.phase
    need(phase in ('pure','native') and plan['max_cumulative_seconds'] == 60 and plan['pure_reserved_seconds'] == 10, 'fixed global allocation')
    expected={**plan['source_sha256'],**plan['inputs_sha256'],PLAN.relative_to(ROOT).as_posix():args.plan_sha256}
    need(all(sha(ROOT/n) == h for n,h in expected.items()), 'all pinned sources/inputs before')
    out=PREP/('prediction-mastery-pure12-attempt01' if phase == 'pure' else 'prediction-mastery-native-outer01')
    inner=PREP/plan['output_name']
    need(not physical(out).exists() and (phase == 'pure' or not physical(inner).exists()), 'exclusive fresh attempt/no retry')
    out.mkdir();error=None;owned=None;run=None;self_sha=sha(Path(__file__).resolve())
    cap=10 if phase == 'pure' else 50
    saved={k:os.environ.get(k) for k in ('CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTHONDONTWRITEBYTECODE')}
    os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    try:
        sys.path.insert(0,str(ROOT/'scripts/research'))
        from windows_owned_worker import run_owned
        if phase == 'native':
            pure=PREP/'prediction-mastery-pure12-attempt01/final.json'
            need(pure.is_file() and not pure.with_name('postwrite_rejection.json').exists(), 'actual pure receipt prerequisite')
            previous=json.loads(pure.read_bytes())
            need(previous['status'] == 'ACCEPTED_12_SYNTHETIC_TRACE_FIXTURES' and previous['errors'] == []
                 and previous['plan_sha256'] == args.plan_sha256 and previous['source_after'] == expected
                 and previous['counts'] == dict(tests=12,failures=0,errors=0,skipped=0), 'same plan actual12 pure accepted')
            need(sha(PREP/'prediction-mastery-pure12-attempt01/owned/receipt.json') == previous['owned_receipt_sha256'], 'pure ownership binding')
            sys.path.insert(0,str(ROOT/'src'))
            from knowledge_tracing.akt.resources import memory_snapshot
            memory=memory_snapshot()
            need(type(memory['system_available_ram_bytes']) is int and memory['system_available_ram_bytes'] >= plan['min_free_ram_bytes']
                 and memory['process_rss_bytes'] <= plan['max_rss_bytes'], 'ROOT preflight RAM')
            inner.mkdir();allowance=min(55.,cap-elapsed()-4.1)
            need(allowance > 0, 'remaining native time includes preflight')
            write(inner/'dispatch.json',dict(status='ONE_RESERVED_NO_RETRY',approval_reference=args.approval_reference,
                plan_sha256=args.plan_sha256,source_input_before=expected,pure_receipt_sha256=sha(pure),
                pure_charged_seconds=10,native_allowance_seconds=allowance,max_cumulative_seconds=60,
                preflight_memory=memory,direct_reservations=plan['direct_call_caps']))
            target=WORKER;worker_args=['--plan-sha256',args.plan_sha256,'--remaining-seconds',str(allowance)]
        else:
            target=Path(__file__).resolve();worker_args=['--pure-worker','--plan-sha256',args.plan_sha256]
        helper_allowance=cap-elapsed()-2.
        need(helper_allowance > 2., 'cleanup2s/finalization2s included in same allocation')
        owned=run_owned(target,worker_args,out/'owned',expected_worker_sha256=sha(target),
            approval_reference=args.approval_reference,max_seconds=helper_allowance,cleanup_reserve_seconds=2.,max_output_bytes=65536)
        write(out/'owned/receipt.json',owned)
        need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
             and owned['actual_worker_in_job_before_GO'] is True and owned['popen_handle_closed'] is True
             and owned['worker_returncode_before_cleanup'] == 0 and owned['errors'] == [], 'owned execution+cleanup')
        need(not (out/'owned/postwrite_rejection.json').exists(), 'no late ownership rejection')
        if phase == 'pure':
            stderr=(out/'owned/stderr.log').read_text(encoding='utf-8')
            need(re.search(r'Ran 12 tests in [0-9.]+s',stderr) is not None and stderr.rstrip().endswith('OK'), 'actual12 unittest result, no partial dots')
        else:
            run=validate_trace(inner,plan)
            need(run['source_input_before'] == run['source_input_after'] == expected, 'native all bindings unchanged')
            final_memory=memory_snapshot()
            need(type(final_memory['system_available_ram_bytes']) is int and final_memory['system_available_ram_bytes'] >= plan['min_free_ram_bytes']
                 and max(final_memory['process_rss_bytes'],final_memory['process_peak_rss_bytes'] or 0) <= plan['max_rss_bytes'], 'outer postvalidation RAM')
        need(all(sha(ROOT/n) == h for n,h in expected.items()) and sha(Path(__file__).resolve()) == self_sha, 'post source/input stable')
        need(elapsed() < cap, 'finite postelapsed includes all phases')
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc))
        with (out/'failure.log').open('x',encoding='utf-8') as stream:traceback.print_exc(file=stream)
    finally:
        for k,v in saved.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    after={n:sha(ROOT/n) for n in expected}
    if after != expected:error=error or dict(type='SourceDrift')
    files=[p for folder in ([out] if phase == 'pure' else [out,inner]) for p in folder.rglob('*') if p.is_file()]
    need(len(files) <= 64 and all(p.stat().st_size <= plan['max_output_file_bytes'] for p in files)
         and sum(p.stat().st_size for p in files) <= plan['max_total_output_bytes'], 'bounded whole output set')
    result=dict(status=('ACCEPTED_12_SYNTHETIC_TRACE_FIXTURES' if phase == 'pure' else 'ACCEPTED_FIXED_HISTORY_MASTERY_TRACE_ONLY') if error is None else 'REJECTED_KEEP_ALL_NO_RETRY',
        errors=[] if error is None else [error],phase=phase,plan_sha256=args.plan_sha256,
        elapsed_before_receipt_seconds=elapsed(),phase_cap_seconds=cap,pure_reserved_charge_seconds=10,
        cumulative_charged_before_receipt_seconds=(elapsed() if phase == 'pure' else 10+elapsed()),
        counts=dict(tests=12,failures=0,errors=0,skipped=0) if phase == 'pure' and error is None else None,
        source_before=expected,source_after=after,owned_receipt_sha256=sha(out/'owned/receipt.json') if owned is not None else None,
        worker_run_sha256=sha(inner/'worker_run.json') if run is not None else None,
        files_sha256={p.relative_to(PREP).as_posix():sha(p,plan['max_output_file_bytes']) for p in files},
        new_independent_N=0,automatic_retry=False)
    write(out/'final.json',result)
    if elapsed() >= cap:
        write(out/'postwrite_rejection.json',dict(status='REJECTED_POSTWRITE',elapsed_seconds=elapsed(),cap_seconds=cap))
        error=error or dict(type='PostwriteBudget')
    print(json.dumps(dict(status=result['status'] if error is None else 'REJECTED_KEEP_ALL_NO_RETRY',elapsed_seconds=elapsed(),error=error)))
    raise SystemExit(0 if error is None else 1)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--pure-worker',action='store_true');parser.add_argument('--phase',choices=('pure','native'))
    parser.add_argument('--approval-reference')
    args=parser.parse_args()
    if args.pure_worker:pure_worker(args.plan_sha256)
    else:
        need(args.phase is not None and args.approval_reference is not None,'explicit phase/approval required')
        main(args)


