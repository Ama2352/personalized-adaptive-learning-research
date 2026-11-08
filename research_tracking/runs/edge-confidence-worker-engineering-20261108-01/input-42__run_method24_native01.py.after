"""ROOT-only prepare/run một Method24 operation; chưa auto-authorization.

prepare chỉ ghi request metadata exclusive, không tạo worker/fit. run cần ROOT
review source/request trước dispatch. Không retry, không sửa canonical/oracle.
"""
import time
START = time.perf_counter()
WALL = time.time()
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PREP_REL = PREP.relative_to(ROOT).as_posix()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def worker_module():
    path = PREP/'method24_worker01.py'
    spec = importlib.util.spec_from_file_location('method24_reviewed_stdlib_worker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Definitions only; no worker_gate/imports/fit.
    return module


def write(name, value):
    with (PREP/name).open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False)
        handle.write('\n');handle.flush();os.fsync(handle.fileno())


def prepare_request(module, approval_reference):
    need(type(approval_reference) is str and approval_reference.strip(), 'explicit ROOT approval reference for future dispatch')
    config_sha = module.hash_file(module.CONFIG)
    config = module.read_json(module.CONFIG, config_sha)
    profile_sha = module.hash_file(module.PROFILE)
    module.validate_profile(module.read_json(module.PROFILE, profile_sha))
    c = config['corpus']
    prior = module.read_json(c['prior_inventory_relative'],c['prior_inventory_sha256'])
    prefix = 'artifacts/simulator/corpora/'+c['id']+'/'
    request = dict(schema_version=1,purpose='method24_train_only_conditional_surrogate',approval_reference=approval_reference,
        config_sha256=config_sha,runtime_profile_sha256=profile_sha,
        source_sha256={name:module.hash_file(name,cap=262144) for name in module.SOURCES},source_count=len(module.SOURCES),
        public_sha256={name:prior['files'][prefix+name]['sha256'] for name in module.PUBLIC},output_relative=module.OUTPUT)
    # Request generation is not execution authority. No fit/target process here.
    path = module.safe(module.REQUEST)
    with path.open('xb') as handle:
        handle.write(module.encode(request));handle.flush();os.fsync(handle.fileno())
    return dict(status='PREPARED_NOT_DISPATCHED',request_relative=module.REQUEST,request_sha256=module.hash_file(module.REQUEST))


def worker_argv(module, request_sha, deadline_perf, deadline_wall):
    module.valid_sha(request_sha)
    need(all(type(x) in (int,float) and math.isfinite(x) for x in (deadline_perf,deadline_wall)), 'finite bound deadlines')
    return ['--request',module.REQUEST,'--request-sha256',request_sha,
        '--active-deadline-perf',repr(deadline_perf),'--active-deadline-wall',repr(deadline_wall)]


def _memory_api():
    from knowledge_tracing.akt.resources import memory_snapshot
    return memory_snapshot


def _owned_api():
    from windows_owned_worker import run_owned
    return run_owned


def resource_preflight(snapshot, caps):
    rss, peak, free = snapshot['process_rss_bytes'],snapshot['process_peak_rss_bytes'],snapshot['system_available_ram_bytes']
    need(type(rss) is int and rss >= 0 and (peak is None or type(peak) is int and peak >= 0) and type(free) is int and free >= 0,
         'valid parent memory telemetry')
    need(max(rss,peak or 0) <= caps['max_rss_bytes'] and free >= caps['min_available_ram_bytes'], 'parent fresh RAM preflight')


def accept_worker(module, request_sha, request, owned, elapsed):
    need(owned['accepted'] and owned['cleanup_accepted'] and owned['cleanup_errors'] == [] and
         owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] and
         owned['worker_returncode_before_cleanup'] == owned['returncode'] == 0 and owned['actual_worker_in_job_before_GO'],
         'owned launch/worker/cleanup acceptance required')
    directory = module.safe(module.OUTPUT)
    names = {p.name for p in directory.iterdir() if p.is_file()}
    need(names == set(module.OUTPUT_FILES) and len(list(directory.iterdir())) == len(module.OUTPUT_FILES), 'exact output population/no failure files')
    def artifact_json(name):
        rel = module.OUTPUT+'/'+name
        return module.read_json(rel,module.hash_file(rel),cap=2*1024**2)
    result, done, resources = artifact_json('worker_result.json'),artifact_json('DONE.json'),artifact_json('resources.json')
    need(result['status'] == 'COMPLETE_CONDITIONAL_SURROGATE_PENDING_OUTER_ACCEPTANCE' and
         result['request_sha256'] == request_sha and result['config_sha256'] == request['config_sha256'] and
         result['outer_acceptance_required'] is True and result['processed_fit_slots'] == 2352 and
         type(result['actual_solver_calls']) is int and 0 <= result['actual_solver_calls'] <= 2352 and
         result['oof_rows'] == 272160 and result['edge_summaries'] == 756 and
         result['teacher_calls'] == result['neural_optimizer_steps'] == result['modal_spend_usd'] == 0, 'result scope/counts')
    owner = result['owner']
    need(owner['worker'] == owned['actual_worker'] and owner['parent_owner'] == owned['parent'] and
         owner['job_name'] == owned['job_name'], 'actual worker/parent/Job output owner mismatch')
    need(resources['observed_peak_rss_bytes'] <= module.CAPS['max_rss_bytes'] and
         resources['observed_minimum_available_ram_bytes'] >= module.CAPS['min_available_ram_bytes'] and
         resources['samples'] > 0, 'resource observation acceptance')
    need(set(done) == {'schema_version','status','request_sha256','files_sha256'} and type(done['schema_version']) is int and
         done['schema_version'] == 1 and done['status'] == 'COMPLETE_METHOD24_PENDING_OUTER_ACCEPTANCE' and
         done['request_sha256'] == request_sha and type(done['files_sha256']) is dict and
         set(done['files_sha256']) == set(module.OUTPUT_FILES)-{'DONE.json'}, 'closed DONE map')
    inventory,total = {},0
    for name in module.OUTPUT_FILES:
        path = module.safe(module.OUTPUT+'/'+name)
        size = path.stat().st_size
        limit = module.CAPS['max_oof_file_bytes'] if name == 'edge-oof.csv' else module.CAPS['max_total_output_bytes']
        digest = module.hash_file(module.OUTPUT+'/'+name,cap=limit,check=lambda:need(elapsed()<=120,'post-artifact global cap'))
        if name != 'DONE.json':
            need(done['files_sha256'][name] == digest, 'published file hash mismatch')
        inventory[name] = dict(sha256=digest,bytes=size)
        total += size
    need(total <= module.CAPS['max_total_output_bytes'], 'total output byte cap')
    need(type(result['data_sha256']) is dict and set(result['data_sha256']) == set(module.DATA_FILES) and
         result['data_sha256'] == {name:inventory[name] for name in module.DATA_FILES}, 'data/result/DONE inventory mismatch')
    need(result['graph_status'] in ('SUPPORTED_DAG','UNSUPPORTED_EDGE_BUDGET') and
         (result['graph_status'] != 'SUPPORTED_DAG' or result['graph_edges'] == 31), 'no forced graph acceptance')
    return result, inventory


def run(module, request_sha):
    start, wall = START, WALL
    elapsed = lambda: max(time.perf_counter()-start,time.time()-wall)
    need(Path(sys.executable).absolute() == ROOT/'.venv/Scripts/python.exe' and Path(sys.prefix).resolve() == ROOT/'.venv', 'repository venv only')
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='')
    sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts/research'))
    # No heavy libraries before actual fresh parent RAM check.
    memory = _memory_api()()
    resource_preflight(memory,module.CAPS)
    request,config,profile,runtime_files = module.validate_request(module.REQUEST,request_sha)
    need(not (PREP/'method24_dispatch01.json').exists() and not (PREP/'method24-owned01').exists() and
         not (PREP/'method24_run01.json').exists(), 'exclusive one dispatch, no retry')
    allowance = 120-elapsed()-7
    need(allowance > 3, 'no owned cleanup allowance')
    argv = worker_argv(module,request_sha,start+110,wall+110)
    # Parse-only check prevents missing worker CLI flags before Popen.
    module.parse_args(argv)
    write('method24_dispatch01.json',dict(status='RESERVED_NOT_ACTUAL_FITS',request_sha256=request_sha,
        source_sha256=request['source_sha256'],runtime_profile_sha256=request['runtime_profile_sha256'],
        reserved_solver_calls=2352,actual_solver_calls=None,oof_rows=272160,outer_cap=120,active_cap=110,
        cleanup_reserve=3,outer_finalization_reserve=7,export_reserve=8,memory_before=memory,worker_argv=argv,
        approval_reference=request['approval_reference'],automatic_retry=False))
    result=owned=None;inventory={};error=None
    try:
        allowance = 120-elapsed()-7
        need(allowance > 3, 'no remaining cleanup/finalization allowance after dispatch write')
        owned = _owned_api()(module.safe(module.SELF),argv,PREP/'method24-owned01',
            expected_worker_sha256=request['source_sha256'][module.SELF],approval_reference=request['approval_reference'],
            max_seconds=allowance,cleanup_reserve_seconds=3,max_output_bytes=65536)
        write('method24_owned_receipt01.json',owned)
        result,inventory = accept_worker(module,request_sha,request,owned,elapsed)
        need(all(module.hash_file(p,cap=262144) == h for p,h in request['source_sha256'].items()), 'post-worker source drift')
        need(all(module.hash_file(p) == h for p,h in runtime_files.items()), 'post-worker runtime packet drift')
        prefix = 'artifacts/simulator/corpora/'+config['corpus']['id']+'/'
        need(all(module.hash_file(prefix+p) == h for p,h in request['public_sha256'].items()) and
             not module.safe(prefix+'failure.json').exists(), 'post-worker public drift/failure override')
        need(module.hash_file(module.REQUEST) == request_sha and module.hash_file(module.CONFIG) == request['config_sha256'] and
             module.hash_file(module.PROFILE) == request['runtime_profile_sha256'], 'post-worker request/config/profile drift')
        need(elapsed() <= 120, 'whole-operation posthash cap')
    except Exception as exception:
        error=dict(type=type(exception).__name__,message=str(exception))
        with (PREP/'method24_outer_failure01.log').open('x',encoding='utf-8') as handle:
            traceback.print_exc(file=handle)
    if elapsed() > 120:
        error=error or dict(type='BudgetExceeded',message='outer120seconds')
    receipt=dict(status='ACCEPTED_CONDITIONAL_TRAIN_SURROGATE_NOT_EDGE_TRUTH' if error is None else 'REJECTED_KEEP_PARTIAL_NO_RETRY',
        error=error,elapsed_before_receipt_seconds=elapsed(),request_sha256=request_sha,reserved_solver_calls=2352,
        actual_solver_calls=None if result is None else result['actual_solver_calls'],artifacts=inventory,
        owned_cleanup_accepted=None if owned is None else owned['cleanup_accepted'],automatic_retry=False,
        graph_status=None if result is None else result['graph_status'],terminal_RC0_and_no_postbudget_failure_required=True,
        teacher_calls=0,neural_optimizer_steps=0,modal_spend_usd=0)
    write('method24_run01.json',receipt)
    run_sha = module.hash_file(PREP_REL+'/method24_run01.json')
    final_elapsed = elapsed()
    if final_elapsed > 120:
        write('method24_postbudget_failure01.json',dict(status='REJECTED_POST_RECEIPT_TIME',elapsed=elapsed(),prior_run_status_superseded=True))
        return 1
    print(json.dumps(dict(status=receipt['status'],elapsed_seconds=final_elapsed,error=error,run_sha256=run_sha),ensure_ascii=False))
    return 0 if error is None else 1


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare');prep.add_argument('--approval-reference',required=True)
    execute=commands.add_parser('run');execute.add_argument('--request-sha256',required=True)
    args=parser.parse_args(argv)
    module=worker_module()
    if args.command == 'prepare':
        print(json.dumps(prepare_request(module,args.approval_reference),ensure_ascii=False));return 0
    return run(module,args.request_sha256)


if __name__ == '__main__':
    raise SystemExit(main())
