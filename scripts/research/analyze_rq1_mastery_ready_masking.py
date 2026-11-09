"""Hậu kiểm cached I/E/A/F và readiness; không mô hình, oracle hoặc policy mới.

Main chỉ chạy trong owned worker sau ROOT review. Các helpers thuần không đọc
artifact khi import. C/B là source-reconstructed, không phải trường logged mới.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / 'artifacts/akt/local-tests/akt-research-runner-20261108-01'
OLD = 'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01/'
TRACE = 'research_tracking/runs/rq1-prediction-mastery-trace-20261109-01/'
CONTROL = 'research_tracking/runs/rq1-fixed-controller-candidates-20261109-01/'
DATA = 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/'
JOIN = 'scripts/research/analyze_rq1_cross_ready.py'
SPEC = 'artifacts/akt/local-tests/akt-research-runner-20261108-01/RQ1_MASTERY_READY_MASKING_SPEC01.md'
TEST = 'tests/shared_kt/test_rq1_mastery_ready_masking.py'
SEEDS = (20000, 20001, 20002)
PROFILES = ('PG', 'PY', 'PYH')
VARIANTS = ('graph_package', 'empty_graph_package')
PINS = {
    TRACE + 'manifest.json': 'a45099f30ab6d4e239275fae6e40cf174b2dcac615fcb55a6e2b9d79f0c35ae3',
    TRACE + 'native__worker_run.json': '891a69a3546599782e530d04c3fa29b53fd832f130399404fe159a5fcab2b178',
    TRACE + 'native_outer__final.json': '81cf9dd9df724338d6c8d57e01be16b5d2120d27b9730c186b5eb539803e4594',
    TRACE + 'analyze_prediction_mastery_trace01.py': '52370bcc27a0b7ca072d2182b7e2e0f519d21e2113aa7057378eeb76199ade27',
    CONTROL + 'manifest.json': 'cf1861ddc02105af92b64e4356ca2a816c55940e50e82415523092f27999665a',
    CONTROL + 'event_flags.json': '1cf3ba08a6d5aff1f25d1cdd91f1aefa5fdd9578a3c1c17c7625fe7a0097942b',
    CONTROL + 'analyze_fixed_controller_candidates02.py': '56630668fbfe7175f3ae3c643f4bffa2a7e53213983778875ae349c1a08cbd8f',
    OLD + 'manifest.json': '906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044',
    OLD + 'observed_legacy.jsonl.gz': 'eeef1796da63e3fb8c9c02b4af2065491a9ff744cfe276b05f78d12f90f4206d',
    OLD + 'observed_query_sidecar.jsonl.gz': '6452e88c62c4fe33b1ce759015c6ef0f1cab4c79f82d57e1a029069662564939',
    OLD + 'event_flags.json': '1cdbba3f3d66f99f87bb14d35e3f664877d246026db473b1b399a8ab6ed9d188',
    OLD + 'parity.json': '4636f1caef8d121b919922928b1f785e81d62eb4be2f378424b34424fd5e980f',
    DATA + 'nodes.csv': '6db464d1fd3df5d4215d51c9f90dc0f7e24f252517252784c80bdb5fa6291650',
    DATA + 'edges.csv': 'ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb',
    DATA + 'concept_to_chapter_map.csv': 'aa99cffb251ce6757258d2e87fe707455bc74b6b3917ead1acf48c5e96ee0a17',
    JOIN: '423968f864c84c8fc66a6678bf9351b195cc3ce47d38eb8696ddbab0ee830398',
    'scripts/research/windows_owned_worker.py': '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1',
    SPEC: '24d229ed64f6709cecf8f625bd8e7f925bb9ba99edd0a4b6ccd73907b4d53031',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def event_key(row):
    need(type(row['seed']) is int and row['seed'] in SEEDS
         and type(row['profile']) is str and row['profile'] in PROFILES
         and type(row['event_id']) is str and row['event_id'].isdigit(), 'typed in-population prefix key')
    event = int(row['event_id'])
    need(row['event_id'] == str(event) and 0 <= event < 120, 'canonical bounded event string')
    return row['seed'], row['profile'], event


def predicate_frame(nodes, parents, mastered, visits):
    """I/E/A/F chỉ là predicate frontier, chưa áp dụng returned-R fallback."""
    universe = set(nodes)
    need(len(nodes) == len(universe) > 0 and set(parents) == set(visits) == universe,
         'exact concept/parent/visit domain')
    need(set(mastered) == universe and all(type(value) is bool for value in mastered.values()),
         'explicit boolean mastery for every concept')
    need(all(type(value) is int and value >= 0 for value in visits.values()), 'past visit integers only')
    frame = {}
    for concept in nodes:
        ps = parents[concept]
        need(len(ps) == len(set(ps)) and set(ps) <= universe and concept not in ps,
             'unique in-domain parents without self edge')
        parent_eligible = {parent: mastered[parent] or visits[parent] >= 6 for parent in ps}
        include_self = not mastered[concept]
        all_parents = all(parent_eligible.values())
        frame[concept] = dict(I=include_self, E=parent_eligible, A=all_parents,
                              F=include_self and all_parents, root=not ps)
    return frame


def paired_predicates(nodes, parents, full_mastered, empty_mastered, visits):
    full = predicate_frame(nodes, parents, full_mastered, visits)
    empty = predicate_frame(nodes, parents, empty_mastered, visits)
    codes, opportunities = [], []
    for child_index, child in enumerate(nodes):
        f, e = full[child], empty[child]
        code = ''.join(str(int(f[name] != e[name])) for name in ('I', 'A', 'F'))
        need(code != '001', 'AND cannot change F while I and A both stay equal')
        codes.append(code)
        for parent in parents[child]:
            if full_mastered[parent] == empty_mastered[parent]:
                continue
            exposed = visits[parent] >= 6
            eligible_changed = f['E'][parent] != e['E'][parent]
            need(eligible_changed is not exposed, 'native M OR visits predicate identity')
            opportunities.append(dict(parent_index=nodes.index(parent), child_index=child_index,
                prior_visits=visits[parent], exposure_masked=exposed,
                E_changed=eligible_changed, A_changed=f['A'] != e['A'],
                I_changed=f['I'] != e['I'], F_changed=f['F'] != e['F']))
    return dict(concept_codes=codes, changed_parent_opportunities=opportunities,
                root_concepts=sum(full[c]['root'] for c in nodes),
                all_parent_opportunities=sum(len(parents[c]) for c in nodes))


def frontier_matches(frame, ready, branch):
    frontier = {concept for concept, row in frame.items() if row['F']}
    need(branch in ('frontier', 'all_mastered', 'minimum_unresolved'), 'known native R branch')
    if frontier:
        need(branch == 'frontier' and set(ready) == frontier, 'frontier predicates match returned R')
    else:
        all_mastered = all(not row['I'] for row in frame.values())
        expected_branch = 'all_mastered' if all_mastered else 'minimum_unresolved'
        need(branch == expected_branch, 'empty frontier keeps the genuine fallback branch')
        if all_mastered:
            need(set(ready) == set(frame), 'all-mastered fallback returns full domain')


def controller_match(actual, recorded, node_indices, exact):
    """Đối chiếu nguyên source branch/order, không ép frontier hoặc own-R membership."""
    expected = dict(R=[node_indices[c] for c in actual['R']],
                    C=[node_indices[c] for c in actual['C']],
                    B=[node_indices[c] for c in actual['B']],
                    R_branch=actual['R_branch'], C_branch=actual['C_branch'],
                    selected_index=node_indices[actual['selected']], native_key=actual['selected_key'])
    need(exact(expected, recorded), 'all source R/C/B/CID/key/branch fields must match admitted cache')


def summary_group(events, name):
    concepts = Counter(code for event in events for code in event['concept_codes'])
    parents = Counter(''.join(str(int(row[key])) for key in
        ('exposure_masked', 'A_changed', 'I_changed', 'F_changed'))
        for event in events for row in event['changed_parent_opportunities'])
    branches = Counter((event['full_R_branch'], event['empty_R_branch']) for event in events)
    return dict(group=name, paired_events=len(events),
        paired_concept_snapshots=sum(len(event['concept_codes']) for event in events),
        root_concept_snapshots=sum(event['root_concepts'] for event in events),
        all_parent_opportunities=sum(event['all_parent_opportunities'] for event in events),
        changed_mastery_parent_opportunities=sum(parents.values()),
        concept_IAF_cells=[dict(signature=f'{i:03b}', count=concepts[f'{i:03b}']) for i in range(8)],
        parent_exposure_A_I_F_cells=[dict(signature=f'{i:04b}', count=parents[f'{i:04b}']) for i in range(16)],
        R_branch_pairs=[dict(full=f, empty=e, count=branches[(f, e)])
            for f in ('frontier', 'all_mastered', 'minimum_unresolved')
            for e in ('frontier', 'all_mastered', 'minimum_unresolved')],
        M_changed_events=sum(event['M_changed'] for event in events),
        R_changed_events=sum(event['R_changed'] for event in events),
        M_changed_R_same_events=sum(event['M_changed'] and not event['R_changed'] for event in events))


def main():
    started, wall = time.perf_counter(), time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--test-sha256', required=True)
    parser.add_argument('--output-name', required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode is True, 'use -B; never create bytecode beside immutable helper sources')
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()

    def audit(event, values):
        if event == 'subprocess.Popen' or event.startswith('socket.') or event in ('os.system', 'os.posix_spawn', 'os.spawn'):
            raise RuntimeError('cached analyzer denies child/network')
        if event == 'import' and str(values[0]).split('.')[0] in ('knowledge_tracing', 'numpy', 'pandas', 'torch', 'sklearn', 'scipy'):
            raise RuntimeError('cached analyzer denies native/model imports')
    sys.addaudithook(audit)
    need(not any(name in sys.modules for name in ('knowledge_tracing', 'numpy', 'pandas', 'torch', 'sklearn', 'scipy')),
         'cold stdlib-only analyzer')

    def check():
        need(max(time.perf_counter() - started, time.time() - wall) < 7, 'shared worker7s cooperative cap')

    def physical(path):
        need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace path')
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no path aliases')
        return path

    input_pins = {}

    def read(path, cap=4 * 1024**2):
        check()
        physical(path)
        need(path.is_file() and path.stat().st_size <= cap, 'bounded regular input')
        with path.open('rb') as stream:
            raw = stream.read(cap + 1)
        need(len(raw) <= cap and len(raw) == path.stat().st_size, 'stable bounded input bytes')
        check()
        return raw

    def pinned(relative, expected, cap=4 * 1024**2):
        need(type(expected) is str and len(expected) == 64 and all(c in '0123456789abcdef' for c in expected), 'SHA256 form')
        raw = read(ROOT / relative, cap)
        need(hashlib.sha256(raw).hexdigest() == expected, 'input SHA before parsing ' + relative)
        input_pins[relative] = expected
        return raw

    source = Path(__file__).resolve()
    pinned(source.relative_to(ROOT).as_posix(), args.source_sha256, 65536)
    pinned(TEST, args.test_sha256, 65536)
    raw = {name: pinned(name, pin) for name, pin in PINS.items()}

    def helpers(relative, name):
        spec = importlib.util.spec_from_file_location(name, ROOT / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # SHA-pinned stdlib definitions only; no main/native call.
        return module

    join = helpers(JOIN, 'masking_cached_join')
    control = helpers(CONTROL + 'analyze_fixed_controller_candidates02.py', 'masking_source_controller')
    mastery = helpers(TRACE + 'analyze_prediction_mastery_trace01.py', 'masking_native_predicates')
    manifests = {}
    for prefix in (OLD, TRACE, CONTROL):
        manifest = join.decode(raw[prefix + 'manifest.json'])
        need(manifest['status'] == 'completed', 'closed immutable input bundle')
        manifests[prefix] = manifest
        for name, pin in PINS.items():
            if name.startswith(prefix) and name != prefix + 'manifest.json':
                need(manifest['outputs_sha256'].get(name[len(prefix):]) == pin, 'closed manifest selected-input identity')
    native_outer = join.decode(raw[TRACE + 'native_outer__final.json'])
    run = join.decode(raw[TRACE + 'native__worker_run.json'])
    need(native_outer['status'] == 'ACCEPTED_FIXED_HISTORY_MASTERY_TRACE_ONLY' and native_outer['errors'] == []
         and native_outer['source_before'] == native_outer['source_after']
         and native_outer['worker_run_sha256'] == PINS[TRACE + 'native__worker_run.json'], 'accepted whole E4 native evidence')
    need(run['status'] == 'INNER_ALL2160_LEGACY_AND18_FINAL_FINGERPRINTS_EXACT_PENDING_ROOT'
         and run['errors'] == [] and run['legacy_rows_exact'] == 2160 and run['profiler_restored'] is True
         and run['source_input_before'] == run['source_input_after'] == native_outer['source_before']
         and len(run['completed_trajectories']) == 18, 'all2160/18 native endpoint admission')
    parity = join.decode(raw[OLD + 'parity.json'])
    need(parity['status'] == 'PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY'
         and parity['logical_event_keys'] == 1080 and parity['new_independent_N'] == 0, 'fixed-stream original parity')
    nodes, parents, chapters, chapter_coverage = control.domain(raw)
    need(nodes == run['node_order'], 'exact native28 node index order')
    indices = {concept: i for i, concept in enumerate(nodes)}
    decoded_bytes = 0

    def gzip_rows(payload, count, cap):
        nonlocal decoded_bytes
        records, size = [], 0
        with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
            while True:
                check()
                line = stream.readline(65537)
                if not line:
                    break
                size += len(line)
                decoded_bytes += len(line)
                need(len(line) <= 65536 and line.endswith(b'\n') and size <= cap
                     and decoded_bytes <= 40 * 1024**2 and len(records) < count, 'bounded decompression/complete lines')
                records.append(join.decode(line))
        need(len(records) == count, 'exact gzip population and CRC/footer')
        return records

    keys = {(s, p, t) for s in SEEDS for p in PROFILES for t in range(120)}
    legacy = gzip_rows(raw[OLD + 'observed_legacy.jsonl.gz'], 3240, 16 * 1024**2)
    sidecars = gzip_rows(raw[OLD + 'observed_query_sidecar.jsonl.gz'], 3240, 8 * 1024**2)
    paired = join.paired_events(legacy, sidecars, join.decode(raw[OLD + 'event_flags.json']),
                              expected_keys=keys, node_count=28, check=check)
    prior = {(row['seed'], row['profile'], int(row['event_id'])): row for row in paired}
    left, right = join.index_records(legacy, keys), join.index_records(sidecars, keys)
    admitted_controls = {}
    for row in join.decode(raw[CONTROL + 'event_flags.json']):
        key = event_key(row)
        need(key in keys and key not in admitted_controls, 'unique canonical controller keys')
        admitted_controls[key] = row
    need(set(admitted_controls) == keys, 'all1080 controller records, no intersection')
    snapshots = {}
    for ordinal, trajectory in enumerate(run['completed_trajectories'], 1):
        alias = TRACE + f'native__trace-{ordinal:02d}.jsonl.gz'
        need(trajectory['trace_file'] == f'trace-{ordinal:02d}.jsonl.gz' and trajectory['gzip_closed'] is True
             and trajectory['trace_records'] == trajectory['exact_legacy_rows'] == trajectory['full_preview_exact'] == 120,
             'all18 closed streams and endpoints')
        need(manifests[TRACE]['outputs_sha256'][alias[len(TRACE):]] == trajectory['trace_sha256'], 'manifest/trajectory trace SHA')
        payload = pinned(alias, trajectory['trace_sha256'])
        need(len(payload) == trajectory['trace_bytes'], 'trajectory compressed size')
        for t, row in enumerate(gzip_rows(payload, 120, 2 * 1024**2)):
            key = event_key(row)
            need(key[2] == t and type(row['variant']) is str, 'typed chronological native prefix key')
            arm_key = row['variant'], *key
            need(key in keys and row['event_id'] == str(t) and row['variant'] in VARIANTS
                 and (row['seed'], row['profile'], row['variant']) ==
                 (trajectory['seed'], trajectory['profile'], trajectory['variant']) and arm_key not in snapshots,
                 'chronological unique exact native trajectory keys')
            old, meta = left[arm_key], right[arm_key]
            need(row['phase'] == 'PRE_CURRENT_UPDATE_NO_LABEL_IN_CAPTURE'
                 and row['legacy_row_sha256'] == join.row_sha(old) == meta['legacy_row_sha256']
                 and join.exact(row['query'], meta['query']) and join.exact(row['probability'], old['probability'])
                 and join.exact(row['full_preview'], meta['preview']), 'all2160 pre-update legacy/query/P/preview identities')
            need(len(row['native_state']) == 28, 'full native state28')
            mastered = {c: mastery.gates(state)[2] for c, state in zip(nodes, row['native_state'], strict=True)}
            need({c for c, value in mastered.items() if value} == set(old['mastered']), 'all2160 M predicates match legacy')
            snapshots[arm_key] = mastered
    need(set(snapshots) == {(variant, *key) for variant in VARIANTS for key in keys}, 'all2160 arm states')
    events = []
    for seed in SEEDS:
        for profile in PROFILES:
            visits, recent, chapter = dict.fromkeys(nodes, 0), [], None
            for t in range(120):
                check()
                key = seed, profile, t
                recorded, old_flags = admitted_controls[key], prior[key]
                need(join.exact(recorded['query'], old_flags['query'])
                     and join.exact(recorded['past_visits'], [visits[c] for c in nodes])
                     and join.exact(recorded['past_recent'], [indices[c] for c in recent])
                     and join.exact(recorded['past_chapter'], chapter), 'shared past-only query bookkeeping')
                for label, variant in zip(('full', 'empty'), VARIANTS, strict=True):
                    old = left[(variant, *key)]
                    arm = control.controller(nodes, parents, chapters, set(old['mastered']), old['ready'],
                                             old['mastery'], visits, recent, chapter, old['action'])
                    controller_match(arm, recorded[label], indices, join.exact)
                    frame = predicate_frame(nodes, parents, snapshots[(variant, *key)], visits)
                    frontier_matches(frame, arm['R'], arm['R_branch'])
                measured = paired_predicates(nodes, parents, snapshots[(VARIANTS[0], *key)],
                                              snapshots[(VARIANTS[1], *key)], visits)
                need(join.exact(recorded['M_changed'], old_flags['M_event_changed'])
                     and join.exact(recorded['R_changed'], old_flags['R_event_changed']), 'old M/R event reconciliation')
                events.append(dict(seed=seed, profile=profile, event_id=str(t), **measured,
                    M_changed=recorded['M_changed'], R_changed=recorded['R_changed'],
                    full_R_branch=recorded['full']['R_branch'], empty_R_branch=recorded['empty']['R_branch']))
                chapter = control.advance_logged(visits, recent, recorded['query']['concept'], chapters)
    group_specs = [('pooled', events)]
    group_specs += [('profile:' + p, [r for r in events if r['profile'] == p]) for p in PROFILES]
    group_specs += [('seed:' + str(s), [r for r in events if r['seed'] == s]) for s in SEEDS]
    group_specs += [(f'trajectory:{s}:{p}', [r for r in events if r['seed'] == s and r['profile'] == p])
                    for s in SEEDS for p in PROFILES]
    groups = []
    for name, records in group_specs:
        check()
        groups.append(summary_group(records, name))
    pooled = groups[0]
    need(len(events) == 1080 and len(groups) == 16 and pooled['paired_concept_snapshots'] == 30240
         and pooled['M_changed_events'] == 90 and pooled['R_changed_events'] == 60
         and pooled['M_changed_R_same_events'] == 30, 'whole population and previously accepted marginals')
    need(args.output_name == 'rq1-mastery-ready-masking-attempt01', 'fixed fresh cached output namespace')
    output = physical(PREP / args.output_name)
    need(not output.exists(), 'no overwrite, retry, resume, or partial acceptance')
    check()
    output.mkdir()

    def write(name, value):
        check()
        payload = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
        need(len(payload) <= 4 * 1024**2, 'small output4MiB cap')
        with (output / name).open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        need(hashlib.sha256(read(output / name)).digest() == hashlib.sha256(payload).digest(), 'closed output readback')

    write('summary.json', dict(kind='POST_HOC_SOURCE_PREDICATE_MASKING_NOT_MASTERY_TRUTH_OR_MEDIATION',
        node_order=nodes, groups=groups, new_independent_N=0,
        units=dict(concept='one concept in a paired pre-update snapshot',
                   parent='one changed-M parent in one child prerequisite set at a paired snapshot'),
        scope='I/E/A/F reconstructed; returned-R fallback kept separate; preview not served; no calibration/causal/benefit claim'))
    write('event_flags.json', events)
    for name, pin in input_pins.items():
        need(hashlib.sha256(read(ROOT / name)).hexdigest() == pin, 'source/input unchanged after computation')
    write('validation.json', dict(paired_keys=1080, arm_states=2160, exact_R_C_B_CID_keys=2160,
        closed_gzip_streams=18, concept_pairs=30240, groups=16, concept_cells=128, parent_cells=256,
        source_input_before=input_pins, source_input_after=dict(input_pins), chapter_coverage=chapter_coverage,
        own_R_membership_assumed_universal=False, logged_R_order_parity_claimed=False,
        native_model_simulator_calls=0, oracle_reads=0, new_independent_N=0))
    hashes = {path.name: dict(sha256=hashlib.sha256(read(path)).hexdigest(), bytes=path.stat().st_size)
              for path in output.iterdir()}
    write('result.json', dict(status='INNER_COMPLETE_PENDING_ROOT_OWNED_POSTWRITE_ACCEPTANCE',
        worker_seconds=max(time.perf_counter() - started, time.time() - wall), worker_cap_seconds=7,
        owner_status=owner['status'], outputs=hashes, no_actual_native_or_scientific_population_added=True))
    check()


if __name__ == '__main__':
    main()
