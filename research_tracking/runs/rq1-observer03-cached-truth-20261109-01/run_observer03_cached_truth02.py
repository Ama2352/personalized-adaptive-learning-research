"""ROOT-owned pure/cached dispatch, hai allocation độc lập8s và15s, không tự retry."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import types

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP / 'observer03_cached_truth02_packet.json'
START, WALL = time.perf_counter(), time.time()
FORBIDDEN = ('torch', 'numpy', 'pandas', 'knowledge_tracing', 'sklearn', 'scipy')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'Physical repository path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'No aliases')
    return path


def read(path, cap=1024**2):
    physical(path)
    need(path.is_file() and path.stat().st_size <= cap, 'Bounded regular input')
    raw = path.read_bytes()
    need(len(raw) <= cap and len(raw) == path.stat().st_size, 'Stable bounded input')
    return raw


def sha(path):
    return hashlib.sha256(read(path)).hexdigest()


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    need(len(raw) <= 1024**2, 'Output cap1MiB')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    need(path.read_bytes() == raw, 'Actual persisted output readback')


class Status(ctypes.Structure):
    _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD),
        *[(name, ctypes.c_ulonglong) for name in ('total_phys', 'available', 'total_page', 'available_page',
          'total_virtual', 'available_virtual', 'available_extended')]]
class Counters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD),
        *[(name, ctypes.c_size_t) for name in ('peak', 'working', 'peak_paged', 'paged',
          'peak_nonpaged', 'nonpaged', 'pagefile', 'peak_pagefile')]]
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)
kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(Status)]
kernel.GlobalMemoryStatusEx.restype = wintypes.BOOL
kernel.GetCurrentProcess.restype = wintypes.HANDLE
psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL


def memory():
    status, process = Status(), Counters()
    status.length = ctypes.sizeof(status)
    process.cb = ctypes.sizeof(process)
    need(kernel.GlobalMemoryStatusEx(ctypes.byref(status))
         and psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(process), ctypes.sizeof(process)),
         'Actual Windows worker RSS/free memory API')
    return dict(available_bytes=int(status.available), worker_highwater_bytes=max(int(process.peak), int(process.working)))


def load(raw, name, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def worker(args, packet):
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    config = packet['phases'][args.phase]
    output = physical(PREP/config['child'])
    need(not output.exists(), 'Exclusive child output')
    output.mkdir()
    cold = {name: not any(k == name or k.startswith(name+'.') for k in sys.modules) for name in FORBIDDEN}
    need(all(cold.values()), 'Cold stdlib-only child')
    forbidden = []
    def audit(event, values):
        if event == 'import' and str(values[0]).split('.')[0] in FORBIDDEN:
            forbidden.append(event+':'+str(values[0]));raise RuntimeError('No model/scientific imports')
        if event == 'subprocess.Popen' or event == 'os.system' or event.startswith(('os.spawn', 'socket.')):
            forbidden.append(event);raise RuntimeError('No child/network operations')
        if event == 'open' and values and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.path.abspath(os.fsdecode(values[0])))
            for relative in ('dataset', 'artifacts/bkt_baseline', 'artifacts/simulator/corpora', 'venv', '.wsl', 'experiments'):
                if path == ROOT/relative or path.is_relative_to(ROOT/relative):
                    forbidden.append('protected read');raise RuntimeError('No protected corpus/weights')
            if args.phase == 'pure' and path.is_relative_to(ROOT/'research_tracking/runs'):
                forbidden.append('pure data read');raise RuntimeError('Pure fixtures never open research rows')
            mode, flags = values[1] or '', values[2] if type(values[2]) is int else 0
            if any(c in mode for c in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR):
                need(path.is_relative_to(output) or os.fsdecode(values[0]) == os.devnull, 'Only child output writes')
    sys.addaudithook(audit)
    stop = threading.Event();monitor_errors = []
    resources = dict(samples=0, peak_worker_rss_bytes=0, minimum_available_ram_bytes=None)
    def guard():
        need(elapsed() < config['worker_seconds'], 'Same worker clock including startup/finalization')
        sample = memory()
        resources['samples'] += 1
        resources['peak_worker_rss_bytes'] = max(resources['peak_worker_rss_bytes'], sample['worker_highwater_bytes'])
        old = resources['minimum_available_ram_bytes']
        resources['minimum_available_ram_bytes'] = sample['available_bytes'] if old is None else min(old, sample['available_bytes'])
        need(sample['worker_highwater_bytes'] <= 256*1024**2 and sample['available_bytes'] >= 512*1024**2,
             'Worker256MiB/free512MiB')
    timer = threading.Timer(max(.001, config['worker_seconds']-elapsed()), lambda: os._exit(124))
    timer.daemon = True;timer.start()
    def watch():
        while not stop.wait(.1):
            try:
                guard()
            except BaseException as exc:
                monitor_errors.append(str(exc))
                try:
                    write(output/'resource-failure.json', dict(error=str(exc), resources=resources))
                finally:
                    os._exit(125)
    monitor = threading.Thread(target=watch, daemon=True)
    error = None;counts = None;before = {};after = {};artifacts = {}
    expected = dict(packet['source_pins'])
    if args.phase == 'cached':
        expected.update({name: row['sha256'] for name, row in packet['inputs'].items()})
    try:
        guard();monitor.start()
        before = {name: sha(ROOT/name) for name in expected}
        need(before == expected and sha(PACKET) == args.packet_sha256, 'Reviewed source/input bytes')
        module = load(read(ROOT/packet['analyzer']), 'analyze_observer03_cached_truth01', ROOT/packet['analyzer'])
        if args.phase == 'pure':
            import unittest
            tests = load(read(ROOT/packet['tests']), 'observer03_truth_tests01', ROOT/packet['tests'])
            suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
            ids = []
            def flatten(value):
                for item in value:
                    if isinstance(item, unittest.TestSuite):
                        flatten(item)
                    else:
                        ids.append(item.id())
            flatten(suite)
            need(ids == packet['expected_test_ids'] and len(ids) == len(set(ids)) == 8, 'Exactly8 fixture IDs')
            with (output/'unittest.log').open('x', encoding='utf-8') as stream:
                result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
                stream.flush();os.fsync(stream.fileno())
            counts = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
            need(counts == dict(tests=8, failures=0, errors=0, skipped=0) and result.wasSuccessful()
                 and result.expectedFailures == result.unexpectedSuccesses == [], 'All8 fixtures passed')
        else:
            def checked_read(path):
                guard()
                relative = path.relative_to(ROOT).as_posix()
                need(relative in packet['inputs'], 'Exact cached input allowlist')
                raw = read(path, packet['inputs'][relative]['bytes'])
                need(len(raw) == packet['inputs'][relative]['bytes']
                     and hashlib.sha256(raw).hexdigest() == packet['inputs'][relative]['sha256'], 'Pinned bytes before parse')
                return raw
            joined, summary, validation = module.analyze_files(ROOT, packet, checked_read, guard)
            need(validation['joined_rows'] == validation['unique_keys'] == len(joined) == 120, 'Whole120 admission')
            for name, data in (('joined120.json', joined), ('summary.json', summary), ('validation.json', validation)):
                guard();write(output/name, data)
            counts = dict(joined_rows=120, cache_rows=14400, cache_histories=120)
        guard()
        after = {name: sha(ROOT/name) for name in expected}
        need(after == before and not forbidden and sha(PACKET) == args.packet_sha256, 'Source/input postcheck')
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc))
    finally:
        stop.set()
        if monitor.ident is not None:
            monitor.join(timeout=.25)
        try:
            guard()
        except BaseException as exc:
            error = error or dict(type=type(exc).__name__, message=str(exc))
        timer.cancel()
    need(not monitor.is_alive(), 'Monitor stopped')
    for path in output.iterdir():
        if path.is_file():
            artifacts[path.name] = dict(sha256=sha(path), bytes=path.stat().st_size)
    accepted = error is None and not monitor_errors and not forbidden and after == expected
    write(output/'result.json', dict(status='INNER_COMPLETE_PENDING_ROOT_OUTER' if accepted else 'REJECTED_KEEP_ALL',
        phase=args.phase, counts=counts, error=error, forbidden=forbidden, monitor_errors=monitor_errors,
        monitor_stopped=not monitor.is_alive(), resources=resources, source_input_before=before, source_input_after=after,
        packet_sha256=args.packet_sha256, owner=owner, cold=cold, artifacts=artifacts,
        elapsed_seconds=elapsed(), worker_cap_seconds=config['worker_seconds'], model_calls=0, world_calls=0,
        scientific_RNG_draws=0, new_independent_N=0))
    if elapsed() >= config['worker_seconds']:
        write(output/'postwrite_rejection.json', dict(elapsed_seconds=elapsed()));accepted=False
    raise SystemExit(0 if accepted else 1)


def outer(args, packet):
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import entry, run_owned
    entry()
    config = packet['phases'][args.phase]
    owned, child = physical(PREP/config['owned']), physical(PREP/config['child'])
    need(not owned.exists() and not child.exists(), 'Fresh namespaces, no automatic retry')
    expected = dict(packet['source_pins'])
    if args.phase == 'cached':
        expected.update({name: row['sha256'] for name, row in packet['inputs'].items()})
        pure = json.loads(read(PREP/packet['phases']['pure']['owned']/'final.json'))
        need(pure['status'] == 'ACCEPTED_OBSERVER03_PURE8' and pure['counts'] == dict(tests=8, failures=0, errors=0, skipped=0)
             and pure['packet_sha256'] == args.packet_sha256 and pure['source_input_before'] == pure['source_input_after'] == packet['source_pins'],
             'Actual same-source pure8 before cached operation')
        need(pure['receipt']['accepted'] is True and pure['receipt']['cleanup_accepted'] is True
             and pure['receipt']['job_active_after_cleanup'] == 0
             and not (PREP/packet['phases']['pure']['owned']/'postwrite_rejection.json').exists(),
             'Pure actual owned cleanup and no late rejection')
    before = {name: sha(ROOT/name) for name in expected}
    need(before == expected, 'Reviewed source/input pins before launch')
    available = memory()['available_bytes']
    if available < 1024**3:
        owned.mkdir();write(owned/'final.json', dict(status='NO_GO_RAM_NO_CHILD', available_bytes=available,
            required_bytes=1024**3, counts=None, automatic_retry=False, packet_sha256=args.packet_sha256))
        raise SystemExit(1)
    allowance = min(config['owned_seconds'], config['whole_seconds']-elapsed()-config['final_reserve_seconds'])
    need(allowance > config['cleanup_seconds'], 'Final/cleanup reserves remain')
    receipt = run_owned(Path(__file__), ['--worker', '--phase', args.phase, '--packet-sha256', args.packet_sha256], owned,
        expected_worker_sha256=packet['source_pins'][Path(__file__).relative_to(ROOT).as_posix()],
        approval_reference='ROOT_REVIEW_REQUIRED_OBSERVER03_'+args.phase.upper()+'_STDLIB_NO_NEW_GAM',
        max_seconds=allowance, cleanup_reserve_seconds=config['cleanup_seconds'], max_output_bytes=32768)
    if not owned.exists():
        owned.mkdir()
    write(owned/'receipt.json', receipt)
    errors = [];result = None;artifacts = {};after = {}
    try:
        if (child/'result.json').exists():
            result = json.loads(read(child/'result.json'))
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['errors'] == receipt['cleanup_errors'] == [], 'Genuine owned cleanup')
        need(result is not None and result['status'] == 'INNER_COMPLETE_PENDING_ROOT_OUTER' and result['error'] is None
             and result['forbidden'] == result['monitor_errors'] == [] and result['monitor_stopped'] is True
             and all(result['cold'].values()) and result['source_input_before'] == result['source_input_after'] == expected,
             'Actual child acceptance and full source/input postcheck')
        wanted = {'unittest.log', 'result.json'} if args.phase == 'pure' else {'joined120.json', 'summary.json', 'validation.json', 'result.json'}
        need({p.name for p in child.iterdir()} == wanted, 'Exact output files, no late failure')
        for path in child.iterdir():
            artifacts[path.name] = dict(sha256=sha(path), bytes=path.stat().st_size)
        need(sum(row['bytes'] for row in artifacts.values()) <= 896*1024
             and result['artifacts'] == {n: r for n, r in artifacts.items() if n != 'result.json'}, 'Actual output readback/SHA/quota')
        resource = result['resources']
        need(resource['samples'] > 0 and resource['peak_worker_rss_bytes'] <= 256*1024**2
             and resource['minimum_available_ram_bytes'] >= 512*1024**2
             and result['elapsed_seconds'] < config['worker_seconds'], 'Actual worker resource/clock verdict')
        if args.phase == 'cached':
            rows = json.loads(read(child/'joined120.json'));summary = json.loads(read(child/'summary.json'))
            validation = json.loads(read(child/'validation.json'))
            need(len(rows) == validation['joined_rows'] == validation['unique_keys'] == 120
                 and validation['cache_rows'] == 14400 and validation['cache_histories'] == 120
                 and validation['ON_used_once'] is True and validation['OFF_integrity_only'] is True
                 and [r['step'] for r in rows] == list(range(120)), 'Full populations and chronology')
            need(set(summary['native_M_by_latent']) == set(summary['theta_gate_by_latent']) == {'00', '01', '10', '11'}
                 and sum(summary['native_M_by_latent'].values()) == sum(summary['theta_gate_by_latent'].values()) == 120,
                 'All zero-inclusive two-by-two cells')
    except BaseException as exc:
        errors.append(dict(type=type(exc).__name__, message=str(exc)))
    after = {name: sha(ROOT/name) for name in expected}
    owned_bytes = sum(path.stat().st_size for path in owned.iterdir() if path.is_file())
    if owned_bytes > 64*1024:
        errors.append(dict(type='OutputQuota', message='Owned pre-final receipts/logs exceed64KiB'))
    accepted = not errors and after == before and sha(PACKET) == args.packet_sha256 and elapsed() < config['whole_seconds']
    status = ('ACCEPTED_OBSERVER03_PURE8' if args.phase == 'pure' else 'ACCEPTED_OBSERVER03_CACHED120_LATENT_WITNESS') if accepted else 'REJECTED_KEEP_ALL'
    final = dict(status=status, errors=errors, counts=None if result is None else result['counts'],
        receipt=receipt, artifacts=artifacts, source_input_before=before, source_input_after=after,
        packet_sha256=args.packet_sha256, elapsed_seconds=elapsed(), cap_seconds=config['whole_seconds'],
        automatic_retry=False, actual_model_calls=0, actual_world_calls=0, new_independent_N=0)
    need(len((json.dumps(final, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()) <= 64*1024,
         'Final receipt64KiB reserved inside total1MiB')
    write(owned/'final.json', final)
    if elapsed() >= config['whole_seconds']:
        write(owned/'postwrite_rejection.json', dict(elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(accepted=accepted, elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--phase', choices=('pure', 'cached'), required=True)
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT/'.venv' and Path.cwd().resolve() == ROOT,
         'Exact repository .venv, cwd and -B')
    need(sha(PACKET) == args.packet_sha256, 'Externally reviewed packet SHA')
    packet = json.loads(read(PACKET))
    worker(args, packet) if args.worker else outer(args, packet)
