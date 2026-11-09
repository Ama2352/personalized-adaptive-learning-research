"""ROOT-only: CPU checkpoint06,120s/owned116/child110/native100,4GiB admission."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
WORKER = P/'check_graph_checkpoint_native06.py'
PACKET = P/'graph_checkpoint_native06_allocation.json'
OUT = P/'graph-checkpoint-native06-owned'
CHILD = P/'graph-checkpoint-native06'
TMP = R/'artifacts/akt/local-tests/gcn06'


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush()


need(len(sys.argv) == 3 and not OUT.exists() and not CHILD.exists() and not TMP.exists(), 'packetSHA/actual metadataSHA/exclusive native06')
raw = PACKET.read_bytes()
need(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == sys.argv[1], 'reviewed packet SHA')
packet = json.loads(raw); pins = packet['source_pins']
need(len(pins) == packet['source_count'] and all(sha(R/n) == h for n,h in pins.items()), 'current source pins')
need(all(sha(Path(n)) == h for n,h in packet['runtime_pins'].items()), 'runtime pins')
pure_ref = packet['current_metadata_acceptance']
need(sha(R/pure_ref['path']) == sys.argv[2], 'ROOT external current38 metadata outer receipt SHA')
pure = json.loads((R/pure_ref['path']).read_bytes())
need(sha(R/pure_ref['packet_path'])==pure_ref['packet_sha256']
    and pure['packet_sha256']==pure_ref['packet_sha256']
    and not (R/pure_ref['path']).with_name('postwrite_rejection.json').exists(), 'current38 reviewed packet/terminal deadline')
need(pure['status'] == 'ACCEPTED_CURRENT38_CHECKPOINT_METADATA_NOT_NATIVE'
    and pure['child_result']['counts'] == dict(tests=38,failures=0,errors=0,skipped=0)
    and pure['owned_receipt']['returncode'] == 0 and pure['owned_receipt']['cleanup_accepted'] is True
    and pure['owned_receipt']['job_active_after_cleanup'] == 0 and pure['errors'] == []
    and pure['owned_receipt']['actual_worker_in_job_before_GO'] is True
    and pure['child_result']['environment_and_sys_restored'] is True
    and pure['child_result']['scientific_modules_absent'] is True
    and pure['child_result']['source_before'] == pure['child_result']['source_after']
    and all(pins[name] == digest for name,digest in pure['child_result']['source_before'].items()
            if not name.startswith(P.relative_to(R).as_posix()+'/')),
    'current38 metadata prerequisite, not native/CUDA proof')
main_ref=packet['current_mainc_metadata_acceptance']
need(sha(R/main_ref['path'])==main_ref['sha256'],'actual MainC221 metadata receipt')
main_metadata=json.loads((R/main_ref['path']).read_bytes())
need(main_metadata['status']=='ACCEPTED_BATCHC_METADATA_TESTS_NOT_NATIVE'
    and all(main_metadata['child_result']['source_after'][name]==pins[name] for name in packet['mainc_applied_paths']),
    'current eight MainC tested source bindings, no native/GPU authority')
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import run_owned, safe, entry
entry(); safe(WORKER); safe(OUT); safe(CHILD); safe(TMP)
import psutil
available = int(psutil.virtual_memory().available)
if available < 4*1024**3:
    OUT.mkdir(exist_ok=False)
    write(OUT/'final.json', dict(status='NO_GO_INSUFFICIENT_RAM_BEFORE_OWNED_LAUNCH',
        preflight_available_ram_bytes=available, required_available_ram_bytes=4*1024**3,
        allocation_sha256=sys.argv[1], actual_native_calls=None, owned_launch_started=False,
        elapsed_seconds=elapsed(), cap_seconds=120))
    raise SystemExit(1)
owned_seconds = min(116., 120.-elapsed()-4.)
need(owned_seconds > 3, 'outer reserve before GO')
receipt = run_owned(WORKER, [sys.argv[1]], OUT,
    expected_worker_sha256=pins[WORKER.relative_to(R).as_posix()],
    approval_reference='ROOT_REVIEW_REQUIRED_CPU_CHECKPOINT_BATCHB_NATIVE16_4ADAMBODIES_120S',
    max_seconds=owned_seconds, cleanup_reserve_seconds=3, max_output_bytes=32768)
helper_attempt_directory_present = OUT.is_dir()
errors = []; child = counts = None
try:
    # Helper có thể từ chối trước attempt.mkdir; giữ nguyên receipt sau return.
    if not OUT.exists():
        OUT.mkdir(exist_ok=False)
    write(OUT/'receipt.json', receipt)
    need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['actual_worker_in_job_before_GO'] is True
        and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
        and receipt['cleanup_errors'] == [] and receipt['returncode'] == 0, 'owned Job/cleanup')
    child = json.loads((CHILD/'result.json').read_bytes())
    tree = ET.parse(CHILD/'junit.xml').getroot()
    counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    cases = list(tree.iter('testcase'))
    actual_ids = [case.get('classname')+'::'+case.get('name') for case in cases]
    need(len(cases) == counts['tests'] and len(actual_ids) == len(set(actual_ids))
         and sorted(actual_ids) == sorted(packet['expected_junit_ids']), 'exact native16 JUnit identities')
    need(child['status'] == 'ACCEPTED_CHILD_GRAPH11_PENDING_OUTER' and child['pytest_exit_code'] == 0
        and counts == child['counts'] == dict(tests=16,failures=0,errors=0,skipped=0), 'actual16native fixtures')
    need(child['native_started'] == child['native_body_returned'] == packet['counter_caps'], 'exact native/serialization counts')
    need(child['source_before'] == child['source_after'] == pins
        and child['allocation_sha256'] == child['packet_sha256_after'] == sys.argv[1], 'childsource/packet unchanged')
    need(child['runtime_before'] == child['runtime_after'] == packet['runtime_pins'], 'runtime unchanged')
    need(child['original_error'] is None and child['junit_error'] is None and child['forbidden_attempts'] == []
        and child['monitor_errors'] == [] and child['monitor_stopped'] is True and child['owned_job_query_handle_closed'] is True
        and child['environment_restored'] is True, 'scope/errors/restoration')
    need(child['method_restoration']['accepted'] is True and child['method_restoration']['restore_errors'] == []
        and all(r['restored'] for r in child['method_restoration']['final_checks']), 'observer baselines restored')
    need(child['resources']['observed_peak_rss_bytes'] <= 1024**3
        and child['resources']['observed_peak_family_rss_bytes'] <= 1024**3
        and child['resources']['maximum_sampled_job_processes'] >= 1
        and child['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'owned Job family/worker/free memory limits')
    need(len(child['actual_collected_nodeids'])==16,'fresh exact collection before native bodies')
    need(len(child['local_git_calls']) == 20 and len(child['original_loaders']) == 2
        and all(r['original'] is True and r['cached'] is False for r in child['original_loaders']), 'two genuine loaders/no cache')
    need(0 < child['cuda_false_queries']['total'] <= packet['cuda_false_query_cap']
        and child['cuda_false_queries']['true_results'] == 0
        and sum(child['cuda_false_queries']['counts_by_phase_kind'].values()) == child['cuda_false_queries']['total'], 'bounded realFalse queries')
    proof = child['native_proof']
    need(proof['completed_epoch'] == dict(epoch=1,targets=48,windows=8,batches=2,optimizer_steps=2)
        and proof['control_cumulative_bodies'] == proof['restored_cumulative_bodies'] == 3
        and proof['continuation_scope'] == 'ONE_ACTIVE_BATCH_EACH_NOT_COMPLETE_EPOCH2', 'E1/partialE2 semantics')
    need(proof['direct_three_rng_restored_after_deliberate_perturbation'] is True
        and proof['all_module_modes_restored_after_deliberate_inversion'] is True
        and proof['epoch1_prediction_loss_count_exact'] is True
        and proof['continuous_model_sha256'] == proof['restored_continuation_model_sha256']
        and proof['continuous_adam_sha256'] == proof['restored_continuation_adam_sha256'], 'restored state/parity')
    need(proof['malformed_payloads_rejected_before_either_mutator'] ==
        ['missing_positive','python_rng','numpy_rng','torch_rng','mode_bool','mode_name'], 'authenticated negatives')
    need(len(proof['negative_binary_references']) == 6 and proof['fitted_research_model'] is False
        and proof['lifecycle_resume_supported'] is False, 'no fit/lifecycle promotion')
    need(len(child['target_observations']) == 4
        and all(r == dict(reserved=24,returned=24) for r in child['target_observations']), '96 training targets')
    need(len(child['timings']['adam_body_seconds']) == len(child['timings']['tracker_pre_seconds'])
        == len(child['timings']['tracker_post_seconds']) == len(child['timings']['adapter_optimizer_seconds']) == 4, 'timing population')
    need(child['native_work_seconds'] < 100 and child['elapsed_seconds'] < 110
        and not any((CHILD/n).exists() for n in ('resource-failure.json','postwrite_rejection.json')), 'child budget verdict')
except BaseException as error:
    errors.append(dict(type=type(error).__name__,message=str(error)))
source_after = {n:sha(R/n) for n in pins}
runtime_after = {n:sha(Path(n)) for n in packet['runtime_pins']}
accepted = not errors and source_after == pins and runtime_after == packet['runtime_pins'] and sha(PACKET) == sys.argv[1]
accepted = accepted and sha(R/pure_ref['path']) == sys.argv[2] and elapsed() < 120
result = dict(status='ACCEPTED_CPU_CHECKPOINT_BATCHB_NATIVE16_NOT_CUDA_OR_RESEARCH_FIT' if accepted else 'REJECTED_CPU_CHECKPOINT_BATCHB_KEEP_ALL',
    counts=counts, native_counts=None if child is None else child['native_body_returned'], errors=errors,
    source_before=pins, source_after=source_after, allocation_sha256=sys.argv[1], preflight_available_ram_bytes=available,
    elapsed_seconds=elapsed(), cap_seconds=120, owned_allocated_seconds=owned_seconds, cleanup_reserve_seconds=3,
    metadata_receipt_sha256=sys.argv[2], prior_native_reference=packet['historical_native_reference'],
    helper_attempt_directory_present_on_return=helper_attempt_directory_present,
    owned_GO_released=receipt.get('GO_released') is True, actual_worker_identity=receipt.get('actual_worker'),
    owned_receipt=receipt,
    new_max_adam_bodies=4, native_work_cap_seconds=100, child_cap_seconds=110,
    scope_vi='Fixture CPU cùng process, hai containers; E1 hoàn chỉnh và continuation E2 từng batch. Chưa actual corpus, fresh-process resume, main fit hoặc CUDA.')
write(OUT/'final.json', result)
if elapsed() >= 120:
    write(OUT/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_BUDGET',elapsed_seconds=elapsed()))
    accepted = False
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_CPU_CHECKPOINT_BATCHB_KEEP_ALL', counts=counts, elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
