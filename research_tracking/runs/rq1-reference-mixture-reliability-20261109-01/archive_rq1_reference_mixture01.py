"""ROOT tạo inventory/closure sau review. Không tính lại reliability hoặc replay."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'rq1-reference-mixture-reliability-20261109-01'
REPORT = ROOT / 'research_tracking/reports/rq1_reference_mixture_reliability_20261109.md'
DRY = PREP / 'rq1_reference_mixture_archive_dry01.json'
INNER = PREP / 'reference-mixture-cached-attempt01'
OUTER = PREP / 'reference-mixture-cached-outer01'
OWNED = PREP / 'reference-mixture-cached-owned01'
BEFORE = PREP / 'pre-reference-mixture-test-rounding-fix01'
PINS = {
    'analyze_rq1_reference_mixture01.py': '52ee0f409ad6752a3413e18565e31b95908dec57574739a8f76fe5aa01121b43',
    'test_rq1_reference_mixture01.py': 'a6b6bc737f79489824fa4622c0b6a11ee18ebf398bca375a502d444912ec23b7',
    'rq1_reference_mixture_contract01.json': '5ba4d9da4fd98aeac4dd9ead2250b7f8252cb83c076e52cc6fa4242eb94b510a',
    'run_reference_mixture_cached01.py': '05308306d46c537381b505b0588e638aa1c567cfdb2a48eb07d85c39af586eb1',
    'RQ1_REFERENCE_MIXTURE_STATIC_REVIEW01.md': '4637db5c57046a702ab9b01021d35cc9e5f3d16c51d158b36306f968cfca3730',
    'crosscheck_reference_mixture_numeric01.py': '0afddc1332c5d9ed4fcc43148bb61471e8b1cbc833760ef1046f2771eeb41ea0',
    'reference_mixture_numeric_check01.json': '142af81352c48b0557d839b4a31354734019bf216eb1c5c128550edbd8e37d41',
}
OUTER_SHA = 'ba0b9fbb25012d65964ea2cb5c2063edc3a7c9c66e7c12eabfe043784595b7a3'
PURE01_SHA = 'cd34065167616b59b454f3b4d9bbb46b9694d48eccf11ed570f2f2c47c7750aa'
PURE02_SHA = 'a8bfb05a49e7b887805a4d6e8782dce78f1ea89450f78864e299a242c01a3896'
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json',
             'scope.json', 'timing_scope.json', 'closure_review.json', 'reviewed_dry.json', 'raw_log_paths.txt')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'root-bound physical path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no aliases')
    need(path.is_file(), 'regular selected file')


def sha(path):
    safe(path)
    need(path.stat().st_size <= 4 * 1024**2, 'bounded small source/receipt')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable read size')
    return hashlib.sha256(raw).hexdigest()


def read(path):
    sha(path)
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def gather(report_sha):
    need(re.fullmatch('[a-f0-9]{64}', report_sha) and sha(REPORT) == report_sha, 'externally reviewed report SHA')
    for name, pin in PINS.items():
        need(sha(PREP / name) == pin, 'final selected source/independent proof pin')
    pure01 = read(PREP / 'reference-mixture-pure01/result.json')
    pure02 = read(PREP / 'reference-mixture-pure02/result.json')
    need(sha(PREP / 'reference-mixture-pure01/result.json') == PURE01_SHA
         and sha(PREP / 'reference-mixture-pure02/result.json') == PURE02_SHA, 'actual pure receipts')
    need(pure01['status'] == 'REJECTED' and pure01['returncode'] == 1 and pure01['tests'] == 8
         and pure01['timeout'] is False and pure01['elapsed_seconds'] < 10
         and pure01['source_before'] == pure01['source_after'], 'preserved failed pure01')
    need(pure02['status'] == 'ACCEPTED_REFERENCE_MIXTURE_PURE' and pure02['returncode'] == 0
         and pure02['tests'] == 8 and pure02['timeout'] is False and pure02['elapsed_seconds'] < 10
         and pure02['source_before'] == pure02['source_after'], 'actual accepted pure02')
    old_test = BEFORE / 'test_rq1_reference_mixture01.py.before'
    old_contract = BEFORE / 'rq1_reference_mixture_contract01.json.before'
    need(sha(old_test) == '59c1aec7ccf34611433ad3f2cea1bcc3d08e2782656d3f9689b707b44f9f110c'
         and sha(old_contract) == '40e54f22b5aefe70f0234856379d762c5289c5823a59b3a81a5e28116e91b69e', 'old tested bytes retained')
    for label, receipt in (('copy-verification.json', old_test), ('contract-copy-verification.json', old_contract)):
        proof = read(BEFORE / label)
        need(proof['exact_copy'] is True and proof['source_before_sha256'] == proof['copy_sha256']
             == proof['source_after_copy_sha256'] == sha(receipt), 'before/copy/after preservation')
    stderr01 = (PREP / 'reference-mixture-pure01/stderr.log').read_text(encoding='utf-8')
    stderr02 = (PREP / 'reference-mixture-pure02/stderr.log').read_text(encoding='utf-8')
    need('Ran 8 tests' in stderr01 and 'FAILED (failures=1)' in stderr01
         and 'test_exact_join_one_response_mean_and_input_immutability' in stderr01, 'actual eight / one failure log')
    need('Ran 8 tests' in stderr02 and 'OK' in stderr02 and 'FAILED' not in stderr02, 'actual accepted eight log')
    for name, pin in pure02['source_after'].items():
        need(sha(ROOT / name) == pin, 'current pure02 sources')
    final = read(OUTER / 'final.json')
    need(sha(OUTER / 'final.json') == OUTER_SHA and final['status'] == 'ACCEPTED_CACHED_REFERENCE_MIXTURE'
         and final['error'] is None and final['elapsed_seconds'] < 10 and final['whole_cap_seconds'] == 10
         and final['environment_restored'] is True and final['automatic_retry'] is False, 'whole cached operation accepted')
    owned = final['receipt']
    need(owned['accepted'] is True and owned['returncode'] == 0 and owned['worker_returncode_before_cleanup'] == 0
         and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
         and owned['errors'] == owned['cleanup_errors'] == [] and owned['popen_handle_closed'] is True
         and owned['actual_worker_in_job_before_GO'] is True, 'actual owned clean exit / Job0')
    need(not any((OUTER / name).exists() for name in ('postwrite-rejection.json', 'failure.log'))
         and not any((INNER / name).exists() for name in ('postwrite-rejection.json', 'failure.log')), 'no late failure')
    need({p.name for p in INNER.iterdir()} == {'summary.json', 'joined_rows.jsonl', 'validation.json', 'result.json'}, 'exact four terminal outputs')
    for name, item in final['outputs'].items():
        need((INNER / name).stat().st_size == item['bytes'] and sha(INNER / name) == item['sha256'], 'outer actual output inventory')
    result, summary, validation = (read(INNER / name) for name in ('result.json', 'summary.json', 'validation.json'))
    need(result['status'] == 'ACCEPTED_CACHED_REFERENCE_MIXTURE_RESPONSE_DIAGNOSTIC_ONLY'
         and result['source_input_before'] == result['source_input_after']
         and result['no_added_native_calls'] is True and result['independent_new_N'] == 0, 'actual cached-only result')
    need(result['outputs_sha256'] == {name: item['sha256'] for name, item in final['outputs'].items() if name != 'result.json'}, 'actual result / outer output binding')
    need(summary['arm_rows'] == 2160 and summary['unique_query_responses'] == 1080
         and len(summary['groups']) == 32 and sum(len(g['bins']) for g in summary['groups']) == 480
         and sum(len(g['threshold_strata']) for g in summary['groups']) == 64
         and validation['all2160arm_rows'] is True and validation['all1080query_y_pairs'] is True
         and validation['all18CRC'] is True and validation['source_input_before'] == validation['source_input_after']
         == result['source_input_before'], 'exact population / partitions / joins')
    numeric = read(PREP / 'reference_mixture_numeric_check01.json')
    need(numeric['status'] == 'ACCEPTED_INDEPENDENT_DECIMAL_NUMERIC_CHECK' and numeric['groups'] == 32
         and numeric['bins'] == 480 and numeric['strata'] == 64 and numeric['decimal_precision'] == 50
         and numeric['elapsed_seconds'] < numeric['cap_seconds'] == 5
         and numeric['source_sha256'] == PINS['crosscheck_reference_mixture_numeric01.py']
         and numeric['input_sha256'] == {name: sha(INNER / name) for name in ('summary.json', 'joined_rows.jsonl')}, 'independent numeric proof')
    references = {}
    for name, pin in result['source_input_after'].items():
        path = ROOT / name
        need(sha(path) == pin, 'all original reference/current source SHA')
        references[name] = dict(sha256=pin, bytes=path.stat().st_size, copied_original=False)
    paths = {}

    def add(alias, path):
        safe(path)
        need(alias not in paths and Path(alias).name == alias and not any(c in alias for c in '\t\r\n'), 'unique portable flat alias')
        need(path.suffix.lower() in ('.py', '.md', '.json', '.jsonl', '.log', '.before'), 'selected text only')
        paths[alias] = path

    for name in (*PINS, 'run_reference_mixture_pure01.py', 'run_reference_mixture_pure02.py'):
        add(name, PREP / name)
    add(Path(__file__).name, Path(__file__).resolve())
    add('report_snapshot.md', REPORT)
    for path in sorted(BEFORE.iterdir()):
        need(path.is_file(), 'flat preservation folder')
        add('pre_fix__' + path.name, path)
    for prefix, directory in (('pure01', PREP / 'reference-mixture-pure01'),
                              ('pure02', PREP / 'reference-mixture-pure02'),
                              ('cached_outer', OUTER), ('cached_owned', OWNED)):
        for path in sorted(directory.iterdir()):
            need(path.is_file(), 'flat terminal-only folder')
            add(prefix + '__' + path.name, path)
    for path in sorted(INNER.iterdir()):
        add(path.name, path)
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)
                 for alias, path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory) < 4 * 1024**2, 'compact bundle payload under4MiB')
    return inventory, references, pure01, pure02, final, numeric


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
    need(sum((args.prepare_dry, args.check_dry, args.close)) == 1, 'one explicit metadata operation')
    destination = ROOT / 'research_tracking/runs' / RUN_ID
    need(not destination.exists(), 'new immutable bundle destination absent')
    inventory, refs, pure01, pure02, final, numeric = gather(args.report_sha256)
    dry = dict(run_id=RUN_ID, report_sha256=args.report_sha256, copies=inventory, reference_inputs=refs,
               generated_outputs=list(GENERATED), expected_output_count=len(inventory) + len(GENERATED),
               cached_outer_sha256=OUTER_SHA, pure01_sha256=PURE01_SHA, pure02_sha256=PURE02_SHA,
               independent_numeric_sha256=PINS['reference_mixture_numeric_check01.json'])
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=len(inventory),
                              outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'exact reviewed dry/current bytes')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', outputs=dry['expected_output_count'])))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact-dry closure approval')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# RQ1 — Reliability của raw reference-mixture response\n\n'
            'Đọc lại2160arm rows/1080query-response của9fixed trajectories,3seedfamilies cũ. '
            'Mỗi arm dùng một y cho một mean3forecast, không ba reference labels. '
            'Giữ32views/480bins/64strata; pooled/profile/seed khác nhau. '
            'Pure01 7PASS/1known-answer roundingFAIL và pure02 8PASS được giữ riêng. '
            'ROOTcachedouter accepted/Job0, independent Decimalcheck đủmọi cells. '
            'Không chạy policy, oracle, teacher, fit hoặc thêm N. Không masterytruth/calibrator/causalbenefit. '
            'Các gzip cũ tham chiếu SHA, không copy lại. Manifest xác nhận closure thực tế. '
            'Báo cáo tại ../../reports/rq1_reference_mixture_reliability_20261109.md.\n')
    sources = [ROOT / row['source'] for row in inventory] + [ROOT / name for name in refs] + [DRY]
    sources = list(dict.fromkeys(sources))
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='RQ1_CACHED_REFERENCE_MIXTURE_RESPONSE_DIAGNOSTIC',
            arm_rows=2160, unique_query_responses=1080, new_independent_N=0,
            native_calls=0, oracle_reads=0, research_RQ_completion=False), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source before copy')
            with (out / row['copy']).open('xb') as stream:
                stream.write(source.read_bytes())
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/source-after SHA')
            copied.append(dict(**row, source_sha256_after_copy=sha(source), copy_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', refs)
        write(out / 'scope.json', dict(arm_rows=2160, unique_query_responses=1080, paired_trajectories=9,
              reused_seed_families=3, fixed_group_specs=16, views=32, bins=480, threshold_strata=64,
              one_y_per_mean3_per_arm=True, new_independent_N=0, native_model_teacher_optimizer_calls=0,
              oracle_reads=0, target='UNIFORM_REFERENCE_MIXTURE_RESPONSE_CONDITIONAL_ON_HISTORY_AND_CONCEPT',
              mastery_truth_or_accuracy=False, calibrated_V1_or_Tfit=False, causal_or_learning_benefit=False,
              stopped_native05_lane_reopened=False, all_results_preserved=True))
        write(out / 'timing_scope.json', dict(pure01_seconds=pure01['elapsed_seconds'], pure01_cases=8,
              pure01_pass=7, pure01_fail=1, pure02_seconds=pure02['elapsed_seconds'], pure02_cases=8,
              pure02_pass=8, cached_outer_stored_seconds=final['elapsed_seconds'],
              cached_owned_seconds=final['receipt']['elapsed_seconds'], cached_whole_cap_seconds=10,
              numeric_check_seconds=numeric['elapsed_seconds'], numeric_cap_seconds=5,
              root_tool_observation=dict(origin='ROOT message, distinct from stored receipts',
                  postwrite_seconds=1.5012412, toolwall_seconds=2.0847346), nested_times_not_summed=True))
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
              report_sha256=args.report_sha256, no_reexecution_at_closure=True))
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(DRY.read_bytes())
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'dry copy pin')
        (out / 'raw_log_paths.txt').write_text('\n'.join(row['source'] for row in inventory
              if row['source'].endswith(('.log', '.jsonl'))) + '\n', encoding='utf-8')
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact output inventory')
        need(all(sha(ROOT / row['source']) == row['sha256'] for row in inventory)
             and all(sha(ROOT / name) == item['sha256'] for name, item in refs.items()), 'all selected bytes unchanged after copies')
    verification = verify_evidence_bundle(destination)
    need(verification['artifacts'] == dry['expected_output_count'], 'verified manifest output count')
    print(json.dumps(dict(**verification, manifest_sha256=sha(destination / 'manifest.json'),
                          path=destination.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
