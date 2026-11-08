"""Đề xuất ROOT-only GRAPH11 native16; outer90/owned87/cleanup3/worker80/native60."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
WORKER = P/'check_graph_checkpoint_native01.py'
PACKET = P/'graph_checkpoint_native01_allocation.json'
OUT = P/'graph-checkpoint-native01-owned'
CHILD = P/'graph-checkpoint-native01'
TMP = R/'artifacts/akt/local-tests/gcn01'


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n'); stream.flush()


need(len(sys.argv) == 2 and not OUT.exists() and not CHILD.exists() and not TMP.exists(), 'exclusive native attempt only/no automatic retry')
raw = PACKET.read_bytes(); need(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == sys.argv[1], 'exact reviewed packet SHA')
packet = json.loads(raw); pins = packet['source_pins']
need(len(pins) == packet['source_count'] and all(sha(R/n) == h for n,h in pins.items()), 'current component source pins')
need(all(sha(Path(n)) == h for n,h in packet['runtime_pins'].items()), 'preflight runtime component bytes')
for receipt in packet['pure_acceptance']:
    need(sha(R/receipt['path']) == receipt['sha256'], 'reviewed actual pure receipt')
pure = json.loads((R/packet['pure_acceptance'][0]['path']).read_bytes())
need(pure['status'] == 'ACCEPTED_GRAPH11_35_PURE_CASES_NOT_NATIVE_RESEARCH'
    and pure['counts'] == dict(tests=35,failures=0,errors=0,skipped=0), 'actual pure35 prerequisite, not native approval')
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import run_owned, safe, entry
entry(); safe(WORKER); safe(OUT); safe(CHILD); safe(TMP)
import psutil
available = int(psutil.virtual_memory().available)
need(available >= 2*1024**3, 'native preflight free2GiB; no automatic retry')
owned_seconds = min(87., 90.-elapsed()-3.)
need(owned_seconds > 3, 'original outer budget before GO')
receipt = run_owned(WORKER, [sys.argv[1]], OUT,
    expected_worker_sha256=pins[WORKER.relative_to(R).as_posix()],
    approval_reference='ROOT_REVIEW_REQUIRED_GRAPH11_NATIVE16_COMPLETE_E1_AND_PARTIAL_CONTINUATION_4ADAMBODIES_90S',
    max_seconds=owned_seconds, cleanup_reserve_seconds=3, max_output_bytes=32768)
write(OUT/'receipt.json', receipt)
errors = []; child = counts = None
try:
    child = json.loads((CHILD/'result.json').read_bytes())
    tree = ET.parse(CHILD/'junit.xml').getroot()
    counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    need(len(list(tree.iter('testcase'))) == counts['tests'], 'exact native JUnit population')
    need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['actual_worker_in_job_before_GO'] is True
        and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
        and receipt['cleanup_errors'] == [] and receipt['returncode'] == 0, 'owned Job/cleanup')
    need(child['status'] == 'ACCEPTED_CHILD_GRAPH11_PENDING_OUTER' and child['pytest_exit_code'] == 0
        and counts == child['counts'] == dict(tests=16,failures=0,errors=0,skipped=0), 'actual16native fixtures')
    need(child['native_started'] == child['native_body_returned'] == packet['counter_caps'], 'exact native/serialization counts')
    need(child['source_before'] == child['source_after'] == pins and child['allocation_sha256'] == child['packet_sha256_after'] == sys.argv[1], 'childsource/packet unchanged')
    need(child['runtime_before'] == child['runtime_after'] == packet['runtime_pins'], 'runtime component bytes unchanged')
    need(child['original_error'] is None and child['junit_error'] is None and child['forbidden_attempts'] == []
        and child['monitor_errors'] == [] and child['monitor_stopped'] is True and child['environment_restored'] is True, 'scope/errors/restoration')
    need(child['method_restoration']['accepted'] is True and child['method_restoration']['restore_errors'] == []
        and all(r['restored'] for r in child['method_restoration']['final_checks']), 'all observer baselines restored')
    need(child['resources']['observed_peak_rss_bytes'] <= 1024**3
        and child['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'observed/cooperative memory limits')
    need(len(child['local_git_calls']) == 20 and len(child['original_loaders']) == 2
        and all(r['original'] is True and r['cached'] is False for r in child['original_loaders']), 'two genuine loaders/no cache')
    need(0 < child['cuda_false_queries']['total'] <= packet['cuda_false_query_cap']
        and child['cuda_false_queries']['true_results'] == 0
        and sum(child['cuda_false_queries']['counts_by_phase_kind'].values()) == child['cuda_false_queries']['total'], 'bounded realFalse metadata queries')
    proof = child['native_proof']
    need(proof['completed_epoch'] == dict(epoch=1,targets=48,windows=8,batches=2,optimizer_steps=2)
        and proof['control_cumulative_bodies'] == proof['restored_cumulative_bodies'] == 3
        and proof['continuation_scope'] == 'ONE_ACTIVE_BATCH_EACH_NOT_COMPLETE_EPOCH2', 'completeE1/partialE2 semantics')
    need(proof['direct_three_rng_restored_after_deliberate_perturbation'] is True
        and proof['all_module_modes_restored_after_deliberate_inversion'] is True
        and proof['epoch1_prediction_loss_count_exact'] is True
        and proof['continuous_model_sha256'] == proof['restored_continuation_model_sha256']
        and proof['continuous_adam_sha256'] == proof['restored_continuation_adam_sha256'], 'direct restored state/parity')
    need(proof['malformed_payloads_rejected_before_either_mutator'] ==
        ['missing_positive','python_rng','numpy_rng','torch_rng','mode_bool','mode_name'], 'all authenticated negatives')
    need(len(proof['negative_binary_references']) == 6 and proof['fitted_research_model'] is False
        and proof['lifecycle_resume_supported'] is False, 'no fit/lifecycle promotion')
    need(len(child['target_observations']) == 4 and all(r == dict(reserved=24,returned=24) for r in child['target_observations']), '96actual supported training targets')
    need(len(child['timings']['adam_body_seconds']) == len(child['timings']['tracker_pre_seconds'])
        == len(child['timings']['tracker_post_seconds']) == len(child['timings']['adapter_optimizer_seconds']) == 4,
        'real body/hook timing population, not throughput')
    need(child['native_work_seconds'] < 60 and child['elapsed_seconds'] < 80
        and not any((CHILD/n).exists() for n in ('resource-failure.json','postwrite_rejection.json')), 'native/child budget verdict')
except BaseException as error:
    errors.append(dict(type=type(error).__name__,message=str(error)))
source_after = {n:sha(R/n) for n in pins}
runtime_after = {n:sha(Path(n)) for n in packet['runtime_pins']}
accepted = not errors and source_after == pins and runtime_after == packet['runtime_pins'] and sha(PACKET) == sys.argv[1] and elapsed() < 90
result = dict(status='ACCEPTED_GRAPH11_NATIVE16_STATE_PERSISTENCE_NOT_RESEARCH_FIT' if accepted else 'REJECTED_GRAPH11_NATIVE_KEEP_ALL',
    counts=counts, native_counts=None if child is None else child['native_body_returned'], errors=errors,
    source_before=pins, source_after=source_after, allocation_sha256=sys.argv[1], preflight_available_ram_bytes=available,
    elapsed_seconds=elapsed(), cap_seconds=90, owned_allocated_seconds=owned_seconds, cleanup_reserve_seconds=3,
    native_work_cap_seconds=60, child_cap_seconds=80,
    scope_vi='Handmade same-process fresh-container E1 persistence, four physical updates incl partial controlled continuation. NOT actualcorpus/selectedfit/main/lifecycle/fresh-process resume/GPU readiness.')
write(OUT/'final.json', result)
if elapsed() >= 90:
    write(OUT/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_BUDGET',elapsed_seconds=elapsed())); accepted = False
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_GRAPH11_NATIVE_KEEP_ALL', counts=counts, elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
