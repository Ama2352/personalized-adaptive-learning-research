"""ROOT-reviewed source-only launcher. One60s owned metadata operation, no fit."""
import time
START = time.perf_counter()
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
WORKER = P/'prepare_graph29_a0_control_package01.py'
HELPER = R/'scripts/research/windows_owned_worker.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main(args):
    need(Path(sys.prefix).resolve() == R/'.venv', 'repository .venv only')
    need(sha(WORKER) == args.worker_sha256 and sha(Path(__file__)) == args.outer_sha256
         and sha(HELPER) == HELPER_SHA and args.approval_reference.strip(), 'ROOT exact source/operation pins')
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import run_owned,entry
    entry()
    import psutil
    need(psutil.virtual_memory().available >= 2*1024**3, 'free2GiB before metadata')
    name = 'graph29-a0-control-package01-materialize' if args.materialize else 'graph29-a0-control-package01'
    owned,out = P/(name+'-owned'),P/name
    need(not owned.exists() and not out.exists(), 'fresh mode-specific operation, no retry')
    env = dict(os.environ)
    error = None; receipt = None; result = None
    try:
        # ROOT supplies this exact process profile. Do not strip additional
        # variables or repair an incompatible caller profile into acceptance.
        expected_git = dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_CONFIG_COUNT='3',
            GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',GIT_CONFIG_KEY_1='safe.directory',
            GIT_CONFIG_VALUE_1=(R/'artifacts/akt/dependencies/upstream').as_posix(),
            GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='true',GIT_OPTIONAL_LOCKS='0',
            GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
        need({key:value for key,value in os.environ.items() if key.startswith(('GIT_','GH_'))} == expected_git,
             'ROOT reviewed Git profile required unchanged; no environment stripping')
        os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
            TEMP=str(owned/'runtime-temp'),TMP=str(owned/'runtime-temp'),TMPDIR=str(owned/'runtime-temp'))
        argv = ['--materialize' if args.materialize else '--prepare-dry',
                '--approval-reference',args.approval_reference]
        if args.materialize:
            need(args.expected_dry_sha256 and args.review_reference, 'exact dry review before materialization')
            argv += ['--expected-dry-sha256',args.expected_dry_sha256,'--review-reference',args.review_reference]
        remaining = 60-(time.perf_counter()-START)-2
        need(remaining > 10, 'whole60 includes finalization and cleanup3')
        receipt = run_owned(WORKER,argv,owned,expected_worker_sha256=args.worker_sha256,
            approval_reference=args.approval_reference,max_seconds=min(57.,remaining),
            cleanup_reserve_seconds=3,max_output_bytes=65536)
        if owned.is_dir():
            with (owned/'receipt.json').open('x',encoding='utf-8') as stream:
                json.dump(receipt,stream,ensure_ascii=False,indent=2,allow_nan=False)
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
             and receipt['popen_handle_closed'] is True and receipt['errors'] == [] and receipt['returncode'] == 0,
             'actual owned metadata/cleanup')
        result = json.loads((out/'result.json').read_bytes())
        need(result['status'] == 'METADATA_PACKAGE_PENDING_OUTER' and result['error'] is None
             and result['denied'] == result['monitor_errors'] == [] and result['monitor_stopped'] is True
             and result['elapsed_seconds'] < 50 and len(result['git_calls']) == 10
             and result['model_calls'] == result['optimizer_calls'] == result['teacher_calls'] == 0
             and result['actual_guard_created'] is False and result['actual_selected_fit'] is False,
             'actual metadata scope, never main execution acceptance')
        need(result['resources']['peak_rss_bytes'] <= 1024**3
             and result['resources']['min_available_ram_bytes'] >= 2*1024**3, 'worker observed resources')
        need(all(sha(R/name) == digest for name,digest in result['output_sha256'].items()), 'prepared bytes unchanged')
    except BaseException as exc:
        error = dict(type=type(exc).__name__,message=str(exc))
    finally:
        os.environ.clear(); os.environ.update(env)
    need(dict(os.environ) == env and sha(WORKER) == args.worker_sha256
         and sha(Path(__file__)) == args.outer_sha256, 'outer environment/source restored')
    accepted = error is None and time.perf_counter()-START < 60
    out.mkdir(exist_ok=True)
    final = dict(status='ACCEPTED_METADATA_PACKAGE_ONLY' if accepted else 'REJECTED_KEEP_PARTIAL',
        mode='materialize' if args.materialize else 'prepare-dry',error=error,worker_result=result,
        owned_receipt=receipt,elapsed_seconds=time.perf_counter()-START,cap_seconds=60,
        actual_guard_verified=False,actual_fit_verified=False,environment_restored=True)
    with (out/'outer-final.json').open('x',encoding='utf-8') as stream:
        json.dump(final,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')
    if time.perf_counter()-START >= 60:
        with (out/'postwrite-rejection.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(status='REJECTED_METADATA_POSTWRITE_BUDGET'),stream)
        accepted = False
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker-sha256',required=True); parser.add_argument('--outer-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-dry',action='store_true'); mode.add_argument('--materialize',action='store_true')
    parser.add_argument('--expected-dry-sha256'); parser.add_argument('--review-reference')
    main(parser.parse_args())
