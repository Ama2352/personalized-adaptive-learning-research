"""Đo metadata trước/sau trên cùng native windows Junyi, không Torch/training."""
from dataclasses import asdict
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
from knowledge_tracing.akt.types import TrainingWindow, UnseenTarget
from knowledge_tracing.akt import research_junyi_graph as after


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_before():
    name = 'knowledge_tracing.akt._parent_rows_before_20261112'
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name('research_junyi_graph_before.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def contexts(sessions, windows):
    return {role: tuple(sessions[role].prefix_evidence(window) for window in rows)
            for role, rows in windows.items()}


def numeric_features(audit):
    observed = tuple(parent for parent in audit.parents if parent.support > 0)
    mass = sum(parent.confidence for parent in observed)
    message = sum(parent.confidence*(parent.mean_observed_correctness-.5) for parent in observed)/max(1., mass)
    support = sum(parent.support for parent in observed)
    count = len(audit.parents)
    mean = sum(parent.confidence for parent in audit.parents)/count if count else 0.
    variance = sum((parent.confidence-mean)**2 for parent in audit.parents)/count if count else 0.
    fraction = sum(parent.support > 0 for parent in audit.parents)/count if count else 0.
    return message, (support/(1.+support), mean, variance, fraction)


def payload_stats(data):
    references = tuple(row for rows in data.values() for window in rows for row in window if row is not None)
    unique_ints = {id(value): value for row in references for value in row.audit.observed_rows}
    return dict(query_dataclasses=len(references), observed_row_references=sum(len(row.audit.observed_rows) for row in references),
        observed_row_tuple_bytes=sum(sys.getsizeof(row.audit.observed_rows) for row in references),
        unique_observed_row_integer_bytes=sum(sys.getsizeof(value) for value in unique_ints.values()))


def measure(sessions, windows):
    started = time.perf_counter()
    data = contexts(sessions, windows)
    build_seconds = time.perf_counter()-started
    started = time.perf_counter(); payload_bytes = batches = 0
    digest = hashlib.sha256()
    # Cùng asdict + canonical JSON + SHA256 như Native _evidence_sha, mỗi group4windows.
    for rows in data.values():
        for start in range(0, len(rows), 4):
            payload = tuple(tuple(None if item is None else asdict(item) for item in row)
                            for row in rows[start:start+4])
            raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            digest.update(hashlib.sha256(raw).digest()); payload_bytes += len(raw); batches += 1
    hash_seconds = time.perf_counter()-started
    return dict(build_seconds=build_seconds, digest_seconds=hash_seconds,
        total_seconds=build_seconds+hash_seconds, serialized_metadata_bytes=payload_bytes,
        digest_groups=batches, aggregate_digest=digest.hexdigest(), **payload_stats(data))


def main():
    bundle = Path(__file__).parent
    original = json.loads((ROOT/'research_tracking/runs/junyi-window-cache-20261112-01/actual-bounded-result.json').read_text())
    assert all(sha(ROOT/name) == expected for name, expected in original['source_pins'].items())
    cohort = ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
    roles = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    views, encoding, learners, _ = prepare_inputs(cohort, roles,
        cohort_sha256=original['source_pins'][(cohort/'manifest.json').relative_to(ROOT).as_posix()],
        roles_sha256=original['source_pins'][roles.relative_to(ROOT).as_posix()])
    del learners
    windows = {}
    for role, count in (('train', 11833), ('selection', 1530)):
        cached = original['role_results'][role]
        admitted = JunyiWindowCacheSession(ROOT/cached['root'], views[role], encoding,
            cached['source_data_sha256'], count, cached['receipt']['manifest_sha256'])
        windows[role] = tuple(record.window if type(record) is TrainingWindow else record
            for record in admitted.iter_windows() if type(record) is not UnseenTarget)
    assert (len(windows['train']), len(windows['selection'])) == (315, 50)
    topology = ROOT/'research_tracking/runs/cpu-junyi-graph-reconstruction-20261107-01/graph.json'
    graph_payload = json.loads(topology.read_text())
    graph = PrerequisiteGraph.from_edges(graph_payload['nodes'], graph_payload['corrected_edges'])
    before = load_before()
    versions = {'before': before, 'after': after}
    conditions = {name: module.JunyiGraphCondition(encoding, graph, sha(topology))
                  for name, module in versions.items()}
    assert conditions['before'].identity != conditions['after'].identity
    sessions = {name: {role: module.JunyiGraphPhaseSession(conditions[name], view)
                      for role, view in views.items()} for name, module in versions.items()}
    left, right = contexts(sessions['before'], windows), contexts(sessions['after'], windows)
    compared = 0
    for role, role_windows in windows.items():
        for window, old_rows, new_rows in zip(role_windows, left[role], right[role]):
            for local, (old, new) in enumerate(zip(old_rows, new_rows)):
                if old is None:
                    assert new is None
                    continue
                assert tuple(asdict(parent) for parent in old.audit.parents) == tuple(asdict(parent) for parent in new.audit.parents)
                assert numeric_features(old.audit) == numeric_features(new.audit)
                names = {parent.parent for parent in new.audit.parents}
                expected = tuple(int(window.inputs.source_rows[i]) for i in range(local)
                    if encoding.native.vocabulary.values[int(window.inputs.item_ids[i])] in names)
                assert old.audit.observed_rows == tuple(int(value) for value in window.inputs.source_rows[:local])
                assert new.audit.observed_rows == expected
                compared += 1
    del left, right
    samples = []
    for iteration, order in enumerate((('before','after'),('after','before'),('before','after')), 1):
        for name in order:
            gc.collect()
            sample = dict(iteration=iteration, version=name, **measure(sessions[name], windows))
            samples.append(sample); print(json.dumps(sample), flush=True)
    medians = {name: statistics.median(sample['total_seconds'] for sample in samples if sample['version']==name)
               for name in versions}
    for phase_sessions in sessions.values():
        for session in phase_sessions.values():
            session.assert_boundary()
    assert all(sha(ROOT/name) == expected for name, expected in original['source_pins'].items())
    assert 'torch' not in sys.modules
    result = dict(status='ACTUAL_BOUNDED_PARENT_METADATA_PARITY_AND_BENCHMARK_PASS',
        physical_windows=dict(train=315, selection=50), query_parent_features_compared=compared,
        topology_nodes=len(graph.nodes), topology_edges=len(graph.edges), topology_sha256=sha(topology),
        condition_identities={name: condition.identity for name, condition in conditions.items()},
        audit_schema=after.AUDIT_SCHEMA, samples=samples, median_total_seconds=medians,
        after_over_before_wall_ratio=medians['after']/medians['before'],
        source_pins=original['source_pins'], before_source_sha256=sha(bundle/'research_junyi_graph_before.py'),
        after_source_sha256=sha(ROOT/'src/knowledge_tracing/akt/research_junyi_graph.py'),
        native_hash_source_sha256=sha(ROOT/'src/knowledge_tracing/akt/research_graph_model.py'),
        limits='Một metadata digest pass/group4, localWindows, bound cohort. Không đoTorchforward, đầyđủbatchhash hoặcGPUthroughput. Worstcase mọirowlàparent vẫn cần lưuđủrowgópstats.',
        torch_imported=False, training_performed=False, cloud_execution=False)
    with (bundle/'benchmark-result.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(medians=medians, ratio=result['after_over_before_wall_ratio'])),flush=True)


if __name__ == '__main__':
    main()
