"""ROOT PREPARE ONLY: 2 existing cases, owned20s diagnostic; not a Gate retry.

Run only through reviewed windows_owned_worker.run_owned(max_seconds=20,
cleanup_reserve_seconds=3). Journal is operational evidence, not research data.
Production/test files and fixture fake clocks are never changed by this file.
"""
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from types import SimpleNamespace
import functools
import hashlib
import json
import math
import os
import platform
import sys
import time
import traceback

# Capture real functions before pytest or a fixture can replace its own namespace.
WALL_NS = time.perf_counter_ns
CPU_NS = time.process_time_ns
UTC_NS = time.time_ns
START_NS = WALL_NS()
REAL_STDOUT = sys.stdout
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'gate_diagnostic03'
ACTIVE_SECONDS = 17.0  # Owned outer20 includes3seconds cleanup; not17seconds per node.
PRIOR_CHARGE_SECONDS = 54.055553913116455
PINS = {
    'scripts/akt/refresh_gate2.py': '5b7e60d342f8c2ab27536d3ec02d208a9bdb04728ca5ccdf7371b13d784fa31b',
    'tests/akt/test_gate2_refresh.py': '9a0a41ffde24d0d12996f7294d000d50d9cbc8c1adced6853a0abf2c0c7de758',
    'scripts/research/windows_owned_worker.py': '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1',
}
NODES = (
    'tests/akt/test_gate2_refresh.py::test_gate2_selected_lock_drift_rejects_before_publication',
    'tests/akt/test_gate2_refresh.py::test_gate2_partition_is_disjoint_complete_and_keeps_pure_import_contexts',
)
HEAVY = ('torch', 'numpy', 'pandas', 'sklearn')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    if len(raw) > 256 * 1024:
        raise ValueError('diagnostic receipt byte cap')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


class Journal:
    """Stage writes durable; per-operation duration excludes its own start/end fsync.

    Nested operation durations are inclusive and include nested journal overhead;
    never sum them as exclusive time or call the diagnostic a production benchmark.
    """
    def __init__(self, path):
        self.stream = path.open('xb', buffering=0)
        self.sequence = 0
        self.operation_sequence = 0
        self.bytes = 0
        self.operation_stats = {}
        self.pending_operations = {}
        self.reports = []
        self.finished_nodes = []
        self.collected_nodes = []
        self.active_node = None
        self.restores = []
        self.instrumented_namespaces = set()

    def event(self, event, **fields):
        self.sequence += 1
        if self.sequence > 1024:
            raise ValueError('diagnostic journal record cap')
        value = dict(sequence=self.sequence, event=event, node=self.active_node,
                     real_wall_ns=WALL_NS(), real_cpu_ns=CPU_NS(), utc_ns=UTC_NS(), **fields)
        raw = (json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()
        if len(raw) > 8192 or self.bytes + len(raw) > 1024**2:
            raise ValueError('diagnostic journal byte cap')
        self.stream.write(raw); os.fsync(self.stream.fileno()); self.bytes += len(raw)
        REAL_STDOUT.write(raw.decode()); REAL_STDOUT.flush()

    def timed(self, name, original, *, after=None, path_argument=False):
        @functools.wraps(original)
        def wrapped(*args, **kwargs):
            self.operation_sequence += 1
            operation = self.operation_sequence
            fields = dict(operation=operation, operation_name=name)
            if path_argument and args and isinstance(args[0], (str, Path)):
                fields['path'] = str(args[0])[:1024]
            self.pending_operations[operation] = fields
            self.event('operation_start', **fields)
            w0, c0 = WALL_NS(), CPU_NS()
            error = None
            try:
                result = original(*args, **kwargs)
            except BaseException as exc:
                error = dict(type=type(exc).__name__, message=str(exc)[:512])
                raise  # Preserve the original exception and traceback.
            else:
                if after is not None:
                    after(result)
                return result  # The exact original object, without conversion.
            finally:
                wall, cpu = WALL_NS() - w0, CPU_NS() - c0
                stats = self.operation_stats.setdefault(name, dict(calls=0, wall_ns_inclusive=0,
                    cpu_ns_inclusive=0, max_wall_ns=0, errors=0))
                stats['calls'] += 1; stats['wall_ns_inclusive'] += wall
                stats['cpu_ns_inclusive'] += cpu; stats['max_wall_ns'] = max(stats['max_wall_ns'], wall)
                stats['errors'] += int(error is not None)
                self.event('operation_end', **fields, duration_wall_ns=wall,
                           duration_cpu_ns=cpu, original_exception=error)
                self.pending_operations.pop(operation, None)
        return wrapped

    def namespace(self, namespace):
        if id(namespace) in self.instrumented_namespaces:
            return
        self.instrumented_namespaces.add(id(namespace))
        for name in ('test_partition', 'selected_lock_file', 'sha256_file', 'combine_junit'):
            original = namespace[name]
            namespace[name] = self.timed(name, original,
                path_argument=name in ('selected_lock_file', 'sha256_file'))
            self.restores.append((namespace, name, original))

    def module(self, module):
        # Only replace references in this collected test module, never global runpy.
        original_runpy = module.runpy
        proxy = SimpleNamespace(**vars(original_runpy))
        proxy.run_path = self.timed('runpy.run_path', original_runpy.run_path,
                                   after=self.namespace_from_runpy, path_argument=True)
        module.runpy = proxy
        self.restores.append((module.__dict__, 'runpy', original_runpy))
        original = module._publisher
        def after_publisher(result):
            self.namespace(result[0].__globals__)
        module._publisher = self.timed('_publisher', original, after=after_publisher)
        self.restores.append((module.__dict__, '_publisher', original))

    def namespace_from_runpy(self, result):
        # runpy returns a separate globals dict; functions use their own __globals__.
        if isinstance(result, dict) and callable(result.get('refresh')):
            self.namespace(result['refresh'].__globals__)

    def restore(self):
        for namespace, name, original in reversed(self.restores):
            namespace[name] = original
        self.restores.clear()


def main():
    if Path.cwd().resolve() != ROOT or Path(sys.prefix).resolve() != ROOT / '.venv':
        raise ValueError('fixed repository/project .venv required')
    if sys.argv[1:]:
        raise ValueError('diagnostic has exact two pinned nodes; no caller overrides')
    if any(sha(ROOT / p) != digest for p, digest in PINS.items()):
        raise ValueError('diagnostic source pin mismatch before owned gate')
    driver_before = sha(Path(__file__))
    if any(name in sys.modules for name in HEAVY):
        raise ValueError('unexpected heavy module before owned gate')
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()  # Before pytest/knowledge_tracing imports; no Job creation here.
    OUT.mkdir(exist_ok=False)
    journal = Journal(OUT / 'stage-journal.jsonl')
    subprocess_attempts = []
    testing = {'active': False}
    def audit(event, args):
        if testing['active'] and event == 'subprocess.Popen':
            subprocess_attempts.append(event)
            journal.event('forbidden_actual_subprocess', event_name=event)
            raise AssertionError('actual subprocess/Git/model forbidden in diagnostic test phase')
    sys.addaudithook(audit)
    env_before = dict(os.environ)
    old_platform = platform._syscmd_ver
    native_version = tuple(sys.getwindowsversion().platform_version)
    rc = None; error = None
    journal.event('admission', owner=owner, source_pins=PINS, driver_sha256=driver_before,
                  exact_nodes=NODES, active_worker_seconds=ACTIVE_SECONDS,
                  required_owned_outer_seconds=20, required_cleanup_reserve_seconds=3,
                  prior_objective_charge_seconds=PRIOR_CHARGE_SECONDS,
                  prior_objective_is_not_reset_or_reclassified=True)
    try:
        os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTEST_ADDOPTS='', PYTEST_PLUGINS='',
            CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
            OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
        # Same metadata-only Windows fallback as the earlier pure controllers.
        # It is not installed runtime/OS/CUDA evidence and does not modify files.
        platform._syscmd_ver = lambda system='', release='', version='', supported_platforms=(): (
            'Windows', str(native_version[0]), '.'.join(map(str, native_version)))
        platform._uname_cache = None
        sys.path.insert(0, str(ROOT / 'src'))
        journal.event('pytest_import_start', test_only_WinAPI_version=native_version)
        import pytest
        journal.event('pytest_import_end')

        class Plugin:
            def pytest_collection_modifyitems(self, session, config, items):
                nodeids = [item.nodeid for item in items]
                journal.collected_nodes = nodeids
                journal.event('collected', nodeids=nodeids)
                if nodeids != list(NODES):
                    raise AssertionError('diagnostic requires exactly two predeclared nodes in order')
                if len({id(item.module) for item in items}) != 1:
                    raise AssertionError('both nodes must come from the same pinned test module')
                journal.module(items[0].module)

            def pytest_runtest_logstart(self, nodeid, location):
                journal.active_node = nodeid
                journal.event('node_start')

            @pytest.hookimpl(hookwrapper=True, tryfirst=True)
            def pytest_runtest_setup(self, item):
                journal.event('stage_enter', stage='setup')
                try:
                    yield
                finally:
                    journal.event('stage_hook_exit', stage='setup')

            @pytest.hookimpl(hookwrapper=True, tryfirst=True)
            def pytest_runtest_call(self, item):
                journal.event('stage_enter', stage='call')
                try:
                    yield
                finally:
                    journal.event('stage_hook_exit', stage='call')

            @pytest.hookimpl(hookwrapper=True, tryfirst=True)
            def pytest_runtest_teardown(self, item):
                journal.event('stage_enter', stage='teardown')
                try:
                    yield
                finally:
                    journal.event('stage_hook_exit', stage='teardown')

            def pytest_runtest_logreport(self, report):
                row = dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
                           duration_seconds=report.duration)
                journal.reports.append(row); journal.event('stage_report', **row)

            def pytest_runtest_logfinish(self, nodeid, location):
                journal.finished_nodes.append(nodeid)
                journal.event('node_finish', nodeid=nodeid)
                journal.active_node = None

            def pytest_sessionfinish(self, session, exitstatus):
                journal.event('session_finish', exitstatus=int(exitstatus))

        args = [*NODES, '-q', '-o', 'addopts=', '-p', 'no:cacheprovider',
                '--basetemp', str(OUT / 'tmp'), '--junitxml', str(OUT / 'junit.xml')]
        if (WALL_NS() - START_NS) / 1e9 >= ACTIVE_SECONDS:
            raise TimeoutError('no diagnostic allowance left before pytest')
        journal.event('pytest_main_start', argv=args)
        testing['active'] = True
        try:
            with (OUT / 'pytest.log').open('x', encoding='utf-8') as log:
                with redirect_stdout(log), redirect_stderr(log):
                    rc = int(pytest.main(args, plugins=[Plugin()]))
        finally:
            testing['active'] = False
        journal.event('pytest_main_return', returncode=rc)
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc)[:1024])
        with (OUT / 'failure.log').open('x', encoding='utf-8') as stream:
            traceback.print_exc(file=stream)
        journal.event('driver_failure', error=error)
    finally:
        testing['active'] = False
        journal.restore()
        platform._syscmd_ver = old_platform; platform._uname_cache = None
        os.environ.clear(); os.environ.update(env_before)
        after = {p: sha(ROOT / p) for p in PINS}
        driver_after = sha(Path(__file__))
        elapsed = (WALL_NS() - START_NS) / 1e9
        heavy = [name for name in HEAVY if name in sys.modules]
        expected_reports = {(node, phase) for node in NODES for phase in ('setup', 'call', 'teardown')}
        actual_reports = {(r['nodeid'], r['when']) for r in journal.reports}
        complete = (rc == 0 and error is None and after == PINS and driver_after == driver_before and elapsed <= ACTIVE_SECONDS
                    and not heavy and not subprocess_attempts
                    and journal.collected_nodes == list(NODES) and journal.finished_nodes == list(NODES)
                    and len(journal.reports) == 6 and actual_reports == expected_reports
                    and all(r['outcome'] == 'passed' for r in journal.reports)
                    and not journal.pending_operations and (OUT / 'junit.xml').is_file())
        result = dict(status='DIAGNOSTIC_TWO_NODES_COMPLETE_PENDING_OUTER_ACCEPTANCE' if complete else
            'REJECTED_OR_INCOMPLETE_DIAGNOSTIC_NOT_GATE_PASS', pytest_exit_code=rc, error=error,
            exact_nodes=NODES, collected_nodes=journal.collected_nodes, finished_nodes=journal.finished_nodes,
            stage_reports=journal.reports, operation_stats=journal.operation_stats,
            pending_operations=journal.pending_operations, real_worker_seconds=elapsed,
            active_worker_limit_seconds=ACTIVE_SECONDS, required_owned_outer_cap_seconds=20,
            prior_gate_objective_charge_seconds=PRIOR_CHARGE_SECONDS,
            elapsed_scope='worker import/gate/pytest/journal/restore; actual outer cleanup separately required',
            duration_scope='operation durations exclude own start/end journal write, but nested timings are inclusive',
            source_before=PINS, source_after=after, driver_sha256_before=driver_before,
            driver_sha256_after=driver_after, heavy_modules_loaded=heavy,
            actual_subprocess_attempts=subprocess_attempts, actual_Git_Job_model_calls_inside_tests=0,
            parent_owned_Job_proof_required=True, fixture_clocks_arguments_results_and_purity_unchanged=True,
            test_only_WinAPI_version=native_version, actual_full_Gate=False, actual_model_calls=0,
            no_retry_or_all76_claim=True)
        journal.event('driver_finalization', complete=complete, real_worker_seconds=elapsed)
        write_json(OUT / 'result.json', result)
        post = (WALL_NS() - START_NS) / 1e9
        terminal_ok = complete and post <= ACTIVE_SECONDS
        write_json(OUT / 'terminal.json', dict(status='PENDING_OUTER_ACCEPTANCE' if terminal_ok else
            'REJECTED_RETAIN_NO_RETRY', result_sha256=sha(OUT / 'result.json'), postwrite_worker_seconds=post,
            active_limit_seconds=ACTIVE_SECONDS, whole_owned_outer_limit_seconds=20,
            outputs_sha256={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='terminal.json'}))
        journal.stream.close()
    return 0 if terminal_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
