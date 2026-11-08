"""ROOT outer:80s gồm validation/owned77-ceiling/cleanup3/postchecks, không auto retry."""
import time
START = time.perf_counter()
WALL = time.time()
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
WORKER = P/'check_sakt_research_epoch02.py'
WORKER_SHA = 'f8ec38aa3149e420f7725a3e27289bbe37a77b4ef6b49e3bb47b3c8b12b03630'
PACKET = P/'sakt_research_epoch02_allocation.json'
PACKET_SHA = '6d0824232bd4d3d41f393e5bff8457456a4c77bb0d9221a0edb955a10716fef1'
OUT = P/'sakt-research-epoch02-owned'
CHILD = P/'sakt-research-epoch02'


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
need(len(pins) == 27 and all(sha(R/name) == digest for name, digest in pins.items()), 'source pin drift')
need(all(not (R/name).exists() for name in packet['absent_source_paths']), 'namespace source absence drift')
need(pins['scripts/research/windows_owned_worker.py'] == '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1', 'reviewed owned helper')
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import run_owned, safe, entry
entry()
safe(WORKER); safe(PACKET); safe(OUT); safe(CHILD)
import psutil
available = int(psutil.virtual_memory().available)
need(available >= 1024**3, 'tiny fixture preflight requires1GiB available; fullGate still4GiB')
# Reserve final3s from the original80s; metadata/preflight never reset the clock.
owned_seconds = min(77., 80.-elapsed()-3.)
need(owned_seconds > 3., 'insufficient original outer budget before launch')
receipt = run_owned(WORKER, [], OUT, expected_worker_sha256=WORKER_SHA,
    approval_reference='ROOT_REVIEW_SAKT_EPOCH02_OBSERVER_FIX_22FIXTURES_5LOGICAL_BACKWARDS_5SGDSTEPS_0CORPUS',
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
except BaseException as error:
    errors.append(dict(stage='postrun_hashes', type=type(error).__name__, message=str(error)))
accepted = False
try:
    need(not errors and result is not None, 'missing/invalid final evidence')
    need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True
         and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
         and receipt['popen_handle_closed'] is True and receipt['cleanup_errors'] == []
         and receipt['worker_sha256'] == WORKER_SHA and receipt['returncode'] == 0, 'owned worker/cleanup')
    need(counts == dict(tests=22, failures=0, errors=0, skipped=0) and result['counts'] == counts
         and result['pytest_exit_code'] == 0 and result['status'] == 'ACCEPTED_CHILD_FIXTURES_PENDING_OUTER', 'exact22tests')
    need(result['native_started'] == result['native_body_returned'] == packet['expected_native_counts'], 'exact real native inventory')
    need(result['source_before'] == result['source_after'] == source_after == pins
         and result['source_unchanged'] is True and result['allocation_sha256'] == result['allocation_sha256_after'] == PACKET_SHA
         and result['namespace_absence_unchanged'] is True, 'child exact input identities')
    need(result['forbidden_attempts'] == [] and result['methods_restored'] is True
         and result['runtime_restored'] is True and result['environment_restored'] is True
         and result['monitor_stopped'] is True and result['monitor_errors'] == []
         and result['original_exception'] is None and result['junit_error'] is None, 'scope/restoration guards')
    need(result['resources']['observed_peak_rss_bytes'] <= 512*1024**2
         and result['resources']['observed_minimum_available_ram_bytes'] >= 1024**3, 'observed/cooperative memory bounds')
    need(result['torch_profile']['version'] == '2.7.1+cpu'
         and result['torch_profile']['cuda_build'] is None and result['torch_profile']['cuda_initialized_after'] is False
         and result['native_os_metadata']['system'] == 'Windows' and result['metadata_phase_closed'] is True
         and result['native_os_metadata']['phase_closed'] is True, 'native CPU profile')
    need(not any((CHILD/name).exists() for name in ('resource-failure.json','postwrite_rejection.json'))
         and result['elapsed_seconds'] < 70 and elapsed() < 80, 'late/resource failure')
    accepted = True
except BaseException as error:
    errors.append(dict(stage='outer_acceptance', type=type(error).__name__, message=str(error)))
final = dict(status='ACCEPTED_SAKT_RESEARCH_EPOCH_ENGINEERING_ONLY' if accepted else 'REJECTED_SAKT_RESEARCH_EPOCH_CHECK',
    counts=counts, native_counts=None if result is None else result['native_body_returned'],
    elapsed_seconds=elapsed(), cap_seconds=80, owned_ceiling_seconds=77, owned_allocated_seconds=owned_seconds,
    cleanup_reserve_seconds=3, child_timer_seconds=70, preflight_available_ram_bytes=available,
    worker_sha256=WORKER_SHA, allocation_sha256=PACKET_SHA, source_after=source_after, errors=errors,
    scope_vi='22toy CPU fixtures,5logical backwards/10raw dispatchentries/5SGD bodies incl1wrapper failure aftermutation; no actualcorpus/fittedbaseline/checkpoint/CUDA/fullGate.')
write(OUT/'final.json', final)
if elapsed() >= 80:
    write(OUT/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_BUDGET', elapsed_seconds=elapsed()))
    accepted = False
print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_SAKT_RESEARCH_EPOCH_CHECK',
    counts=counts, native_counts=final['native_counts'], elapsed_seconds=elapsed(), cap_seconds=80,
    actual_corpus_fit=False, fitted_baseline=False), ensure_ascii=False))
raise SystemExit(0 if accepted else 1)
