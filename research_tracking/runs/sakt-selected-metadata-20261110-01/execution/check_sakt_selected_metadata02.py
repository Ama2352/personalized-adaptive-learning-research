"""Root-only 34 metadata cases qua normal import; không model hoặc corpus."""
import time
PERF, WALL = time.perf_counter, time.time
START, START_WALL = PERF(), WALL()
import argparse
from collections import Counter
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP/'sakt_selected_metadata02_packet.json'
OUT = PREP/'sakt-selected-metadata02'
TMP = ROOT/'artifacts/akt/local-tests/ssm02'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(PERF()-START, WALL()-START_WALL)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    need(len(raw) <= 2**20, 'bounded metadata receipt')
    with (OUT/name).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def main():
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate, safe
    owner = worker_gate()
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    need(sha(PACKET) == args.packet_sha256, 'external packet pin')
    packet = json.loads(PACKET.read_bytes())
    pins, runtime = packet['source_pins'], packet['runtime_pins']
    before = {n: sha(safe(ROOT/n)) for n in pins}
    runtime_before = {n: sha(Path(n)) for n in runtime}
    need(before == pins and runtime_before == runtime, 'actual source/runtime bytes')
    need(not OUT.exists() and not TMP.exists(), 'exclusive worker evidence and fixtures')
    OUT.mkdir(); temp = OUT/'runtime-temp'; temp.mkdir()
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT/'.venv', 'actual repository .venv')
    timer = threading.Timer(max(.001, 20.-elapsed()), lambda: os._exit(124))
    timer.daemon = True; timer.start()
    sys.path[:0] = [str(ROOT), str(ROOT/'src')]
    keys = ('TEMP','TMP','TMPDIR','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS',
            'CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES','COLUMNS','LINES')
    env = {n: os.environ.get(n) for n in keys}
    os.environ.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTEST_ADDOPTS='', PYTEST_PLUGINS='', CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', COLUMNS='80', LINES='24')
    blocked = {'torch','numpy','pandas','scipy','sklearn','modal','boto3'}
    need(not blocked.intersection(sys.modules), 'cold scientific modules absent')
    import psutil
    process = psutil.Process()
    resources = dict(samples=0, peak_worker_rss_bytes=0, minimum_available_ram_bytes=None)
    phase = ['windows_metadata']; denied = []; metadata = {}; nodes = []; bodies = []; reports = []
    null_reads = null_writes = metadata_processes = 0
    error = junit_error = counts = rc = None
    source_after = runtime_after = None

    def check():
        need(elapsed() < 20., 'whole worker deadline')
        sample = process.memory_info(); free = int(psutil.virtual_memory().available)
        resources['samples'] += 1
        resources['peak_worker_rss_bytes'] = max(resources['peak_worker_rss_bytes'], sample.rss, getattr(sample, 'peak_wset', 0))
        previous = resources['minimum_available_ram_bytes']
        resources['minimum_available_ram_bytes'] = free if previous is None else min(previous, free)
        need(resources['peak_worker_rss_bytes'] <= 128*2**20 and free >= 2**30, 'metadata worker RSS/free floor')

    def reject(message, details=None):
        if len(denied) < 8:
            denied.append(dict(phase=phase[0], message=message, details=details))
        raise RuntimeError(message)

    allowed = {(ROOT/n).resolve() for n in pins}|{PACKET.resolve()}
    runtime_roots = (ROOT/'.venv', Path(sys.base_prefix).resolve())
    def owned(path):
        return path.is_relative_to(OUT) or path.is_relative_to(TMP)
    def audit(kind, values):
        nonlocal null_reads, null_writes, metadata_processes
        if kind == 'import' and str(values[0]).split('.')[0] in blocked:
            reject('scientific/model/cloud import forbidden')
        if kind == 'subprocess.Popen':
            if phase[0] != 'windows_metadata' or metadata_processes >= 2:
                reject('at most2 genuine metadata processes, none after warmup')
            metadata_processes += 1
        if kind.startswith('socket.') and not (phase[0] == 'windows_metadata' and kind == 'socket.gethostname'):
            reject('network forbidden')
        if kind == 'os.system' or kind.startswith('os.spawn'):
            reject('system/spawn forbidden')
        if kind == 'open' and values and not isinstance(values[0], int):
            name = os.fsdecode(values[0]); mode = values[1] or ''; flags = values[2] if type(values[2]) is int else 0
            writing = any(c in mode for c in 'wax+') or bool(flags & (os.O_WRONLY|os.O_RDWR))
            if name == os.devnull and not flags & (os.O_CREAT|os.O_TRUNC|os.O_APPEND):
                if writing:
                    need(phase[0] == 'windows_metadata' and flags & os.O_RDWR and null_writes < 3, 'bounded genuine metadata NUL only')
                    null_writes += 1
                else:
                    need(null_reads < 8, 'bounded pytest NUL reads')
                    null_reads += 1
                return
            path = Path(name).absolute().resolve()
            details = dict(operation='write' if writing else 'read', raw_path=name[:2048],
                resolved_path=str(path)[:2048], mode=mode[:32], flags=flags)
            if writing:
                if not owned(path): reject('write outside owned metadata/fixture roots', details)
            else:
                source = None
                if path.suffix == '.pyc':
                    try: source = Path(importlib.util.source_from_cache(str(path))).resolve()
                    except ValueError: pass
                if path not in allowed and source not in allowed and not owned(path) and not any(path.is_relative_to(r) for r in runtime_roots):
                    reject('read outside exact source/runtime/fixture allowlist', details)
        if kind in ('os.mkdir','os.remove','os.rmdir','os.rename'):
            paths = values[:2] if kind == 'os.rename' else values[:1]
            if not all(owned(Path(v).absolute().resolve()) for v in paths): reject('mutation outside owned fixtures')
        if kind in ('os.link','os.symlink'): reject('link creation forbidden')
    sys.addaudithook(audit)
    try:
        check()
        helper = ROOT/packet['metadata_helper']
        raw = helper.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == pins[packet['metadata_helper']], 'genuine metadata helper source')
        namespace = dict(__file__=str(helper), __name__='sakt_actual_windows_metadata_only')
        exec(compile(raw, str(helper), 'exec'), namespace)
        namespace['native_windows_metadata'](check, metadata)
        namespace['require_metadata_closed'](metadata)
        write('windows_metadata.json', metadata)
        phase[0] = 'metadata_tests'
        from knowledge_tracing.sakt import research_execution, research_runner
        held = research_execution.AuthorizedSAKTSelectedExecution
        need(research_runner.AuthorizedSAKTSelectedExecution is held and not blocked.intersection(sys.modules), 'normal import cold class identity')
        import pytest
        from _pytest.junitxml import mangle_test_address
        class Journal:
            def pytest_collection_finish(self, session):
                nodes.extend(item.nodeid for item in session.items)
                distribution = Counter(node.split('::')[1].split('[')[0] for node in nodes)
                need(len(nodes) == len(set(nodes)) == 34 and dict(distribution) == packet['expected_function_counts'], 'all exact34 function/parameter cases collected before bodies')
                need(all(n.startswith(packet['test_module']+'::') for n in nodes), 'only canonical test module')
            def pytest_runtest_call(self, item):
                check(); bodies.append(item.nodeid)
            def pytest_runtest_logreport(self, report):
                check(); reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome))
        argv = [packet['test_module'], '-q', '--noconftest', '-p', 'no:cacheprovider', '-o', 'addopts=',
            '--basetemp', str(TMP), '--junitxml', str(OUT/'junit.xml'), '--log-file', str(OUT/'pytest-file.log')]
        with (OUT/'pytest.log').open('x', encoding='utf-8') as log, redirect_stdout(log), redirect_stderr(log):
            rc = int(pytest.main(argv, plugins=[Journal()]))
        need(research_execution.AuthorizedSAKTSelectedExecution is held, 'cached class identity unchanged')
        need(rc == 0 and bodies == nodes and not denied and not blocked.intersection(sys.modules), 'all34 bodies/cold imports accepted')
        namespace['require_metadata_closed'](metadata); check()
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught))
    finally:
        try:
            cases = list(ET.parse(OUT/'junit.xml').iter('testcase'))
            counts = dict(tests=len(cases), failures=sum(len(list(c.iter('failure'))) for c in cases),
                errors=sum(len(list(c.iter('error'))) for c in cases), skipped=sum(len(list(c.iter('skipped'))) for c in cases))
            need(counts == dict(tests=34, failures=0, errors=0, skipped=0), 'actual34 JUnit cases0FES')
            expected_junit = [mangle_test_address(node) for node in nodes]
            expected_junit = [('.'.join(parts[:-1]), parts[-1]) for parts in expected_junit]
            actual_junit = [(case.get('classname'), case.get('name')) for case in cases]
            need(len(set(actual_junit)) == 34 and set(actual_junit) == set(expected_junit), 'physical JUnit IDs match actual collection')
        except BaseException as caught:
            junit_error = dict(type=type(caught).__name__, message=str(caught))
        for name, value in env.items():
            if value is None: os.environ.pop(name, None)
            else: os.environ[name] = value
        restored = env == {n: os.environ.get(n) for n in keys}
        source_after = {n: sha(ROOT/n) for n in pins}
        runtime_after = {n: sha(Path(n)) for n in runtime}
        cold = not blocked.intersection(sys.modules)
        accepted = error is None and junit_error is None and restored and cold and source_after == before and runtime_after == runtime_before and elapsed() < 20.
        write('case_events.json', reports)
        write('result.json', dict(status='ACCEPTED_34_SAKT_METADATA_PENDING_OUTER' if accepted else 'REJECTED_SAKT_METADATA_KEEP_ALL',
            accepted=accepted, pytest_exit_code=rc, error=error, junit_error=junit_error, counts=counts, nodeids=nodes,
            body_nodeids=bodies, denied=denied, actual_scientific_modules_absent=cold, environment_restored=restored,
            source_before=before, source_after=source_after, runtime_before=runtime_before, runtime_after=runtime_after,
            packet_sha256=args.packet_sha256, resources=resources, metadata=metadata, elapsed_seconds=elapsed(),
            worker_cap_seconds=20, owner_gate=owner['status'], resource_scope='COOPERATIVE_WORKER_SAMPLES_NOT_JOB_FAMILY_RSS',
            typed_producer_validated=False, model_or_corpus_executed=False))
        if elapsed() >= 20.:
            write('postwrite_rejection.json', dict(reason='same worker deadline after publication')); accepted = False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
