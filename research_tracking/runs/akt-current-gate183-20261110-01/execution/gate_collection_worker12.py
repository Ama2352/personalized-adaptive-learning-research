"""ROOT-only fresh-group collection; imports có thực thi, test/NN/fit bị chặn."""
import time
START = time.perf_counter()
WALL = time.time()
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import platform
import sys
import threading
import tempfile

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate, safe, bounded, Kernel


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def load_refresh():
    spec = importlib.util.spec_from_file_location('reviewed_gate_collection_refresh', ROOT/'scripts/akt/refresh_gate2.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Lightweight definitions only; never refresh()/main().
    return module


class ImportCalls(ast.NodeVisitor):
    """Potential import-time calls only; không đi vào function/lambda bodies."""
    def __init__(self):
        self.calls = []
    def visit_FunctionDef(self, node):
        for expression in (*node.decorator_list, *node.args.defaults,
                           *[v for v in node.args.kw_defaults if v is not None]):
            self.visit(expression)
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_Lambda(self, node):
        for expression in (*node.args.defaults, *[v for v in node.args.kw_defaults if v is not None]):
            self.visit(expression)
    def visit_Call(self, node):
        self.calls.append(dict(line=node.lineno, function=ast.unparse(node.func)))
        self.generic_visit(node)


def validate_native_shim(observed, token_before, token_after, in_owned_job):
    """Pure predicates; psutil path stays diagnostic, no missing-drive repair."""
    owner = observed['owner']
    entry = observed['expected_shim_entry']
    native_image = token_before['image']
    parent_ticks = int(owner['parent_owner']['created_filetime_100ns'])
    shim_ticks = int(token_before['created_filetime_100ns'])
    worker_ticks = int(owner['worker']['created_filetime_100ns'])
    predicates = dict(
        exact_parent=observed['shim_ppid'] == owner['parent_owner']['pid'],
        creation_order=owner['parent_owner']['create_time'] <= observed['shim_create_time'] <= owner['worker']['create_time'],
        native_pid=type(token_before['pid']) is int and token_before['pid'] == observed['shim_pid'] == owner['os_parent_pid'],
        native_full_entry=Path(native_image).is_absolute() and bool(Path(native_image).drive)
            and os.path.normcase(native_image) == os.path.normcase(entry),
        native_creation_order=parent_ticks <= shim_ticks <= worker_ticks,
        native_handle_identity_unchanged=token_before == token_after,
        exact_owned_job=in_owned_job is True)
    return predicates



NAMESPACE_PROOF_SHA = '318537f3d176fc396ebdc8fb660ffb320e62c4fb8545f7f7168e2512da12f625'


def namespace_record_snapshot():
    path = safe(PREP/'pywin32_namespace_record01.json')
    raw = bounded(path, 65536)
    need(hashlib.sha256(raw).hexdigest() == NAMESPACE_PROOF_SHA, 'pinned local pywin32 RECORD proof')
    proof = json.loads(raw)
    need(proof['status'] == 'INSTALLED_PYWIN32_RECORD_MATCHED_NOT_WHEEL_ATTESTATION'
         and proof['version'] == '312' and proof['project_children_absent'] is True,
         'exact local RECORD proof scope')
    # Startup pywin32.pth is metadata, not a model checkpoint. The outer
    # verifies ALL15 files before/after each operation. Keep the inner's
    # checkpoint-suffix ban untouched: it hashes the other14 files only.
    startup = '.venv/Lib/site-packages/pywin32.pth'
    need(startup in proof['file_sha256'], 'startup metadata remains outer-pinned')
    expected = {name:digest for name,digest in proof['file_sha256'].items() if name != startup}
    need(len(expected) == 14, 'exact inner namespace proof population')
    observed = {name: sha(safe(ROOT/name)) for name in expected}
    need(observed == expected, 'installed namespace bytes drifted')
    namespace = safe(ROOT/proof['namespace_relative'])
    need(namespace == ROOT/'.venv/Lib/site-packages/win32/scripts'
         and not (namespace/'__init__.py').exists()
         and not (namespace/'akt').exists() and not (namespace/'research').exists(),
         'installed namespace cannot supply project children')
    return observed


def validate_scripts_namespace(packages):
    need(set(packages) == {'scripts','scripts.akt','scripts.research'}, 'exact project namespace inventory')
    for name, observation in packages.items():
        expected = [str(ROOT/Path(*name.split('.')))]
        if name == 'scripts':
            expected.append(str(ROOT/'.venv/Lib/site-packages/win32/scripts'))
        need(observation['file'] is None and observation['origin'] is None
             and observation['namespace_paths'] == observation['spec_search_paths'] == expected,
             'ROOT-first parent and exact project child namespace required')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--group', choices=('stdlib','no-torch','remaining'), required=True)
    parser.add_argument('--active-seconds', type=float, required=True)
    args = parser.parse_args()
    need(0 < args.active_seconds <= 60, 'remaining original collection budget required')
    timer = threading.Timer(args.active_seconds, lambda: os._exit(124))
    timer.daemon = True; timer.start()
    owner = worker_gate()
    import_path_before_root = list(sys.path)
    sys.path.insert(0, str(safe(ROOT)))  # Real fixed repository namespace, after GO.
    sys.path.insert(0, str(ROOT/'third_party'))
    packet_path = safe(Path(args.packet))
    raw = bounded(packet_path, 2*1024**2)
    need(hashlib.sha256(raw).hexdigest() == args.packet_sha256, 'ROOT packet SHA')
    packet = json.loads(raw)
    need(type(packet.get('schema_version')) is int and packet['schema_version'] == 1
         and packet.get('kind') == 'ROOT_FROZEN_GATE2_COLLECTION_INPUT'
         and type(packet.get('root_freeze_reference')) is str and packet['root_freeze_reference'].strip(), 'ROOT finalized packet, not template')
    need(type(packet.get('gate_build_hashes')) is dict and packet['gate_build_hashes']
         and type(packet.get('module_groups')) is list and type(packet.get('test_module_sha256')) is dict,
         'explicit source/groups/module hashes required')
    out = PREP/'gate-collection12'/args.group
    out.mkdir(parents=True, exist_ok=False)
    runtime_temp = out/'runtime-temp'
    runtime_temp.mkdir(exist_ok=False)
    temp_keys = ('TEMP','TMP','TMPDIR')
    original_temp_env = {key:os.environ.get(key) for key in temp_keys}
    original_temp_cache = tempfile.tempdir
    for key in temp_keys:
        os.environ[key] = str(runtime_temp)
    tempfile.tempdir = None
    os.chdir(ROOT)
    import psutil
    process = psutil.Process()
    need(psutil.virtual_memory().available >= 4*1024**3, '4GiB fresh admission before native imports')
    # Rooted at actual .venv shim when alive, with exact parent/ctime ancestry;
    # otherwise monitor the already Job-bound actual worker. Never kill by PID.
    leader = process
    if owner['os_parent_pid'] != owner['parent_owner']['pid']:
        try:
            shim = psutil.Process(owner['os_parent_pid'])
            # Trial02 proved psutil.exe omitted the drive; ppid/time-order passed.
            # Preserve all observed values; full native identity is authoritative.
            observed = dict(owner=owner, sys_executable=sys.executable, sys_prefix=sys.prefix,
                            expected_shim_entry=str(ROOT/'.venv/Scripts/python.exe'))
            try:
                observed.update(shim_pid=shim.pid, shim_ppid=shim.ppid(),
                                shim_create_time=shim.create_time(), shim_exe=shim.exe(),
                                actual_worker_psutil_create_time=process.create_time())
                predicates = dict(
                    exact_parent=observed['shim_ppid'] == owner['parent_owner']['pid'],
                    creation_order=owner['parent_owner']['create_time'] <= observed['shim_create_time'] <= owner['worker']['create_time'],
                    exact_venv_entry=os.path.normcase(observed['shim_exe']) == os.path.normcase(observed['expected_shim_entry']))
                observed['original_psutil_predicates'] = predicates
                # Existing helper already proved the actual worker's exact GO
                # and Job membership. Query shim with a read-only process handle:
                # never prefix a missing drive, open termination rights, or kill.
                api = Kernel()
                shim_handle = job_handle = None
                try:
                    shim_handle = api.check(api.k.OpenProcess(0x1000, False, shim.pid))
                    job_handle = api.check(api.k.OpenJobObjectW(0x0004, False, owner['job_name']))
                    token_before = api.token(shim_handle)
                    in_job = api.contains(shim_handle, job_handle)
                    token_after = api.token(shim_handle)
                    observed.update(native_shim_before=token_before, native_shim_after=token_after,
                                    native_shim_in_exact_job=in_job)
                    predicates = validate_native_shim(observed, token_before, token_after, in_job)
                    observed['required_native_predicates'] = predicates
                finally:
                    close_errors = []
                    for handle in (job_handle, shim_handle):
                        if handle is not None:
                            try:
                                api.close(handle)
                            except BaseException as error:
                                close_errors.append(dict(type=type(error).__name__, message=str(error)))
                    observed['query_handle_close_errors'] = close_errors
                    need(not close_errors, 'native identity query handles must close')
            except BaseException as error:
                observed['diagnostic_error'] = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                write(out/'shim-ancestry-observation.json', observed)
            need(all(predicates.values()), 'owned shim ancestry')
            leader = shim
        except psutil.NoSuchProcess:
            pass
    leader_created = leader.create_time()
    resources = dict(observed_minimum_available_ram_bytes=None, workers={}, samples=0,
                     pre_native_available_ram_bytes=int(psutil.virtual_memory().available))
    stop = threading.Event()
    failures = []
    memory_lock = threading.Lock()

    def sample_unlocked():
        available = int(psutil.virtual_memory().available)
        old = resources['observed_minimum_available_ram_bytes']
        resources['observed_minimum_available_ram_bytes'] = available if old is None else min(old, available)
        need(available >= 1024**3, 'system available RAM below1GiB')
        try:
            need(leader.create_time() == leader_created, 'owned leader PID/ctime changed')
            candidates = [leader, *leader.children(recursive=True)]
        except psutil.NoSuchProcess:
            candidates = [process, *process.children(recursive=True)]
        for candidate in candidates:
            try:
                created = candidate.create_time()
                need(created >= leader_created, 'owned descendant predates leader')
                info = candidate.memory_info()
                peak = max(info.rss, getattr(info, 'peak_wset', 0))
                need(peak <= 3*1024**3, 'owned process RSS/peak above3GiB')
                key = str(candidate.pid)+':'+repr(created)
                previous = resources['workers'].get(key, {}).get('observed_peak_bytes', 0)
                resources['workers'][key] = dict(pid=candidate.pid, created=created, observed_peak_bytes=max(previous, peak))
            except psutil.NoSuchProcess:
                continue
        resources['samples'] += 1

    def sample():
        with memory_lock:
            sample_unlocked()

    def watch():
        while not stop.wait(.1):
            try:
                sample()
            except BaseException as error:
                try:
                    write(out/'resource-failure.json', dict(error=str(error), resources=resources))
                finally:
                    os._exit(125)  # Outer owned Job cleans shim/worker/descendants.

    sample()
    monitor = threading.Thread(target=watch, daemon=True); monitor.start()
    counters = dict(test_body=0, model_constructor=0, backward=0, optimizer_step=0,
                    solver_fit=0, teacher_call=0, data_read=0, cuda_execution=0, runtest_protocol=0)
    commands, forbidden = [], []
    metadata_phase = [True]
    changing_profile = [False]
    system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_absolute() and '..' not in system_cmd.parts and system_cmd.is_file()
         and not system_cmd.is_symlink() and not getattr(system_cmd,'is_junction',lambda:False)(), 'actual systemcmd')

    def audit(event, values):
        # CPython emits sys.setprofile with no audit arguments. No new Python
        # thread may silently replace this guard after the reviewed install.
        if event == 'sys.setprofile' and not changing_profile[0]:
            forbidden.append(event); raise RuntimeError('collection call guard cannot be replaced')
        if event == 'subprocess.Popen':
            fixed = os.path.normcase(os.path.abspath(str(system_cmd)))
            allowed = {fixed.casefold()+' /c "ver"', '"'+fixed.casefold()+'" /c "ver"'}
            if (metadata_phase[0] and len(commands) < 3 and type(values[0]) is str and type(values[1]) is str
                    and os.path.normcase(os.path.abspath(values[0])) == fixed and values[1].strip().casefold() in allowed):
                commands.append(dict(executable=values[0], command=values[1])); return
            forbidden.append(event); raise RuntimeError('collection permits only bounded exact Windows metadata command')
        if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
            forbidden.append(event); raise RuntimeError('collection process/network denied')
        if event == 'import':
            name = str(values[0])
            root_name = name.split('.')[0]
            if ((args.group == 'stdlib' and root_name in ('numpy','pandas','torch','sklearn','scipy','duckdb'))
                    or (args.group == 'no-torch' and root_name == 'torch') or root_name in ('modal','boto3')):
                forbidden.append('import:'+name); raise RuntimeError('group purity/cloud import denied')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0], (str,bytes,os.PathLike)):
            path = os.path.normcase(os.path.abspath(os.fsdecode(values[0])))
            for rel in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl'):
                base = os.path.normcase(str(ROOT/rel))
                if path == base or path.startswith(base+os.sep):
                    forbidden.append('actual_data'); raise RuntimeError('actual/protected data forbidden during collection')
            if event == 'open' and Path(path).suffix in ('.pt','.pth','.ckpt','.safetensors'):
                forbidden.append('checkpoint'); raise RuntimeError('no checkpoint I/O during collection')
            if event == 'open' and Path(path).suffix in ('.parquet','.csv','.gz','.npy','.npz'):
                relative = None
                try:
                    relative = Path(path).relative_to(ROOT).as_posix()
                except ValueError:
                    pass
                # Native gate inventory stream-hashes declared simulator source
                # CSVs; no arbitrary data read/parse permission follows.
                allowed_sources = {os.path.normcase(str(ROOT/name)) for name in packet['gate_build_hashes']}
                if path not in allowed_sources:
                    forbidden.append('undeclared_data_file'); raise RuntimeError('no undeclared data during collection')

    sys.addaudithook(audit)
    begun = time.perf_counter()
    try:
        uname = platform.uname()
    finally:
        metadata_phase[0] = False
    native_os = dict(system=uname.system, release=uname.release, version=uname.version, machine=uname.machine,
                     commands=commands, phase_closed=True, seconds=time.perf_counter()-begun)
    # Fail before the function body, including constructor calls in decorators.
    repo_imports = {}

    def blocked_call(category, module, name):
        counters[category] += 1
        # A raising profiler can be disabled by CPython. Persist and terminate
        # before the guarded body instead of continuing collection unguarded.
        try:
            write(out/'call-guard-failure.json', dict(category=category, module=module, function=name,
                counters=counters, elapsed_seconds=max(time.perf_counter()-START,time.time()-WALL)))
        finally:
            os._exit(126)

    def profile(frame, event, arg):
        if event == 'c_call':
            if getattr(arg, '__name__', '') in ('cuda','_cuda_init','_cuda_setDevice','_cuda_synchronize'):
                blocked_call('cuda_execution', getattr(arg,'__module__',''), getattr(arg,'__name__',''))
            if (str(getattr(arg,'__module__','')).startswith(('_duckdb','duckdb'))
                    and getattr(arg,'__name__','') in ('connect','read_csv','read_parquet','query','execute')):
                blocked_call('data_read', getattr(arg,'__module__',''), getattr(arg,'__name__',''))
            return
        if event != 'call':
            return
        name = frame.f_code.co_name
        module = frame.f_globals.get('__name__', '')
        category = None
        if name == '<module>':
            path = Path(frame.f_code.co_filename)
            if (path.is_absolute() and path.is_relative_to(ROOT)
                    and not path.is_relative_to(ROOT/'.venv')
                    and path.is_file() and path.suffix == '.py'):
                relative = path.relative_to(ROOT).as_posix()
                digest = sha(safe(path))
                if relative in repo_imports and repo_imports[relative] != digest:
                    blocked_call('test_body', module, 'source changed while importing')
                repo_imports[relative] = digest
        if name.startswith('test_') and os.path.normcase(os.path.abspath(frame.f_code.co_filename)).startswith(os.path.normcase(str(ROOT/'tests'))+os.sep):
            category = 'test_body'
        elif name == '__init__' and 'self' in frame.f_locals:
            mro = type(frame.f_locals['self']).__mro__
            if any(cls.__module__ == 'torch.nn.modules.module' and cls.__name__ == 'Module' for cls in mro):
                category = 'model_constructor'
            elif module.startswith(('pyBKT.models','knowledge_tracing.akt.model','knowledge_tracing.sakt.model',
                                    'knowledge_tracing.gam_kt.original_junyi')):
                category = 'model_constructor'
        if name in ('backward','_engine_run_backward') and module.startswith('torch'):
            category = 'backward'
        elif name == 'step' and module.startswith('torch.optim'):
            category = 'optimizer_step'
        elif name in ('fit','partial_fit','fit_predict','_fit_logistic') and module.startswith(('sklearn','pyBKT','knowledge_tracing.edge_confidence')):
            category = 'solver_fit'
        elif module.startswith(('knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection')) and name.startswith('collect'):
            category = 'teacher_call'
        elif module.startswith(('pandas.io','numpy.lib._npyio','duckdb')) and name in ('read_csv','read_table','read_parquet','read_json','load','loadtxt','genfromtxt','connect'):
            category = 'data_read'
        elif module.startswith('torch.cuda') and name in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all',
                                                         'is_available','device_count','current_device','get_device_properties'):
            category = 'cuda_execution'
        if category is not None:
            blocked_call(category, module, name)

    class Collector:
        nodeids = []
        reports = []
        terminal_reporter_disabled = False
        def pytest_sessionstart(self, session):
            need(session.config.option.collectonly is True, 'collect-only option required')
            self.terminal_reporter_disabled = (session.config.pluginmanager.get_plugin('terminal') is None
                and session.config.pluginmanager.get_plugin('terminalreporter') is None)
            need(self.terminal_reporter_disabled, 'terminal reporting must be disabled; nodeids captured by Collector')
        def pytest_collectreport(self, report):
            if report.failed or report.skipped:
                self.reports.append(dict(nodeid=report.nodeid, outcome=report.outcome, message=str(report.longrepr)))
        def pytest_collection_finish(self, session):
            self.nodeids = [item.nodeid for item in session.items]
            need(len(self.nodeids) == len(set(self.nodeids)), 'duplicate collected nodeids')
        def pytest_runtest_protocol(self, item, nextitem):
            counters['runtest_protocol'] += 1
            raise RuntimeError('test execution forbidden in collection stage')

    old_profile = sys.getprofile()
    old_thread_profile = threading.getprofile()
    need(old_profile is None and old_thread_profile is None, 'unexpected preexisting profiler')
    source_before = {}
    docs_before = {}
    result = None
    rc = None
    plugin = Collector()
    try:
        changing_profile[0] = True
        sys.setprofile(profile); threading.setprofile(profile)
        changing_profile[0] = False
        refresh = load_refresh()
        source_before = refresh.gate2_build_hashes()
        expected_docs = packet['support_document_sha256']
        need(set(expected_docs) == {'docs/thesis_recovery/'+name for name in (
            '21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md','22_A0_RESEARCH_LIFECYCLE_CONTRACT.md',
            '23_TRAINING_MATRIX_ACCOUNTING_V1.md','26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md',
            'EXPERIMENT_ALLOCATION_V1.json')}, 'exact five support documents, separate from native source map')
        docs_before = {name:sha(safe(ROOT/name)) for name in expected_docs}
        need(docs_before == expected_docs, 'support document prehash')
        actual_groups = [dict(name=name, modules=modules) for name, modules in refresh.test_partition(ROOT)]
        need(source_before == packet['gate_build_hashes'] and actual_groups == packet['module_groups'], 'current canonical source/partition differs from ROOT packet')
        modules = next(group['modules'] for group in actual_groups if group['name'] == args.group)
        need(all(sha(safe(ROOT/name)) == packet['test_module_sha256'][name] for name in modules), 'module hashes')
        need(sha(safe(ROOT/packet['lock_file'])) == packet['lock_sha256'], 'Windows lock binding')
        upstream = ROOT/'artifacts/akt/dependencies/upstream'
        need(set(packet['upstream_file_sha256']) == {'akt.py','README.md','LICENSE','load_data.py'}
             and all(sha(safe(upstream/name)) == digest for name,digest in packet['upstream_file_sha256'].items()), 'upstream4local bytes')
        inventory = []
        for name in modules:
            tree = ast.parse((ROOT/name).read_bytes(), filename=name)
            statements = []
            for node in tree.body:
                visitor = ImportCalls(); visitor.visit(node)
                if visitor.calls or isinstance(node, (ast.Import, ast.ImportFrom)):
                    statements.append(dict(line=node.lineno, kind=type(node).__name__, potential_calls=visitor.calls,
                        imports=ast.unparse(node) if isinstance(node,(ast.Import,ast.ImportFrom)) else None))
            inventory.append(dict(module=name, sha256=packet['test_module_sha256'][name], top_level_inventory=statements))
        write(out/'import-time-inventory.json', dict(scope='STATIC_POTENTIAL_CALLS_NOT_DYNAMIC_SIDE_EFFECT_ATTESTATION', modules=inventory))

        def scripts_namespace_snapshot():
            packages = {}
            for name in ('scripts','scripts.akt','scripts.research'):
                module = sys.modules.get(name)
                need(module is not None, 'real scripts namespace missing')
                spec = getattr(module, '__spec__', None)
                packages[name] = dict(file=getattr(module,'__file__',None),
                    origin=None if spec is None else spec.origin,
                    namespace_paths=list(getattr(module,'__path__',())),
                    spec_search_paths=[] if spec is None else list(spec.submodule_search_locations or ()))
            return packages

        # Use the ordinary import mechanism. Do not synthesize sys.modules or
        # change test imports. Persist observations before validating origins.
        namespace_before = None
        namespace_error = None
        try:
            for name in ('scripts','scripts.akt','scripts.research'):
                importlib.import_module(name)
            namespace_before = scripts_namespace_snapshot()
        except BaseException as error:
            namespace_error = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            write(out/'scripts-namespace-before.json', dict(
                sys_path_before_ROOT=import_path_before_root, actual_sys_path=list(sys.path),
                packages=namespace_before, error=namespace_error, ROOT=str(ROOT)))
        namespace_files_before = namespace_record_snapshot()
        validate_scripts_namespace(namespace_before)
        import pytest
        with (out/'collection.log').open('x', encoding='utf-8') as log:
            from contextlib import redirect_stdout, redirect_stderr
            with redirect_stdout(log), redirect_stderr(log):
                rc = int(pytest.main([*modules,'--collect-only','-p','no:terminal','-o','addopts=','-p','no:cacheprovider',
                    '--log-file='+str(out/'pytest-file.log')], plugins=[plugin]))
        need(sys.getprofile() is profile and threading.getprofile() is profile, 'collection profiler replaced')
        namespace_after = scripts_namespace_snapshot()
        write(out/'scripts-namespace-after.json', dict(packages=namespace_after, actual_sys_path=list(sys.path)))
        need(namespace_after == namespace_before, 'scripts namespace origin changed during collection')
        validate_scripts_namespace(namespace_after)
        need(namespace_record_snapshot() == namespace_files_before, 'namespace RECORD bytes changed')
        after = refresh.gate2_build_hashes()
        docs_after = {name:sha(safe(ROOT/name)) for name in expected_docs}
        need(docs_after == docs_before, 'support document posthash')
        need(after == source_before and refresh.test_partition(ROOT) == [(g['name'],g['modules']) for g in packet['module_groups']], 'source or partition drift')
        need(sha(packet_path) == args.packet_sha256, 'packet changed')
        need(all(sha(safe(ROOT/name)) == digest for name,digest in packet['test_module_sha256'].items()), 'all module bytes changed')
        need(sha(safe(ROOT/packet['lock_file'])) == packet['lock_sha256']
             and all(sha(safe(upstream/name)) == digest for name,digest in packet['upstream_file_sha256'].items()), 'lock/upstream changed')
        node_modules = {node.split('::',1)[0] for node in plugin.nodeids}
        need(node_modules == set(modules), 'foreign or silently empty test module')
        loaded = {name: str(getattr(module,'__file__',None)) for name,module in sys.modules.copy().items()
                  if name.startswith('knowledge_tracing')}
        need(all(sha(safe(ROOT/name)) == digest for name,digest in repo_imports.items()), 'imported repo source changed')
        torch_module = sys.modules.get('torch')
        cpu_import = None if torch_module is None else dict(version=str(torch_module.__version__),
            origin=torch_module.__file__, cuda_build=torch_module.version.cuda,
            cuda_initialized=torch_module.cuda.is_initialized())
        if torch_module is not None:
            need(args.group == 'remaining' and torch_module.version.cuda is None and not torch_module.cuda.is_initialized()
                 and Path(torch_module.__file__).resolve().is_relative_to((ROOT/'.venv').resolve()), 'isolated CPU-only Torch import')
        sample()
        result = dict(status='COLLECTED_ONLY_PENDING_OUTER', group=args.group, modules=modules,
            nodeids=plugin.nodeids, collected_count=len(plugin.nodeids), collection_reports=plugin.reports,
            pytest_exit_code=rc, terminal_reporter_disabled=plugin.terminal_reporter_disabled,
            root_namespace_verified=True, scripts_namespace=namespace_after,
            namespace_record_proof_sha256=NAMESPACE_PROOF_SHA,
            forbidden_attempts=forbidden, zero_body_counters=counters,
            source_before=source_before, source_after=after, packet_sha256=args.packet_sha256,
            support_document_before=docs_before, support_document_after=docs_after,
            native_os_metadata=native_os, loaded_repo_modules=loaded,
            imported_repo_source_sha256=repo_imports, cpu_torch_import=cpu_import,
            modules_without_items=sorted(set(modules)-node_modules), resources=resources,
            elapsed_seconds=max(time.perf_counter()-START,time.time()-WALL),
            scope_vi='Collection imports execute module tops; no test-body/model/fit acceptance. Exact nodeids independent of passing. Monitoring cooperative, not hard RAM quota.')
    except BaseException as error:
        failures.append(dict(type=type(error).__name__, message=str(error)))
    finally:
        changing_profile[0] = True
        sys.setprofile(old_profile); threading.setprofile(old_thread_profile)
        changing_profile[0] = False
        stop.set(); monitor.join(timeout=.5)
        for key,value in original_temp_env.items():
            if value is None: os.environ.pop(key,None)
            else: os.environ[key] = value
        tempfile.tempdir = original_temp_cache
        temp_restored = (all(os.environ.get(key) == value for key,value in original_temp_env.items())
                         and tempfile.tempdir is original_temp_cache)
        if result is None:
            result = dict(status='REJECTED_COLLECTION', group=args.group, collected_count=len(plugin.nodeids),
                nodeids=plugin.nodeids, pytest_exit_code=rc, zero_body_counters=counters, resources=resources,
                forbidden_attempts=forbidden, source_before=source_before, collection_reports=plugin.reports)
        result.update(failures=failures, profiler_restored=sys.getprofile() is old_profile,
            owned_runtime_temp=str(runtime_temp), temporary_environment_and_cache_restored=temp_restored,
            monitor_stopped=not monitor.is_alive(), elapsed_seconds=max(time.perf_counter()-START,time.time()-WALL))
        write(out/'result.json', result)
        if max(time.perf_counter()-START,time.time()-WALL) >= args.active_seconds:
            write(out/'postwrite-rejection.json', dict(status='REJECTED_CHILD_POSTWRITE_BUDGET'))
        timer.cancel()
    accepted = (result['status'] == 'COLLECTED_ONLY_PENDING_OUTER' and rc == 0
        and plugin.nodeids and not failures and not plugin.reports and not forbidden
        and not any(counters.values()) and result['profiler_restored'] and result['monitor_stopped'] and temp_restored
        and max(time.perf_counter()-START,time.time()-WALL) < args.active_seconds)
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
