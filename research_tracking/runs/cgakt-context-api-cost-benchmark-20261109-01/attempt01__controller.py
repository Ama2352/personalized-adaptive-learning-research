"""ROOT review/dispatch90s; public Dev audit + TRAIN80 context hash only, no NN."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONFIG = PREP/'graph_context_hash_benchmark01_config.json'
WORKER = PREP/'check_graph_context_hash_benchmark01.py'
OWNED = PREP/'graph-context-hash-benchmark01-owned'
CHILD = PREP/'graph-context-hash-benchmark01'
EXPECTED = sys.argv[1] if len(sys.argv) == 2 else None


def need(ok, message):
    if not ok: raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(65536): digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush()


need(not OWNED.exists() and not CHILD.exists(), 'exclusive new attempt; no retry/overwrite')
need(CONFIG.stat().st_size <= 131072 and sha(CONFIG) == EXPECTED, 'exact reviewed config pin')
config = json.loads(CONFIG.read_bytes())
need(config['scope'] == 'SIMULATOR_DEVELOPMENT_AUDIT_TRAIN80_HASH_COST_NO_NEURAL'
     and config['passes'] == ['full', 'fast', 'fast', 'full'], 'fixed benchmark scope/order')
need(config['limits']['outer_seconds'] == 90 and config['limits']['owned_seconds'] == 87
     and config['limits']['cleanup_seconds'] == 3 and config['limits']['worker_seconds'] == 83, 'exact finite allocation')
pins = config['source_pins']
need(all(sha(ROOT/name) == digest for name, digest in pins.items()), 'source/runtime pins before launch')
public = ROOT/'artifacts/simulator/corpora'/config['corpus_id']
need(all(sha(public/name) == digest for name, digest in config['public_inputs_sha256'].items()), 'exact public input pins before launch')
need(not (public/'failure.json').exists(), 'published corpus must remain complete')
sys.path.insert(0, str(ROOT/'scripts/research'))
from windows_owned_worker import run_owned, safe, entry
entry()
for path in (CONFIG, WORKER, OWNED, CHILD, public): safe(path)
import psutil
available = int(psutil.virtual_memory().available)
need(available >= config['limits']['min_available_ram_bytes'], 'preflight available RAM floor')
owned_seconds = min(87., 90.-elapsed()-3.)
need(owned_seconds > 3., 'remaining original outer deadline')
receipt = run_owned(WORKER, [EXPECTED], OWNED,
    expected_worker_sha256=pins[WORKER.relative_to(ROOT).as_posix()],
    approval_reference='ROOT_REVIEWED_COMPLETE_SIMULATOR_TRAIN80_CONTEXT_HASH_BENCHMARK90S_NO_MODEL',
    max_seconds=owned_seconds, cleanup_reserve_seconds=3, max_output_bytes=65536)
write(OWNED/'receipt.json', receipt)
errors, result, calls, source_after, input_after = [], None, None, None, None
try:
    result = json.loads((CHILD/'result.json').read_bytes())
    calls = json.loads((CHILD/'bench_calls.json').read_bytes())
    source_after = {name: sha(ROOT/name) for name in pins}
    input_after = {name: sha(public/name) for name in config['public_inputs_sha256']}
    need(source_after == pins and input_after == config['public_inputs_sha256'] and sha(CONFIG) == EXPECTED, 'final source/input/config guards')
    need(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['actual_worker_in_job_before_GO']
         and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed']
         and receipt['cleanup_errors'] == [] and receipt['returncode'] == 0, 'owned worker terminal/cleanup')
    need(result['status'] == 'ACCEPTED_TRAIN80_HASH_BENCHMARK_PENDING_OUTER' and result['error'] is None
         and result['source_before'] == result['source_after'] == pins
         and result['public_input_sha256_after'] == input_after, 'actual benchmark/source accepted')
    need(result['completed_calls'] == len(calls) == config['counts']['calls']
         and result['full_targets'] == 10080 and result['windows'] == 144
         and result['all3_development_roles_audited'] is True, 'complete TRAIN80 and ABBA population')
    expected_keys = [(p, g, mode) for p, mode in enumerate(config['passes']) for g in range(config['counts']['groups'])]
    need([(r['pass_number'], r['group_number'], r['mode']) for r in calls] == expected_keys, 'canonical ABBA no skipped/reordered calls')
    for group in range(config['counts']['groups']):
        rows = [r for r in calls if r['group_number'] == group]
        need(len({r['evidence_sha256'] for r in rows}) == 1 and all(r['window_ids'] == rows[0]['window_ids'] for r in rows), 'selected input/evidence parity')
    need(all(r['counters']['full_payload'] == (0 if r['mode'] == 'fast' else 1)
             and r['counters']['selected_record_hash'] == (len(r['window_ids']) if r['mode'] == 'fast' else 0)
             and r['counters']['source_inventory'] > 0 for r in calls), 'measured source/serializer work')
    resources = result['resources']
    need(resources['samples'] > 0 and resources['observed_peak_rss_bytes'] <= config['limits']['max_rss_bytes']
         and resources['observed_minimum_available_ram_bytes'] >= config['limits']['min_available_ram_bytes'], 'observed/cooperative memory budget')
    need(result['no_torch_loaded'] and result['forbidden'] == [] and result['resource_errors'] == []
         and result['monitor_stopped'] and result['instrumentation_restored'], 'scope and instrumentation cleanup')
    need(not (CHILD/'postwrite_rejection.json').exists() and not (public/'failure.json').exists()
         and result['seconds'] < 83 and elapsed() < 90, 'late/resource rejection')
except BaseException as error:
    errors.append(dict(type=type(error).__name__, message=str(error)))
accepted = not errors
outputs = {p.name: sha(p) for p in CHILD.iterdir() if p.is_file()} if CHILD.exists() else {}
final = dict(status='ACCEPTED_TRAIN80_CONTEXT_HASH_COST_ONLY_NOT_FIT' if accepted else 'REJECTED_KEEP_PARTIAL',
    seconds=elapsed(), cap_seconds=90, errors=errors, config_sha256=EXPECTED, worker_sha256=sha(WORKER),
    source_after=source_after, public_input_after=input_after, output_sha256=outputs,
    owned_allocated_seconds=owned_seconds, preflight_available_ram_bytes=available,
    benchmark_accepted=accepted, fitted_model=False, gpu_ready_claim=False,
    scope_vi='All3simulator Development roles read for canonical provenance only; onlyTRAIN80 context/window hashing. NoNN/teacher/solver/oracle/Holdout/metrics/selection/tuning. ABBA retained allcalls; no throughput inference.')
write(OWNED/'final.json', final)
if elapsed() >= 90:
    write(OWNED/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_BUDGET', seconds=elapsed()))
    accepted = False
print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_KEEP_PARTIAL', seconds=elapsed(), error_count=len(errors))))
raise SystemExit(0 if accepted else 1)
