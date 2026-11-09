"""ROOT-only pure7, owned Job, source bodies thật và 31subtests tổng hợp."""

import argparse
import functools
import hashlib
import importlib
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
PACKET = PREP / 'rq1_response_reliability_pure01_packet.json'
OUT = PREP / 'rq1-response-reliability-pure01'
OWNED = PREP / 'rq1-response-reliability-pure01-owned'
HELPER = ROOT / 'scripts/research/windows_owned_worker.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
CALLS = dict(response_bins=75, grouped_reliability=2, main=0)
FORBIDDEN = {'numpy', 'pandas', 'torch', 'scipy', 'sklearn', 'networkx', 'duckdb', 'knowledge_tracing'}


def need(value, message):
    if not value:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter() - START, time.time() - WALL)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def allocation(expected):
    need(sha(PACKET) == expected, 'external packet SHA')
    value = json.loads(PACKET.read_bytes())
    need(value['expected_calls'] == CALLS and value['expected_methods'] == 7
         and value['expected_subtests'] == 31, 'finite reviewed case/call allocation')
    need(all(sha(ROOT / n) == h for n, h in value['source_sha256'].items()), 'reviewed three sources')
    return value


def worker(args, owner):
    packet = allocation(args.packet_sha256)
    denied, metadata_commands = [], []
    metadata_phase = [True]
    cmd = Path(os.environ['SystemRoot']) / 'System32/cmd.exe'
    literal = os.path.normcase(str(cmd.absolute())).casefold()
    commands = {literal + ' /c "ver"', '"' + literal + '" /c "ver"'}
    protected = tuple(ROOT / n for n in ('dataset', 'paper1', 'paper2', 'research_tracking',
                                         'experiments', 'venv', '.wsl', 'artifacts/simulator'))

    def audit(event, values):
        if event == 'subprocess.Popen':
            if (metadata_phase[0] and len(metadata_commands) < 3 and type(values[0]) is str
                    and type(values[1]) is str and os.path.normcase(os.path.abspath(values[0])).casefold() == literal
                    and values[1].strip().casefold() in commands):
                metadata_commands.append(dict(executable=values[0], command=values[1])); return
            denied.append(event); raise RuntimeError('only bounded literal metadata cmd permitted')
        if event.startswith('socket.') and event != 'socket.gethostname' or event in ('os.system', 'os.posix_spawn', 'os.spawn'):
            denied.append(event); raise RuntimeError('process/network scope')
        if event == 'import' and str(values[0]).split('.')[0] in FORBIDDEN:
            denied.append(event); raise RuntimeError('scientific/model import denied')
        if event in ('open', 'os.listdir', 'os.scandir') and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.path.abspath(os.fsdecode(values[0])))
            if (any(path == p or path.is_relative_to(p) for p in protected)
                    or path.suffix.lower() in ('.gz', '.csv', '.pt', '.parquet', '.npy', '.npz')
                    or path.name in ('rq2_cache_mechanism_contract01.json', 'reliability.json')):
                denied.append(event); raise RuntimeError('cached/protected data access denied')

    sys.addaudithook(audit)
    try:
        native_os = platform.uname()._asdict()
        import psutil
    finally:
        metadata_phase[0] = False
    process = psutil.Process()
    born = process.create_time()
    resources = dict(samples=0, peak_rss_bytes=0, minimum_available_ram_bytes=None)
    resource_errors, errors, originals, executed, subtests = [], [], [], [], []
    stop = threading.Event()

    def sample():
        need(process.create_time() == born, 'actual worker PID identity')
        info = process.memory_info(); available = int(psutil.virtual_memory().available)
        peak = max(info.rss, getattr(info, 'peak_wset', 0))
        resources['samples'] += 1
        resources['peak_rss_bytes'] = max(resources['peak_rss_bytes'], peak)
        previous = resources['minimum_available_ram_bytes']
        resources['minimum_available_ram_bytes'] = available if previous is None else min(previous, available)
        need(peak <= 1024**3 and available >= 2*1024**3, 'original pure RAM limits')

    def monitor():
        while not stop.wait(.1):
            try:
                sample()
            except BaseException as exc:
                write(OUT / 'resource-failure.json', dict(error=repr(exc), resources=resources))
                os._exit(125)

    sample()
    watcher = threading.Thread(target=monitor, daemon=True); watcher.start()
    timer = threading.Timer(max(.001, 15 - elapsed()), lambda: os._exit(124)); timer.daemon = True; timer.start()
    calls = dict.fromkeys(CALLS, 0)
    counts = None
    try:
        sys.path.insert(0, str(PREP))
        analysis = importlib.import_module('analyze_rq1_response_reliability01')
        tests = importlib.import_module('test_rq1_response_reliability01')
        need(Path(analysis.__file__).resolve() == PREP / 'analyze_rq1_response_reliability01.py'
             and Path(tests.__file__).resolve() == PREP / 'test_rq1_response_reliability01.py'
             and tests.analysis is analysis, 'actual source module identities')
        for name in CALLS:
            original = getattr(analysis, name)

            def observe(function, label):
                @functools.wraps(function)
                def counted(*a, **kw):
                    calls[label] += 1
                    need(calls[label] <= CALLS[label], 'finite real-body call allocation')
                    return function(*a, **kw)
                return counted

            originals.append((name, original)); setattr(analysis, name, observe(original, name))

        class Result(unittest.TextTestResult):
            def startTest(self, test):
                executed.append(test.id()); super().startTest(test)

            def addSubTest(self, test, subtest, error):
                subtests.append(dict(parameters={k: str(v) for k, v in subtest.params.items()},
                                     error_type=None if error is None else error[0].__name__))
                super().addSubTest(test, subtest, error)

        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        need(suite.countTestCases() == 7, 'exact seven methods')
        result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
        counts = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                      skipped=len(result.skipped), unexpected_successes=len(result.unexpectedSuccesses),
                      expected_failures=len(result.expectedFailures))
        need(counts == dict(tests=7, failures=0, errors=0, skipped=0, unexpected_successes=0, expected_failures=0)
             and len(set(executed)) == 7 and result.wasSuccessful(), 'all actual7 methods accepted')
        need(calls == CALLS and len(subtests) == 31 and all(r['error_type'] is None for r in subtests),
             'actual body calls and31 subtests')
        need(sum('edge' in r['parameters'] for r in subtests) == 16
             and sum('value' in r['parameters'] for r in subtests) == 15, 'boundary/malformed subtest kinds')
    except BaseException as exc:
        errors.append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        for name, original in originals:
            setattr(analysis, name, original)
        restored = all(getattr(analysis, n) is f for n, f in originals)
        stop.set(); watcher.join(timeout=.5)
        try: sample()
        except BaseException as exc: resource_errors.append(repr(exc))
        heavy = sorted(n for n in sys.modules if n.split('.')[0] in FORBIDDEN)
        after = {n: sha(ROOT / n) for n in packet['source_sha256']}
        accepted = (not errors and not denied and not heavy and not resource_errors and restored
                    and not watcher.is_alive() and after == packet['source_sha256'] and elapsed() < 15)
        write(OUT / 'worker-result.json', dict(status='ACCEPTED_RESPONSE7_PENDING_OUTER' if accepted else 'REJECTED_RESPONSE7',
              counts=counts, calls=calls, executed_test_ids=executed, subtests=subtests, source_after=after,
              packet_sha256=args.packet_sha256, errors=errors, forbidden=denied, heavy_modules=heavy,
              resource_errors=resource_errors, resources=resources, methods_restored=restored,
              monitor_stopped=not watcher.is_alive(), metadata_commands=metadata_commands,
              native_os=native_os, elapsed_seconds=elapsed(), cached_file_opens=0 if not denied else None, owner=owner))
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


def root(args):
    need(args.approval_reference and not OUT.exists() and not OWNED.exists(), 'review reference/exclusive pure attempt')
    packet = allocation(args.packet_sha256)
    need(sha(SELF) == args.controller_sha256 and sha(HELPER) == HELPER_SHA, 'controller/helper review pins')
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import entry, run_owned
    entry()
    import psutil
    need(psutil.virtual_memory().available >= 2*1024**3, 'fresh free2GiB')
    OUT.mkdir()
    write(OUT / 'before.json', dict(source_sha256=packet['source_sha256'], controller_sha256=args.controller_sha256,
                                  packet_sha256=args.packet_sha256, approval_reference=args.approval_reference))
    errors, receipt, child = [], None, None
    try:
        need(elapsed() < 10, 'setup within whole30')
        receipt = run_owned(SELF, ['--worker', '--packet-sha256', args.packet_sha256], OWNED,
              expected_worker_sha256=args.controller_sha256, approval_reference=args.approval_reference,
              max_seconds=18, cleanup_reserve_seconds=3, max_output_bytes=32768)
        write(OWNED / 'receipt.json', receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['errors'] == [], 'owned pure completion/Job0')
        child = json.loads((OUT / 'worker-result.json').read_bytes())
        need(child['status'] == 'ACCEPTED_RESPONSE7_PENDING_OUTER' and child['calls'] == CALLS
             and child['source_after'] == packet['source_sha256'] and child['methods_restored'] is True
             and child['errors'] == child['forbidden'] == child['heavy_modules'] == child['resource_errors'] == []
             and child['cached_file_opens'] == 0 and child['monitor_stopped'] is True, 'actual pure source/scope/calls')
        need(sha(SELF) == args.controller_sha256 and sha(PACKET) == args.packet_sha256
             and all(sha(ROOT / n) == h for n, h in packet['source_sha256'].items()), 'source postchecks')
        need(all(sha(OWNED / n) == h for n, h in receipt['output_sha256'].items()), 'original pure streams')
    except BaseException as exc:
        errors.append(dict(type=type(exc).__name__, message=str(exc)))
    accepted = not errors and elapsed() < 30
    write(OUT / 'result.json', dict(status='ACCEPTED_7_RESPONSE_RELIABILITY_PURE_METHODS' if accepted else 'REJECTED_RESPONSE_PURE',
          errors=errors, counts=None if child is None else child['counts'], elapsed_seconds=elapsed(), whole_cap_seconds=30,
          source_sha256=packet['source_sha256'], controller_sha256=args.controller_sha256,
          packet_sha256=args.packet_sha256, owned_receipt=receipt, worker_result=child))
    if elapsed() >= 30:
        write(OUT / 'postwrite-rejection.json', dict(elapsed_seconds=elapsed())); accepted = False
    print(json.dumps(dict(accepted=accepted, elapsed_seconds=elapsed(), result_sha256=sha(OUT / 'result.json'))))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    owner = None
    if '--worker' in sys.argv:
        sys.path.insert(0, str(ROOT / 'scripts/research'))
        from windows_owned_worker import worker_gate
        owner = worker_gate()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--controller-sha256')
    parser.add_argument('--approval-reference')
    args = parser.parse_args()
    if args.worker: worker(args, owner)
    else: root(args)
