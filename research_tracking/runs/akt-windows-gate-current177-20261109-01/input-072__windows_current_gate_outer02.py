"""ROOT-only current Windows CPU Gate; no publication, no prior Gate admission.

Native580s/owned<=600s(including3s cleanup)/outer630s; immutable collection required.
"""
import time
START = time.perf_counter()
WALL = time.time()
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'windows_current_gate_worker02.py'
HELPER = ROOT/'scripts/research/windows_owned_worker.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
JUNIT = ROOT/'.venv/Lib/site-packages/_pytest/junitxml.py'
JUNIT_SHA = '557b8978c66b8010fafc50ada4bf56333f9927f31b2b5909fe4c1a9df1a3c0f0'
GIB = 1024**3


def need(ok, reason):
    if not ok: raise ValueError(reason)


def elapsed(): return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def load_worker(expected):
    need(sha(WORKER) == expected, 'reviewed worker SHA')
    spec = importlib.util.spec_from_file_location('current_gate_reviewed_worker',WORKER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def mapped_ids(expected, utility):
    names = []
    for nodeid in expected:
        parts = utility.mangle_test_address(nodeid)
        names.append(dict(classname='.'.join(parts[:-1]),name=utility.bin_xml_escape(parts[-1])))
    need(len(names) == len({(n['classname'],n['name']) for n in names}), 'collection nodeIDs collide under actual JUnit encoding')
    return names


def read_junit(path, expected, utility, pinned_ids):
    raw = bounded(path,32*1024**2)
    root = ET.fromstring(raw)
    actual = [(case.get('classname'),case.get('name')) for case in root.iter('testcase')]
    mapped = mapped_ids(expected,utility)
    need(mapped == pinned_ids, 'external collection JUnit mapping drift')
    names = [(v['classname'],v['name']) for v in mapped]
    need(len(actual) == len(set(actual)) and Counter(actual) == Counter(names), 'executed JUnit identity population differs from collection')
    counts = {key:sum(int(s.get(key,'0')) for s in root.iter('testsuite'))
              for key in ('tests','failures','errors','skipped')}
    need(counts == dict(tests=len(expected),failures=0,errors=0,skipped=0)
         and not any(list(root.iter(tag)) for tag in ('failure','error','skipped')), 'complete no-FES actual JUnit')
    return dict(sha256=hashlib.sha256(raw).hexdigest(),counts=counts,identities=actual)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet',required=True); parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--worker-sha256',required=True); parser.add_argument('--outer-sha256',required=True)
    parser.add_argument('--run-id',required=True); parser.add_argument('--approval-reference',required=True)
    args = parser.parse_args()
    need(re.fullmatch(r'win-current-gate-[A-Za-z0-9_-]{1,42}',args.run_id) is not None and args.approval_reference.strip(), 'exclusive reviewed run ID')
    need(sha(Path(__file__)) == args.outer_sha256 and sha(HELPER) == HELPER_SHA, 'outer/helper pins')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import entry,run_owned
    global safe,bounded
    from windows_owned_worker import safe,bounded
    entry()
    import psutil
    available = int(psutil.virtual_memory().available)
    need(available >= 4*GIB and 'torch' not in sys.modules, 'fresh4GiB admission before Torch')
    worker = load_worker(args.worker_sha256)
    packet_path = safe(Path(args.packet))
    packet,inputs,nodes,_ = worker.load_collection(packet_path,args.packet_sha256)
    # A ROOT-reviewed external packet must pin these additional, non-Gate-map sources.
    controller_pins = packet['controller_source_pins']
    required = {WORKER.relative_to(ROOT).as_posix():args.worker_sha256,
                Path(__file__).resolve().relative_to(ROOT).as_posix():args.outer_sha256,
                HELPER.relative_to(ROOT).as_posix():HELPER_SHA,JUNIT.relative_to(ROOT).as_posix():JUNIT_SHA}
    need(controller_pins == required and all(worker.sha(ROOT/name) == digest for name,digest in required.items()), 'exact controller/runtime-mapping sources')
    from _pytest import junitxml as utility
    import pytest
    need(Path(utility.__file__).resolve() == JUNIT.resolve() and Path(pytest.__file__).resolve().is_relative_to((ROOT/'.venv').resolve())
         and 'torch' not in sys.modules, 'lightweight isolated installed pytest mapping')
    total_nodes = [n for group in inputs['module_groups'] for n in nodes[group['name']]]
    expected_mapping = {name:mapped_ids(group_nodes,utility) for name,group_nodes in nodes.items()}
    expected_mapping['merged'] = mapped_ids(total_nodes,utility)
    need(packet['expected_JUnit_ids'] == expected_mapping
         and packet['expected_native_counts'] == {name:len(ids) for name,ids in expected_mapping.items()},
         'ROOT-pinned collection identities/counts required BEFORE native tests')
    native = worker.native_module(); worker.current_source(inputs,native)
    from knowledge_tracing.akt.authorization import preflight
    from knowledge_tracing.akt.config import AKTConfig
    need('torch' not in sys.modules, 'preflight must remain lightweight')
    directory = ROOT/'artifacts/akt/preflight'
    run = args.run_id
    report_path = directory/f'gate2-evidence-{run}.json'
    log_path = directory/f'gate2-tests-{run}.log'
    xml_path = directory/f'gate2-tests-{run}.xml'
    output_paths = [report_path,log_path,xml_path]
    for group in inputs['module_groups']:
        output_paths.extend(directory/f'gate2-tests-{run}-{group["name"]}.{suffix}' for suffix in ('log','xml'))
    out,child = safe(PREP/(run+'-outer')),safe(PREP/(run+'-child'))
    need(not out.exists() and not child.exists() and not any(safe(p).exists() for p in output_paths), 'exclusive attempt/native artifacts; no retry/overwrite')
    out.mkdir(exist_ok=False)
    pointer = safe(directory/'gate2-current.json')
    old_pointer = bounded(pointer,128*1024) if pointer.exists() else None
    if old_pointer is not None:
        with (out/'pointer-before.bytes').open('xb') as stream: stream.write(old_pointer)
    environment_before = dict(os.environ)
    errors,receipt,result,report,readiness = [],None,None,None,None
    verified_xml = {}
    try:
        for key in list(os.environ):
            if key.startswith('PYTEST_') or key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP','PYTHONINSPECT'):
                os.environ.pop(key,None)
        os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='',
            CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
            OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        count = int(os.environ.get('GIT_CONFIG_COUNT','0')); need(0 <= count < 32, 'bounded local Git environment')
        os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'
        os.environ[f'GIT_CONFIG_VALUE_{count}'] = (ROOT/'artifacts/akt/dependencies/upstream').as_posix()
        os.environ['GIT_CONFIG_COUNT'] = str(count+1)
        runtime_path,_ = worker.reference(packet['runtime_report'])
        readiness = preflight(AKTConfig(),project_root=ROOT,runtime_report_path=runtime_path,lock_file=ROOT/inputs['lock_file'])
        write(out/'preflight.json',readiness)
        need(psutil.virtual_memory().available >= 4*GIB, 'fresh4GiB launch admission')
        # Existing helper has an honest tighter600s ceiling. Overall active
        # cutoff stays at most615; reserve at least15s final outer processing.
        owned_seconds = min(600.,615.-elapsed())
        need(owned_seconds >= 590, 'setup left insufficient reviewed native580/cleanup allowance')
        receipt = run_owned(WORKER,['--packet',str(packet_path),'--packet-sha256',args.packet_sha256,'--run-id',run],
            out/'owned',expected_worker_sha256=args.worker_sha256,approval_reference=args.approval_reference,
            max_seconds=owned_seconds,cleanup_reserve_seconds=3,max_output_bytes=65536)
        write(out/'owned-receipt.json',receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['actual_worker_in_job_before_GO'] is True
             and receipt['cleanup_errors'] == [] and receipt['popen_handle_closed'] is True, 'owned worker/Job cleanup')
        result = json.loads(bounded(child/'result.json',4*1024**2))
        need(result['status'] == 'NATIVE_RETURNED_PENDING_OUTER' and result['native_returncode'] == 0
             and result['packet_sha256'] == args.packet_sha256 and result['errors'] == []
             and result['temporary_environment_and_cache_restored'] is True
             and result['monitor_stopped'] is True and not (child/'resource-failure.json').exists(), 'actual worker outcome')
        resources = result['resources']
        need(resources['samples'] > 0 and resources['observed_minimum_available_ram_bytes'] >= GIB
             and all(v['observed_peak_bytes'] <= 3*GIB for v in resources['workers'].values()), 'observed RAM guards')
        report = json.loads(bounded(report_path,8*1024**2))
        need(report['schema_version'] == 1 and report['status'] == 'PASS'
             and report['test_result'] == dict(passed=len(total_nodes),failed=0,errors=0,skipped=0)
             and report['suite'] == 'tests/akt tests/shared_kt'
             and report['build_hashes'] == inputs['gate_build_hashes']
             and report['test_module_sha256'] == inputs['test_module_sha256']
             and report['source'] == readiness['source'] and report['source_commit'] == AKTConfig().source_commit
             and report['lock_sha256'] == inputs['lock_sha256'] and report['lock_file'] == str(ROOT/inputs['lock_file'])
             and report['python'] == str(ROOT/'.venv/Scripts/python.exe'), 'new independent native report identity')
        need(type(report['elapsed_seconds']) in (int,float) and math.isfinite(report['elapsed_seconds'])
             and 0 <= report['elapsed_seconds'] <= 580 and report['timeout_seconds'] == 580, 'actual native580s budget')
        need(sha(JUNIT) == JUNIT_SHA, 'installed JUnit mapper source pin')
        need(len(report['process_groups']) == 3, 'exact three executed native groups')
        for group,actual in zip(inputs['module_groups'],report['process_groups']):
            name = group['name']
            group_xml = directory/f'gate2-tests-{run}-{name}.xml'
            group_log = directory/f'gate2-tests-{run}-{name}.log'
            need(actual['name'] == name and actual['modules'] == group['modules'] and actual['returncode'] == 0
                 and actual['junit_path'] == str(group_xml) and actual['log_path'] == str(group_log), 'executed canonical group')
            verified_xml[name] = read_junit(group_xml,nodes[name],utility,expected_mapping[name])
            need(actual['junit_sha256'] == verified_xml[name]['sha256'] and actual['log_sha256'] == sha(group_log), 'native group hashes')
        verified_xml['merged'] = read_junit(xml_path,total_nodes,utility,expected_mapping['merged'])
        need(report['junit_sha256'] == verified_xml['merged']['sha256'] and report['test_log_sha256'] == sha(log_path), 'native merged hashes')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
    finally:
        os.environ.clear(); os.environ.update(environment_before)
    try:
        worker.current_source(inputs,native)
        worker.load_collection(packet_path,args.packet_sha256)
        need(all(worker.sha(ROOT/name) == digest for name,digest in required.items()), 'posthash controller/runtime drift')
        now_pointer = bounded(pointer,128*1024) if pointer.exists() else None
        if now_pointer is not None:
            with (out/'pointer-after.bytes').open('xb') as stream: stream.write(now_pointer)
        need(now_pointer == old_pointer, 'unexpected pointer change; preserved, never automatically rewritten')
        need(dict(os.environ) == environment_before, 'environment restoration')
        need(psutil.virtual_memory().available >= GIB, 'final1GiB RAM floor')
        memory = psutil.Process().memory_info()
        need(max(memory.rss,getattr(memory,'peak_wset',0)) <= 3*GIB, 'outer3GiB process bound')
    except BaseException as error:
        errors.append(dict(stage='final_inputs_pointer_resources',type=type(error).__name__,message=str(error)))
    outputs = {p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in output_paths if p.exists()}
    accepted = not errors and elapsed() < 630
    final = dict(status='ACCEPTED_WINDOWS_CPU_SOFTWARE_GATE_ONLY' if accepted else 'REJECTED_WINDOWS_CPU_GATE',
        run_id=run,run_accepted=accepted,elapsed_seconds=elapsed(),limits=dict(native=580,owned_max=600,owned_cleanup=3,outer=630,active_max=615),
        external_collection_packet_sha256=args.packet_sha256,controller_source_pins=required,errors=errors,
        readiness=readiness,worker_result=result,owned_receipt=receipt,verified_JUnit=verified_xml,outputs=outputs,
        pointer_before_sha256=None if old_pointer is None else hashlib.sha256(old_pointer).hexdigest(),
        pointer_changed=False if not any(e.get('stage') == 'final_inputs_pointer_resources' for e in errors) else None,
        publication_requested=False,pointer_manually_rewritten=False,automatic_retry=False,
        scope_vi='Actual synthetic software suite only. NativePASS alone insufficient; require exact acceptedcollection/JUnit IDs, sources, runtime, resources, ownedJob0 and outertime. No research/GPU claim.')
    write(out/'result.json',final)
    if elapsed() >= 630:
        write(out/'postwrite-rejection.json',dict(status='REJECTED_OUTER_POSTWRITE_BUDGET',elapsed_seconds=elapsed())); accepted=False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_WINDOWS_CPU_GATE',result=str(out/'result.json'),elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__': main()
