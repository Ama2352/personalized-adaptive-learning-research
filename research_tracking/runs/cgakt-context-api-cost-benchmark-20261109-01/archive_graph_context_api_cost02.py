"""ROOT-only compact metadata archive; không benchmark/test/NumPy/model import."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
DRY = PREP/'graph_context_api_cost02_dry.json'
RUN = 'cgakt-context-api-cost-benchmark-20261109-01'
PRIOR = 'research_tracking/runs/cgakt-context-model-hotpath-engineering-20261109-01/manifest.json'
PRIOR_SHA = '38ce2196a3472a674dad94bef48f79b7a248f126729c85651d6dac8559dfd6ef'
HELPER = ROOT/'src/knowledge_tracing/evidence.py'
HELPER_SHA = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
GENERATED = {'README.md', 'execution.log', 'approved_dry_inventory.json', 'copy_inventory_before.json',
             'copy_inventory_after.json', 'frozen_acceptance.json', 'closure_review.json', 'raw_log_paths.txt'}
NOTE = '''# Chi phí vận hành for_windows API — không epoch/model/GPU throughput

Actual02 accepted144ABBAcalls/completeTRAIN8010080targets/144windows, parity/source/
publicinputs/Jobcleanup accepted. Full-cache36/0/0/36calls theo full/fast/fast/full.
Chỉ API lookup/hash; canonicalreader audit cả3Developmentroles provenance, sauđó
chỉTRAIN80 index. Không fit/evaluate/select/calibrate hoặc gọi teacher/NN/oracle.

Actual01 REJECTED duplicate seconds journal saufirstbody; giữallraw/sources/Job0.
Hai AST regressions lấy actualevent/callsite, memoryjournal/fsyncstub không NN.
02 chargedcontroller đã gồm5sregression; không cộnglại. Prior26.7053/cap206.7053.

Venv/dependencies/corpus không copy: source/runtime/input SHAs nằmtrongactualconfigs/
receipts, hotpath41manifest đượcthamchiếu. O(W)lookup/sourceIO chưa biếnmất.
Output integrity completed không RQ3 efficacy/fittedmodel/currentGate authority.
'''


def need(ok, message):
    if not ok: raise ValueError(message)


def physical(path):
    path = path.absolute()
    need(path.is_relative_to(ROOT) and ROOT.resolve() == ROOT.absolute(), 'physical workspace only')
    cursor = ROOT
    for part in ('', *path.relative_to(ROOT).parts):
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias')
    need(path.resolve() == path, 'resolved alias'); return path


def sha(path):
    path = physical(path)
    need(path.is_file() and path.stat().st_size <= 2*1024**2, 'small evidence only')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    sha(path); return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')


def check():
    dry = read(DRY)
    need(dry['run_id'] == RUN and sha(HELPER) == HELPER_SHA, 'fixed run/helper')
    prior = read(ROOT/PRIOR)
    need(sha(ROOT/PRIOR) == PRIOR_SHA and prior['status'] == 'completed'
         and len(prior['outputs_sha256']) == 41, 'immutable hotpath41 reference')
    aliases, paths = set(), set()
    for row in dry['copies']:
        path, name = physical(ROOT/row['source']), row['copy']
        need(path.suffix not in ('.pt', '.pth', '.bin', '.zip', '.parquet')
             and not path.is_relative_to(ROOT/'.venv') and name not in aliases and row['source'] not in paths
             and '/' not in name and '\\' not in name, 'unique flat small metadata only')
        need(sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], 'copy SHA/size drift')
        aliases.add(name); paths.add(row['source'])
    old = read(PREP/'graph-context-hash-benchmark01/result.json')
    old_outer = read(PREP/'graph-context-hash-benchmark01-owned/final.json')
    old_job = read(PREP/'graph-context-hash-benchmark01-owned/receipt.json')
    need(old['status'] == 'REJECTED_KEEP_PARTIAL' and old['error']['type'] == 'TypeError'
         and 'seconds' in old['error']['message'] and old['completed_calls'] == 1
         and read(PREP/'graph-context-hash-benchmark01/bench_calls.json') == []
         and old_outer['benchmark_accepted'] is False, 'rejected01 journal failure retained, no accepted timings')
    need(old_job['returncode'] == 1 and old_job['cleanup_accepted'] and old_job['job_active_after_cleanup'] == 0
         and old_job['popen_handle_closed'], 'failed01 terminal cleanup')
    config = read(PREP/'graph_context_hash_benchmark02_config.json')
    child = read(PREP/'graph-context-hash-benchmark02/result.json')
    final = read(PREP/'graph-context-hash-benchmark02-owned/final.json')
    job = read(PREP/'graph-context-hash-benchmark02-owned/receipt.json')
    regression = read(PREP/'graph-context-hash-benchmark02-journal-regression.json')
    calls = read(PREP/'graph-context-hash-benchmark02/bench_calls.json')
    readout = read(PREP/'graph_context_hash_benchmark02_readout01.json')
    need(final['status'] == 'ACCEPTED_TRAIN80_CONTEXT_HASH_COST_ONLY_NOT_FIT' and final['errors'] == []
         and final['benchmark_accepted'] is True and child['error'] is None, 'accepted02 outer/child')
    need(job['accepted'] and job['cleanup_accepted'] and job['job_active_after_cleanup'] == 0
         and job['popen_handle_closed'] and job['returncode'] == 0 and job['cleanup_errors'] == [], 'actual02 Job0')
    need(final['conservative_regression_charge_seconds'] == 5 and final['prior_charged_seconds'] == 26.7053
         and final['seconds'] < 180 and final['cumulative_operational_charge_seconds'] <= 206.7053
         and child['seconds'] < 173, 'charged controller/cumulative accounting')
    need(regression['tests'] == regression['passed'] == 2 and regression['errors'] == []
         and regression['status'] == 'ACCEPTED_2_STDLIB_AST_JOURNAL_REGRESSIONS_NOT_BENCHMARK'
         and regression['no_corpus_or_model_imports'] and regression['synthetic_memory_only_fsync'], 'actual AST cases')
    need(config['passes'] == ['full','fast','fast','full'] and len(calls) == child['completed_calls'] == 144
         and child['full_targets'] == 10080 and child['windows'] == 144, 'complete TRAIN80 ABBA')
    need(child['source_before'] == child['source_after'] == config['source_pins'] == final['source_after']
         and child['public_input_sha256_after'] == config['public_inputs_sha256'] == final['public_input_after'], 'historical execution source/public maps')
    need(child['no_torch_loaded'] and child['forbidden'] == child['resource_errors'] == []
         and child['monitor_stopped'] and child['instrumentation_restored'], 'data-only/scope cleanup')
    for pass_number, summary in enumerate(readout['passes']):
        rows = [r for r in calls if r['pass_number'] == pass_number]
        need(len(rows) == summary['calls'] == 36 and [r['group_number'] for r in rows] == list(range(36)), 'all ordered groups')
        need(all(r['mode'] == config['passes'][pass_number] for r in rows)
             and math.isclose(sum(r['seconds'] for r in rows), summary['seconds'], rel_tol=0, abs_tol=1e-8), 'existing readout reconciles raw call sums')
        need(all(r['counters']['full_payload'] == (0 if r['mode'] == 'fast' else 1)
                 and r['counters']['source_inventory'] > 0 for r in rows), 'actual serializer/source guards')
    for group in range(36):
        need(len({r['evidence_sha256'] for r in calls if r['group_number'] == group}) == 1, 'same selected evidence all passes')
    need(child['resources']['observed_peak_rss_bytes'] <= 536870912
         and child['resources']['observed_minimum_available_ram_bytes'] >= 1073741824, 'observed resources')
    for folder in ('graph-context-hash-benchmark02', 'graph-context-hash-benchmark02-owned'):
        need(not (PREP/folder/'postwrite_rejection.json').exists(), 'late override')
    need(dry['generated_outputs'] == sorted(GENERATED) and not aliases & GENERATED
         and dry['expected_output_count'] == len(aliases)+len(GENERATED), 'exact generated output order/set')
    return dry, final


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check-dry', action='store_true'); parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256'); parser.add_argument('--review-reference'); args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv' and args.check_dry != args.close, 'project venv; explicit check/close')
    dry, final = check()
    if args.check_dry:
        print(json.dumps(dict(status='DRY_VERIFIED_NOT_CLOSED', dry_sha256=sha(DRY), copies=len(dry['copies']), expected_outputs=dry['expected_output_count']))); return
    need(sha(DRY) == args.expected_dry_sha256 and type(args.review_reference) is str and args.review_reference.strip(), 'exact ROOT-reviewed dry/ref')
    need(not (ROOT/'research_tracking/runs'/RUN).exists(), 'new exclusive bundle')
    before = [dict(row, sha256_before_copy=sha(ROOT/row['source'])) for row in dry['copies']]
    spec = importlib.util.spec_from_file_location('pinned_evidence', HELPER)
    evidence = importlib.util.module_from_spec(spec); spec.loader.exec_module(evidence)
    with evidence.record_evidence_run(ROOT, RUN, metadata=dict(kind='OPERATIONAL_FOR_WINDOWS_API_COST_NOT_NEURAL_THROUGHPUT',
            prior_hotpath41_manifest_sha256=PRIOR_SHA, actual01='REJECTED_JOURNAL_COLLISION', actual02='ACCEPTED144ABBA',
            charged_controller_seconds=final['seconds']), sources=[ROOT/r['source'] for r in dry['copies']]+[DRY, HELPER], note=NOTE) as out:
        with (out/'approved_dry_inventory.json').open('xb') as stream: stream.write(DRY.read_bytes())
        write(out/'copy_inventory_before.json', before)
        after = []
        for row in dry['copies']:
            source, target = ROOT/row['source'], out/row['copy']
            with target.open('xb') as stream: stream.write(source.read_bytes())
            need(sha(source) == sha(target) == row['sha256'], 'source/copy prepost mismatch')
            after.append(dict(row, source_sha256_after=sha(source), copy_sha256=sha(target)))
        write(out/'copy_inventory_after.json', after)
        write(out/'frozen_acceptance.json', dict(old01_rejected=True, actual02_accepted=True, AST_cases=2,
            calls=144, comparison='same completeTRAIN80 index; no NN', charge_scope='02 already includes5s; no double charge',
            cumulative_charge=final['cumulative_operational_charge_seconds'], cumulative_ceiling=206.7053,
            venv_or_corpus_copied=False, current_gate_or_fitted_claim=False))
        write(out/'closure_review.json', dict(reference=args.review_reference, dry_sha256=sha(DRY), scope='ROOT archive admission, no reruns'))
        with (out/'raw_log_paths.txt').open('x', encoding='utf-8') as stream:
            stream.write('\n'.join(r['source'] for r in dry['copies'] if r['source'].endswith('.log'))+'\n')
        need({p.name for p in out.iterdir() if p.name != 'manifest.json'} == set(GENERATED)|{r['copy'] for r in dry['copies']}, 'exact output population')
        need(all(sha(ROOT/r['source']) == r['sha256'] for r in dry['copies']), 'final selected input guards')
    directory = ROOT/'research_tracking/runs'/RUN
    verified = evidence.verify_evidence_bundle(directory)
    need(verified['artifacts'] == dry['expected_output_count'], 'closed output count')
    print(json.dumps(dict(**verified, manifest_sha256=sha(directory/'manifest.json'), run_id=RUN)))


if __name__ == '__main__': main()
