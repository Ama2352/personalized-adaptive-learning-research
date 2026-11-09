"""ROOT-only pure9 contract check; no actual request/corpus/native collection."""
import argparse
import functools
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import threading
import time
import unittest

START, WALL = time.perf_counter(), time.time()
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
PACKET = PREP/'main_engineering10x84_pure01_packet.json'
OUT = PREP/'main-engineering10x84-pure01'
OWNED = PREP/'main-engineering10x84-pure01-owned'
HELPER = ROOT/'scripts/research/windows_owned_worker.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
CALLS = dict(validate_contract=dict(attempted=20, returned=1, raised=19),
             failure_accounting=dict(attempted=7, returned=2, raised=5))
FORBIDDEN = {'numpy', 'pandas', 'torch', 'scipy', 'sklearn', 'networkx', 'duckdb',
             'knowledge_tracing', 'pyBKT', 'joblib', 'modal', 'boto3'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def allocation(pin):
    need(sha(PACKET) == pin, 'external ROOT packet SHA')
    value = json.loads(PACKET.read_bytes())
    need(value['expected_methods'] == 9 and value['expected_subtests'] == 21
         and value['expected_calls'] == CALLS and value['limits'] == dict(whole_seconds=30,
             owned_seconds=18, worker_seconds=15, cleanup_reserve_seconds=3,
             max_rss_bytes=1024**3, min_available_ram_bytes=2*1024**3), 'fixed pure9 workload/caps')
    need(all(sha(ROOT/name) == digest for name, digest in value['source_sha256'].items()), 'frozen source inputs')
    need(all(sha(ROOT/name) == digest for name, digest in value['runtime_sha256'].items()), 'pinned runtime entries')
    return value


def worker(args, owner):
    packet = allocation(args.packet_sha256)
    need(not any(name.split('.')[0] in FORBIDDEN for name in sys.modules), 'cold stdlib worker')
    denied, commands = [], []
    phase = ['windows_metadata']
    cmd = os.path.normcase(os.path.abspath(str(Path(os.environ['SystemRoot'])/'System32/cmd.exe'))).casefold()
    protected = tuple(ROOT/name for name in ('dataset', 'paper1', 'paper2', 'research_tracking',
                                              'experiments', 'venv', '.wsl', 'artifacts/simulator'))
    def audit(event, values):
        if event == 'subprocess.Popen':
            if (phase[0] == 'windows_metadata' and len(commands) < 3 and type(values[0]) is str
                    and type(values[1]) is str and os.path.normcase(os.path.abspath(values[0])).casefold() == cmd
                    and values[1].strip().casefold() in {cmd+' /c "ver"', '"'+cmd+'" /c "ver"'}):
                commands.append(dict(executable=values[0], command=values[1])); return
            denied.append(event); raise RuntimeError('only bounded literal Windows metadata process')
        if event.startswith('socket.') and not (phase[0] == 'windows_metadata' and event == 'socket.gethostname'):
            denied.append(event); raise RuntimeError('no network')
        if event == 'os.system' or event.startswith(('os.spawn', 'os.posix_spawn')):
            denied.append(event); raise RuntimeError('no undeclared process')
        if event == 'import' and str(values[0]).split('.')[0] in FORBIDDEN:
            denied.append('import:'+str(values[0])); raise RuntimeError('no scientific/native/model import')
        if event in ('open', 'os.listdir', 'os.scandir') and values and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.path.abspath(os.fsdecode(values[0])))
            if (any(path == parent or path.is_relative_to(parent) for parent in protected)
                    or path.suffix.lower() in ('.gz', '.csv', '.parquet', '.pt', '.ckpt', '.npy', '.npz', '.safetensors')):
                denied.append('actual_or_protected_data'); raise RuntimeError('pure manufactured metadata only')
    sys.addaudithook(audit)
    try:
        native_os = platform.uname()._asdict()
        need(native_os['system'] == 'Windows', 'actual Windows metadata')
        import psutil
    finally:
        phase[0] = 'pure_methods_no_process'
    process = psutil.Process()
    created = process.create_time()
    resources = dict(samples=0, peak_rss_bytes=0, minimum_available_ram_bytes=None)
    errors, resource_errors, originals, executed, subtests = [], [], [], [], []
    calls = {name: dict(attempted=0, returned=0, raised=0) for name in CALLS}
    stop = threading.Event()
    def sample():
        need(process.create_time() == created, 'same owned worker PID identity')
        info = process.memory_info(); free = int(psutil.virtual_memory().available)
        peak = max(info.rss, getattr(info, 'peak_wset', 0))
        resources['samples'] += 1; resources['peak_rss_bytes'] = max(resources['peak_rss_bytes'], peak)
        prior = resources['minimum_available_ram_bytes']
        resources['minimum_available_ram_bytes'] = free if prior is None else min(prior, free)
        need(peak <= 1024**3 and free >= 2*1024**3, 'RSS1GiB/free2GiB')
    def monitor():
        while not stop.wait(.1):
            try:
                sample()
            except BaseException as error:
                write(OUT/'resource-failure.json', dict(error=repr(error), resources=resources))
                os._exit(125)
    sample()
    watcher = threading.Thread(target=monitor, daemon=True); watcher.start()
    timer = threading.Timer(max(.001, 15-elapsed()), lambda: os._exit(124)); timer.daemon = True; timer.start()
    counts = None; analysis = None
    try:
        path = PREP/'test_main_engineering10x84_contract01.py'
        spec = importlib.util.spec_from_file_location('reviewed_engineering10x84_pure_tests', path)
        tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        analysis = tests.worker
        need(Path(tests.__file__).resolve() == path
             and Path(analysis.__file__).resolve() == PREP/'collect_main_engineering10x84_01.py', 'real pinned source/test origins')
        for name in CALLS:
            original = getattr(analysis, name)
            def observer(function, label):
                @functools.wraps(function)
                def counted(*a, **kw):
                    calls[label]['attempted'] += 1
                    need(calls[label]['attempted'] <= CALLS[label]['attempted'], 'finite helper call reservation')
                    try:
                        result = function(*a, **kw)
                    except BaseException:
                        calls[label]['raised'] += 1
                        raise
                    calls[label]['returned'] += 1
                    return result
                return counted
            originals.append((name, original)); setattr(analysis, name, observer(original, name))
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                executed.append(test.id().split('.')[-1]); super().startTest(test)
            def addSubTest(self, test, subtest, error):
                subtests.append(dict(method=test.id().split('.')[-1], parameters={k: str(v) for k, v in subtest.params.items()},
                                     error_type=None if error is None else error[0].__name__))
                super().addSubTest(test, subtest, error)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(tests.EngineeringContract)
        need(suite.countTestCases() == 9, 'nine actual methods before bodies')
        result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
        counts = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
                      expected_failures=len(result.expectedFailures), unexpected_successes=len(result.unexpectedSuccesses))
        need(result.wasSuccessful() and counts == dict(tests=9, failures=0, errors=0, skipped=0,
             expected_failures=0, unexpected_successes=0) and sorted(executed) == packet['expected_test_methods'], 'all9 exact methods/zeroFES')
        need(calls == CALLS and len(subtests) == 21 and all(row['error_type'] is None for row in subtests), 'actual helper/subtest counts')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    finally:
        for name, original in originals:
            setattr(analysis, name, original)
        restored = all(getattr(analysis, name) is original for name, original in originals)
        stop.set(); watcher.join(timeout=.5)
        try:
            sample()
        except BaseException as error:
            resource_errors.append(repr(error))
        heavy = sorted(name for name in sys.modules if name.split('.')[0] in FORBIDDEN)
        after = {name: sha(ROOT/name) for name in packet['source_sha256']}
        runtime_after = {name: sha(ROOT/name) for name in packet['runtime_sha256']}
        accepted = (not errors and not denied and not heavy and not resource_errors and restored and not watcher.is_alive()
                    and after == packet['source_sha256'] and runtime_after == packet['runtime_sha256'] and elapsed() < 15)
        write(OUT/'worker-result.json', dict(status='ACCEPTED_CONTRACT9_PENDING_OUTER' if accepted else 'REJECTED_CONTRACT9',
            counts=counts, calls=calls, executed_test_methods=executed, subtests=subtests, source_after=after,
            runtime_after=runtime_after, packet_sha256=args.packet_sha256, errors=errors, forbidden=denied,
            heavy_modules=heavy, resource_errors=resource_errors, resources=resources, methods_restored=restored,
            monitor_stopped=not watcher.is_alive(), metadata_commands=commands, native_os=native_os,
            elapsed_seconds=elapsed(), owner=owner,
            scope_vi='Pure9manufactured metadata; no actualrequest/teacher/corpus/model. No neural counter observer claimed.'))
        if elapsed() >= 15:
            write(OUT/'worker-postwrite-rejection.json', dict(elapsed_seconds=elapsed())); accepted = False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


def root(args):
    need(args.approval_reference and not OUT.exists() and not OWNED.exists(), 'ROOT reference and exclusive attempt')
    packet = allocation(args.packet_sha256)
    need(sha(SELF) == args.controller_sha256 and sha(HELPER) == HELPER_SHA, 'reviewed controller/helper')
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import entry, run_owned, safe
    entry(); safe(SELF); safe(OUT); safe(OWNED)
    import psutil
    need(psutil.virtual_memory().available >= 2*1024**3, 'fresh free2GiB')
    OUT.mkdir(); (OUT/'runtime-temp').mkdir()
    write(OUT/'before.json', dict(source_sha256=packet['source_sha256'], runtime_sha256=packet['runtime_sha256'],
          controller_sha256=args.controller_sha256, packet_sha256=args.packet_sha256, approval_reference=args.approval_reference))
    errors, receipt, child = [], None, None
    environment = dict(os.environ)
    try:
        os.environ.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void',
                          TEMP=str(OUT/'runtime-temp'), TMP=str(OUT/'runtime-temp'), TMPDIR=str(OUT/'runtime-temp'))
        need(elapsed() < 10, 'whole30 setup reserve')
        receipt = run_owned(SELF, ['--worker', '--packet-sha256', args.packet_sha256], OWNED,
            expected_worker_sha256=args.controller_sha256, approval_reference=args.approval_reference,
            max_seconds=18, cleanup_reserve_seconds=3, max_output_bytes=32768)
        write(OWNED/'receipt.json', receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
             and receipt['popen_handle_closed'] is True and receipt['errors'] == [], 'owned actual completion/Job0')
        child = json.loads((OUT/'worker-result.json').read_bytes())
        need(child['status'] == 'ACCEPTED_CONTRACT9_PENDING_OUTER' and child['calls'] == CALLS
             and child['counts'] == dict(tests=9, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
             and child['source_after'] == packet['source_sha256'] and child['runtime_after'] == packet['runtime_sha256']
             and child['methods_restored'] is True and child['monitor_stopped'] is True
             and child['packet_sha256'] == args.packet_sha256
             and child['errors'] == child['forbidden'] == child['heavy_modules'] == child['resource_errors'] == []
             and child['elapsed_seconds'] < 15 and len(child['subtests']) == 21
             and sorted(child['executed_test_methods']) == packet['expected_test_methods'], 'actual pure9 scope/calls/restoration')
        need(not any((OUT/name).exists() for name in ('resource-failure.json', 'worker-postwrite-rejection.json'))
             and all(sha(OWNED/name) == pin for name, pin in receipt['output_sha256'].items()),
             'original raw logs and no late resource failure')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    finally:
        os.environ.clear(); os.environ.update(environment)
    try:
        need(sha(SELF) == args.controller_sha256 and sha(PACKET) == args.packet_sha256
             and all(sha(ROOT/name) == pin for name, pin in packet['source_sha256'].items())
             and all(sha(ROOT/name) == pin for name, pin in packet['runtime_sha256'].items()), 'final source/runtime/packet hashes')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    accepted = not errors and elapsed() < 30 and dict(os.environ) == environment
    write(OUT/'result.json', dict(status='ACCEPTED_9_ENGINEERING10X84_CONTRACT_METHODS_ONLY' if accepted else 'REJECTED_CONTRACT9',
        errors=errors, counts=None if child is None else child['counts'], elapsed_seconds=elapsed(), whole_cap_seconds=30,
        source_sha256=packet['source_sha256'], runtime_sha256=packet['runtime_sha256'], controller_sha256=args.controller_sha256,
        packet_sha256=args.packet_sha256, owned_receipt=receipt, worker_result=child, environment_restored=dict(os.environ) == environment))
    if elapsed() >= 30:
        write(OUT/'postwrite-rejection.json', dict(elapsed_seconds=elapsed())); accepted = False
    print(json.dumps(dict(accepted=accepted, elapsed_seconds=elapsed(), result_sha256=sha(OUT/'result.json'))))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    owner = None
    if '--worker' in sys.argv:
        sys.path.insert(0, str(ROOT/'scripts/research'))
        from windows_owned_worker import worker_gate
        owner = worker_gate()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--controller-sha256'); parser.add_argument('--approval-reference')
    args = parser.parse_args()
    if args.worker:
        worker(args, owner)
    else:
        root(args)
