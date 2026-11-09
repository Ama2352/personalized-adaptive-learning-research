"""Root-only 20 unittest normal-entry GKT, owned Job, không model/corpus thực."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import threading
import time
import traceback
import unittest

START, WALL = time.perf_counter(), time.time()
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
PACKET = PREP/'gkt_research_data_normal03_packet.json'
OUT = PREP/'gkt-research-data-normal03'
OWNED = PREP/'gkt-research-data-normal03-owned'
OUTER = PREP/'gkt-research-data-normal03-outer'
HELPER = ROOT/'scripts/research/windows_owned_worker.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
sys.path.insert(0, str(HELPER.parent))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def hashes(packet):
    return {name: sha(ROOT/name) for name in packet['source_sha256']}


def allocation(expected):
    need(sha(PACKET) == expected, 'External packet SHA mismatch')
    packet = json.loads(PACKET.read_bytes())
    need(packet['controller_sha256'] == sha(SELF) and packet['helper_sha256'] == sha(HELPER) == HELPER_SHA,
         'Frozen controller/helper identity')
    need(packet['limits'] == dict(whole_seconds=30, owned_seconds=24, cleanup_seconds=3, worker_seconds=20,
        max_rss_bytes=512*1024**2, min_available_bytes=1536*1024**2, prelaunch_available_bytes=2*1024**3),
        'Exact reviewed finite limits')
    need(len(packet['expected_ids']) == len(set(packet['expected_ids'])) == 20
         and packet['expected_ids'] == sorted(packet['expected_ids']), 'Exact20 sorted IDs')
    need(all(not Path(name).is_absolute() and '..' not in Path(name).parts
             and (ROOT/name).resolve().is_relative_to(ROOT) for name in packet['source_sha256']), 'Fixed source paths')
    need(hashes(packet) == packet['source_sha256'], 'Candidate/dependency source drift')
    return packet


def worker(expected):
    # Genuine ownership handshake precedes data/framework imports and test discovery.
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    packet = allocation(expected)
    need(sys.prefix == str(ROOT/'.venv') and os.name == 'nt', 'Actual repository Windows .venv required')
    OUT.mkdir(exist_ok=False)
    before = hashes(packet)
    write(OUT/'source_before.json', before)
    timer = threading.Timer(max(.001, 20-elapsed()), lambda: os._exit(124))
    timer.daemon = True; timer.start()
    # Fixture OS metadata dùng actual WinAPI, tránh platform fallback tạo cmd child.
    native_version = tuple(sys.getwindowsversion().platform_version)
    old_syscmd, old_uname = platform._syscmd_ver, platform._uname_cache
    platform._syscmd_ver = lambda system='', release='', version='', supported_platforms=(): (
        'Windows', str(native_version[0]), '.'.join(map(str, native_version)))
    platform._uname_cache = None
    old_cache = sys.pycache_prefix
    sys.pycache_prefix = str(OUT/'fresh-bytecode')
    denied, collected, started, completed = [], [], [], []
    forbidden = ('torch', 'pandas', 'scipy', 'sklearn', 'tensorflow', 'jax', 'modal', 'boto3', 'botocore')
    neural = ('knowledge_tracing.gkt.recurrent', 'knowledge_tracing.gkt.training',
              'knowledge_tracing.sakt.model', 'knowledge_tracing.sakt.training', 'knowledge_tracing.akt.model',
              'knowledge_tracing.akt.training', 'knowledge_tracing.akt.research_graph_model')
    protected = tuple(os.path.normcase(str(ROOT/name)) for name in (
        'dataset', 'artifacts/bkt_baseline', 'artifacts/simulator', 'experiments', 'research_tracking',
        'paper1', 'paper2', 'venv', '.wsl'))

    def audit(event, args):
        reason = None
        if event == 'import' and (str(args[0]).split('.')[0] in forbidden
                or any(str(args[0]) == name or str(args[0]).startswith(name+'.') for name in neural)):
            reason = 'forbidden model/framework import'
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn') or event in ('socket.__new__', 'socket.getaddrinfo'):
            reason = 'no process/network in fixture'
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
            if any(path == base or path.startswith(base+os.sep) for base in protected) or 'holdout' in Path(path).parts:
                reason = 'no protected/real data reads or writes'
        if reason:
            if len(denied) < 32:
                denied.append(dict(event=event, reason=reason))
            raise RuntimeError(reason)
    sys.addaudithook(audit)
    import psutil
    process = psutil.Process()
    stop = threading.Event()
    resources = dict(samples=0, peak_family_rss_bytes=0, peak_worker_rss_bytes=0,
                     min_available_bytes=None, errors=[])
    lock = threading.Lock()

    def sample():
        with lock:
            need(resources['samples'] < 400, 'Finite monitor sample cap')
            info = process.memory_info()
            family = info.rss
            for child in process.children(recursive=True):
                try:
                    family += child.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            available = psutil.virtual_memory().available
            resources['samples'] += 1
            resources['peak_family_rss_bytes'] = max(resources['peak_family_rss_bytes'], family)
            resources['peak_worker_rss_bytes'] = max(resources['peak_worker_rss_bytes'], getattr(info, 'peak_wset', info.rss))
            resources['min_available_bytes'] = available if resources['min_available_bytes'] is None else min(resources['min_available_bytes'], available)
            need(elapsed() < 20, 'Whole worker time includes imports/cleanup')
            need(max(resources['peak_worker_rss_bytes'], family) <= 512*1024**2, '512MiB RSS cap')
            need(available >= 1536*1024**2, '1536MiB available floor')

    def guard():
        sample()
        need(not resources['errors'], 'Monitor resource failure')

    def monitor():
        while not stop.wait(.1):
            try:
                sample()
            except BaseException as error:
                resources['errors'].append(type(error).__name__+': '+str(error))
                return

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    result = None; error = None
    try:
        guard(); monitor_thread.start()
        sys.path.insert(0, str(ROOT/'src'))
        suite = unittest.defaultTestLoader.discover(str(ROOT/'tests/gkt'), pattern='test_research_data.py')
        def ids(items):
            for item in items:
                if isinstance(item, unittest.TestSuite):
                    yield from ids(item)
                else:
                    yield item.id()
        collected = list(ids(suite))
        need(collected == packet['expected_ids'], 'Exact collected20 IDs, no omissions')
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                guard(); started.append(test.id()); super().startTest(test)
            def stopTest(self, test):
                completed.append(test.id()); super().stopTest(test); guard()
        with (OUT/'unittest.log').open('x', encoding='utf-8') as log, redirect_stdout(log), redirect_stderr(log):
            result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
        guard()
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught), traceback=traceback.format_exc())
    finally:
        stop.set()
        if monitor_thread.ident is not None:
            monitor_thread.join(timeout=.5)
        monitor_stopped = not monitor_thread.is_alive()
        platform._syscmd_ver, platform._uname_cache = old_syscmd, old_uname
        sys.pycache_prefix = old_cache
        timer.cancel()
    counts = None if result is None else dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        skipped=len(result.skipped), expected_failures=len(result.expectedFailures), unexpected_successes=len(result.unexpectedSuccesses))
    after = hashes(packet)
    module = sys.modules.get('knowledge_tracing.gkt.research_data')
    actual_source_identity = None if module is None else dict(module.source_identity())
    heavy = sorted(name for name in sys.modules if name.split('.')[0] in forbidden or any(name == n or name.startswith(n+'.') for n in neural))
    origins = {name: str(Path(sys.modules[name].__file__).resolve()) for name in ('numpy', 'psutil') if name in sys.modules}
    accepted = (error is None and counts == dict(tests=20, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
        and collected == started == completed == packet['expected_ids'] and before == after == packet['source_sha256']
        and actual_source_identity == packet['candidate_source_identity']
        and not denied and not heavy and not resources['errors'] and monitor_stopped and elapsed() < 20
        and all(Path(value).is_relative_to(ROOT/'.venv') for value in origins.values())
        and set(origins) == {'numpy', 'psutil'} and (OUT/'unittest.log').stat().st_size <= 65536)
    record = dict(status='ACCEPTED20_GKT_DATA_NORMAL_ENTRY_PENDING_OUTER' if accepted else 'REJECTED_GKT_DATA_CANDIDATES',
        counts=counts, error=error, collected_ids=collected, started_ids=started, completed_ids=completed,
        source_before=before, source_after=after, candidate_source_identity=actual_source_identity,
        denied=denied, heavy_modules=heavy, origins=origins,
        resources=resources, monitor_stopped=monitor_stopped, elapsed_seconds=elapsed(), owner_gate=owner,
        platform_fixture=dict(actual_WinAPI_version=native_version, purpose='platform display metadata only'),
        platform_restored=platform._syscmd_ver is old_syscmd and platform._uname_cache is old_uname,
        model_calls=0, actual_corpus=False, corpus_publication=False, automatic_retry=False)
    write(OUT/'result.json', record)
    if elapsed() >= 20:
        write(OUT/'postwrite-rejection.json', dict(reason='worker publication elapsed cap'))
        accepted = False
    raise SystemExit(0 if accepted else 1)


def outer(expected):
    packet = allocation(expected)
    need(sys.prefix == str(ROOT/'.venv') and os.name == 'nt', 'Repository Windows .venv required')
    need(not OUT.exists() and not OWNED.exists(), 'Exclusive native output namespaces')
    OUTER.mkdir(exist_ok=False)
    import psutil
    available = psutil.virtual_memory().available
    receipt = result = None; error = None
    before = hashes(packet)
    try:
        need(available >= 2*1024**3, 'Prelaunch available RAM must be at least2GiB')
        from windows_owned_worker import run_owned
        receipt = run_owned(SELF, ['--worker', '--packet-sha256', expected], OWNED,
            expected_worker_sha256=packet['controller_sha256'], approval_reference='ROOT_REVIEW_GKT_DATA20_CANDIDATES_0NN',
            max_seconds=24, cleanup_reserve_seconds=3, max_output_bytes=65536)
        if OWNED.is_dir():
            write(OWNED/'receipt.json', receipt)
        if (OUT/'result.json').exists():
            result = json.loads((OUT/'result.json').read_bytes())
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught), traceback=traceback.format_exc())
    after = hashes(packet)
    accepted = bool(error is None and receipt and receipt['accepted'] and receipt['returncode'] == 0
        and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup'] == 0
        and receipt['popen_handle_closed'] and receipt['actual_worker_in_job_before_GO'] and result
        and result['status'] == 'ACCEPTED20_GKT_DATA_NORMAL_ENTRY_PENDING_OUTER'
        and result['counts'] == dict(tests=20, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
        and result['source_before'] == result['source_after'] == before == after == packet['source_sha256']
        and result['candidate_source_identity'] == packet['candidate_source_identity']
        and result['collected_ids'] == result['started_ids'] == result['completed_ids'] == packet['expected_ids']
        and result['monitor_stopped'] and result['platform_restored'] and not result['denied'] and not result['heavy_modules']
        and not result['resources']['errors'] and result['resources']['samples'] > 0
        and max(result['resources']['peak_family_rss_bytes'], result['resources']['peak_worker_rss_bytes']) <= 512*1024**2
        and result['resources']['min_available_bytes'] >= 1536*1024**2
        and result['elapsed_seconds'] < 20 and not (OUT/'postwrite-rejection.json').exists() and elapsed() < 30)
    final = dict(status='ACCEPTED20_GKT_DATA_ONLY_NORMAL_ENTRY_FIXTURES' if accepted else 'REJECTED_GKT_DATA_NORMAL_ENTRY_FIXTURES',
        elapsed_seconds=elapsed(), whole_cap_seconds=30, prelaunch_available_bytes=available, error=error,
        source_before=before, source_after=after, packet_sha256=expected, controller_sha256=sha(SELF),
        owned_receipt=receipt, worker_result=result, output_sha256={p.name: sha(p) for p in OUT.iterdir() if p.is_file()} if OUT.exists() else {},
        actual_corpus=False, corpus_publication=False, model_calls=0, automatic_retry=False)
    write(OUTER/'final.json', final)
    if elapsed() >= 30:
        write(OUTER/'postwrite-rejection.json', dict(reason='outer publication elapsed cap'))
        accepted = False
    print(json.dumps(dict(status=final['status'], elapsed_seconds=elapsed()), ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    # Fixed argv tránh HelpFormatter/terminal metadata trước owned handshake.
    args = sys.argv[1:]
    is_worker = args[:1] == ['--worker']
    need(len(args) == (3 if is_worker else 2)
         and args[-2] == '--packet-sha256', 'Exact reviewed argv required')
    expected = args[-1]
    need(len(expected) == 64 and all(c in '0123456789abcdef' for c in expected), 'Packet SHA256 required')
    (worker if is_worker else outer)(expected)
