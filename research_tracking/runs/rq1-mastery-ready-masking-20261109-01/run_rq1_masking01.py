"""ROOT-only pure9/cached masking dispatch, hai allocation tách biệt, không retry.

Cached12/owned10/worker7/cleanup2. Pure20/owned16/worker12/cleanup2.
Không gọi mô hình hoặc policy, không thay source analyzer/test đã freeze.
"""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP / 'rq1_masking_allocation01.json'
HELPER = ROOT / 'scripts/research/windows_owned_worker.py'
FORBIDDEN = ('torch', 'numpy', 'pandas', 'knowledge_tracing', 'sklearn', 'scipy')
ANALYZER = ROOT / 'scripts/research/analyze_rq1_mastery_ready_masking.py'
PURE_WORKER = PREP / 'check_rq1_masking_pure09_01.py'
PURE_INNER = PREP / 'rq1-mask-pure09-attempt01'
PURE_OUTER = PREP / 'rq1-mask-pure09-outer01'
START, WALL = time.perf_counter(), time.time()
WHOLE_CAP = 20


def need(condition, message):
    if not condition:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter() - START, time.time() - WALL)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace evidence')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no aliases')
    return path


def read(path, cap=4 * 1024**2):
    need(elapsed() < WHOLE_CAP, 'same whole clock before bounded read')
    physical(path)
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular metadata/source file')
    with path.open('rb') as stream:
        raw = stream.read(cap + 1)
    need(len(raw) <= cap and len(raw) == path.stat().st_size, 'stable bounded file bytes')
    need(elapsed() < WHOLE_CAP, 'same whole clock after bounded read')
    return raw


def sha(path):
    return hashlib.sha256(read(path)).hexdigest()


def document(path):
    return json.loads(read(path))


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    need(len(raw) <= 1024**2, 'outer metadata1MiB')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def load_definitions(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Only externally pinned stdlib module definitions.
    return module


def require_owned(receipt, owned):
    need(receipt['accepted'] is True and receipt['returncode'] == receipt['worker_returncode_before_cleanup'] == 0
         and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup'] == 0
         and receipt['popen_handle_closed'] is True and receipt['actual_worker_in_job_before_GO'] is True
         and receipt['errors'] == receipt['cleanup_errors'] == [], 'genuine successful terminal and Job0')
    for name, pin in receipt['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log') and sha(owned / name) == pin, 'actual bounded child log SHA')


def pure_admission(inner, expected_ids):
    need({p.name for p in inner.iterdir()} == {'result.json', 'unittest.log'}, 'exact two pure outputs')
    record = document(inner / 'result.json')
    expected_counts = dict(tests=9, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
    need(record['status'] == 'INNER_ACCEPTED_9_MANUFACTURED_MASKING_FIXTURES_PENDING_ROOT'
         and record['counts'] == expected_counts and record['collected_ids'] == record['started_ids']
         == record['completed_ids'] == expected_ids, 'exact9 physical IDs completed with zero F/E/S')
    need(record['source_before'] == record['source_after'] and record['worker_cap_seconds'] == 12
         and record['elapsed_before_receipt_seconds'] < 12
         and record['cold_before'] == record['cold_after'] == dict.fromkeys(FORBIDDEN, False)
         and record['audit_attempts'] == dict(forbidden_import_attempts=0, undeclared_child_attempts=0, socket_attempts=0)
         and record['native_model_calls'] == 0 and record['cached_research_inputs_opened'] is False,
         'actual cold/source/zero forbidden-route diagnostics')
    for name, pin in record['source_after'].items():
        need(sha(ROOT / name) == pin, 'actual pure source posthash')
    log = read(inner / 'unittest.log', 65536)
    lines = log.decode('utf-8').splitlines()
    need(record['log_sha256'] == hashlib.sha256(log).hexdigest() and lines[-1] == 'OK'
         and re.search(r'\bRan 9 tests\b', '\n'.join(lines)) is not None, 'actual unittest log, CRLF-safe')
    return record


def cached_admission(inner, analyzer, inputs_before):
    need({p.name for p in inner.iterdir()} == {'summary.json', 'event_flags.json', 'validation.json', 'result.json'},
         'exact four cached outputs, no failure/partial acceptance')
    files = {p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in inner.iterdir()}
    need(sum(r['bytes'] for r in files.values()) <= 8 * 1024**2, 'total cached output8MiB')
    result, validation = document(inner / 'result.json'), document(inner / 'validation.json')
    summary, events = document(inner / 'summary.json'), document(inner / 'event_flags.json')
    need(result['status'] == 'INNER_COMPLETE_PENDING_ROOT_OWNED_POSTWRITE_ACCEPTANCE'
         and result['outputs'] == {n: r for n, r in files.items() if n != 'result.json'}
         and result['worker_cap_seconds'] == 7 and result['worker_seconds'] < 7, 'inner closed output SHA/size and cap')
    need(validation['source_input_before'] == validation['source_input_after'] == inputs_before
         and all(validation[name] == count for name, count in dict(paired_keys=1080, arm_states=2160,
             exact_R_C_B_CID_keys=2160, closed_gzip_streams=18, concept_pairs=30240,
             groups=16, concept_cells=128, parent_cells=256).items())
         and validation['native_model_simulator_calls'] == validation['oracle_reads'] == validation['new_independent_N'] == 0
         and validation['own_R_membership_assumed_universal'] is False
         and validation['logged_R_order_parity_claimed'] is False, 'whole source/CRC/prefix/controller admission')
    need(summary['kind'] == 'POST_HOC_SOURCE_PREDICATE_MASKING_NOT_MASTERY_TRUTH_OR_MEDIATION'
         and summary['new_independent_N'] == 0 and type(events) is list and len(events) == 1080,
         'descriptive old population and event count')
    nodes = [r['concept_id'] for r in csv.DictReader(io.StringIO(read(ROOT / (analyzer.DATA + 'nodes.csv')).decode('utf-8-sig')))]
    edges = [(r['source'], r['target']) for r in csv.DictReader(io.StringIO(read(ROOT / (analyzer.DATA + 'edges.csv')).decode('utf-8-sig')))]
    need(summary['node_order'] == nodes and len(nodes) == len(set(nodes)) == 28
         and len(edges) == len(set(edges)) == 31, 'actual bound node/edge domain')
    indices = {n: i for i, n in enumerate(nodes)}
    indexed_edges = {(indices[p], indices[c]) for p, c in edges}
    roots = len(set(nodes) - {c for p, c in edges})
    controls = {(r['seed'], r['profile'], r['event_id']): r
                for r in document(ROOT / (analyzer.CONTROL + 'event_flags.json'))}
    expected_keys = [(s, p, str(t)) for s in analyzer.SEEDS for p in analyzer.PROFILES for t in range(120)]
    need([(r['seed'], r['profile'], r['event_id']) for r in events] == expected_keys
         and len(set(expected_keys)) == 1080, 'all keys and native prefix order, no drops/duplicates')
    for row in events:
        need(elapsed() < WHOLE_CAP, 'same whole clock during independent event checks')
        key = analyzer.event_key(row)
        control = controls[(key[0], key[1], str(key[2]))]
        codes = row['concept_codes']
        need(len(codes) == 28 and all(type(c) is str and c in {f'{i:03b}' for i in range(8)} and c != '001' for c in codes),
             'all28 concept codes and impossible001 absent')
        need(row['root_concepts'] == roots and row['all_parent_opportunities'] == 31
             and type(row['M_changed']) is bool and type(row['R_changed']) is bool
             and row['M_changed'] == any(c[0] == '1' for c in codes)
             and row['M_changed'] == control['M_changed'] and row['R_changed'] == control['R_changed']
             and row['full_R_branch'] == control['full']['R_branch']
             and row['empty_R_branch'] == control['empty']['R_branch'], 'M/R/branch reconciliation and distinct root/parent units')
        seen = set()
        for parent in row['changed_parent_opportunities']:
            edge = parent['parent_index'], parent['child_index']
            need(all(type(v) is int for v in edge) and edge in indexed_edges and edge not in seen,
                 'unique actual parent-child opportunity')
            seen.add(edge)
            need(type(parent['prior_visits']) is int and parent['prior_visits'] >= 0
                 and parent['prior_visits'] == control['past_visits'][edge[0]]
                 and all(type(parent[n]) is bool for n in ('exposure_masked', 'E_changed', 'A_changed', 'I_changed', 'F_changed')),
                 'actual prior visits and boolean fields')
            need(parent['exposure_masked'] == (parent['prior_visits'] >= 6)
                 and parent['E_changed'] is not parent['exposure_masked']
                 and parent['A_changed'] == (codes[edge[1]][1] == '1')
                 and parent['I_changed'] == (codes[edge[1]][0] == '1')
                 and parent['F_changed'] == (codes[edge[1]][2] == '1'), 'parent E vs child A/I/F without unique causal attribution')
        need(seen == {edge for edge in indexed_edges if codes[edge[0]][0] == '1'}, 'every changed-M parent opportunity retained')
    specs = [('pooled', events)]
    specs += [('profile:' + p, [r for r in events if r['profile'] == p]) for p in analyzer.PROFILES]
    specs += [('seed:' + str(s), [r for r in events if r['seed'] == s]) for s in analyzer.SEEDS]
    specs += [(f'trajectory:{s}:{p}', [r for r in events if r['seed'] == s and r['profile'] == p])
              for s in analyzer.SEEDS for p in analyzer.PROFILES]
    need([g['group'] for g in summary['groups']] == [name for name, rows in specs], 'all16 unique predetermined groups')
    for group, (name, rows) in zip(summary['groups'], specs, strict=True):
        need(elapsed() < WHOLE_CAP, 'same whole clock during all16 group checks')
        concept = Counter(code for row in rows for code in row['concept_codes'])
        parent = Counter(''.join(str(int(r[n])) for n in ('exposure_masked', 'A_changed', 'I_changed', 'F_changed'))
                         for row in rows for r in row['changed_parent_opportunities'])
        branches = Counter((r['full_R_branch'], r['empty_R_branch']) for r in rows)
        need(group['paired_events'] == len(rows) and group['paired_concept_snapshots'] == 28 * len(rows)
             and group['root_concept_snapshots'] == roots * len(rows)
             and group['all_parent_opportunities'] == 31 * len(rows)
             and group['changed_mastery_parent_opportunities'] == sum(parent.values()), 'independent group/unit denominators')
        need(group['concept_IAF_cells'] == [dict(signature=f'{i:03b}', count=concept[f'{i:03b}']) for i in range(8)]
             and group['parent_exposure_A_I_F_cells'] == [dict(signature=f'{i:04b}', count=parent[f'{i:04b}']) for i in range(16)]
             and group['R_branch_pairs'] == [dict(full=f, empty=e, count=branches[(f, e)])
                 for f in ('frontier', 'all_mastered', 'minimum_unresolved')
                 for e in ('frontier', 'all_mastered', 'minimum_unresolved')], 'independent all8/all16/all9 zero-inclusive counts')
        need(group['M_changed_events'] == sum(r['M_changed'] for r in rows)
             and group['R_changed_events'] == sum(r['R_changed'] for r in rows)
             and group['M_changed_R_same_events'] == sum(r['M_changed'] and not r['R_changed'] for r in rows), 'independent old marginals')
    need(summary['groups'][0]['M_changed_events'] == 90 and summary['groups'][0]['R_changed_events'] == 60
         and summary['groups'][0]['M_changed_R_same_events'] == 30, 'previously accepted population counts')
    return files, dict(paired_keys=1080, arm_states=2160, concept_pairs=30240, groups=16,
                       independently_recounted_concept_cells=128, independently_recounted_parent_cells=256,
                       independently_recounted_R_branch_cells=144, no_new_model_calls=True)


def main():
    global WHOLE_CAP
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('pure', 'cached'), required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--approval-reference', required=True)
    parser.add_argument('--pure-final-sha256')
    args = parser.parse_args()
    WHOLE_CAP = 20 if args.phase == 'pure' else 12
    need(Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode, 'repository .venv -B only')
    need(sha(Path(__file__).resolve()) == args.source_sha256 and sha(PACKET) == args.packet_sha256
         and args.approval_reference.strip(), 'ROOT exact external source/packet pins and operation reference')
    packet = document(PACKET)
    expected_sources = {Path(__file__).resolve(), PURE_WORKER, ANALYZER,
                        ROOT / 'tests/shared_kt/test_rq1_mastery_ready_masking.py', HELPER,
                        PREP / 'RQ1_MASTERY_READY_MASKING_SPEC01.md'}
    need(set(packet['sources']) == {p.relative_to(ROOT).as_posix() for p in expected_sources}, 'exact six reviewed source paths')
    need(packet['sources'][Path(__file__).resolve().relative_to(ROOT).as_posix()] == args.source_sha256,
         'packet binds actual outer source')
    source_before = {name: sha(ROOT / name) for name in packet['sources']}
    need(source_before == packet['sources'], 'all frozen source pins')
    caps = packet['caps'][args.phase]
    need(caps == (dict(whole_seconds=20, owned_seconds=16, worker_seconds=12, cleanup_seconds=2, finalization_seconds=2)
                  if args.phase == 'pure' else
                  dict(whole_seconds=12, owned_seconds=10, worker_seconds=7, cleanup_seconds=2, finalization_seconds=2)),
         'same finite ROOT-reviewed phase envelope')
    phase = packet['paths'][args.phase]
    inner, output, owned = (physical(ROOT / phase[name]) for name in ('inner', 'outer', 'owned'))
    need(all(path.parent == PREP and not path.exists() for path in (inner, output, owned)), 'fresh exclusive phase namespaces')
    cold_before = {name: name in sys.modules for name in FORBIDDEN}
    need(not any(cold_before.values()), 'stdlib-only outer')
    analyzer = load_definitions(ANALYZER, 'masking_outer_constants')
    pure_definitions = load_definitions(PURE_WORKER, 'masking_outer_test_ids')
    need(packet['physical_test_ids'] == list(pure_definitions.IDS), 'packet contains exact frozen nine test IDs')
    inputs_before = {}
    if args.phase == 'cached':
        need(type(args.pure_final_sha256) is str and re.fullmatch('[a-f0-9]{64}', args.pure_final_sha256)
             and sha(PURE_OUTER / 'final.json') == args.pure_final_sha256, 'ROOT pins actual pure terminal before parsing')
        pure = document(PURE_OUTER / 'final.json')
        need(pure['status'] == 'ACCEPTED_MASKING_PURE_9_FIXTURES' and pure['errors'] == []
             and pure['source_before'] == pure['source_after'] == source_before
             and pure['packet_sha256'] == args.packet_sha256
             and not (PURE_OUTER / 'postwrite-rejection.json').exists(), 'actual accepted unchanged pure9 prerequisite')
        pure_admission(PURE_INNER, packet['physical_test_ids'])
        require_owned(pure['receipt'], ROOT / packet['paths']['pure']['owned'])
        for name, record in pure['outputs'].items():
            need(sha(PURE_INNER / name) == record['sha256'] and (PURE_INNER / name).stat().st_size == record['bytes'],
                 'actual prerequisite output files unchanged')
        inputs_before = dict(analyzer.PINS)
        inputs_before[ANALYZER.relative_to(ROOT).as_posix()] = packet['sources'][ANALYZER.relative_to(ROOT).as_posix()]
        inputs_before[analyzer.TEST] = packet['sources'][analyzer.TEST]
        need(all(sha(ROOT / n) == pin for n, pin in inputs_before.items()), 'fixed cached sources pinned before metadata parse')
        run = document(ROOT / (analyzer.TRACE + 'native__worker_run.json'))
        need(len(run['completed_trajectories']) == 18, 'exact dynamic trace inventory count')
        for i, record in enumerate(run['completed_trajectories'], 1):
            inputs_before[analyzer.TRACE + f'native__trace-{i:02d}.jsonl.gz'] = record['trace_sha256']
        need(len(inputs_before) == 38 and all(sha(ROOT / n) == pin for n, pin in inputs_before.items()), 'all38 actual cached source/input pins before work')
    else:
        need(args.pure_final_sha256 is None, 'pure phase has no invented prior terminal pin')
    need(elapsed() < caps['whole_seconds'] - caps['cleanup_seconds'] - caps['finalization_seconds'], 'time remains before child launch')
    output.mkdir()
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    import windows_owned_worker as helper
    import psutil
    need(psutil.virtual_memory().available >= 512 * 1024**2, 'prelaunch available RAM512MiB, not a measured peak claim')
    worker = PURE_WORKER if args.phase == 'pure' else ANALYZER
    worker_sha = packet['sources'][worker.relative_to(ROOT).as_posix()]
    argv = ['--source-sha256', worker_sha]
    if args.phase == 'cached':
        argv += ['--test-sha256', packet['sources'][analyzer.TEST], '--output-name', inner.name]
    environment = {n: os.environ.get(n) for n in ('CUDA_VISIBLE_DEVICES', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}
    receipt, errors, files, proof, inputs_after = None, [], {}, None, {}
    try:
        os.environ.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        allowance = min(caps['owned_seconds'], caps['whole_seconds'] - elapsed() - caps['finalization_seconds'])
        need(allowance > caps['cleanup_seconds'], 'same clock and cleanup allowance')
        receipt = helper.run_owned(worker, argv, owned, expected_worker_sha256=worker_sha,
            approval_reference=args.approval_reference, max_seconds=allowance,
            cleanup_reserve_seconds=caps['cleanup_seconds'], max_output_bytes=65536)
        if owned.is_dir():
            write(owned / 'receipt.json', receipt)
        require_owned(receipt, owned)
        if args.phase == 'pure':
            record = pure_admission(inner, packet['physical_test_ids'])
            files = {p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in inner.iterdir()}
            proof = dict(counts=record['counts'], physical_test_ids=record['completed_ids'], native_model_calls=0)
        else:
            files, proof = cached_admission(inner, analyzer, inputs_before)
            inputs_after = {n: sha(ROOT / n) for n in inputs_before}
            need(inputs_after == inputs_before, 'all38 source/input hashes after cached operation')
        need({n: sha(ROOT / n) for n in source_before} == source_before
             and sha(PACKET) == args.packet_sha256, 'source/packet posthash')
        if args.phase == 'cached':
            need(sha(PURE_OUTER / 'final.json') == args.pure_final_sha256, 'actual prerequisite terminal unchanged')
        need(not any(n in sys.modules for n in FORBIDDEN) and elapsed() < caps['whole_seconds'], 'cold stdlib and whole deadline')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    finally:
        for name, value in environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    restored = all(os.environ.get(n) == value for n, value in environment.items())
    source_after = {}
    try:
        source_after = {name: sha(ROOT / name) for name in source_before}
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error), phase='terminal_source_postcheck'))
    if source_after != source_before or not restored or elapsed() >= caps['whole_seconds']:
        errors.append(dict(type='TerminalSourceEnvironmentBudget', message='source/env/whole deadline rejected'))
    status = 'ACCEPTED_MASKING_PURE_9_FIXTURES' if args.phase == 'pure' else 'ACCEPTED_CACHED_MASTERY_READY_MASKING'
    accepted = not errors
    final = dict(status=status if accepted else 'REJECTED_KEEP_PARTIAL_NO_RETRY', phase=args.phase,
        errors=errors, receipt=receipt, source_before=source_before, source_after=source_after,
        input_before=inputs_before, input_after=inputs_after, outputs=files, independent_output_proof=proof,
        packet_sha256=args.packet_sha256, caps=caps, environment_restored=restored,
        prerequisite_pure_final_sha256=args.pure_final_sha256,
        cold_before=cold_before, cold_after={n: n in sys.modules for n in FORBIDDEN},
        elapsed_before_final_seconds=elapsed(), automatic_retry=False,
        native_model_calls=0, native_zero_scope='No scientific module imports or model/policy entrypoints in this operation',
        resource_scope='Bounded bytes/time and prelaunch RAM only, no continuous RSS peak certificate')
    write(output / 'final.json', final)
    if elapsed() >= caps['whole_seconds']:
        accepted = False
        write(output / 'postwrite-rejection.json', dict(status='REJECTED_AFTER_FINALWRITE', elapsed_seconds=elapsed()))
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_KEEP_PARTIAL_NO_RETRY',
                          elapsed_seconds=elapsed(), phase=args.phase, errors=errors)))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
