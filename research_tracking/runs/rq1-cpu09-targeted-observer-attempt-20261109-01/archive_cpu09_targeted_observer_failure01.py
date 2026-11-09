"""Chuẩn bị dry hoặc đóng archive pilot bị từ chối. ROOT thực thi sau review."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'rq1-cpu09-targeted-observer-attempt-20261109-01'
REPORT = PREP / 'CPU09_TARGETED_OBSERVER_FAILURE_REPORT_DRAFT01.md'
DRY = PREP / 'cpu09_targeted_observer_failure_archive_dry01.json'
INNER = PREP / 'cpu09-targeted-observer-native01'
OUTER = PREP / 'cpu09-targeted-observer-native01-outer'
OWNED = PREP / 'cpu09-targeted-observer-native01-owned'
SNAPSHOT = PREP / 'targeted-observer-before-restoration-fix01'
OLD = ROOT / 'research_tracking/runs/rq1-cpu09-native-mastery-replay-attempts-20261109-01'
PINS = {
    'pilot_rq1_cpu09_targeted_observer01.py': '23698defe20f5cccb5f8f70bc100c3709c353f7cb6e91cf0e12405b315814660',
    'run_rq1_cpu09_targeted_observer01.py': 'c892124ff8efe531374a95fa770a019c91418e14c1a7d12eb5a50a8a5f438e86',
    'rq1_cpu09_targeted_observer_contract01.json': '7f8f8b16371ea95fb2d99642f613b83896a54f3ef61a58a99ed5e423d693e163',
    'CPU09_TARGETED_OBSERVER_ROOT_REVIEW02.md': '4b671b97f182f0596960b38775c6605e60c7565f429fc73655da06929fe37c66',
    'RQ1_CPU09_OBSERVER_COST_PROPOSAL01.md': 'db68861629ae2810570683feb075db7059085db0683573eb0fa8700467c44705',
}
FINAL_SHA = '3c9572ab30529983259cf49239fc3f752faa9f46d36eb30ca0dac1f516dc60a8'
FAILURE_SHA = '6fb81020f5f97ceba360feb1b6bdc00ddf4a9c109f30b1ed5d19efe320798d7b'
OLD_MANIFEST_SHA = '95ffcb2e4922ff820231d3f57ff3e633c3edac5b1f50fec30ff6ff3b4c9222aa'
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json',
             'scope.json', 'timing_scope.json', 'closure_review.json', 'reviewed_dry.json', 'raw_log_paths.txt')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical repository path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no source/copy aliases')
    need(path.is_file() and path.stat().st_size <= 4 * 1024**2, 'bounded regular evidence input')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable byte size')
    return hashlib.sha256(raw).hexdigest()


def read(path):
    sha(path)
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def gather(report_sha):
    need(re.fullmatch('[a-f0-9]{64}', report_sha) and sha(REPORT) == report_sha, 'reviewed exact report bytes')
    for name, pin in PINS.items():
        need(sha(PREP / name) == pin, 'actual executed source/review pin')
    need(sha(OUTER / 'final.json') == FINAL_SHA and sha(INNER / 'failure.json') == FAILURE_SHA, 'actual rejected attempt pins')
    final, failure = read(OUTER / 'final.json'), read(INNER / 'failure.json')
    admission, contract = read(OUTER / 'admission.json'), read(PREP / 'rq1_cpu09_targeted_observer_contract01.json')
    need(final['status'] == failure['status'] == 'REJECTED_KEEP_PILOT_NO_RETRY'
         and final['phase'] == failure['phase'] == 'native' and final['automatic_retry'] is False
         and final['old_five_attempt_lane_reopened'] is False, 'rejected operational pilot, not scientific admission')
    need(final['elapsed_before_receipt_seconds'] < final['whole_cap_seconds'] == 60
         and failure['elapsed_before_receipt_seconds'] < 53, 'recorded terminal allocation scope')
    need(final['errors'] == [dict(type='ValueError', message='actual clean owned terminal')]
         and failure['errors'] == [
             dict(message='read outside pinned sources/inputs/runtime', phase='native_import_and_full_cache_validation', type='RuntimeError'),
             dict(message='read outside pinned sources/inputs/runtime', phase='postchecks', type='RuntimeError')],
         'actual generic read denials, no inferred first path')
    need(failure['direct_started'] == failure['direct_returned'] == {} and failure['phases'] == []
         and failure['loader_truth_validation_started'] is False and failure['loader_truth_validation_completed'] is False
         and failure['restoration_errors'] == [], 'pre-estimator/pre-cache-validation control flow')
    need({p.name for p in INNER.iterdir()} == {'failure.json', 'native_metadata.json', 'pure_checks.json'}, 'no reservation/OFF/ON/parity outputs')
    checks = read(INNER / 'pure_checks.json')
    need(checks['manufactured_checks'] == 5 and checks['native_calls'] == 0
         and len(checks['claims']) == 5 and checks['source_only_helpers'] is True, 'actual five inline checks')
    metadata = read(INNER / 'native_metadata.json')
    need(metadata == failure['native_windows_metadata'] and metadata['phase_closed'] is True
         and metadata['helper_calls'] == 1 and metadata['local_gethostname_calls'] == 1
         and metadata['hostname_persisted'] is False and metadata['outside_phase_popen_attempts']
         == metadata['outside_phase_socket_attempts'] == metadata['blocked_bootstrap_attempts'] == 0,
         'real metadata discovery, no false zero-process claim')
    receipt = read(OWNED / 'receipt.json')
    need(receipt == final['receipt'] and receipt['accepted'] is False and receipt['returncode'] == 1
         and receipt['worker_returncode_before_cleanup'] == 1 and receipt['cleanup_accepted'] is True
         and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
         and receipt['errors'] == receipt['cleanup_errors'] == [], 'worker failure with accepted owned cleanup')
    need(final['resources']['errors'] == [] and final['resources']['monitor_stopped'] is True
         and final['resources']['observed_family_peak_rss_bytes'] <= 1024**3
         and final['resources']['observed_minimum_available_ram_bytes'] >= 2 * 1024**3
         and final['environment_restored'] is True and final['outputs'] == {}, 'resource/cleanup versus missing scientific output')
    for name, pin in receipt['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log') and sha(OWNED / name) == pin, 'original owned stdout/stderr hashes')
    need(not (OUTER / 'postwrite-rejection.json').exists(), 'this attempt was not resource/postwrite rejection')
    expected = {name: row['sha256'] for name, row in contract['bindings'].items()}
    need(len(expected) == 33 and admission['source_input_before'] == failure['source_before']
         == failure['source_after'] == expected and final['source_input_before'] == expected
         and final['source_input_after'] == {}, 'recorded binding loop versus unsuccessful overall postchecks')
    need(sha(OLD / 'manifest.json') == OLD_MANIFEST_SHA and read(OLD / 'manifest.json')['status'] == 'completed', 'prior closed failure lane unchanged reference')
    refs = {}
    for name, pin in {**expected, (OLD / 'manifest.json').relative_to(ROOT).as_posix(): OLD_MANIFEST_SHA}.items():
        path = ROOT / name
        need(sha(path) == pin, 'archive-time reference source hash, not historical worker acceptance')
        refs[name] = dict(sha256=pin, bytes=path.stat().st_size, raw_copied=False,
                          scope='ARCHIVE_TIME_REFERENCE_BYTE_CHECK_ONLY')
    before_inventory = read(SNAPSHOT / 'inventory-before.json')
    copy_proof = read(SNAPSHOT / 'copy-verification.json')
    need(copy_proof['exact_copies'] is True and len(before_inventory['files']) == len(copy_proof['files']) == 4,
         'all old three sources and review01 retained')
    for row in copy_proof['files']:
        need(row['source_before_sha256'] == row['copy_sha256'] == row['source_after_copy_sha256']
             == sha(SNAPSHOT / row['copy']), 'old before/copy/after SHA proof')
    paths = {}

    def add(alias, path):
        sha(path)
        need(alias not in paths and Path(alias).name == alias and not any(c in alias for c in '\t\n\r')
             and path.suffix.lower() in ('.py', '.md', '.json', '.jsonl', '.log', '.before'), 'flat exact selected text input')
        paths[alias] = path

    for name in PINS:
        add(name, PREP / name)
    add('report.md', REPORT)
    add(Path(__file__).name, Path(__file__).resolve())
    for prefix, directory in (('worker', INNER), ('outer', OUTER), ('owned', OWNED), ('pre_fix', SNAPSHOT)):
        for path in sorted(directory.iterdir()):
            need(path.is_file(), 'only flat terminal evidence')
            add(prefix + '__' + path.name, path)
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)
                 for alias, path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory) < 2 * 1024**2, 'compact failure evidence under2MiB')
    return inventory, refs, final, failure


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
    need(not destination.exists(), 'immutable new destination absent')
    inventory, refs, final, failure = gather(args.report_sha256)
    dry = dict(run_id=RUN_ID, report_sha256=args.report_sha256, copies=inventory, reference_inputs=refs,
        generated_outputs=list(GENERATED), expected_output_count=len(inventory) + len(GENERATED),
        actual_native_pilot_verdict='REJECTED_KEEP_PILOT_NO_RETRY', actual_final_sha256=FINAL_SHA,
        failure_sha256=FAILURE_SHA, archive_completion_is_not_native_acceptance=True)
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=len(inventory), outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'exact reviewed dry matches current selected bytes')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', outputs=dry['expected_output_count'])))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact dry closure review')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# CPU09 targeted observer — pilot bị từ chối trước estimator\n\n'
            'Đây là archive failure vận hành. Five inline manufacturedchecks đã chạy; '
            'readguard từ chối trước cachevalidation/constructor/update, không có OFF/ON/parity/timing result. '
            'Knownpostcheckselfcontract không nằmallowlist, firstreadpathUNKNOWN do messagegeneric. '
            'Nativeverdict REJECTED, cleanupJob0/resourcechecks riêng đạt. '
            'Manifestcompleted chỉ xác nhận archive hoàn tất, không nativePASS/RQprogress. '
            'Lane5attempts cũ vẫnSTOPPED, không retry/đổi nguồn trongclosure. '
            'Report chi tiết tại [report.md](report.md). Originalcache/dependencies chỉreferenceSHA.\n')
    sources = [ROOT / row['source'] for row in inventory] + [ROOT / name for name in refs] + [DRY]
    sources = list(dict.fromkeys(sources))
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='CPU09_TARGETED_OBSERVER_PRE_ESTIMATOR_FAILURE_ARCHIVE',
            actual_pilot_verdict='REJECTED_KEEP_PILOT_NO_RETRY', actual_estimator_constructors=0,
            actual_estimator_updates=0, parity_accepted=False, new_independent_N=0), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'before copy SHA')
            with (out / row['copy']).open('xb') as stream:
                stream.write(source.read_bytes())
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'before/copy/after SHA')
            copied.append(dict(**row, source_after_copy_sha256=sha(source), copied_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', refs)
        write(out / 'scope.json', dict(actual_native_verdict='REJECTED_KEEP_PILOT_NO_RETRY',
            inline_manufactured_checks_passed=5, cache_validation_completed=False, estimator_constructors=0,
            estimator_updates=0, history_parity_accepted=False, targeted_ON_OFF_cost_measured=False,
            first_denied_read_path='UNKNOWN_NOT_LOGGED', postcheck_self_contract_allowlist_gap='SOURCE_IDENTIFIED',
            cleanup_accepted=True, job_active_after_cleanup=0, old_five_attempt_lane_reopened=False,
            new_independent_N=0, truth_accuracy_calibration_learning_benefit_claimed=False,
            archive_complete_status_does_not_promote_native_verdict=True))
        write(out / 'timing_scope.json', dict(worker_before_failure_receipt_seconds=failure['elapsed_before_receipt_seconds'],
            owned_seconds=final['receipt']['elapsed_seconds'], outer_stored_before_receipt_seconds=final['elapsed_before_receipt_seconds'],
            root_terminal_observed_seconds_approx=3.3976, root_observation_origin='ROOT message, not worker-generated receipt',
            whole_allocation_seconds=60, worker_allocation_seconds=53, nested_times_not_summed=True,
            resources=final['resources']))
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
            report_sha256=args.report_sha256, no_reexecution=True, actual_native_verdict_preserved='REJECTED_KEEP_PILOT_NO_RETRY'))
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(DRY.read_bytes())
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'reviewed dry exact copy')
        (out / 'raw_log_paths.txt').write_text('\n'.join(row['source'] for row in inventory
              if row['source'].endswith(('.log', '.jsonl'))) + '\n', encoding='utf-8')
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact selected outputs only')
        need(all(sha(ROOT / row['source']) == row['sha256'] for row in inventory)
             and all(sha(ROOT / name) == row['sha256'] for name, row in refs.items()), 'all sources unchanged after copies')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == dry['expected_output_count'], 'exact closed manifest count')
    print(json.dumps(dict(**verified, manifest_sha256=sha(destination / 'manifest.json'), path=destination.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
