"""Native Windows CPU Gate worker; ROOT dispatch only, existing owned GO first."""
import time
START = time.perf_counter()
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate, safe, bounded
GIB = 1024**3


def need(ok, reason):
    if not ok: raise ValueError(reason)


def sha(path):
    with safe(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with safe(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def reference(descriptor, cap=8*1024**2):
    need(type(descriptor) is dict and set(descriptor) == {'path','sha256'}, 'closed reference')
    name = descriptor['path']
    need(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts, 'relative reference')
    path = safe(ROOT/name)
    need(path.is_relative_to(ROOT/'artifacts/akt') or path.is_relative_to(ROOT/'research_tracking/runs'), 'evidence-only reference')
    raw = bounded(path, cap)
    need(hashlib.sha256(raw).hexdigest() == descriptor['sha256'], 'referenced exact bytes')
    return path, json.loads(raw)


def load_collection(packet_path, packet_sha):
    raw = bounded(packet_path, 2*1024**2)
    need(hashlib.sha256(raw).hexdigest() == packet_sha, 'external ROOT packet SHA')
    packet = json.loads(raw)
    need(type(packet.get('schema_version')) is int and packet['schema_version'] == 1
         and packet.get('kind') == 'ACCEPTED_CURRENT_COLLECTION'
         and type(packet.get('root_review_reference')) is str and packet['root_review_reference'].strip(), 'accepted ROOT review packet, not template')
    _, inputs = reference(packet['collection_input'])
    final_path, final = reference(packet['collection_result'])
    need(final['status'] == 'ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS' and final['gate_pass'] is False
         and final['errors'] == [] and final['environment_restored'] is True
         and final['packet_sha256'] == packet['collection_input']['sha256'], 'actual accepted collection required')
    build = inputs['gate_build_hashes']
    need(type(build) is dict and len(build) == 154 and len(inputs['test_module_sha256']) == 69,
         'this ROOT-frozen154source/69module recipe only')
    need(final['source_before'] == final['source_after'] and final['source_before']['gate_build_hashes'] == build
         and final['root_freeze_reference'] == inputs['root_freeze_reference'], 'collection source freeze')
    groups = inputs['module_groups']
    need([g['name'] for g in groups] == ['stdlib','no-torch','remaining']
         and len(final['stages']) == 3, 'canonical three fresh groups')
    nodes = {}
    for group, stage in zip(groups, final['stages']):
        need(stage['group'] == group['name'], 'collection group order')
        path, result = reference(dict(path=stage['child_result_relative'], sha256=stage['child_result_sha256']))
        receipt = stage['owned_receipt']
        need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['returncode'] == 0, 'collection owned cleanup')
        need(result['status'] == 'COLLECTED_ONLY_PENDING_OUTER' and result['modules'] == group['modules']
             and result['pytest_exit_code'] == 0 and result['collection_reports'] == result['failures'] == result['forbidden_attempts'] == []
             and not any(result['zero_body_counters'].values())
             and result['source_before'] == result['source_after'] == build
             and result['packet_sha256'] == packet['collection_input']['sha256'], 'exact actual collection shard')
        need(result['nodeids'] and len(result['nodeids']) == len(set(result['nodeids'])) == result['collected_count']
             and {n.split('::',1)[0] for n in result['nodeids']} == set(group['modules']), 'exact node inventory')
        nodes[group['name']] = result['nodeids']
    flattened = [node for group in groups for node in nodes[group['name']]]
    need(flattened == final['nodeids'] and len(flattened) == len(set(flattened)) == final['collected_count'], 'actual collection union, not passing count')
    _, runtime = reference(packet['runtime_report'])
    return packet, inputs, nodes, runtime


def native_module():
    spec = importlib.util.spec_from_file_location('current_gate_native_refresh', ROOT/'scripts/akt/refresh_gate2.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def current_source(inputs, native):
    need(native.gate2_build_hashes() == inputs['gate_build_hashes'], 'actual canonical source hashes/population drift')
    need([dict(name=n,modules=m) for n,m in native.test_partition(ROOT)] == inputs['module_groups'], 'canonical partition drift')
    need(all(sha(ROOT/name) == digest for name,digest in inputs['test_module_sha256'].items()), 'test module byte drift')
    need(inputs['lock_file'] == 'requirements-akt.lock.txt' and sha(ROOT/inputs['lock_file']) == inputs['lock_sha256'], 'Windows lock')
    need(set(inputs['upstream_file_sha256']) == {'akt.py','load_data.py','LICENSE','README.md'}
         and all(sha(ROOT/'artifacts/akt/dependencies/upstream'/name) == digest for name,digest in inputs['upstream_file_sha256'].items()), 'upstream4 bytes')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True); parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    owner = worker_gate()  # Existing helper/actual-worker membership, before native imports.
    import psutil
    need(psutil.virtual_memory().available >= 4*GIB, 'fresh4GiB admission before native Gate')
    out = PREP/(args.run_id+'-child'); safe(out).mkdir(exist_ok=False)
    packet_path = safe(Path(args.packet))
    packet, inputs, nodes, _ = load_collection(packet_path, args.packet_sha256)
    native = native_module(); current_source(inputs, native)
    need('torch' not in sys.modules, 'Gate launcher remains lightweight before pytest')
    resources = dict(samples=0, observed_minimum_available_ram_bytes=None, workers={})
    stop = threading.Event()
    own = psutil.Process(); born = own.create_time()
    def sample():
        available = int(psutil.virtual_memory().available)
        previous = resources['observed_minimum_available_ram_bytes']
        resources['observed_minimum_available_ram_bytes'] = available if previous is None else min(previous,available)
        need(available >= GIB, 'available RAM below1GiB')
        need(own.create_time() == born, 'owned worker PID reused')
        for candidate in [own,*own.children(recursive=True)]:
            try:
                created = candidate.create_time(); need(created >= born, 'descendant predates owned worker')
                memory = candidate.memory_info(); peak = max(memory.rss,getattr(memory,'peak_wset',0))
                need(peak <= 3*GIB, 'owned process peak above3GiB')
                key = str(candidate.pid)+':'+repr(created)
                prior = resources['workers'].get(key,{}).get('observed_peak_bytes',0)
                resources['workers'][key] = dict(pid=candidate.pid,created=created,observed_peak_bytes=max(prior,peak))
            except psutil.NoSuchProcess: pass
        files = [out/'native-launcher.log',
                 *(ROOT/'artifacts/akt/preflight').glob('gate2-*'+args.run_id+'*')]
        for path in files:
            if path.is_file():
                need(safe(path).stat().st_size <= 32*1024**2, 'native/log32MiB output cap')
        resources['samples'] += 1
    def watch():
        while not stop.wait(.1):
            try: sample()
            except BaseException as error:
                try: write(out/'resource-failure.json',dict(error=str(error),resources=resources))
                finally: os._exit(125)  # Original outer Job cleans all descendants.
    sample(); monitor = threading.Thread(target=watch, daemon=True); monitor.start()
    command = [sys.executable,'-B',str(ROOT/'scripts/akt/refresh_gate2.py'),'--run-id',args.run_id,
               '--timeout-seconds','580','--lock-file',str(ROOT/inputs['lock_file'])]
    rc, errors = None, []
    try:
        # NO --publish-current. Native still runs exactly three fresh pytest groups.
        with (out/'native-launcher.log').open('xb') as stream:
            result = subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=585)
        rc = result.returncode
        need(rc == 0, 'native CLI failure; preserve all logs')
        current_source(inputs,native)
        need(sha(packet_path) == args.packet_sha256, 'ROOT collection packet drift')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
    finally:
        stop.set(); monitor.join(timeout=.5)
        sample()
        write(out/'result.json',dict(status='NATIVE_RETURNED_PENDING_OUTER' if not errors else 'REJECTED_NATIVE_GATE',
            native_command=command,native_returncode=rc,owner=owner,resources=resources,
            monitor_stopped=not monitor.is_alive(),errors=errors,packet_sha256=args.packet_sha256,
            elapsed_seconds=time.perf_counter()-START,expected_node_counts={k:len(v) for k,v in nodes.items()},
            limits=dict(native_seconds=580,owned_max_seconds=600,owned_cleanup_seconds=3,outer_seconds=630),
            scope_vi='Full synthetic software Gate only if outer validates exact JUnit IDs/source/resources/Job0; no research/GPU proof.'))
    raise SystemExit(0 if not errors and not monitor.is_alive() else 1)


if __name__ == '__main__': main()
