"""Root tính lại trực tiếp từ native snapshots, không dùng analyzer/helper của nó."""
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
start = time.perf_counter()
outer = json.loads((PREP / 'rq1-mask-cached-outer01/final.json').read_bytes())
assert outer['status'] == 'ACCEPTED_CACHED_MASTERY_READY_MASKING'
assert outer['receipt']['job_active_after_cleanup'] == 0 and outer['errors'] == []
assert outer['input_before'] == outer['input_after'] and len(outer['input_before']) == 38
pins = outer['input_before'] | outer['source_before']
for name, digest in pins.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
data = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs'
with (data / 'nodes.csv').open(encoding='utf-8-sig', newline='') as stream:
    nodes = [row['concept_id'] for row in csv.DictReader(stream)]
with (data / 'edges.csv').open(encoding='utf-8-sig', newline='') as stream:
    edges = [(row['source'], row['target']) for row in csv.DictReader(stream)]
indices = {node: i for i, node in enumerate(nodes)}
parents = {node: [] for node in nodes}
children = {node: [] for node in nodes}
for parent, child in edges:
    parents[child].append(parent)
    children[parent].append(child)
assert len(nodes) == 28 and len(edges) == 31
control_path = ROOT / 'research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/event_flags.json'
controls = {(row['seed'], row['profile'], int(row['event_id'])): row
            for row in json.loads(control_path.read_bytes())}
events = json.loads((PREP / 'rq1-mastery-ready-masking-attempt01/event_flags.json').read_bytes())
snapshots = {}
trace_paths = [ROOT / name for name in pins if '/native__trace-' in name]
assert len(trace_paths) == 18
for path in trace_paths:
    count = 0
    with gzip.open(path, 'rb') as stream:
        for raw in stream:
            assert time.perf_counter() - start < 15
            row = json.loads(raw)
            count += 1
            state = row['native_state']
            assert len(state) == 28
            mastered = {}
            for node, values in zip(nodes, state, strict=True):
                theta, pi, theta_gate, pi_gate, native_m = values
                assert all(type(value) is bool for value in (theta_gate, pi_gate, native_m))
                assert theta_gate == (theta >= 1250) and pi_gate == (pi <= .55)
                assert native_m == (theta_gate and pi_gate)
                mastered[node] = native_m
            key = row['variant'], row['seed'], row['profile'], int(row['event_id'])
            assert key not in snapshots
            snapshots[key] = mastered
    assert count == 120
assert len(snapshots) == 2160

concept_cells, parent_categories, event_reasons = Counter(), Counter(), []
own_prerequisite_blocked = 0
visits = {}
for event in events:
    key = event['seed'], event['profile'], int(event['event_id'])
    group_key = key[:2]
    history = visits.setdefault(group_key, dict.fromkeys(nodes, 0))
    control = controls[key]
    assert control['past_visits'] == [history[node] for node in nodes]
    full = snapshots[('graph_package', *key)]
    empty = snapshots[('empty_graph_package', *key)]
    frames = []
    for mastery, label in ((full, 'full'), (empty, 'empty')):
        frame = {node: (not mastery[node], all(mastery[parent] or history[parent] >= 6
                 for parent in parents[node])) for node in nodes}
        frames.append(frame)
        ready = {indices[node] for node, (include, eligible) in frame.items() if include and eligible}
        assert control[label]['R_branch'] == 'frontier' and set(control[label]['R']) == ready
    codes = []
    for node in nodes:
        fi, fa = frames[0][node]
        ei, ea = frames[1][node]
        codes.append(f'{int(fi != ei)}{int(fa != ea)}{int((fi and fa) != (ei and ea))}')
    assert codes == event['concept_codes']
    concept_cells.update(codes)
    changed = [node for node in nodes if full[node] != empty[node]]
    assert len(changed) in (0, 1)
    if changed:
        node = changed[0]
        assert frames[0][node][1] is False and frames[1][node][1] is False
        own_prerequisite_blocked += 1
    expected_opportunities = []
    for parent, child in edges:
        if full[parent] == empty[parent]:
            continue
        fi, fa = frames[0][child]
        ei, ea = frames[1][child]
        opportunity = dict(parent_index=indices[parent], child_index=indices[child], prior_visits=history[parent],
            exposure_masked=history[parent] >= 6,
            E_changed=(full[parent] or history[parent] >= 6) != (empty[parent] or history[parent] >= 6),
            A_changed=fa != ea, I_changed=fi != ei, F_changed=(fi and fa) != (ei and ea))
        expected_opportunities.append(opportunity)
        if opportunity['exposure_masked']:
            category = 'exposure'
        elif not opportunity['A_changed']:
            category = 'other_prerequisite_blocks'
        elif not opportunity['F_changed']:
            assert full[child] is True and empty[child] is True
            category = 'child_already_mastered'
        else:
            category = 'readiness_changes'
        parent_categories[category] += 1
    sort_key = lambda row: (row['parent_index'], row['child_index'])
    assert sorted(expected_opportunities, key=sort_key) == sorted(event['changed_parent_opportunities'], key=sort_key)
    if event['M_changed'] and not event['R_changed']:
        node = changed[0]
        child = None if not children[node] else children[node][0]
        child_mastered = exposure = None
        if child is None:
            reason = 'no_direct_child_and_own_prerequisites_blocked'
        else:
            assert len(children[node]) == 1
            child_mastered = full[child] and empty[child]
            exposure = history[node] >= 6
            if child_mastered and exposure:
                reason = 'child_mastered_and_exposure'
            elif child_mastered:
                reason = 'child_mastered_without_exposure'
            elif exposure:
                reason = 'exposure_without_child_mastered'
            else:
                reason = 'other_parent_block'
        event_reasons.append(dict(seed=key[0], profile=key[1], event_id=key[2],
            changed_concept=node, child=child, child_mastered_both=child_mastered,
            exposure_exception=exposure, prior_visits=history[node], reason=reason))
    history[control['query']['concept']] += 1
assert len(events) == 1080 and own_prerequisite_blocked == 90
assert parent_categories == dict(exposure=4, other_prerequisite_blocks=20,
                                 child_already_mastered=44, readiness_changes=80)
reasons = Counter(row['reason'] for row in event_reasons)
assert sum(reasons.values()) == 30
assert len(event_reasons) == 30 and {row['profile'] for row in event_reasons} == {'PG'}
for name, digest in pins.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
assert not any(name in sys.modules for name in ('torch', 'numpy', 'pandas', 'knowledge_tracing'))
proof = dict(status='INDEPENDENT_NATIVE_SNAPSHOT_PREDICATE_RECOUNT_PASS', inputs=len(pins),
    gzip_crc_streams=18, native_states=2160, paired_events=1080, paired_concepts=30240,
    own_changed_concept_blocked_by_prerequisites=90, concept_cells=dict(concept_cells),
    changed_parent_opportunities=148, parent_categories=dict(parent_categories),
    M_changed_R_same_events=30, event_reason_counts=dict(reasons), event_reasons=event_reasons,
    nonexclusive_predicate_counts=dict(
        child_mastered_both=sum(row['child_mastered_both'] is True for row in event_reasons),
        exposure_exception=sum(row['exposure_exception'] is True for row in event_reasons),
        both=sum(row['child_mastered_both'] is True and row['exposure_exception'] is True for row in event_reasons)),
    source_before_after_equal=True, input_sha256=pins, scientific_modules_absent=True,
    new_independent_N=0, elapsed_seconds=time.perf_counter() - start, cap_seconds=15,
    interpretation_vi='Phân rã Boolean trên snapshots cũ, chưa đánh giá mastery truth hoặc lợi ích học tập.')
with (PREP / 'masking_independent_native_recount02.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(proof, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({key: value for key, value in proof.items() if key not in ('event_reasons', 'input_sha256')}))
