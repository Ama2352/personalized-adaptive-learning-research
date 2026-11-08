"""ROOT review/dispatch180s; public Dev audit + TRAIN80 context hash only, no NN."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONFIG = PREP/'graph_context_hash_benchmark02_config.json'
WORKER = PREP/'check_graph_context_hash_benchmark02.py'
OWNED = PREP/'graph-context-hash-benchmark02-owned'
CHILD = PREP/'graph-context-hash-benchmark02'
EXPECTED = sys.argv[1] if len(sys.argv) == 3 else None
EXPECTED_REGRESSION = sys.argv[2] if len(sys.argv) == 3 else None
REGRESSION = PREP/'graph-context-hash-benchmark02-journal-regression.json'
REGRESSION_REJECTED = PREP/'graph-context-hash-benchmark02-journal-regression-rejected.json'
REGRESSION_CHARGE = 0.


def need(ok, message):
    if not ok: raise ValueError(message)


def elapsed():
    return REGRESSION_CHARGE + max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(65536): digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush()



def check_journal_only(expected_config):
    """Hai AST-extracted event calls, memory-only journal; không data/NN import."""
    import ast
    import io
    from types import SimpleNamespace
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'project venv only')
    need(not REGRESSION.exists() and not REGRESSION_REJECTED.exists(), 'exclusive regression receipt')
    need(sha(CONFIG) == expected_config, 'exact prospective config for AST regression')
    cfg = json.loads(CONFIG.read_bytes())
    need(sha(Path(__file__).resolve()) == cfg['source_pins'][Path(__file__).resolve().relative_to(ROOT).as_posix()], 'controller pin')
    old_path = ROOT/cfg['prior_attempt']['worker_path']
    need(sha(old_path) == cfg['prior_attempt']['worker_sha256'], 'actual old event source pin')
    need(sha(WORKER) == cfg['source_pins'][WORKER.relative_to(ROOT).as_posix()], 'actual new event source pin')
    class MemoryJournal(io.BytesIO):
        def fileno(self): return 12345  # Synthetic descriptor, fsync is a local stub.
    observations = []
    errors = []
    for label, path, field in (('old01', old_path, 'seconds'), ('new02', WORKER, 'call_seconds')):
        raw = path.read_text(encoding='utf-8')
        tree = ast.parse(raw, filename=str(path))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'event']
        need(len(functions) == 1, 'one actual event function')
        callsites = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                     and n.func.id == 'event' and n.args and isinstance(n.args[0], ast.Constant)
                     and n.args[0].value == 'call_body_returned']
        need(len(callsites) == 1 and {k.arg for k in callsites[0].keywords} ==
             {'pass_number', 'group_number', 'mode', field}, 'actual callsite journal field schema')
        journal = MemoryJournal(); fsync_calls = []
        ns = dict(json=json, need=need, packet={'limits': {'max_journal_bytes': 1024}}, journal=journal,
                  elapsed=lambda: .25, os=SimpleNamespace(fsync=lambda fd: fsync_calls.append(fd)))
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(path)+'::event_only', 'exec'), ns)
        original_error = None
        try:
            ns['event']('call_body_returned', pass_number=0, group_number=0, mode='full', **{field: .1})
        except BaseException as caught:
            original_error = dict(type=type(caught).__name__, message=str(caught))
        if label == 'old01':
            accepted = (original_error is not None and original_error['type'] == 'TypeError'
                        and 'seconds' in original_error['message'] and journal.getvalue() == b'' and fsync_calls == [])
            row = None
        else:
            row = json.loads(journal.getvalue()) if original_error is None else None
            accepted = (original_error is None and row == dict(phase='call_body_returned', seconds=.25,
                call_seconds=.1, pass_number=0, group_number=0, mode='full') and fsync_calls == [12345])
        observations.append(dict(source=path.relative_to(ROOT).as_posix(), source_sha256=sha(path), label=label,
            accepted=accepted, original_exception=original_error, parsed_row=row, journal_bytes=len(journal.getvalue()),
            actual_callsite_keywords=sorted(k.arg for k in callsites[0].keywords)))
        if not accepted: errors.append(label)
    need(not any(n in sys.modules for n in ('numpy','torch','knowledge_tracing','pandas')), 'stdlib-only isolated regression')
    result = dict(status='ACCEPTED_2_STDLIB_AST_JOURNAL_REGRESSIONS_NOT_BENCHMARK' if not errors else 'REJECTED_JOURNAL_REGRESSION',
        tests=2, passed=2-len(errors), errors=errors, observations=observations, config_sha256=expected_config,
        seconds=elapsed(), cap_seconds=5, conservative_charge_within_new180_seconds=5,
        no_corpus_or_model_imports=True, synthetic_memory_only_fsync=True)
    write(REGRESSION, result)
    if errors or elapsed() >= 5:
        write(REGRESSION_REJECTED, dict(status='REJECTED_REGRESSION_OR_POSTWRITE_CAP', seconds=elapsed(), errors=errors))
        raise ValueError('regression or postwrite5s acceptance')
    print(json.dumps(dict(status=result['status'], receipt_sha256=sha(REGRESSION), seconds=elapsed())))


if len(sys.argv) == 3 and sys.argv[1] == '--check-journal-only':
    check_journal_only(sys.argv[2])
    raise SystemExit(0)

need(not OWNED.exists() and not CHILD.exists(), 'exclusive new attempt; no retry/overwrite')
need(CONFIG.stat().st_size <= 131072 and sha(CONFIG) == EXPECTED, 'exact reviewed config pin')
config = json.loads(CONFIG.read_bytes())
need(REGRESSION.is_file() and not REGRESSION_REJECTED.exists() and sha(REGRESSION) == EXPECTED_REGRESSION,
     'Root-reviewed actual AST regression receipt SHA required')
regression = json.loads(REGRESSION.read_bytes())
need(regression['status'] == 'ACCEPTED_2_STDLIB_AST_JOURNAL_REGRESSIONS_NOT_BENCHMARK'
     and regression['tests'] == regression['passed'] == 2 and regression['errors'] == []
     and regression['config_sha256'] == EXPECTED and regression['seconds'] < 5, 'actual AST regression accepted')
REGRESSION_CHARGE = 5.  # Conservative full prereview cap within the new180s, no reset.
prior = config['prior_attempt']
need(prior['charged_seconds'] == 26.7053 and config['cumulative_ceiling_seconds'] == 206.7053,
     'protective cumulative old01+new180 ledger, not reset')
need(all(sha(ROOT/n) == h for n,h in prior['raw_sha256'].items()), 'immutable actual01 source/raw evidence')
old_final = json.loads((ROOT/prior['outer_final_path']).read_bytes())
old_owned = json.loads((ROOT/prior['owned_receipt_path']).read_bytes())
need(old_final['benchmark_accepted'] is False and old_owned['returncode'] == 1
     and old_owned['cleanup_accepted'] is True and old_owned['job_active_after_cleanup'] == 0
     and old_owned['popen_handle_closed'] is True and old_owned['cleanup_errors'] == [], 'actual01 failed/owned Job terminal proof')
need(config['scope'] == 'SIMULATOR_DEVELOPMENT_AUDIT_TRAIN80_HASH_COST_NO_NEURAL'
     and config['passes'] == ['full', 'fast', 'fast', 'full'], 'fixed benchmark scope/order')
need(config['limits']['outer_seconds'] == 180 and config['limits']['owned_seconds'] == 177
     and config['limits']['cleanup_seconds'] == 3 and config['limits']['worker_seconds'] == 173, 'exact finite allocation')
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
owned_seconds = min(177., 180.-elapsed()-3.)
need(owned_seconds > 3., 'remaining original outer deadline')
receipt = run_owned(WORKER, [EXPECTED], OWNED,
    expected_worker_sha256=pins[WORKER.relative_to(ROOT).as_posix()],
    approval_reference='ROOT_REVIEWED_COMPLETE_SIMULATOR_TRAIN80_CONTEXT_HASH_BENCHMARK180S_NO_MODEL',
    max_seconds=owned_seconds, cleanup_reserve_seconds=3, max_output_bytes=65536)
write(OWNED/'receipt.json', receipt)
errors, result, calls, source_after, input_after = [], None, None, None, None
try:
    result = json.loads((CHILD/'result.json').read_bytes())
    calls = json.loads((CHILD/'bench_calls.json').read_bytes())
    source_after = {name: sha(ROOT/name) for name in pins}
    input_after = {name: sha(public/name) for name in config['public_inputs_sha256']}
    need(source_after == pins and input_after == config['public_inputs_sha256'] and sha(CONFIG) == EXPECTED
         and sha(REGRESSION) == EXPECTED_REGRESSION and all(sha(ROOT/n) == h for n,h in prior['raw_sha256'].items()), 'final source/input/config/prior guards')
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
         and result['seconds'] < 173 and elapsed() < 180, 'late/resource rejection')
except BaseException as error:
    errors.append(dict(type=type(error).__name__, message=str(error)))
accepted = not errors
outputs = {p.name: sha(p) for p in CHILD.iterdir() if p.is_file()} if CHILD.exists() else {}
final = dict(status='ACCEPTED_TRAIN80_CONTEXT_HASH_COST_ONLY_NOT_FIT' if accepted else 'REJECTED_KEEP_PARTIAL',
    seconds=elapsed(), cap_seconds=180, errors=errors, config_sha256=EXPECTED, worker_sha256=sha(WORKER),
    source_after=source_after, public_input_after=input_after, output_sha256=outputs,
    owned_allocated_seconds=owned_seconds, preflight_available_ram_bytes=available,
    benchmark_accepted=accepted, fitted_model=False, gpu_ready_claim=False,
    journal_regression_sha256=EXPECTED_REGRESSION, conservative_regression_charge_seconds=REGRESSION_CHARGE,
    prior_charged_seconds=prior['charged_seconds'], cumulative_operational_charge_seconds=prior['charged_seconds']+elapsed(),
    cumulative_ceiling_seconds=config['cumulative_ceiling_seconds'],
    scope_vi='All3simulator Development roles read for canonical provenance only; onlyTRAIN80 context/window hashing. NoNN/teacher/solver/oracle/Holdout/metrics/selection/tuning. ABBA retained allcalls; no throughput inference.')
write(OWNED/'final.json', final)
if elapsed() >= 180:
    write(OWNED/'postwrite_rejection.json', dict(status='REJECTED_OUTER_POSTWRITE_BUDGET', seconds=elapsed()))
    accepted = False
print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_KEEP_PARTIAL', seconds=elapsed(), error_count=len(errors))))
raise SystemExit(0 if accepted else 1)
