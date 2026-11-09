"""ROOT-only outer60s/owned57s/worker54s cho native runtime CLI CPU."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'check_runtime_schema2_main177_01.py'
CHILD = PREP/'runtime-schema2-main177-01'
OUT = PREP/'runtime-schema2-main177-01-owned'
PACKET = PREP/'runtime_schema2_main177_01_packet.json'
PACKET_SHA = 'e4d97a562f4140bfe7b3dbba8bdefda4746ef93d718b6586fc995ac6a31206a9'
TARGET = ROOT/'artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json'


def need(ok, message):
    if not ok: raise ValueError(message)


def elapsed(): return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker-sha256',required=True)
    parser.add_argument('--controller-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    args = parser.parse_args()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import run_owned,safe,entry
    entry()
    need(args.approval_reference.strip() and sha(Path(__file__).resolve()) == args.controller_sha256
         and sha(WORKER) == args.worker_sha256 and sha(PACKET) == PACKET_SHA,'ROOT reviewed controller/worker/packet')
    need(not any(safe(path).exists() for path in (OUT,CHILD,TARGET)),'exclusive runtime attempt/output')
    packet = json.loads(PACKET.read_bytes())
    pins = packet['source_pins']
    need(all(sha(safe(ROOT/name)) == value for name,value in pins.items()),'native CLI/input prehash')
    need({key:value for key,value in os.environ.items() if key.startswith(('GIT_','GH_'))} == packet['git_environment'],
         'caller exact reviewed Git environment')
    before_environment = dict(os.environ)
    import psutil
    need(psutil.virtual_memory().available >= 2*1024**3,'fresh2GiB RAM admission before native library imports')
    allowance = min(57.,60.-elapsed()-1.)
    need(allowance > 55,'remaining worker/cleanup allowance')
    receipt = run_owned(WORKER,[],OUT,expected_worker_sha256=args.worker_sha256,
        approval_reference=args.approval_reference,max_seconds=allowance,cleanup_reserve_seconds=3,max_output_bytes=131072)
    write(OUT/'receipt.json',receipt)
    result, errors = None,[]
    try:
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['cleanup_errors'] == [],'native worker/owned cleanup')
        result = json.loads((CHILD/'result.json').read_bytes())
        need(result['status'] == 'NATIVE_SCHEMA2_RUNTIME_PENDING_OUTER' and result['accepted'] is True
             and result['errors'] == result['forbidden'] == [] and not any(result['counters'].values()),'actual zero model/fit/device bodies')
        need(result['source_before'] == result['source_after'] == pins and result['packet_sha256'] == PACKET_SHA,
             'actual native source prepost')
        need(all(result[key] is True for key in ('profiler_restored','argv_restored','path_restored','environment_restored',
             'temp_cache_restored','bytecode_setting_restored','monitor_stopped','global_pointer_unchanged','legacy_runtime_unchanged')),
             'observers/environment/historical metadata restored')
        need(len(result['git_commands']) == 10 and len(result['platform_commands']) <= 3
             and len(result['availability_queries']) == 2 and all(row.get('returned') is True and row.get('value') is False
                 for row in result['availability_queries']),'actual bounded provenance/platform/availability calls')
        need(result['cpu_library_observation']['cuda_build'] is None
             and result['cpu_library_observation']['cuda_initialized'] is False,'actual CPU build/no CUDA initialization')
        resources = result['resources']
        need(resources['samples'] > 0 and resources['peak_rss_bytes'] <= 1024**3
             and resources['minimum_available_ram_bytes'] >= 2*1024**3 and result['elapsed_seconds'] < 54,'native runtime resource profile')
        report = json.loads(TARGET.read_bytes())
        proof = json.loads((PREP/'upstream_verify_process_eol03.json').read_bytes())
        need(report == result['report'] and sha(TARGET) == result['report_sha256']
             and report['source'] == proof['result'] and report['runtime_schema_version'] == 2
             and report['python'] == str(ROOT/'.venv/Scripts/python.exe')
             and report['python_prefix'] == str((ROOT/'.venv').resolve()) and report['project_root'] == str(ROOT.resolve())
             and report['device'] == 'cpu' and report['cuda_available'] is False
             and report['lock_sha256'] == pins['requirements-akt.lock.txt'],'genuine native runtime metadata')
        for name in ('torch','numpy'):
            need(Path(report[name+'_origin']).resolve().is_relative_to((ROOT/'.venv').resolve())
                 and report[name+'_origin'] == result['package_entries_before'][name]['path']
                 and sha(Path(report[name+'_origin'])) == result['package_entries_before'][name]['sha256'],'native package origin beforeafter')
        need(not any((CHILD/name).exists() for name in ('resource-failure.json','call-guard-failure.json','postwrite-rejection.json')),
             'late native failure absent')
        need(all(sha(OUT/name) == value for name,value in receipt['output_sha256'].items()),'raw stdout/stderr identities')
        need(all(sha(ROOT/name) == value for name,value in pins.items()) and sha(WORKER) == args.worker_sha256
             and sha(PACKET) == PACKET_SHA and dict(os.environ) == before_environment,'final source/environment bindings')
        memory = psutil.Process().memory_info()
        need(psutil.virtual_memory().available >= 2*1024**3
             and max(memory.rss,getattr(memory,'peak_wset',0)) <= 1024**3,'outer resource postcheck')
    except BaseException as error: errors.append(dict(type=type(error).__name__,message=str(error)))
    accepted = not errors and elapsed()<60
    write(OUT/'final.json',dict(status='ACCEPTED_NATIVE_SCHEMA2_CPU_RUNTIME_ONLY' if accepted else 'REJECTED_NATIVE_RUNTIME_ATTEMPT',
        accepted=accepted,errors=errors,worker_result=result,owned_receipt=receipt,source_pins=pins,
        worker_sha256=args.worker_sha256,controller_sha256=args.controller_sha256,packet_sha256=PACKET_SHA,
        runtime_report=str(TARGET),runtime_sha256=sha(TARGET) if TARGET.exists() else None,
        elapsed_seconds=elapsed(),whole_cap_seconds=60,owned_seconds=allowance,worker_cap_seconds=54,
        environment_unchanged=dict(os.environ)==before_environment,automatic_retry=False))
    if elapsed()>=60:
        write(OUT/'postwrite-rejection.json',dict(elapsed_seconds=elapsed())); accepted=False
    print(json.dumps(dict(accepted=accepted,elapsed_seconds=elapsed(),report_sha256=sha(TARGET) if TARGET.exists() else None)))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__': main()
