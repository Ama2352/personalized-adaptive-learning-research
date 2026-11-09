"""Chuẩn bị inventory hoặc đóng bằng chứng response reliability sau review Root."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'rq1-response-reliability-diagnostic-20261109-01'
REPORT = ROOT / 'research_tracking/reports/rq1_response_reliability_diagnostic_20261109.md'
DRY = PREP / 'rq1_response_reliability_archive_dry01.json'
BASE = ROOT / 'research_tracking/runs/cpu-factorial-20261107-01'
OLD_CACHE = ROOT / 'research_tracking/runs/rq2-cached-mechanism-diagnostic-20261109-01'
PURE_SHA = '087c94b14e67939e66792e07217bdf0ebdda4dfab0a74e15dfecdad52bff5edd'
NATIVE_SHA = 'e68aae35eca99c111107d2748a62baeb1a78bf5e4b5952bb777befe980ae6ca8'
SYNTHESIS_SHA = '9cbfef811bc496f7c29c093ad80fcd1d14947fe2d60450e88835591f48cfe03a'
RECIPE_SHA = '44137a62e1762568ad3c043bedec79549e753c4ce4a7932e4a397ea9286bea8c'
RELIABILITY_SHA = 'a139398062bcb424ad759d5ee07c81521d322c49ab119b8deedc3c3d98697d26'
OLD_CACHE_SHA = '673e38d84b2af15d79b7daa4e086eb7e7fc9fa174a230345ed3f4146c2807adf'
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
    need(sha(REPORT) == report_sha, 'external reviewed report SHA')
    pure_path = PREP / 'rq1-response-reliability-pure01/result.json'
    final_path = PREP / 'rq1-response-reliability-native01-outer/final.json'
    pure = read(pure_path)
    final = read(final_path)
    synth = read(PREP / 'rq1_response_reliability_synthesis01.json')
    verification = read(PREP / 'rq1_response_reliability_synthesis_verification01.json')
    packet = read(PREP / 'rq1_response_reliability_native01_packet.json')
    contract = read(PREP / 'rq1_response_reliability_contract01.json')
    base_contract = read(PREP / 'rq2_cache_mechanism_contract01.json')
    need(sha(pure_path) == PURE_SHA and pure['status'] == 'ACCEPTED_7_RESPONSE_RELIABILITY_PURE_METHODS'
         and pure['counts'] == dict(tests=7, failures=0, errors=0, skipped=0,
                                   unexpected_successes=0, expected_failures=0)
         and pure['errors'] == [] and pure['elapsed_seconds'] < 30, 'actual pure7')
    worker = pure['worker_result']
    need(worker['calls'] == dict(response_bins=75, grouped_reliability=2, main=0)
         and len(worker['subtests']) == 31 and worker['cached_file_opens'] == 0
         and worker['errors'] == [] and worker['forbidden'] == [] and worker['heavy_modules'] == []
         and worker['methods_restored'] is True and worker['monitor_stopped'] is True, 'pure fixture scope')
    need(sha(final_path) == NATIVE_SHA and final['status'] == 'ACCEPTED_CACHED_RQ1_RESPONSE_RELIABILITY'
         and final['errors'] == [] and final['elapsed_seconds'] < 60
         and final['source_before'] == final['source_after'] == packet['source_pins'], 'actual native/source binding')
    for stage in (pure['owned_receipt'], final['owned_receipt']):
        need(stage['accepted'] is True and stage['cleanup_accepted'] is True
             and stage['job_active_after_cleanup'] == 0 and stage['returncode'] == 0, 'accepted cleanup')
    for directory in ('rq1-response-reliability-pure01', 'rq1-response-reliability-native01-outer'):
        need(not (PREP / directory / 'postwrite-rejection.json').exists(), 'no late rejection')
    scope = final['bootstrap_scope']
    need(scope['status'] == 'RESPONSE_RELIABILITY_MAIN_RETURNED' and scope['original_main_exit_code'] == 0
         and scope['error'] is None and scope['denied_events'] == []
         and scope['bootstrap_process_network_denials'] == [] and scope['unexpected_heavy_modules'] == []
         and scope['display_environment_restored'] is True, 'actual read/import/display scope')
    resources = final['resources']
    need(resources['errors'] == [] and resources['monitor_stopped'] is True
         and resources['observed_family_peak_rss_bytes'] <= 1024**3
         and resources['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'observed resource bounds')
    need(final['actual_model_calls'] == final['new_world_transitions']
         == final['new_independent_seed_families'] == 0, 'no new model/world/seed')
    inner = PREP / 'rq1-response-reliability-attempt01'
    need({p.name for p in inner.iterdir()} == set(contract['expected_complete_files'])
         == set(final['artifacts']), 'exact terminal inner outputs')
    for name, row in final['artifacts'].items():
        need(sha(inner / name) == row['sha256'] and (inner / name).stat().st_size == row['bytes'], 'accepted artifact bytes')
    result = read(inner / 'result.json')
    need((result['worlds'], result['trace_rows'], result['groups'], result['bins'], result['repeated_group_row_uses'])
         == (120, 14400, 136, 2040, 43200), 'complete actual populations')
    need(sha(inner / 'reliability.json') == RELIABILITY_SHA
         and sha(PREP / 'rq1_response_reliability_synthesis01.json') == SYNTHESIS_SHA
         and sha(PREP / 'verify_response_reliability_synthesis01.py') == RECIPE_SHA
         and synth['source_sha256'] == RELIABILITY_SHA and synth['accepted_outer_sha256'] == NATIVE_SHA
         and len(synth['groups']) == 16, 'exact accepted bins/summary')
    need(verification['status'] == 'VERIFIED_EXISTING_SYNTHESIS_FROM_ACCEPTED_BINS'
         and verification['recipe_sha256'] == RECIPE_SHA and verification['synthesis_sha256'] == SYNTHESIS_SHA
         and verification['reliability_input_sha256'] == RELIABILITY_SHA
         and verification['groups'] == 16, 'later stored recipe actual verification')
    need(sha(OLD_CACHE / 'manifest.json') == OLD_CACHE_SHA, 'closed previous cache reference')
    original_refs = base_contract['inputs']
    need(final['inputs_before'] == final['inputs_after']
         == {name: row['sha256'] for name, row in original_refs.items()}, 'original21 input hashes unchanged')
    refs = dict(original_refs)
    for name, pin in packet['source_pins'].items():
        path = ROOT / name
        need(sha(path) == pin, 'executed source/runtime byte identity')
        refs[name] = dict(sha256=pin, bytes=path.stat().st_size)
    for name, row in refs.items():
        need(sha(ROOT / name) == row['sha256'] and (ROOT / name).stat().st_size == row['bytes'], 'reference bytes')
    paths = {}

    def add(alias, path):
        safe(path)
        need(alias not in paths and Path(alias).name == alias and path.stat().st_size <= 1024**2,
             'unique bounded flat evidence')
        need(path.suffix.lower() not in ('.gz', '.pt', '.pyd', '.dll', '.parquet', '.bin'), 'large/runtime reference only')
        paths[alias] = path

    for name in ('analyze_rq1_response_reliability01.py', 'test_rq1_response_reliability01.py',
                 'rq1_response_reliability_contract01.json', 'check_rq1_response_reliability_pure01.py',
                 'rq1_response_reliability_pure01_packet.json', 'check_rq1_response_reliability_native01.py',
                 'run_rq1_response_reliability_native01.py', 'rq1_response_reliability_native01_packet.json',
                 'ROOT_RQ1_RESPONSE_PURE_REVIEW01.md', 'ROOT_RQ1_RESPONSE_NATIVE_REVIEW01.md',
                 'RQ1_CACHED_CALIBRATION_FEASIBILITY01.md', 'verify_response_reliability_synthesis01.py',
                 'analyze_rq2_cached_mechanism01.py', 'rq2_cache_mechanism_contract01.json'):
        add(name, PREP / name)
    add(Path(__file__).name, Path(__file__).resolve())
    add('report.md', REPORT)
    add('synthesis.json', PREP / 'rq1_response_reliability_synthesis01.json')
    add('synthesis_verification.json', PREP / 'rq1_response_reliability_synthesis_verification01.json')
    add('reference_CPU09_manifest.json', BASE / 'manifest.json')
    add('reference_RQ2_cache_manifest.json', OLD_CACHE / 'manifest.json')
    for alias, name in (('source__windows_owned_worker.py', 'scripts/research/windows_owned_worker.py'),
                        ('source__evidence.py', 'src/knowledge_tracing/evidence.py'),
                        ('source__gam_evaluation.py', 'src/knowledge_tracing/gam_kt/evaluation.py'),
                        ('source__bkt_metrics.py', 'src/knowledge_tracing/bkt_baseline/metrics.py')):
        add(alias, ROOT / name)
    for path in sorted(inner.iterdir()):
        add(path.name, path)
    for label, directory in (('pure', 'rq1-response-reliability-pure01'),
                             ('pure_owned', 'rq1-response-reliability-pure01-owned'),
                             ('native_outer', 'rq1-response-reliability-native01-outer'),
                             ('native_owned', 'rq1-response-reliability-native01-owned')):
        for path in sorted((PREP / directory).iterdir()):
            need(path.is_file() and path.suffix in ('.json', '.jsonl', '.log'), 'flat terminal evidence only')
            add(label + '__' + path.name, path)
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), sha256=sha(path),
                      bytes=path.stat().st_size) for alias, path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory) <= 4*1024**2, 'compact evidence cap4MiB')
    return inventory, refs, pure, final


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
    need(sum((args.prepare_dry, args.check_dry, args.close)) == 1, 'one explicit operation')
    destination = ROOT / 'research_tracking/runs' / RUN_ID
    need(not destination.exists(), 'immutable destination absent')
    inventory, refs, pure, final = gather(args.report_sha256)
    dry = dict(run_id=RUN_ID, report_sha256=args.report_sha256, copies=inventory, reference_inputs=refs,
               generated_outputs=list(GENERATED), expected_output_count=len(inventory)+len(GENERATED),
               native_final_sha256=NATIVE_SHA, pure_final_sha256=PURE_SHA,
               synthesis_sha256=SYNTHESIS_SHA, synthesis_recipe_sha256=RECIPE_SHA)
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=len(inventory),
                              outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'reviewed dry/current selected bytes identical')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', outputs=dry['expected_output_count'])))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'Root exact-dry closure approval')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# RQ1 — response reliability và sai lệch theo persona\n\n'
            'Phân tích thứ cấp giữ120worlds/14400served events,10seedclusters cũ. '
            'ECE15 gộp có thể che lệch trái dấu giữa persona. Native actual và pure7 đạt. '
            'Oraclep chỉ ở evaluator, conceptmastery/thresholdtruth chưa được chấm. '
            'Không fit hoặc sinh world mới. Gzip/runtime chỉ referenceSHA. '
            'Báo cáo chính tại ../../reports/rq1_response_reliability_diagnostic_20261109.md.\n')
    sources = [ROOT / row['source'] for row in inventory] + [ROOT / name for name in refs] + [DRY]
    sources = list(dict.fromkeys(sources))
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='RQ1_CACHED_RESPONSE_RELIABILITY_DIAGNOSTIC',
            actual_model_calls=0, new_world_transitions=0, new_independent_seed_families=0), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source before copy')
            (out / row['copy']).write_bytes(source.read_bytes())
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/aftercopy SHA')
            copied.append(dict(**row, input_sha256_after=sha(source), copied_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', refs)
        write(out / 'source_binding.json', dict(source_before=final['source_before'], source_after=final['source_after'],
              inputs_before=final['inputs_before'], inputs_after=final['inputs_after'],
              CPU09_manifest_sha256=sha(BASE / 'manifest.json'), prior_RQ2_cache_manifest_sha256=OLD_CACHE_SHA,
              original_gzip_and_runtime_copied=False, analysis_test_contract_unchanged=True,
              synthesis_recipe_saved_after_original_derivation=True))
        write(out / 'scope.json', dict(worlds_reused=120, events_reused=14400, reused_seed_clusters=10,
              world_groups=120, persona_arm_groups=12, pooled_arm_groups=4, bins=2040, repeated_row_uses=43200,
              new_independent_seed_families=0, actual_model_calls=0, new_world_transitions=0,
              oracle_role='ACTUAL_SERVED_ITEM_RESPONSE_EVALUATOR_ONLY', response_temperature_fitted=False,
              native_mastery_truth_evaluated=False, inference='SECONDARY_DESCRIPTIVE_NO_CI_PVALUES',
              cross_arm_population='OWN_SERVED_HISTORIES', research_completion=False))
        write(out / 'timing_scope.json', dict(pure_seconds=pure['elapsed_seconds'],
              native_outer_seconds=final['elapsed_seconds'], owned_seconds=final['owned_receipt']['elapsed_seconds'],
              native_resources=final['resources'], native_whole_cap_seconds=60, pure_whole_cap_seconds=30,
              nested_times_are_not_summed=True,
              root_tool_observations=dict(origin='Root messages, separate from stored receipts',
                  pure_terminal_seconds=1.2688417, pure_printed_seconds=.6585864,
                  native_terminal_seconds=1.4715582, native_printed_seconds=.8931119)))
        write(out / 'closure_review.json', dict(reference=args.review_reference,
              dry_sha256=args.expected_dry_sha256, report_sha256=args.report_sha256, root_closure_no_reexecution=True))
        (out / 'reviewed_dry.json').write_bytes(DRY.read_bytes())
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'reviewed dry copy')
        (out / 'raw_log_paths.txt').write_text('\n'.join(row['source'] for row in inventory
              if row['source'].endswith(('.log', '.jsonl'))) + '\n', encoding='utf-8')
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact declared outputs')
        need(all(sha(ROOT / row['source']) == row['sha256'] for row in inventory)
             and all(sha(ROOT / name) == row['sha256'] for name, row in refs.items()), 'all inputs unchanged after copy')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == dry['expected_output_count'], 'exact closed output count')
    print(json.dumps(dict(**verified, path=destination.relative_to(ROOT).as_posix(),
                          manifest_sha256=sha(destination / 'manifest.json'))))


if __name__ == '__main__':
    main()
