"""Bind sáu condition từ artifact cũ; chỉ dữ liệu, không quyền train hoặc model."""
import time
START, WALL = time.perf_counter(), time.time()
import argparse
import csv
import ctypes
from ctypes import wintypes
from dataclasses import asdict, replace
import hashlib
from importlib.util import source_from_cache
import io
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP/'main60_graph_bindings02_packet.json'
OUT = PREP/'main60-graph-conditions02'
OWNED = PREP/'main60-graph-conditions02-owned'
TEMP = OWNED/'runtime-temp'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def check():
    need(elapsed() < 50., 'single worker50 deadline')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(65536):
            check(); digest.update(block)
    return digest.hexdigest()


def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)+'\n').encode()
    need(len(raw) <= 2**20, 'small data-only output')
    with (OUT/name).open('xb') as stream:
        need(stream.write(raw) == len(raw), 'complete output write')
        stream.flush(); os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def main():
    sys.path.insert(0, str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate, safe, Kernel, MAX_PROCESSES
    owner = worker_gate()
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet-sha256', required=True)
    args = parser.parse_args()
    need(sha(safe(PACKET)) == args.packet_sha256, 'external Root packet SHA')
    packet = json.loads(PACKET.read_bytes())
    pins, inputs, runtime = (packet[n] for n in ('source_pins', 'input_pins', 'runtime_pins'))
    before = {n: sha(safe(ROOT/n)) for n in pins}
    input_before = {n: sha(safe(ROOT/n)) for n in inputs}
    runtime_before = {n: sha(Path(n)) for n in runtime}
    need(before == pins and input_before == inputs and runtime_before == runtime, 'current external pins')
    need(not OUT.exists(), 'exclusive condition output')
    OUT.mkdir()
    environment_keys = ('TEMP', 'TMP', 'TMPDIR', 'COLUMNS', 'LINES')
    environment = {n: os.environ.get(n) for n in environment_keys}
    os.environ.update(TEMP=str(TEMP), TMP=str(TEMP), TMPDIR=str(TEMP), COLUMNS='80', LINES='24')
    old_path, old_cache = list(sys.path), sys.pycache_prefix
    sys.pycache_prefix = str(TEMP/'fresh-bytecode')
    phase = ['metadata']; denied = []; monitor_errors = []; metadata = {}
    stop = threading.Event(); lock = threading.RLock()
    monitor = api = job_handle = None
    error = summary = None; handle_closed = False
    resources = dict(samples=0, peak_worker_rss_bytes=0, peak_family_rss_bytes=0,
        minimum_available_ram_bytes=None, maximum_job_processes=0, exited_during_sample=0)
    allowed = {safe(ROOT/n) for n in (*pins, *inputs, *packet['artifact_read_files'])}|{PACKET}
    runtime_roots = (ROOT/'.venv', Path(sys.base_prefix).resolve())
    blocked = {'torch', 'pandas', 'sklearn', 'scipy', 'joblib', 'modal', 'boto3', 'pyBKT'}
    need(not blocked.intersection(sys.modules), 'fresh no model/solver modules')

    def owned(path):
        return path.is_relative_to(OUT) or path.is_relative_to(TEMP)

    def reject(event, detail):
        if len(denied) < 8:
            denied.append(dict(event=event, phase=phase[0], detail=detail))
        raise RuntimeError('outside bounded data-only binding scope')

    def audit(event, values):
        if event == 'import' and (str(values[0]).split('.')[0] in blocked or str(values[0]) in
                {'knowledge_tracing.edge_confidence', 'knowledge_tracing.paper2_reference',
                 'knowledge_tracing.simulator_research_collection'}):
            reject(event, str(values[0]))
        if event == 'subprocess.Popen' and phase[0] != 'metadata': reject(event, 'closed process phase')
        if event.startswith('socket.') and not (phase[0] == 'metadata' and event == 'socket.gethostname'):
            reject(event, 'network')
        if event == 'os.system' or event.startswith('os.spawn') or event in ('os.link', 'os.symlink'):
            reject(event, 'process/link')
        if event in ('open', 'os.listdir', 'os.scandir') and values and isinstance(values[0], (str, bytes, os.PathLike)):
            name = os.fsdecode(values[0]); path = Path(name).absolute().resolve()
            if 'oracle' in tuple(part.lower() for part in path.parts): reject(event, str(path))
            if any(path == ROOT/n or path.is_relative_to(ROOT/n) for n in
                   ('dataset', 'artifacts/bkt_baseline', 'venv', '.wsl', 'experiments')): reject(event, str(path))
            if event == 'open':
                mode = values[1] or ''; flags = values[2] if type(values[2]) is int else 0
                if phase[0] == 'metadata' and name == os.devnull and not flags & (os.O_CREAT|os.O_TRUNC|os.O_APPEND): return
                if any(c in mode for c in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR):
                    if not owned(path): reject(event, str(path))
                else:
                    source = None
                    if path.suffix == '.pyc':
                        try: source = Path(source_from_cache(str(path))).resolve()
                        except ValueError: pass
                    if path not in allowed and source not in allowed and not owned(path) and not any(path.is_relative_to(r) for r in runtime_roots):
                        reject(event, str(path))
        if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.rename'):
            paths = values[:2] if event == 'os.rename' else values[:1]
            if not all(owned(Path(v).absolute().resolve()) for v in paths): reject(event, 'outside own output/temp mutation')

    sys.addaudithook(audit)
    timer = threading.Timer(max(.001, 50.-elapsed()), lambda: os._exit(124)); timer.daemon = True; timer.start()
    try:
        import psutil
        process = psutil.Process(); api = Kernel()
        job_handle = api.check(api.k.OpenJobObjectW(0x0004, False, owner['job_name']))
        need(api.contains(api.k.GetCurrentProcess(), job_handle), 'actual owned Job')
        class ProcessList(ctypes.Structure):
            _fields_ = [('assigned', wintypes.DWORD), ('listed', wintypes.DWORD), ('pids', ctypes.c_size_t*MAX_PROCESSES)]

        def memory():
            with lock:
                check(); row = ProcessList()
                api.check(api.k.QueryInformationJobObject(job_handle, 3, ctypes.byref(row), ctypes.sizeof(row), None))
                pids = [int(row.pids[i]) for i in range(min(int(row.listed), MAX_PROCESSES))]
                need(0 < row.assigned == row.listed <= MAX_PROCESSES and process.pid in pids and len(pids) == len(set(pids)), 'complete Job members')
                family = 0
                for pid in pids:
                    handle = api.k.OpenProcess(0x1000, False, pid)
                    if not handle:
                        need(not psutil.pid_exists(pid), 'live Job member denied'); resources['exited_during_sample'] += 1; continue
                    try:
                        need(api.contains(handle, job_handle), 'same sampled Job')
                        token = api.token(handle); child = psutil.Process(pid)
                        need(abs(child.create_time()-token['create_time']) <= 1e-5, 'sampled PID creation identity')
                        family += int(child.memory_info().rss)
                    except psutil.NoSuchProcess: resources['exited_during_sample'] += 1
                    finally: api.close(handle)
                info = process.memory_info(); worker = max(int(info.rss), int(getattr(info, 'peak_wset', 0)))
                free = int(psutil.virtual_memory().available)
                resources['samples'] += 1; need(resources['samples'] <= 5000, 'bounded monitor samples')
                resources['peak_worker_rss_bytes'] = max(worker, resources['peak_worker_rss_bytes'])
                resources['peak_family_rss_bytes'] = max(family, resources['peak_family_rss_bytes'])
                old = resources['minimum_available_ram_bytes']
                resources['minimum_available_ram_bytes'] = free if old is None else min(old, free)
                resources['maximum_job_processes'] = max(len(pids), resources['maximum_job_processes'])
                need(worker <= 512*2**20 and family <= 512*2**20 and free >= 1536*2**20, 'Job512MiB/free1536MiB')

        memory()
        def watch():
            while not stop.wait(.1):
                try: memory()
                except BaseException as caught:
                    monitor_errors.append(dict(type=type(caught).__name__, message=str(caught)))
                    try: write('resource-failure.json', dict(errors=monitor_errors, resources=resources))
                    finally: os._exit(125)
        monitor = threading.Thread(target=watch, daemon=True); monitor.start()
        helper = ROOT/packet['metadata_helper']
        namespace = dict(__file__=str(helper), __name__='main60_real_windows_metadata_only')
        exec(compile(helper.read_bytes(), str(helper), 'exec'), namespace)
        namespace['native_windows_metadata'](check, metadata); namespace['require_metadata_closed'](metadata)
        write('windows-metadata.json', metadata); phase[0] = 'binding'
        sys.path.insert(0, str(ROOT/'src'))
        from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus
        from knowledge_tracing.simulator_bridge import identity_hash
        from knowledge_tracing.shared_kt import PrerequisiteGraph
        from knowledge_tracing.edge_confidence_artifact import Method24ArtifactRef, Method24TrainingBinding, Method24ReadLimits, load_method24_scores
        from knowledge_tracing.akt.research_graph_condition import GraphTrain80Binding, prepare_research_graph_condition, source_inventory
        from knowledge_tracing.akt.research_main_execution import MainGraphInput
        plan = json.loads((ROOT/packet['plan_file']).read_bytes())
        corpus = read_public_research_corpus(plan['corpus_id'], expected_corpus_sha256=plan['corpus_sha256'],
            expected_done_sha256=plan['corpus_done_sha256'], limits=CorpusReadLimits(**packet['corpus_read_limits']))
        roles = {role: corpus.role_data(role) for role in ('train', 'selection', 'calibration')}
        need(tuple(len(roles[r].trajectories) for r in roles) == (48, 6, 6), 'actual48/6/6 roles')
        need(tuple(roles[r].audit['audit']['targets'] for r in roles) == (10080, 1260, 1260), 'actual complete target populations')
        need(corpus.plan.identity == plan['logical_research_plan_sha256'], 'logical plan identity')
        binding = GraphTrain80Binding(corpus.corpus_id, plan['corpus_sha256'], corpus.done_sha256, corpus.plan.identity,
            roles['train'].provenance.identity, plan['train_observable_sha256'], identity_hash(corpus.bank.identity),
            *(roles[r].audit['audit']['shard_sha256'] for r in roles))
        nodes = tuple(sorted({item.concept_id for item in corpus.bank.items}))
        raw = (ROOT/packet['expert_csv']).read_bytes(); need(len(raw) <= 16384, 'bounded expert CSV')
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        need(reader.fieldnames == ['source', 'target'], 'expert header')
        edge_rows = list(reader); need(len(edge_rows) == 31 and all(set(row) == {'source', 'target'} for row in edge_rows), 'exact expert31 rows')
        edges = tuple(sorted((row['source'], row['target']) for row in edge_rows))
        expert = PrerequisiteGraph.from_edges(nodes, edges)
        need(len(expert.nodes) == 28 and expert.edges == edges and len(set(edges)) == 31, 'canonical full expert28/31')
        expert_sha = write('expert-topology.json', dict(nodes=list(expert.nodes), edges=[list(e) for e in expert.edges]))
        graph_raw = json.loads((ROOT/packet['learned_graph_file']).read_bytes())
        learned = PrerequisiteGraph.from_edges(graph_raw['nodes'], graph_raw['edges'])
        values = dict(plan['expected_training_binding'])
        for n in ('public_files_sha256', 'source_files_sha256', 'runtime_files_sha256'): values[n] = tuple(sorted(values[n].items()))
        expected = Method24TrainingBinding(**values); reference = Method24ArtifactRef(**plan['expected_artifact_ref'])
        limits = Method24ReadLimits(**plan['existing_read_limits'])
        need(limits.max_read_bytes == 160*2**20 and limits.max_wall_seconds == 20., 'unchanged per-call limits')
        loaded = {}; timings = {}
        for mode, graph in (('expert_declared', expert), ('method24_learned', learned)):
            check(); started = time.perf_counter()
            loaded[mode] = load_method24_scores(reference, expected_training=expected, bank=corpus.bank,
                declared_graph=graph, graph_binding='declared' if mode == 'expert_declared' else 'method24_learned', limits=limits)
            timings[mode] = time.perf_counter()-started
        need(loaded['method24_learned'].identity == packet['prior_learned_scores_sha256'], 'historical learned semantic identity')
        conditions = {}; output_pins = {}; sources = source_inventory()
        wire = lambda value: json.dumps(value, sort_keys=True, allow_nan=False)
        expected_wire = asdict(expected)
        for mode, graph in (('expert_declared', expert), ('method24_learned', learned)):
            for variant in ('A1', 'A2', 'A3'):
                requires = variant != 'A1' or mode == 'method24_learned'
                score = loaded[mode] if requires else None
                topology_sha = expert_sha if mode == 'expert_declared' else loaded[mode].exported_graph_sha256
                condition = prepare_research_graph_condition(variant=variant, graph_mode=mode, bank=corpus.bank,
                    nodes=graph.nodes, edges=graph.edges, train80=binding, expected_sources=sources,
                    topology_source_sha256=topology_sha, loaded_scores=score,
                    expected_method24_training=expected if requires else None, expected_scores_sha256=score.identity if requires else None)
                name = variant+('_EXPERT' if mode == 'expert_declared' else '_LEARNED')
                topology_file = (OUT/'expert-topology.json').relative_to(ROOT).as_posix() if mode == 'expert_declared' else packet['learned_graph_file']
                raw_sha = expert_sha if mode == 'expert_declared' else inputs[packet['learned_graph_file']]
                main_input = MainGraphInput(topology_file, raw_sha, wire(asdict(reference)) if requires else None,
                    wire(expected_wire) if requires else None, wire(asdict(limits)) if requires else None,
                    score.identity if requires else None, condition.identity)
                need(MainGraphInput(**asdict(main_input)) == main_input, 'actual MainGraphInput wire shape')
                condition.assert_integrity()
                conditions[name] = dict(identity=condition.identity, graph_sha256=condition.graph_sha256,
                    topology_source_sha256=condition.topology_source_sha256, weights=[asdict(e) for e in condition.edge_weights],
                    confidence_kind=condition.confidence_kind, confidence_semantics=condition.confidence_semantics,
                    train80=asdict(binding), main_graph_input=asdict(main_input), authority=False, fitted_neural_weights=False)
                output_pins[name+'.json'] = write(name+'.json', conditions[name])
        need(set(conditions) == set(packet['expected_conditions']), 'exact six conditions')
        for suffix in ('EXPERT', 'LEARNED'):
            need(conditions['A2_'+suffix]['weights'] == conditions['A3_'+suffix]['weights'], 'A2/A3 identical conditional scores')
            need(all(e['operational_weight'] == 1. for e in conditions['A1_'+suffix]['weights']), 'uniform A1')
        # Wrong-corpus metadata negative uses no extra corpus read or model call.
        wrong = replace(binding, corpus_id='grade10-main-lifecycle-engineering10x84-20261109-01')
        try:
            prepare_research_graph_condition(variant='A2', graph_mode='expert_declared', bank=corpus.bank,
                nodes=expert.nodes, edges=expert.edges, train80=wrong, expected_sources=sources, topology_source_sha256=expert_sha,
                loaded_scores=loaded['expert_declared'], expected_method24_training=expected,
                expected_scores_sha256=loaded['expert_declared'].identity)
        except ValueError as caught: need('lineage mismatch: corpus_id' in str(caught), 'exact wrong-corpus rejection')
        else: raise ValueError('wrong corpus accepted')
        corpus.assert_integrity(); memory()
        summary = dict(status='SIX_DATA_ONLY_GRAPH_CONDITIONS_BOUND_NOT_NEURAL_FITS', conditions=conditions,
            output_sha256=output_pins, expert_topology_sha256=expert_sha, loaded_identities={k:v.identity for k,v in loaded.items()},
            loader_calls=2, loader_seconds=timings, max_method24_read_bytes_per_call=160*2**20,
            method24_read_bytes_aggregate_cap=320*2**20, physical_native_output_bytes=packet['physical_native_output_bytes'],
            measured_method24_read_bytes=None, public_input_bytes=corpus.input_bytes,
            graph_input_minimum_cap_bytes=160*2**20, train80_binding=asdict(binding),
            new_surrogate_fits=0, neural_model_calls=0, optimizer_calls=0, teacher_calls=0,
            wrong_corpus_rejected=True, authority=False, full_main_matrix_completed=False)
    except BaseException as caught:
        error = dict(type=type(caught).__name__, message=str(caught), phase=phase[0])
    finally:
        phase[0] = 'closed'; stop.set()
        if monitor is not None: monitor.join(timeout=2.)
        stopped = monitor is None or not monitor.is_alive()
        if job_handle is not None and stopped:
            try:
                with lock: api.close(job_handle); handle_closed = True
            except BaseException as caught:
                if error is None: error = dict(type=type(caught).__name__, message=str(caught))
        for n, value in environment.items():
            if value is None: os.environ.pop(n, None)
            else: os.environ[n] = value
        sys.path[:] = old_path; sys.pycache_prefix = old_cache
        restored = environment == {n:os.environ.get(n) for n in environment_keys} and sys.path == old_path and sys.pycache_prefix == old_cache
        after = {n:sha(ROOT/n) for n in pins}; input_after = {n:sha(ROOT/n) for n in inputs}; runtime_after = {n:sha(Path(n)) for n in runtime}
        accepted = error is None and not denied and not monitor_errors and stopped and handle_closed and restored
        accepted = accepted and before == after and input_before == input_after and runtime_before == runtime_after and not blocked.intersection(sys.modules)
        write('result.json', dict(status='SIX_MAIN60_CONDITIONS_PENDING_OUTER' if accepted else 'REJECTED_KEEP_PARTIAL',
            error=error, summary=summary, source_before=before, source_after=after, input_before=input_before, input_after=input_after,
            runtime_before=runtime_before, runtime_after=runtime_after, resources=resources, resource_scope='CURRENT_EXACT_OWNED_JOB_MEMBERS',
            denied=denied, monitor_errors=monitor_errors, monitor_stopped=stopped, job_query_handle_closed=handle_closed,
            environment_and_sys_restored=restored, scientific_modules_absent=not blocked.intersection(sys.modules),
            metadata=metadata, packet_sha256=args.packet_sha256, elapsed_seconds=elapsed()))
        if elapsed() >= 50.:
            write('postwrite-rejection.json', dict(reason='worker50 deadline')); accepted = False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
