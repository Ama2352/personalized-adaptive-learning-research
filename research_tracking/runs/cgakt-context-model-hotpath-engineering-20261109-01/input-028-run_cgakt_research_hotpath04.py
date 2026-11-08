"""ROOT outer:90s gồm sourcepreflight/owned87/cleanup3/final3; source-only/chưa dispatch."""
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
WORKER = P/'check_cgakt_research_hotpath04.py'
WORKER_SHA = '34b68e699b654dff05f1b8152deb5058753b01f0f712505f2ef289f1e02706aa'
PACKET = P/'cgakt_research_hotpath04_allocation.json'
PACKET_SHA = '2ac8712184fdf2f1c2e233db8a8559983a80eb712bd76c1760abb12656874401'
OUT = P/'cgakt-research-hotpath04-owned'
CHILD = P/'cgakt-research-hotpath04'


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
need(len(pins) == 29 and all(sha(R/name) == digest for name, digest in pins.items()), 'source pin drift')
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
    approval_reference='ROOT_REVIEW_CGAKT_RECIPE26_HOTPATH04_SELECTED_SEALS_25FIXTURES_8FORWARDS_5LOGICAL_BACKWARDS_0OPTIMIZER_0CORPUS',
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
    need(counts == dict(tests=25, failures=0, errors=0, skipped=0) and result['counts'] == counts
         and result['pytest_exit_code'] == 0 and result['status'] == 'ACCEPTED_CHILD_FIXTURES_PENDING_OUTER', 'exact25tests')
    need(result['native_started'] == result['native_body_returned'] == packet['expected_native_counts'], 'exact real native inventory')
    cache = result['full_cache_observation']
    boundary = result['whole_inference_boundary']
    need(cache['full_payload_started'] == cache['full_payload_returned'] > 0
         and cache['hotpath_attempts'] == [] and result['remaining_hot_regions'] == []
         and all(cache['region_calls'][name] > 0 for name in ('collate','step','native','inference')),
         'zero full serializer attempts inside observed per-batch hot paths')
    need(all(boundary[name] == 1 for name in ('before_started','before_returned','after_started','after_returned'))
         and boundary['before_identity'] == boundary['after_identity'] and boundary['errors'] == [],
         'explicit full audit before and after whole actual inference')
    names = [case.get('name') for case in tree.iter('testcase')]
    need(len(set(names)) == 25 and set(names) == set(packet['expected_test_names'])
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
    native_paths = ('akt.py','README.md','LICENSE')
    need(git['native_source_after'] == {name: pins['artifacts/akt/dependencies/upstream/'+name] for name in native_paths},
         'pinned native source before/after')
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
    need(not any((CHILD/name).exists() for name in ('resource-failure.json','postwrite_rejection.json'))
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
    owned_receipt_sha256=sha(OUT/'receipt.json'), status='ACCEPTED_CGAKT_RESEARCH_HOTPATH_ENGINEERING_ONLY' if accepted else 'REJECTED_CGAKT_RESEARCH_HOTPATH_CHECK',
    counts=counts, native_counts=None if result is None else result['native_body_returned'],
    elapsed_seconds=elapsed(), cap_seconds=90, owned_ceiling_seconds=87, owned_allocated_seconds=owned_seconds,
    cleanup_reserve_seconds=3, child_timer_seconds=80, preflight_available_ram_bytes=available,
    worker_sha256=WORKER_SHA, allocation_sha256=PACKET_SHA, source_after=source_after, errors=errors,
    scope_vi='25fixture recipe26,1backbone+1wrapper+1gate/8Architectureforwards/5logicalbackwards/0optimizer. Actualfalseupstreamavailabilityquery;CPUlib2.7.1+cpu/0CUDAinitialized.1GiBRSS/2GiBfreehypothesis;0fullserializerhotregions+explicitfullinferenceboundaries;O(W)lookupretained,notmaintraining/costbenchmark/actualcorpus/checkpoint/fullGate.')
write(OUT/'final.json', final)
if elapsed() >= 90:
    write(OUT/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_BUDGET', elapsed_seconds=elapsed()))
    accepted = False
print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_CGAKT_RESEARCH_HOTPATH_CHECK',
    counts=counts, native_counts=final['native_counts'], elapsed_seconds=elapsed(), cap_seconds=90,
    actual_corpus_fit=False, fitted_baseline=False, optimizer_updates=0), ensure_ascii=False))
raise SystemExit(0 if accepted else 1)
