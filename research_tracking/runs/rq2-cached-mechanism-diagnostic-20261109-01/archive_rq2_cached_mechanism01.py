"""ROOT dry/close bằng chứng RQ2 cache, chỉ hash/copy metadata và source nhỏ."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'rq2-cached-mechanism-diagnostic-20261109-01'
REPORT = ROOT / 'research_tracking/reports/rq2_cached_mechanism_diagnostic_20261109.md'
DRY = PREP / 'rq2_cached_mechanism_archive_dry01.json'
BASE = ROOT / 'research_tracking/runs/cpu-factorial-20261107-01'
PURE_SHA = 'e7c877eb601e9a753e55959d1794e1a7b9a85a71fff82afc3769304e6c125658'
NATIVE_SHA = 'ad5170d4cd312b126b78f4fc96b01a4f1809962a7cee820010e2ab86a44d757c'
SYNTHESIS_SHA = '157b65c5ecc10c848eef4b054420356a61eedd860c824c17552ce5564f1e69db'
GENERATED = tuple(sorted(('README.md', 'execution.log', 'copy_inventory.json', 'source_binding.json',
                          'reference_inputs.json', 'scope.json', 'timing_scope.json', 'closure_review.json',
                          'reviewed_dry.json', 'raw_log_paths.txt')))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and ROOT.resolve() == ROOT, 'fixed repository')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'physical input')
    need(path.resolve() == path and path.is_file(), 'regular selected input')
    return path


def sha(path, cap=4*1024**2):
    safe(path)
    need(path.stat().st_size <= cap, 'small artifact cap')
    digest = hashlib.sha256()
    count = 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            count += len(block)
            need(count <= cap, 'stream byte cap')
            digest.update(block)
    need(count == path.stat().st_size, 'stable byte size')
    return digest.hexdigest()


def read(path):
    safe(path)
    need(path.stat().st_size <= 1024**2, 'bounded JSON')
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def gather(report_sha):
    need(sha(REPORT) == report_sha, 'external reviewed canonical report SHA')
    pure = read(PREP / 'rq2-cached-mechanism-pure01/result.json')
    final = read(PREP / 'rq2-cached-mechanism-native02-outer/final.json')
    failed = read(PREP / 'rq2-cached-mechanism-native01-outer/final.json')
    synth = read(PREP / 'rq2_cached_secondary_synthesis01.json')
    contract = read(PREP / 'rq2_cache_mechanism_contract01.json')
    packet = read(PREP / 'rq2_cached_mechanism_native02_packet.json')
    need(sha(PREP / 'rq2-cached-mechanism-pure01/result.json') == PURE_SHA
         and pure['status'] == 'ACCEPTED_16_SYNTHETIC_RQ2_METHODS_ONLY'
         and pure['counts'] == dict(tests=16, failures=0, errors=0, skipped=0,
                                   unexpected_successes=0, expected_failures=0)
         and pure['errors'] == [], 'actual pure16')
    need(sha(PREP / 'rq2-cached-mechanism-native02-outer/final.json') == NATIVE_SHA
         and final['status'] == 'ACCEPTED_CACHED_RQ2_SECONDARY_ANALYSIS' and final['errors'] == []
         and final['source_before'] == final['source_after'] == packet['source_pins']
         and final['elapsed_seconds'] < 60, 'actual accepted02')
    need(failed['status'] == 'REJECTED_KEEP_CACHED_RQ2_ATTEMPT'
         and failed['owned_receipt']['GO_released'] is False
         and failed['owned_receipt']['cleanup_accepted'] is False
         and failed['owned_receipt']['job_active_after_cleanup'] == 0, 'historical01 remains rejected')
    need(sha(PREP / 'rq2_cached_secondary_synthesis01.json') == SYNTHESIS_SHA
         and synth['accepted_outer_sha256'] == NATIVE_SHA
         and (synth['worlds'], synth['events']) == (120, 14400), 'Root cached synthesis binding')
    for stage in (pure['owned_receipt'], final['owned_receipt']):
        need(stage['accepted'] is True and stage['cleanup_accepted'] is True
             and stage['job_active_after_cleanup'] == 0 and stage['returncode'] == 0, 'accepted stages cleanup')
    need(final['bootstrap_scope']['denied_events'] == []
         and final['bootstrap_scope']['bootstrap_process_network_denials'] == []
         and final['bootstrap_scope']['display_environment_restored'] is True
         and final['resources']['errors'] == [] and final['resources']['monitor_stopped'] is True
         and final['resources']['observed_family_peak_rss_bytes'] <= 1024**3
         and final['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'actual scope/resource guards')
    refs = contract['inputs']
    need(final['inputs_before'] == final['inputs_after'] == {n: r['sha256'] for n, r in refs.items()}, 'all original inputs unchanged')
    for name, row in refs.items():
        need(sha(ROOT / name) == row['sha256'] and (ROOT / name).stat().st_size == row['bytes'], 'reference bytes preflight')
    for name, pin in packet['source_pins'].items():
        need(sha(ROOT / name) == pin, 'executed source/runtime bytes')
    inner = PREP / 'rq2-cache-mechanism-attempt01'
    for name, row in final['artifacts'].items():
        need(sha(inner / name) == row['sha256'] and (inner / name).stat().st_size == row['bytes'], 'accepted artifact bytes')
    need({p.name for p in inner.iterdir()} == set(final['artifacts']), 'exact terminal inner outputs')
    for name, expected in (('arm_exposures.json', 120), ('paired_trajectories.json', 120), ('joined_contrasts.json', 30)):
        need(len(read(inner / name)) == expected, 'complete emitted populations')
    paths = {}

    def add(alias, path):
        safe(path)
        need(alias not in paths and Path(alias).name == alias and path.stat().st_size <= 1024**2,
             'unique small flat evidence')
        need(path.suffix.lower() not in ('.gz', '.pt', '.pyd', '.dll', '.parquet', '.bin'), 'reference large/runtime inputs')
        paths[alias] = path

    files = ('analyze_rq2_cached_mechanism01.py', 'test_rq2_cached_mechanism01.py',
             'rq2_cache_mechanism_contract01.json', 'check_rq2_cached_mechanism_pure01.py',
             'rq2_cached_mechanism_pure01_packet.json', 'check_rq2_cached_mechanism_native01.py',
             'run_rq2_cached_mechanism_native01.py', 'rq2_cached_mechanism_native01_packet.json',
             'check_rq2_cached_mechanism_native02.py', 'run_rq2_cached_mechanism_native02.py',
             'rq2_cached_mechanism_native02_packet.json', 'rq2_cached_mechanism_native02_revision.json',
             'summarize_rq2_cache01.py', 'ROOT_RQ2_PURE16_REVIEW01.md', 'ROOT_RQ2_CACHE_REVIEW01.md',
             'ROOT_RQ2_CACHE_REVIEW02.md', 'RQ2_CACHE_MECHANISM_PROPOSAL01.md')
    for name in files:
        add(name, PREP / name)
    add('archive_rq2_cached_mechanism01.py', Path(__file__).resolve())
    add('report.md', REPORT)
    add('synthesis.json', PREP / 'rq2_cached_secondary_synthesis01.json')
    add('reference_CPU09_manifest.json', BASE / 'manifest.json')
    add('source__windows_owned_worker.py', ROOT / 'scripts/research/windows_owned_worker.py')
    add('source__evidence.py', ROOT / 'src/knowledge_tracing/evidence.py')
    for path in sorted(inner.iterdir()):
        add(path.name, path)
    folders = (('pure', 'rq2-cached-mechanism-pure01'), ('pure_owned', 'rq2-cached-mechanism-pure01-owned'),
               ('native01_outer', 'rq2-cached-mechanism-native01-outer'),
               ('native01_owned', 'rq2-cached-mechanism-native01-owned'),
               ('native02_outer', 'rq2-cached-mechanism-native02-outer'),
               ('native02_owned', 'rq2-cached-mechanism-native02-owned'))
    for label, directory in folders:
        for path in sorted((PREP / directory).iterdir()):
            if path.is_dir():
                need(label == 'pure' and path.name == 'runtime-temp' and not path.is_symlink()
                     and not getattr(path, 'is_junction', lambda: False)() and not any(path.iterdir()),
                     'only known empty restored runtime-temp directory excluded')
                continue
            need(path.is_file() and path.suffix in ('.json', '.jsonl', '.log'), 'bounded flat terminal evidence only')
            add(label + '__' + path.name, path)
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(),
                      sha256=sha(path), bytes=path.stat().st_size) for alias, path in sorted(paths.items())]
    need(sum(r['bytes'] for r in inventory) <= 4*1024**2, 'compact copied evidence cap4MiB')
    return inventory, refs, pure, final, synth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--prepare-dry', action='store_true')
    parser.add_argument('--check-dry', action='store_true')
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv', 'repository .venv only')
    destination = ROOT / 'research_tracking/runs' / RUN_ID
    need(not destination.exists(), 'immutable destination absent')
    inventory, refs, pure, final, synth = gather(args.report_sha256)
    dry = dict(run_id=RUN_ID, report_sha256=args.report_sha256, copies=inventory,
               reference_inputs=refs, generated_outputs=list(GENERATED),
               expected_output_count=len(inventory)+len(GENERATED), native02_final_sha256=NATIVE_SHA,
               pure16_final_sha256=PURE_SHA, synthesis_sha256=SYNTHESIS_SHA)
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=len(inventory),
                              outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'reviewed dry/current selected bytes identical')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', outputs=dry['expected_output_count'])))
        return
    need(args.close and args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'Root explicit exact-dry closure')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# RQ2 — chẩn đoán thứ cấp CPU09 từ cache\n\n'
            'Giữ đủ120worlds/14400events nguồn,120pairedcomparisons/30contrasts,10reusedseedclusters. '
            'Bằng chứng mới là true deficit exposure theoarm và query/label divergence. '
            'Gzip gốc được tham chiếu SHA. Pure16, rejectednative01 và acceptednative02 giữ nguyên. '
            'Báo cáo chính tại ../../reports/rq2_cached_mechanism_diagnostic_20261109.md.\n')
    sources = [ROOT / r['source'] for r in inventory] + [ROOT / n for n in refs] + [DRY]
    sources = list(dict.fromkeys(sources))
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='RQ2_CACHED_SECONDARY_MECHANISM_DIAGNOSTIC',
            actual_model_calls=0, new_world_transitions=0, new_independent_seed_families=0), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'input before copy')
            (out / row['copy']).write_bytes(source.read_bytes())
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/postcopy SHA')
            copied.append(dict(**row, input_sha256_after=sha(source), copied_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', refs)
        write(out / 'source_binding.json', dict(source_before=final['source_before'], source_after=final['source_after'],
              inputs_before=final['inputs_before'], inputs_after=final['inputs_after'],
              historical_manifest_sha256=sha(BASE / 'manifest.json'), original_gzip_copied=False,
              parser_test_contract_identical_in_pure_native01_native02=True))
        write(out / 'scope.json', dict(worlds_reused=120, events_reused=14400, paired_comparisons=120,
              endpoint_contrasts=30, reused_seed_clusters=10, new_independent_seed_families=0,
              actual_model_calls=0, new_world_transitions=0, inference='SECONDARY_EXPLORATORY_NO_CI_PVALUES',
              true_deficit_role='LATENT_WORLD_POSTHOC_DIAGNOSTIC_ONLY', research_completion=False))
        write(out / 'timing_scope.json', dict(pure16_seconds=pure['elapsed_seconds'], native02_seconds=final['elapsed_seconds'],
              native02_resources=final['resources'], per_attempt_cap_seconds=60,
              prior_attempt=final['historical_attempt01'], nested_timings_are_not_summed=True,
              root_tool_observations=dict(origin='Root messages, not archived raw stdout bytes',
                  pure16_terminal_seconds=1.3827869, native01_terminal_seconds=1.5640956,
                  native02_terminal_seconds=1.6758054, native02_printed_seconds=.9854834)))
        write(out / 'closure_review.json', dict(reference=args.review_reference,
              dry_sha256=args.expected_dry_sha256, report_sha256=args.report_sha256, root_closure_no_reexecution=True))
        (out / 'reviewed_dry.json').write_bytes(DRY.read_bytes())
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'reviewed dry copy')
        (out / 'raw_log_paths.txt').write_text('\n'.join(r['source'] for r in inventory
              if r['source'].endswith(('.log', '.jsonl'))) + '\n', encoding='utf-8')
        need({p.name for p in out.iterdir() if p.name != 'manifest.json'}
             == set(GENERATED) | {r['copy'] for r in inventory}, 'exact declared outputs')
        need(all(sha(ROOT / r['source']) == r['sha256'] for r in inventory)
             and all(sha(ROOT / n) == r['sha256'] for n, r in refs.items()), 'all selected/reference inputs unchanged')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == dry['expected_output_count'], 'exact closed output count')
    print(json.dumps(dict(**verified, path=destination.relative_to(ROOT).as_posix(),
                          manifest_sha256=sha(destination / 'manifest.json'))))


if __name__ == '__main__':
    main()
