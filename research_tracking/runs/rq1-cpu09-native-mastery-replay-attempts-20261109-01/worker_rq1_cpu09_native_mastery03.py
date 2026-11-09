"""Owned evaluator CPU09, native estimator replay, chưa được cấp quyền chạy."""

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
import types

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONTRACT = PREP / 'rq1_cpu09_native_mastery_contract03.json'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and ROOT.resolve() == ROOT, 'fixed physical root')
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current /= part
        need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(), 'no path alias')
    need(path.resolve() == path, 'physical source/input/output path')
    return path


def digest(path, cap=4*1024**2):
    physical(path)
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular file')
    result = hashlib.sha256()
    count = 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            count += len(block)
            need(count <= cap, 'bounded streaming hash')
            result.update(block)
    need(count == path.stat().st_size, 'stable file size')
    return result.hexdigest()


def load_source(name, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def load_pinned_project_source(name, expected, records):
    """Nạp bytes nguồn thật vào namespace thật, không gọi loader đọc PYC."""
    paths = {
        'knowledge_tracing': 'src/knowledge_tracing/__init__.py',
        'knowledge_tracing.akt': 'src/knowledge_tracing/akt/__init__.py',
        'knowledge_tracing.akt.resources': 'src/knowledge_tracing/akt/resources.py',
        'knowledge_tracing.gam_kt': 'src/knowledge_tracing/gam_kt/__init__.py',
        'knowledge_tracing.paper2_reference': 'src/knowledge_tracing/paper2_reference.py',
        'knowledge_tracing.gam_kt.simulator_pathways': 'src/knowledge_tracing/gam_kt/simulator_pathways.py',
    }
    need(name in paths and name not in sys.modules, 'reviewed fresh real project module')
    path = physical(ROOT / paths[name])
    need(path.is_file() and path.stat().st_size == expected['bytes'] <= 65536, 'bounded pinned project source')
    raw = path.read_bytes()
    need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'actual executed source bytes')
    package = path.name == '__init__.py'
    parent_name, _, child_name = name.rpartition('.')
    parent = sys.modules.get(parent_name) if parent_name else None
    parent_directory = path.parent.parent if package else path.parent
    need(not parent_name or (parent is not None and str(parent_directory) in parent.__path__
         and not hasattr(parent, child_name)), 'real parent package already source-loaded')
    spec = importlib.util.spec_from_file_location(name, path,
        submodule_search_locations=[str(path.parent)] if package else None)
    need(spec is not None and spec.origin == str(path), 'actual source module spec')
    module = importlib.util.module_from_spec(spec)
    module.__cached__ = None
    need(module.__name__ == name and module.__file__ == str(path)
         and module.__package__ == (name if package else parent_name), 'real module metadata')
    sys.modules[name] = module  # Dataclass/import lookup thấy đúng namespace khi compile.
    record = dict(module=name, source=paths[name], source_sha256=expected['sha256'], bytes=len(raw),
                  package=module.__package__, file=module.__file__, package_module=package,
                  execution='COMPILE_STARTED', project_pyc_loader_called=False)
    records.append(record)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    need(sys.modules[name] is module, 'source module retained exact identity')
    if parent is not None:
        setattr(parent, child_name, module)
    record['execution'] = 'PINNED_SOURCE_BODY_RETURNED'
    return module


def main():
    started, wall = time.perf_counter(), time.time()
    helper_path = ROOT / 'scripts/research/windows_owned_worker.py'
    need(digest(helper_path) == HELPER_SHA, 'reviewed ownership helper')
    sys.path.insert(0, str(helper_path.parent))
    from windows_owned_worker import worker_gate
    owner = worker_gate()  # Trước argparse, metadata và mọi native import.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    need(Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT / '.venv'
         and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'fixed .venv CPU context')
    need(digest(Path(__file__)) == args.source_sha256 and digest(CONTRACT) == args.contract_sha256,
         'external worker/contract byte binding')
    contract = json.loads(CONTRACT.read_bytes())
    need(contract['worker_source_sha256'] == args.source_sha256, 'contract current worker pin')
    limits = contract['limits']
    out = physical(PREP / contract['output_name'])
    need(out.parent == PREP and not out.exists(), 'exclusive output absent')
    out.mkdir()
    phase = 'source_preflight'
    prior_profile = sys.getprofile()
    need(prior_profile is None, 'do not replace an existing profiler')
    started_calls, returned_calls = Counter(), Counter()
    memory = []
    denials = []
    os_metadata = {}
    profile_installed = False
    sources = contract['source_pins']
    inputs = contract['input_pins']
    before = {}
    compiled_sources = []

    def elapsed():
        return max(time.perf_counter()-started, time.time()-wall)

    def check():
        need(math.isfinite(elapsed()) and elapsed() < limits['worker_seconds'], 'worker elapsed allocation')

    def write(name, value, check_deadline=True):
        if check_deadline:
            check()
        raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
        need(len(raw) <= limits['max_output_file_bytes'], 'bounded output')
        with (out / name).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())

    def verify_all():
        check()
        current = {}
        for name, row in {**sources, **inputs}.items():
            path = ROOT / name
            need(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'source/input byte identity')
            current[name] = row['sha256']
            check()
        need(not before or current == before, 'pre/post immutable inputs')
        return current

    try:
        before = verify_all()
        replay = load_source('cpu09_reviewed_estimator_replay', PREP / 'replay_rq1_cpu09_native_mastery01.py')
        cache = load_source('cpu09_reviewed_cache_reader', PREP / 'analyze_rq2_cached_mechanism01.py')
        base = cache.decode((PREP / 'rq2_cache_mechanism_contract01.json').read_bytes())
        accepted = cache.decode((PREP / 'rq2-cached-mechanism-native02-outer/final.json').read_bytes())
        need(accepted['status'] == 'ACCEPTED_CACHED_RQ2_SECONDARY_ANALYSIS' and accepted['errors'] == []
             and accepted['inputs_before'] == accepted['inputs_after']
             == {name: row['sha256'] for name, row in base['inputs'].items()}, 'accepted original cache lineage')
        def project(name):
            relative = 'src/' + name.replace('.', '/')
            relative += '/__init__.py' if name in ('knowledge_tracing', 'knowledge_tracing.akt', 'knowledge_tracing.gam_kt') else '.py'
            return load_pinned_project_source(name, sources[relative], compiled_sources)

        project('knowledge_tracing')
        project('knowledge_tracing.akt')
        memory_snapshot = project('knowledge_tracing.akt.resources').memory_snapshot
        sample_calls = 0

        def guard(force=False):
            nonlocal sample_calls
            check()
            sample_calls += 1
            if force or sample_calls % 64 == 0:
                sample = memory_snapshot()
                need(type(sample['process_rss_bytes']) is int and type(sample['system_available_ram_bytes']) is int,
                     'known actual RAM')
                need(max(sample['process_rss_bytes'], sample['process_peak_rss_bytes'] or 0) <= limits['max_rss_bytes']
                     and sample['system_available_ram_bytes'] >= limits['min_available_ram_bytes'], 'actual RAM allocation')
                memory.append(dict(phase=phase, elapsed_seconds=elapsed(), **sample))
                need(len(memory) <= 1000, 'bounded worker memory receipt')
            check()

        guard(True)
        metadata_source = load_source('reviewed_windows_native_metadata', PREP / 'prediction_mastery_trace_worker03.py')
        metadata_source.native_windows_metadata(check, os_metadata)
        write('native_metadata.json', os_metadata)
        allowed_reads = {os.path.normcase(str((ROOT / name).resolve())) for name in (*sources, *inputs)}
        allowed_reads.add(os.path.normcase(str(CONTRACT)))
        runtime_roots = (ROOT / '.venv/Lib/site-packages', Path(sys.base_prefix) / 'Lib')
        output_names = set(contract['expected_files']) | {'failure.json'}

        def audit(event, values):
            def deny(message, denied_path=None):
                denials.append(dict(message=message, phase=phase, path=denied_path))
                raise RuntimeError(message)
            if event == 'subprocess.Popen' or event.startswith('socket.') or event in (
                    'os.system', 'os.posix_spawn', 'os.spawn', 'os.fork', 'os.exec'):
                deny('no process/network after real metadata phase')
            if event == 'import' and str(values[0]).split('.')[0] in ('torch', 'scipy', 'sklearn', 'networkx'):
                deny('no neural/solver imports')
            if event == 'open' and not isinstance(values[0], int):
                path = Path(values[0]).absolute()
                mode = values[1] or ''
                flags = values[2] if type(values[2]) is int else 0
                writing = any(c in mode for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR))
                if writing:
                    if path.parent != out or path.name not in output_names:
                        deny('write outside exact exclusive output files', str(path))
                else:
                    resolved = path.resolve()
                    runtime_code = path.suffix.lower() in ('.py', '.pyc', '.pyd', '.dll') and any(
                        resolved.is_relative_to(root.resolve()) for root in runtime_roots)
                    owned_output = path.parent == out and path.name in output_names
                    if os.path.normcase(str(resolved)) not in allowed_reads and not runtime_code and not owned_output:
                        deny('read outside pinned inputs/runtime code', str(resolved))
            if event in ('os.remove', 'os.rename', 'os.rmdir', 'os.link', 'os.symlink', 'os.mkdir'):
                deny('no historical filesystem mutation or new directory')

        sys.addaudithook(audit)
        phase = 'native_import_and_source_loader'
        need(not any(n in sys.modules for n in ('numpy', 'pandas', 'torch')), 'fresh pre-native worker')
        import numpy as np
        import pandas as pd
        project('knowledge_tracing.gam_kt')
        load_reference = project('knowledge_tracing.paper2_reference').load_reference
        build_pathway_policy = project('knowledge_tracing.gam_kt.simulator_pathways').build_pathway_policy
        reference = load_reference()
        expected_provenance = cache.decode((ROOT / base['paths']['provenance']).read_bytes())
        need(reference['provenance'] == expected_provenance, 'actual source definitions/input provenance')
        need(reference['estimator']['MASTERY_ELO'] == replay.MASTERY_ELO == 1250.
             and len(reference['estimator']['nodes']) == 28, 'source mastery threshold/node clock binding')
        paths, grid = base['paths'], base['grid']
        cache.validate_manifest(cache.decode((ROOT / paths['manifest']).read_bytes()), base)
        questions, roots = cache.topology({name: (ROOT / paths[name]).read_bytes() for name in ('nodes', 'edges', 'questions')})
        rows = cache.trace_rows(ROOT / paths['traces'], max_compressed=limits['compressed_bytes'],
            max_uncompressed=limits['uncompressed_bytes'], max_line=limits['line_bytes'],
            max_rows=limits['trace_rows'], guard=guard)
        buckets = cache.validate_trace(rows, seeds=grid['seeds'], profiles=grid['profiles'], steps=120,
                                      questions=questions, roots=roots)
        code_names = {}
        estimator = reference['estimator']['GAMKTPolicy']
        for name in ('__init__', 'select', 'predict', 'update', '_decayed_pi'):
            code_names[getattr(estimator, name).__code__] = name
        forbidden = set()
        for namespace in ('environment', 'controller', 'estimator'):
            scope = reference[namespace]
            forbidden.update((scope['persona_base_abilities'].__code__,
                scope['LatentStudentEnvironment'].__init__.__code__, scope['LatentStudentEnvironment'].interact.__code__))

        def profile(frame, event, arg):
            if event in ('call', 'return'):
                if frame.f_code in forbidden:
                    denials.append('world/teacher/persona call')
                    raise RuntimeError('world/teacher/persona forbidden')
                name = code_names.get(frame.f_code)
                if name:
                    target = started_calls if event == 'call' else returned_calls
                    target[name] += 1
                    need(target[name] <= contract['native_call_caps'][name], 'native all-calls cap '+name)
                if event == 'call' and str(frame.f_globals.get('__name__', '')).startswith(('numpy.random', 'random')):
                    denials.append('RNG draw after loader')
                    raise RuntimeError('no replay RNG draws')
            elif event == 'c_call' and str(getattr(arg, '__module__', '')).startswith(('numpy.random', '_random')):
                denials.append('native RNG draw after loader')
                raise RuntimeError('no replay RNG draws')

        phase = 'matched_estimator_replay_before_truth'
        write('reservation.json', dict(status='RESERVED_BEFORE_ANY_ESTIMATOR', owner=owner,
              source_before=before, native_call_caps=contract['native_call_caps'],
              hardkill_counts='UNKNOWN_LE_RESERVED_UNTIL_COMPLETE', truth_to_estimator=False))
        guard(True)
        sys.setprofile(profile)
        profile_installed = True
        start = pd.Timestamp('2026-01-01', tz='UTC')

        def factory(*, graph_on):
            return build_pathway_policy(reference, signal=graph_on, parent_adaptation=graph_on, local_adaptation=False)

        def verify_before_truth():
            nonlocal phase
            need(started_calls == returned_calls == Counter(contract['native_call_caps']), 'all exact native bodies returned')
            verify_all()
            phase = 'post_parity_evaluator_truth_only'

        result = replay.replay_then_evaluate(buckets, seeds=grid['seeds'], profiles=grid['profiles'], steps=120,
            questions=questions, policy_factory=factory,
            timestamp_factory=lambda hours: start + pd.Timedelta(hours=hours), guard=guard,
            verify_after=verify_before_truth)
        sys.setprofile(prior_profile)
        profile_installed = False
        need(len(result['evaluated']) == 14400 and len(result['groups']) == 136, 'full evaluation population')
        write('parity.json', result['parity'])
        write('confusion.json', dict(groups=result['groups'], target='SOURCE_WORLD_QUERIED_CONCEPT_PREUPDATE_THETA_GE_1250',
              native_rule='STORED_THETA_GE_1250_AND_STORED_PI_TASK_LE_0.55',
              new_independent_seed_families=0, reused_seed_clusters=10, causal_arm_comparison=False))
        with (out / 'native_query_readouts.jsonl').open('xb') as stream:
            total = 0
            for row in result['evaluated']:
                raw = (replay.canonical(row) + '\n').encode()
                total += len(raw)
                need(len(raw) <= 2048 and total <= limits['max_output_file_bytes'], 'readout line/file cap')
                stream.write(raw)
                check()
            stream.flush()
            os.fsync(stream.fileno())
        after = verify_all()
        metadata_source.require_metadata_closed(os_metadata)
        guard(True)
        write('result.json', dict(status='COMPLETE_MATCHED_CPU09_MASTERY_REPLAY_PENDING_OUTER',
              elapsed_seconds=elapsed(), phase=phase, source_before=before, source_after=after,
              native_started=dict(started_calls), native_returned=dict(returned_calls),
              direct_calls=result['parity']['calls'], streams=120, queried_concept_events=14400, groups=136,
              repeated_group_row_uses=43200, reused_seed_clusters=10, new_independent_seed_families=0,
              world_teacher_calls=0, new_responses=0, neural_calls=0, fitted_model=False,
              NumPy_version=np.__version__, pandas_version=pd.__version__,
              package_origins=dict(numpy=np.__file__, pandas=pd.__file__),
              native_metadata=os_metadata, memory_samples=memory, scope_denials=denials,
              project_source_execution=compiled_sources,
              native_profile_return_scope='PROFILE_RETURN_EVENTS_INCLUDE_EXCEPTION_UNWIND_IF_ATTEMPT_FAILS',
              profiler_restored=sys.getprofile() is prior_profile))
        inventory = {path.name: dict(sha256=digest(path, limits['max_output_file_bytes']), bytes=path.stat().st_size)
                     for path in sorted(out.iterdir())}
        need(sum(row['bytes'] for row in inventory.values()) <= limits['max_total_output_bytes'], 'total output cap')
        write('output-manifest.json', dict(outputs=inventory))
        guard(True)
        return 0
    except BaseException as error:
        if profile_installed:
            sys.setprofile(prior_profile)
            profile_installed = False
        write('failure.json', dict(status='REJECTED_KEEP_ATTEMPT', phase=phase, error=repr(error),
              traceback=traceback.format_exc(limit=8), elapsed_seconds=elapsed(),
              native_started=dict(started_calls), native_returned=dict(returned_calls),
              native_profile_return_scope='PROFILE_RETURN_EVENTS_NOT_PROOF_OF_SUCCESSFUL_BODY_ON_FAILURE',
              truth_accepted=False, memory_samples=memory, denials=denials, native_metadata=os_metadata,
              project_source_execution=compiled_sources), check_deadline=False)
        raise
    finally:
        if profile_installed:
            sys.setprofile(prior_profile)


if __name__ == '__main__':
    raise SystemExit(main())
