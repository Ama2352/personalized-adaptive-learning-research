"""ROOT outer:90s gồm sourcepreflight/owned87/cleanup3/final3; source-only/chưa dispatch."""
import time
START = time.perf_counter()
WALL = time.time()
from pathlib import Path
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
WORKER = P/'check_cgakt_graph10_optimizer01.py'
WORKER_SHA = '88357c12c0d4ada6d6f048a2e904170936043045bac9197423ff22e9d2593a5d'
PACKET = P/'cgakt_graph10_optimizer01_allocation.json'
PACKET_SHA = 'a424c30c1b15bb9c56dbc8233e5658bb37faa19ef7edb171103415136cc0760a'
OUT = P/'cgakt-graph10-optimizer01-owned'
CHILD = P/'cgakt-graph10-optimizer01'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush()


need(not OUT.exists() and not CHILD.exists(), 'exclusive attempt already exists; no retry/overwrite')
need(sha(WORKER) == WORKER_SHA and sha(PACKET) == PACKET_SHA, 'reviewed controller/allocation bytes')
packet = json.loads(PACKET.read_bytes())
pins = packet['source_pins']
normalization = packet['local_git_provenance']['normalization_evidence']
normalization_path = P/'upstream_git_eol_preflight01.json'
need(normalization['path'] == normalization_path.relative_to(R).as_posix()
     and normalization_path.is_file() and normalization_path.stat().st_size <= 32768
     and sha(normalization_path) == normalization['sha256'], 'actual normalization probe identity')
need(len(pins) == 34 and all(sha(R/name) == digest for name, digest in pins.items()), 'source pin drift')
need(all(not (R/name).exists() for name in packet['absent_source_paths']), 'namespace source absence drift')
need(pins['scripts/research/windows_owned_worker.py'] == '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1', 'reviewed owned helper')
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import run_owned, safe, entry
entry()
safe(WORKER); safe(PACKET); safe(OUT); safe(CHILD)
import psutil
available = int(psutil.virtual_memory().available)
need(available >= 2*1024**3, 'core resource hypothesis requires2GiB available; fullGate still4GiB')
# Reserve final3s from original90s; preflight never resets the clock.
owned_seconds = min(87., 90.-elapsed()-3.)
need(owned_seconds > 3., 'insufficient original outer budget before launch')
receipt = run_owned(WORKER, [], OUT, expected_worker_sha256=WORKER_SHA,
    approval_reference='ROOT_REVIEW_GRAPH10_ONE_CASE_THREE_REAL_ADAM_STEPS_18_DUMMY_TARGETS_0CORPUS',
    max_seconds=owned_seconds, cleanup_reserve_seconds=3, max_output_bytes=32768)
write(OUT/'receipt.json', receipt)
errors = []
result, counts = None, None
try:
    result = json.loads((CHILD/'result.json').read_bytes())
    tree = ET.parse(CHILD/'junit.xml').getroot()
    counts = {key: sum(int(s.get(key, '0')) for s in tree.iter('testsuite'))
              for key in ('tests','failures','errors','skipped')}
    need(len(list(tree.iter('testcase'))) == counts['tests'], 'exact JUnit testcase population')
except BaseException as error:
    errors.append(dict(stage='child_result_or_junit', type=type(error).__name__, message=str(error)))
source_after = {}
try:
    source_after = {name: sha(R/name) for name in pins}
    need(source_after == pins and sha(WORKER) == WORKER_SHA and sha(PACKET) == PACKET_SHA, 'postrun source/controller/allocation drift')
    need(all(not (R/name).exists() for name in packet['absent_source_paths']), 'postrun namespace source absence')
    need(sha(normalization_path) == normalization['sha256'], 'normalization probe changed')
except BaseException as error:
    errors.append(dict(stage='postrun_hashes', type=type(error).__name__, message=str(error)))
accepted = False
try:
    need(not errors and result is not None, 'missing/invalid final evidence')
    need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True
         and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
         and receipt['popen_handle_closed'] is True and receipt['cleanup_errors'] == []
         and receipt['worker_sha256'] == WORKER_SHA and receipt['returncode'] == 0, 'owned worker/cleanup')
    need(counts == dict(tests=1, failures=0, errors=0, skipped=0) and result['counts'] == counts
         and result['pytest_exit_code'] == 0 and result['status'] == 'ACCEPTED_CHILD_FIXTURES_PENDING_OUTER', 'exact1test')
    need(result['native_started'] == result['native_body_returned'] == packet['expected_native_counts'], 'exact real native inventory')
    names = [case.get('name') for case in tree.iter('testcase')]
    need(len(set(names)) == 1 and set(names) == set(packet['expected_test_names'])
         and result['testcase_names'] == names, 'exact reviewed JUnit test names')
    git = result['local_git_provenance']
    need(len(git['commands']) == 10 and len({r['command'] for r in git['commands']}) == 10
         and git['git_sha256_before'] == git['git_sha256_after'] == packet['local_git_provenance']['sha256']
         and git['native_source_before'] == git['native_source_after']
         and git['original_loader_used'] is True and git['original_loader_calls'] == 1
         and git['cached_module_used'] is False, 'actual local Git provenance')
    need(git['process_environment_actual'] == packet['local_git_provenance']['process_config']
         and git['normalization_evidence_sha256_before'] == git['normalization_evidence_sha256_after'] == normalization['sha256'],
         'exact process Git normalization and actual proof binding')
    need(result['upstream_cuda_availability'] == [dict(phase='local_git_provenance', result=False)],
         'actual upstream CPU availability query')
    extra_queries = result['optimizer_cpu_availability']
    need(len(extra_queries) <= 16 and all(q['result'] is False and q['phase'] in
         ('actual_cpu_adam_constructor','actual_cpu_adam_step') and type(q['callpath']) is list for q in extra_queries),
         'actual false CPU optimizer metadata only in declared phases')
    native_paths = ('akt.py','README.md','LICENSE')
    need(git['native_source_after'] == {name: pins['artifacts/akt/dependencies/upstream/'+name] for name in native_paths},
         'pinned native source before/after')
    need(result['test_globals_exported'] is True and result['test_globals_error'] is None
         and sha(CHILD/'test-globals.json') == result['test_globals_sha256'], 'actual test globals exported before verdict')
    test = json.loads((CHILD/'test-globals.json').read_bytes())
    reservation = test['reservation']; rows = test['ledger']; attempts = test['attempts']
    need(reservation['planned_steps'] == 3 and reservation['planned_targets'] == 18
         and reservation['adapter_step_wrapper_returns'] == 3 and reservation['rollback'] is False
         and reservation['native_work_seconds_cap'] == 60, 'explicit reservation and actual wrapper returns')
    need(len(rows) == len(attempts) == 3
         and [r['phase'] for r in rows] == ['inactive_first','active_alpha0','active_after_alpha_update']
         and [r['valid_targets'] for r in rows] == [6,6,6]
         and [r['total_targets'] for r in rows] == [6,12,18], 'three actual six-target batches')
    need(all(a['status'] == 'STEP_WRAPPER_RETURNED' and a['targets_reserved'] == 6 for a in attempts)
         and len(result['target_observation']) == 3
         and sum(r['returned'] or 0 for r in result['target_observation']) == 18
         and all(r['status'] == 'WRAPPER_RETURNED' for r in result['target_observation']), 'independent actual target observer')
    graph_names = ('alpha','gate.weight','gate.bias')
    participants = {}
    for index, row in enumerate(rows):
        need(row['ordinal'] == index+1 and row['stats']['stepped'] is True
             and row['stats']['valid_targets'] == 6, 'actual step result')
        need(math.isfinite(row['clip']['live_post_norm']) and row['clip']['live_post_norm'] <= 1.00001001
             and math.isfinite(row['clip']['pre_norm']), 'live clip norm, not derived min')
        need(any(changed for name, changed in row['parameter_changed'].items() if name.startswith('backbone.')),
             'actual backbone parameter update each step')
        for name, gradient in row['gradients'].items():
            need(gradient['finite'] is True and gradient['kind'] in ('none','zero','nonzero'), 'finite gradient categories')
            participants[name] = participants.get(name, 0) + (gradient['kind'] != 'none')
            expected_step = participants[name] or None
            need(row['state_step_after'][name] == expected_step, 'per-parameter state follows participation, including zero')
    need(all(rows[0]['gradients'][name]['kind'] == 'none' and rows[0]['state_step_after'][name] is None
             and rows[0]['parameter_changed'][name] is False for name in graph_names), 'inactive None/absent state')
    need(rows[1]['gradients']['alpha']['kind'] == 'nonzero' and rows[1]['parameter_changed']['alpha'] is True
         and all(rows[1]['gradients'][name]['kind'] == 'zero' and rows[1]['parameter_changed'][name] is False
                 for name in graph_names[1:]), 'actual alpha update and zero-tensor gate first participation')
    need(all(rows[2]['gradients'][name]['kind'] == 'nonzero' and rows[2]['parameter_changed'][name] is True
             for name in graph_names[1:])
         and all(rows[2]['state_step_after'][name] == 2 for name in graph_names), 'actual second-active gate update/state2')
    need(type(result['native_work_seconds']) in (int,float) and result['native_work_seconds'] < 60, 'native work60 cap')
    need(result['source_before'] == result['source_after'] == source_after == pins
         and result['source_unchanged'] is True and result['allocation_sha256'] == result['allocation_sha256_after'] == PACKET_SHA
         and result['namespace_absence_unchanged'] is True, 'child exact input identities')
    need(result['forbidden_attempts'] == [] and result['methods_restored'] is True
         and result['runtime_restored'] is True and result['environment_restored'] is True
         and result['monitor_stopped'] is True and result['monitor_errors'] == []
         and result['original_exception'] is None and result['junit_error'] is None, 'scope/restoration guards')
    need(result['resources']['observed_peak_rss_bytes'] <= 1024**3
         and result['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'observed/cooperative memory bounds')
    need(result['torch_profile']['version'] == '2.7.1+cpu'
         and result['torch_profile']['cuda_build'] is None and result['torch_profile']['cuda_initialized_after'] is False
         and result['native_os_metadata']['system'] == 'Windows' and result['metadata_phase_closed'] is True
         and result['native_os_metadata']['phase_closed'] is True, 'native CPU profile')
    need(not any((CHILD/name).exists() for name in ('resource-failure.json','postwrite_rejection.json','test-globals-export-error.json'))
         and result['elapsed_seconds'] < 80 and elapsed() < 90, 'late/resource failure')
    accepted = True
except BaseException as error:
    errors.append(dict(stage='outer_acceptance', type=type(error).__name__, message=str(error)))
output_inventory = {}
try:
    for path in sorted(CHILD.iterdir()):
        if path.is_file():
            need(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)(), 'output file alias')
            need(path.stat().st_size <= 2*1024**2, 'bounded individual child output')
            output_inventory[path.name] = dict(bytes=path.stat().st_size, sha256=sha(path))
except BaseException as error:
    errors.append(dict(stage='output_inventory', type=type(error).__name__, message=str(error)))
    accepted = False
# Include output hashing in original outer90s; late evidence cannot be accepted.
if elapsed() >= 90:
    errors.append(dict(stage='posthash_budget', message='outer90s exceeded after output inventory'))
    accepted = False
final = dict(output_inventory=output_inventory, child_result_sha256=sha(CHILD/'result.json') if (CHILD/'result.json').is_file() else None,
    owned_receipt_sha256=sha(OUT/'receipt.json'), status='ACCEPTED_GRAPH10_ACTUAL_ADAM_ENGINEERING_ONLY' if accepted else 'REJECTED_GRAPH10_ACTUAL_ADAM_CHECK',
    counts=counts, native_counts=None if result is None else result['native_body_returned'],
    elapsed_seconds=elapsed(), cap_seconds=90, owned_ceiling_seconds=87, owned_allocated_seconds=owned_seconds,
    cleanup_reserve_seconds=3, child_timer_seconds=80, preflight_available_ram_bytes=available,
    worker_sha256=WORKER_SHA, allocation_sha256=PACKET_SHA, source_after=source_after, errors=errors,
    scope_vi='GRAPH10 một actualAdam syntheticfixture:3Architectureforward/3logicalbackward/3realclip/3Adamsteps/18targets. Conditional perparam participation/state;0actualcorpus/checkpoint/fitted/maintrainingclaim. Actualfalseavailabilitymetadata scoped;0CUDAinitialized.')
write(OUT/'final.json', final)
if elapsed() >= 90:
    write(OUT/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_BUDGET', elapsed_seconds=elapsed()))
    accepted = False
print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_GRAPH10_ACTUAL_ADAM_CHECK',
    counts=counts, native_counts=final['native_counts'], elapsed_seconds=elapsed(), cap_seconds=90,
    actual_corpus_fit=False, fitted_baseline=False, optimizer_updates=None if result is None else result['native_body_returned']['adam_steps']), ensure_ascii=False))
raise SystemExit(0 if accepted else 1)
