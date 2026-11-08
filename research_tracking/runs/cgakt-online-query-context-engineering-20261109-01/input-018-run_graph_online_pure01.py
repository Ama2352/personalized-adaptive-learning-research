"""ROOT-only đề xuất:35NumPy query cases/coldimport; outer90/owned87/cleanup3/worker80."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
WORKER = P/'check_graph_online_pure01.py'
PACKET = P/'graph_online_pure01_allocation.json'
OUT = P/'graph-online-pure01-owned'
CHILD = P/'graph-online-pure01'
TMP = R/'artifacts/akt/local-tests/gop01'


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n'); stream.flush()


need(len(sys.argv) == 2 and not OUT.exists() and not CHILD.exists() and not TMP.exists(), 'one exclusive reviewed attempt only')
raw = PACKET.read_bytes()
need(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == sys.argv[1], 'reviewed packet SHA')
packet = json.loads(raw); pins, runtime_pins = packet['source_pins'], packet['runtime_pins']
need(len(pins) == packet['source_count'] and all(sha(R/n) == h for n,h in pins.items())
    and all(sha(Path(n)) == h for n,h in runtime_pins.items()), 'source/runtime pin drift')
need(packet['call_caps'] == dict(tensors=0,model_constructors=0,optimizer_constructors=0,forwards=0,backwards=0,
    optimizer_steps=0,torch_save=0,torch_load=0), 'pure zero-call allocation only')
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import run_owned, entry, safe
entry(); safe(WORKER); safe(OUT); safe(CHILD); safe(TMP)
need(pins['scripts/research/windows_owned_worker.py'] == '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1', 'reviewed owned Job helper')
import psutil
need(Path(psutil.__file__).resolve() == Path(packet['runtime_origins']['psutil']).resolve(), 'pinned outer psutil origin')
available = int(psutil.virtual_memory().available)
need(available >= 2*1024**3, 'pure preflight requires2GiB free, no automatic retry')
owned = min(87., 90.-elapsed()-3.)
need(owned > 3, 'original outer budget exhausted before launch')
receipt = run_owned(WORKER, [sys.argv[1]], OUT,
    expected_worker_sha256=pins[WORKER.relative_to(R).as_posix()],
    approval_reference='ROOT_REVIEW_REQUIRED_GRAPH16_NUMPY35_NO_MODELS_90S',
    max_seconds=owned, cleanup_reserve_seconds=3, max_output_bytes=32768)
write(OUT/'receipt.json', receipt)
errors = []; counts = child = None
try:
    child = json.loads((CHILD/'result.json').read_bytes())
    tree = ET.parse(CHILD/'junit.xml').getroot()
    counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    need(len(list(tree.iter('testcase'))) == counts['tests'], 'exact testcase population')
    need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['actual_worker_in_job_before_GO'] is True
        and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
        and receipt['cleanup_errors'] == [] and receipt['returncode'] == 0, 'owned process/cleanup verdict')
    need(counts == dict(tests=35,failures=0,errors=0,skipped=0) and child['counts'] == counts
        and child['pytest_exit_code'] == 0 and child['status'] == 'ACCEPTED_35_NUMPY_QUERY_CASES_PENDING_OUTER', '35pure cases actual JUnit')
    need(child['source_before'] == child['source_after'] == pins and child['runtime_before'] == child['runtime_after'] == runtime_pins
        and child['allocation_sha256'] == sys.argv[1], 'child source/runtime/packet stability')
    need(child['cold_import']['fresh_import_accepted'] is True and child['cold_import']['numpy_loaded'] is True
        and child['cold_import']['torch_loaded'] is False and child['held_class_identity_stable'] is True
        and child['verified_no_forbidden_imports'] is True and child['declared_call_caps'] == packet['call_caps'], 'coldimport/pure scope')
    need(child['metadata_phase_closed'] is True and child['native_windows_metadata']['fixture_replaced'] is False
        and child['forbidden_attempts'] == [] and child['monitor_errors'] == [] and child['monitor_stopped'] is True
        and child['environment_restored'] is True and child['original_error'] is None and child['junit_error'] is None, 'scope/errors/restoration')
    need(child['resources']['observed_peak_rss_bytes'] <= 1024**3
        and child['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'cooperative pure RAM observations')
    need(child['elapsed_seconds'] < 80 and not any((CHILD/n).exists() for n in ('resource-failure.json','postwrite_rejection.json')),
        'child late/resource failure')
except BaseException as error:
    errors.append(dict(type=type(error).__name__, message=str(error)))
source_after = {n:sha(R/n) for n in pins}; runtime_after = {n:sha(Path(n)) for n in runtime_pins}
output_inventory = {path.name: dict(bytes=path.stat().st_size, sha256=sha(path))
    for path in CHILD.iterdir() if path.is_file()} if CHILD.is_dir() else {}
accepted = not errors and source_after == pins and runtime_after == runtime_pins and sha(PACKET) == sys.argv[1] and elapsed() < 90
result = dict(status='ACCEPTED_GRAPH16_35_NUMPY_QUERY_CASES_ONLY' if accepted else 'REJECTED_GRAPH16_QUERY_KEEP_ALL',
    counts=counts, errors=errors, source_before=pins, source_after=source_after, runtime_before=runtime_pins,
    runtime_after=runtime_after, allocation_sha256=sys.argv[1], preflight_available_ram_bytes=available,
    owned_allocated_seconds=owned, elapsed_seconds=elapsed(), cap_seconds=90, cleanup_reserve_seconds=3,
    worker_cap_seconds=80, declared_call_caps=packet['call_caps'], output_inventory=output_inventory,
    owned_receipt_sha256=sha(OUT/'receipt.json'),
    scope_vi='35NumPy data cases; no Torch/model/optimizer/backend/corpus/teacher; no fullGRAPH16/17/fit/Gate claim.')
write(OUT/'final.json', result)
if elapsed() >= 90:
    write(OUT/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_TIME', elapsed_seconds=elapsed())); accepted = False
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_GRAPH16_QUERY_KEEP_ALL', counts=counts, elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
