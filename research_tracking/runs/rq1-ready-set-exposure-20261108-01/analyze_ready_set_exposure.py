"""Phân tích POST-HOC cache M→R→served; ROOT review trước mọi execution.

Không gọi simulator/policy, dùng outcome, fit calibration hoặc sinh counterfactual served.
"""
import time
START = time.perf_counter()
WALL = time.time()
import argparse
import ast
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT / 'artifacts/akt/local-tests/rq1-observability-preparation-20261108-01'
BUNDLE = ROOT / 'research_tracking/runs/rq1-closed-loop-reconstruction-20261108-02'
PLAN = ROOT / 'research_tracking/reports/rq1_ready_set_exposure_plan_20261108.md'
PINS = {
    'manifest.json': 'c8bd8f387e5101fca641098257dd5a99d67d2f838cefc3b53b7d9d55248bcb16',
    'accepted_fast__observed_metadata.jsonl.gz': '1ab8dcd5c5521c1f4055887f8d53032592a74e71949e9caaed83898c6efeb5ce',
    'simulator_input__edges.csv': 'ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb',
    'prep__closed_loop_native_source_snapshot.json': 'a080cd079742d83dfef6a78f807d17c62f58dcdff9f8b36e38cc13f4ca428ec8',
}
SEEDS = (20000, 20001, 20002)
PROFILES = ('PG', 'PY', 'PYH')
VARIANTS = ('graph_free', 'graph_package', 'empty_graph_package')
CLASSES = ('already_mastered', 'strict_mastery', 'exposure_exception', 'blocked')
BRANCHES = ('frontier', 'all_mastered_fallback', 'minimum_unresolved_fallback')
PHASES = ['before_selection', 'after_selection_bookkeeping', 'before_predict', 'after_predict',
          'before_environment_interact', 'after_environment_interact', 'legacy_written', 'before_update', 'after_update']
MIN_EXPOSURES = 6  # Recipe cố định theo Paper2 trang3; không suy/fit từ quantities.
NODE_COUNT, STEPS, ROWS = 28, 120, 3240
COMPRESSED_CAP, DECOMPRESSED_CAP, LINE_CAP = 2*1024**2, 64*1024**2, 65536


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_value(value):
    need(type(value) is str and len(value) == 64 and all(x in '0123456789abcdef' for x in value), 'SHA64 lowercase required')
    return value


def physical(path):
    absolute = path.absolute()
    need(absolute.is_relative_to(ROOT), 'path outside workspace')
    current = ROOT
    for part in absolute.relative_to(ROOT).parts:
        current /= part
        need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(), 'path alias rejected')
    need(absolute.resolve() == absolute, 'physical path required')
    return absolute


def bounded(path, cap):
    path = physical(path)
    need(path.is_file() and path.stat().st_size <= cap, 'regular input byte cap')
    with path.open('rb') as handle:
        raw = handle.read(cap+1)
    need(len(raw) <= cap and len(raw) == path.stat().st_size, 'bounded input drift')
    return raw


def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON: '+value)))


def groups(seed, profile, variant):
    return (f'trajectory:{seed}:{profile}:{variant}', f'profile:{profile}:{variant}', f'variant:{variant}', 'pooled')


def classify(mastered, visits, parents, nodes):
    classes = {}
    for cid in nodes:
        if mastered[cid]:
            label = 'already_mastered'
        elif all(mastered[p] for p in parents[cid]):
            label = 'strict_mastery'  # Roots thỏa vacuous condition; root counters xuất riêng.
        elif all(mastered[p] or visits[p] >= MIN_EXPOSURES for p in parents[cid]):
            label = 'exposure_exception'
        else:
            label = 'blocked'
        classes[cid] = label
    return classes


def ready(mastered, visits, parents, nodes):
    unmastered = [cid for cid in nodes if not mastered[cid]]
    frontier = [cid for cid in unmastered if all(mastered[p] or visits[p] >= MIN_EXPOSURES for p in parents[cid])]
    if frontier:
        return frontier, 'frontier'
    if not unmastered:
        return list(nodes), 'all_mastered_fallback'
    deficits = {cid: sum(not mastered[p] for p in parents[cid]) for cid in unmastered}
    minimum = min(deficits.values())  # Nguồn fallback KHÔNG trừ exposure-satisfied parents.
    return [cid for cid in unmastered if deficits[cid] == minimum], 'minimum_unresolved_fallback'


def analyze(rows, edge_pairs, check):
    expected = {(s,p,v,t) for s in SEEDS for p in PROFILES for v in VARIANTS for t in range(STEPS)}
    indexed, nodes = {}, None
    for row in rows:
        check()
        key = row['seed'], row['profile'], row['variant'], row['step']
        need(type(row['seed']) is int and type(row['step']) is int and key in expected and key not in indexed, 'duplicate/foreign event key')
        m = row['mastered_decisions']
        need(type(m) is dict and len(m) == NODE_COUNT and all(type(x) is str and type(y) is bool for x,y in m.items()), 'explicit M28 required')
        calls = [v for v in row['mastery_calls'] if v['direct_caller'] == 'ready_set']
        first = calls[:NODE_COUNT]
        order = [v['concept'] for v in first]
        need(len(order) == NODE_COUNT and len(set(order)) == NODE_COUNT and set(order) == set(m), 'native node order capture missing')
        need(all(type(v['mastered']) is bool and v['concept'] in m and v['mastered'] == m[v['concept']] for v in calls), 'mastery call contradiction')
        if nodes is None:
            nodes = order
        need(order == nodes and row['phases'] == PHASES and row['is_served_in_simulator'] is True
             and row['mastery_ready_capture_phase'] == 'during_selection_before_bookkeeping', 'native order/phase drift')
        need(row['prediction_capture_phase'] == 'after_selection_bookkeeping_before_environment_interact', 'P phase drift')
        for field in ('ready_set','eligible_candidates','balanced_candidates'):
            value = row[field]
            need(type(value) is list and value and len(value) == len(set(value)) and set(value) <= set(nodes), 'invalid membership list')
        need(type(row['served_tuple']) is dict and row['served_tuple']['concept'] in row['balanced_candidates']
             and set(row['balanced_candidates']) <= set(row['eligible_candidates']), 'served not in B subset C')
        indexed[key] = row
    need(set(indexed) == expected, 'all3240 events required; no intersection/subsetting')
    parents = {cid: [] for cid in nodes}
    need(len(edge_pairs) == len(set(edge_pairs)), 'duplicate controller edge')
    for source,target in edge_pairs:
        need(source in parents and target in parents and source != target, 'controller graph identity')
        parents[target].append(source)
    all_groups = [f'trajectory:{s}:{p}:{v}' for s in SEEDS for p in PROFILES for v in VARIANTS]
    all_groups += [f'profile:{p}:{v}' for p in PROFILES for v in VARIANTS] + [f'variant:{v}' for v in VARIANTS] + ['pooled']
    counters = {g: Counter() for g in all_groups}
    concept_counts = {(g,c,label): Counter() for g in all_groups for c in nodes for label in CLASSES}
    flags = []
    for seed in SEEDS:
        for profile in PROFILES:
            for variant in VARIANTS:
                visits = Counter()
                for step in range(STEPS):
                    check()
                    row = indexed[seed,profile,variant,step]; m = row['mastered_decisions']
                    need(sum(visits.values()) == step, 'prior served-count identity')
                    r, branch = ready(m,visits,parents,nodes)
                    need(r == row['ready_set'], 'STOP: native ready_set order/membership mismatch')
                    classes = classify(m,visits,parents,nodes)
                    counts = Counter(classes.values())
                    need(set(classes) == set(nodes) and sum(counts.values()) == NODE_COUNT, 'concept partition')
                    need([cid for cid in nodes if classes[cid] in ('strict_mastery','exposure_exception')] == r
                         if branch == 'frontier' else not any(classes[cid] in ('strict_mastery','exposure_exception') for cid in nodes), 'frontier partition inconsistency')
                    cid = row['served_tuple']['concept']; reason = classes[cid]
                    false_parent = sum(not m[p] for p in parents[cid])
                    satisfied_false = sum(not m[p] and visits[p] >= MIN_EXPOSURES for p in parents[cid])
                    memberships = Counter(classes[c] for c in r)
                    event = dict(seed=seed,profile=profile,variant=variant,step=step,ready_branch=branch,
                        served_concept=cid,served_class=reason,served_is_root=not parents[cid],served_in_returned_ready=cid in r,
                        served_unmastered_parents=false_parent,served_exposure_satisfied_unmastered_parents=satisfied_false,
                        ready_size=len(r),eligible_size=len(row['eligible_candidates']),balanced_size=len(row['balanced_candidates']))
                    for label in CLASSES:
                        event['concepts_'+label] = counts[label]; event['ready_'+label] = memberships[label]
                    flags.append(event)
                    for group in groups(seed,profile,variant):
                        q = counters[group];q['events'] += 1;q['branch:'+branch] += 1;q['served:'+reason] += 1
                        q['served_root'] += not parents[cid];q['served_outside_R'] += cid not in r
                        q['served_unmastered_parent_opportunities'] += false_parent
                        q['served_exposure_satisfied_unmastered_parent_opportunities'] += satisfied_false
                        for concept,label in classes.items():
                            a = concept_counts[group,concept,label];a['concept_events'] += 1
                            a['returned_ready_memberships'] += concept in r;a['served'] += concept == cid
                            q['concept:'+label] += 1;q['ready:'+label] += concept in r
                    visits[cid] += 1  # Current/future outcome không được đọc; tăng SAU current snapshot.
                need(sum(visits.values()) == STEPS, 'complete trajectory count')
    summary = []
    for group in all_groups:
        q = counters[group]
        need(sum(q['served:'+c] for c in CLASSES) == q['events'] and sum(q['branch:'+c] for c in BRANCHES) == q['events'], 'event partitions')
        need(sum(q['concept:'+c] for c in CLASSES) == NODE_COUNT*q['events'], 'concept-event denominator')
        summary.append(dict(group=group,events=q['events'],concept_events=NODE_COUNT*q['events'],
            ready_branches={c:q['branch:'+c] for c in BRANCHES},served_classes={c:q['served:'+c] for c in CLASSES},
            concept_classes={c:q['concept:'+c] for c in CLASSES},ready_membership_classes={c:q['ready:'+c] for c in CLASSES},
            served_roots=q['served_root'],served_outside_returned_ready=q['served_outside_R'],
            served_unmastered_parent_opportunities=q['served_unmastered_parent_opportunities'],
            served_exposure_satisfied_unmastered_parent_opportunities=q['served_exposure_satisfied_unmastered_parent_opportunities']))
    cells = [dict(group=g,concept=c,classification=label,**{k:concept_counts[g,c,label][k] for k in ('concept_events','returned_ready_memberships','served')})
             for g in all_groups for c in nodes for label in CLASSES]
    return summary,cells,flags,nodes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-name', required=True)
    parser.add_argument('--expected-source-sha256', required=True)
    parser.add_argument('--expected-plan-sha256', required=True)
    parser.add_argument('--max-seconds', type=float, required=True)
    args = parser.parse_args()
    need(args.max_seconds == 7.0, 'reviewed worker allocation exactly7s; owned outer10s separately')
    def check():
        need(max(time.perf_counter()-START,time.time()-WALL) <= args.max_seconds, 'cooperative analysis deadline')
    check()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()  # Trước bất kỳ scientific/native import; helper không là science acceptance.
    def audit(event, values):
        if event == 'import' and str(values[0]).split('.')[0] in ('numpy','pandas','torch','scipy','sklearn','knowledge_tracing'):
            raise RuntimeError('native/scientific import denied')
        if event == 'subprocess.Popen' or event in ('os.system','os.posix_spawn','os.spawn') or event.startswith('socket.'):
            raise RuntimeError('process/network denied')
    sys.addaudithook(audit)
    need(not any(n in sys.modules for n in ('numpy','pandas','torch','scipy','sklearn','knowledge_tracing')), 'preloaded native module')
    source = Path(__file__).resolve()
    need(source.parent == PREP and digest(bounded(source,65536)) == sha_value(args.expected_source_sha256), 'analysis source pin')
    plan_raw = bounded(PLAN,32768)
    need(digest(plan_raw) == sha_value(args.expected_plan_sha256), 'prospective plan pin')
    need(args.output_name and len(args.output_name) <= 64 and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.output_name), 'exclusive output basename')
    output = physical(PREP/args.output_name);need(not output.exists(), 'no overwrite/retry/resume')
    inputs = {}
    for name,pin in PINS.items():
        check();raw = bounded(BUNDLE/name,COMPRESSED_CAP);need(digest(raw) == pin, 'committed input pin: '+name);inputs[name] = raw
    manifest = decode(inputs['manifest.json'])
    for name,pin in PINS.items():
        if name != 'manifest.json':need(manifest['outputs_sha256'].get(name) == pin, 'manifest selected-output binding')
    snapshot = decode(inputs['prep__closed_loop_native_source_snapshot.json'])
    selector = snapshot['definitions']['CoverageAwareSelectorMixin']
    need(selector['cell'] == 11 and selector['sha256'] == 'fc616cb9d5067419950cfc4a5e0ae0c2a02afc0d78b6ae86dd72f87224f42310', 'selector source identity')
    need(digest(selector['source'].encode()) == selector['sha256'], 'selector excerpt hash')
    ast.parse(selector['source'])  # Parse only; NEVER exec/eval/import archived code.
    reader = csv.DictReader(io.StringIO(inputs['simulator_input__edges.csv'].decode('utf-8-sig')))
    need(reader.fieldnames == ['source','target'], 'edge schema');edges=[(r['source'],r['target']) for r in reader]
    rows,total = [],0
    with gzip.GzipFile(fileobj=io.BytesIO(inputs['accepted_fast__observed_metadata.jsonl.gz'])) as handle:
        while True:
            check();line=handle.readline(LINE_CAP+1)
            if not line:break  # EOF validates gzip CRC; malformed/truncated fails.
            total += len(line)
            need(len(line) <= LINE_CAP and total <= DECOMPRESSED_CAP and len(rows) < ROWS and line.endswith(b'\n'), 'decompressed population/byte/line bound')
            rows.append(decode(line))
    need(len(rows) == ROWS, 'exact3240 population')
    summary,cells,flags,nodes = analyze(rows,edges,check)
    check()
    for name,pin in PINS.items():need(digest(bounded(BUNDLE/name,COMPRESSED_CAP)) == pin, 'input changed after analysis')
    need(digest(bounded(source,65536)) == args.expected_source_sha256 and digest(bounded(PLAN,32768)) == args.expected_plan_sha256, 'source/plan drift')
    output.mkdir()  # Quantities chỉ publish SAU all3240 exact validation; no overwrite.
    def write(name,value):
        check()
        with (output/name).open('x',encoding='utf-8') as handle:
            json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')
        need((output/name).stat().st_size <= 2*1024**2, 'output byte bound')
        check()
    try:
        write('summary.json',dict(role='POST_HOC_SOURCE_LOCAL_READINESS_EXPOSURE_DESCRIPTION',new_independent_N=0,
            groups=summary,concept_cells_including_zeros=cells,assumptions=dict(min_prerequisite_exposures=6,node_order=nodes),
            limitations=['Không calibrated mastery hoặc causal mediation/learning benefit.',
                'Fallback/escape có thể chọn class blocked/mastered; không tự gọi violation.',
                'Không intervention strict-rule policy hoặc hypothetical served action.',
                'Current-source reconstruction; original a585 source missing; metadata labels/predictions được parse nhưng không dùng.']))
        check()
        with (output/'event_membership_flags.csv').open('x',encoding='utf-8',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(flags[0]));writer.writeheader()
            for row in flags:check();writer.writerow(row)
        need((output/'event_membership_flags.csv').stat().st_size <= 2*1024**2, 'CSV byte bound')
        write('validation.json',dict(status='ALL3240_SOURCE_READY_SETS_ORDER_EXACT',rows=ROWS,trajectories=27,steps_each=120,
            ready_order_exact=ROWS,strict_class_partition_concept_events=ROWS*NODE_COUNT,groups=len(summary),
            concept_cells_including_zeros=len(cells),served_in_B_subset_C_exact=ROWS,no_outcome_fields_used=True,
            node_order_source='first28native is_mastered calls direct_caller=ready_set; same on all3240rows',
            inputs_sha256=PINS,source_sha256=args.expected_source_sha256,plan_sha256=args.expected_plan_sha256,
            source_inputs_before_after_equal=True,actual_model_calls=0,optimizer_steps=0,network_calls=0,child_process_calls=0))
        check()
        write('result.json',dict(status='INNER_COMPLETE_PENDING_OWNED_OUTER_ACCEPTANCE',owned_gate_status=owner['status'],
            worker_seconds=max(time.perf_counter()-START,time.time()-WALL),worker_cap_seconds=args.max_seconds,
            outputs_sha256={p.name:digest(bounded(p,2*1024**2)) for p in output.iterdir() if p.is_file()},
            no_retry=True,full_Gate_or_RQ_acceptance=False))
        for name,pin in PINS.items():
            check();need(digest(bounded(BUNDLE/name,COMPRESSED_CAP)) == pin, 'input changed after publication')
        need(digest(bounded(source,65536)) == args.expected_source_sha256
             and digest(bounded(PLAN,32768)) == args.expected_plan_sha256, 'source/plan changed after publication')
        check()
    except BaseException as exc:
        with (output/'failure.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(status='REJECTED_NO_ACCEPTED_ANALYSIS',error_type=type(exc).__name__,error=str(exc)),handle)
        raise
    print(json.dumps(dict(status='PENDING_OUTER_RESOURCE_CLEANUP_POSTWRITE',output=output.relative_to(ROOT).as_posix(),
                         result_sha256=digest(bounded(output/'result.json',65536)))))
    check()


if __name__ == '__main__':
    main()
