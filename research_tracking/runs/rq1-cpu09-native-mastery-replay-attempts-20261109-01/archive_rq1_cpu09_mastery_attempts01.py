"""Root dry/close hồ sơ replay bị dừng, chỉ hash/copy bằng chứng nhỏ."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'rq1-cpu09-native-mastery-replay-attempts-20261109-01'
REPORT = ROOT / 'research_tracking/reports/rq1_cpu09_native_mastery_replay_readiness_20261109.md'
DRY = PREP / 'rq1_cpu09_mastery_attempts_archive_dry01.json'
PURE_SHA = '05542d273613da117ede00d2c90421735183fb5af41dc6421f902c52d6ca38ee'
CANARY_SHA = 'ff7089d8112df51e6b577779839443e5a4fcbe95a85896e8793ad211ec01b517'
NATIVE_SHAS = (
    '1d9a6910bc5c8cf58e3677e380b31bd30a0ca524753e0232a230d74578957e4c',
    '42ca471369f2d2cfb92c18e9c5ae8f9adc8d0fa041507c611538162faeb422fe',
    '3406e35320346e038d6c4279d7b730ac2a90f3a551ac79d420fb0af0234c626b',
    '181f491b335f7313aed12cf3437b37db0bfd36434e38e58cf176ebfbe7752886',
    '67563ec93cb263748710f26a2c756c16c69b0d949796c42f2ab11fe461bc59d0',
)
GENERATED = tuple(sorted(('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json',
    'scope.json', 'timing_scope.json', 'source_binding.json', 'closure_review.json', 'reviewed_dry.json', 'raw_log_paths.txt')))
TOP_FILES = (
    'replay_rq1_cpu09_native_mastery01.py', 'test_rq1_cpu09_native_mastery01.py',
    'test_rq1_cpu09_source_adapter01.py', 'check_rq1_cpu09_mastery_pure01.py',
    'check_rq1_cpu09_source_adapter_pure01.py', 'rq1_cpu09_mastery_pure01_packet.json',
    'rq1_cpu09_source_adapter_pure01_packet.json', 'rq1_cpu09_mastery_native02_revision.json',
    'ROOT_RQ1_CPU09_MASTERY_PURE_REVIEW01.md', 'ROOT_RQ1_SOURCE_ADAPTER_PURE_REVIEW01.md',
    'RQ1_CPU09_NATIVE_MASTERY_REPLAY_FEASIBILITY02.md', 'RQ1_CPU09_NATIVE_MASTERY_STATIC_REVIEW01.md',
    'RQ1_CPU09_NATIVE_MASTERY_TYPES_SUPPLEMENT01.md',
    'source_adapter_contract03_before_getcode_scope.json', 'source_adapter_packet01_before_getcode_scope.json',
    'source_adapter_test01_before_getcode_scope.py', 'source_adapter_native_packet03_before_count_fix.json',
    'native04_packet_before_metadata_correction.json',
)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and ROOT.resolve() == ROOT, 'fixed repository')
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current /= part
        need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(), 'physical evidence')
    need(path.resolve() == path and path.is_file(), 'regular evidence file')
    return path


def sha(path, cap=4*1024**2):
    safe(path)
    need(path.stat().st_size <= cap, 'bounded evidence input')
    digest = hashlib.sha256()
    count = 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            count += len(block)
            need(count <= cap, 'stream hash cap')
            digest.update(block)
    need(count == path.stat().st_size, 'stable file size')
    return digest.hexdigest()


def read(path):
    safe(path)
    need(path.stat().st_size <= 1024**2, 'small JSON')
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def gather(report_sha):
    need(sha(REPORT) == report_sha, 'reviewed canonical report bytes')
    pure = read(PREP / 'rq1-cpu09-mastery-pure01/result.json')
    canary = read(PREP / 'rq1-cpu09-source-adapter-pure01/result.json')
    for result, stage, pin, count, status in (
        (pure, 'rq1-cpu09-mastery-pure01', PURE_SHA, 12, 'ACCEPTED_12_CPU09_MASTERY_PURE_METHODS'),
        (canary, 'rq1-cpu09-source-adapter-pure01', CANARY_SHA, 5, 'ACCEPTED_5_CPU09_SOURCE_ADAPTER_PURE_METHODS')):
        need(sha(PREP / stage / 'result.json') == pin and result['status'] == status
             and result['counts'] == dict(tests=count, failures=0, errors=0, skipped=0,
                 unexpected_successes=0, expected_failures=0) and result['errors'] == [], 'actual two pure suites')
        owned = result['owned_receipt']
        need(owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
             and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True, 'actual pure cleanup')
        need(result['worker_result']['methods_restored'] is True and result['worker_result']['monitor_stopped'] is True
             and not (PREP / stage / 'postwrite-rejection.json').exists(), 'actual restored pure scope')
    finals = []
    for number, expected in enumerate(NATIVE_SHAS, 1):
        path = PREP / f'rq1-cpu09-mastery-native{number:02d}-outer/final.json'
        result = read(path)
        need(sha(path) == expected and result['status'] == 'REJECTED_KEEP_CPU09_MASTERY_REPLAY'
             and result['artifacts'] == {} and result['validation'] is None, 'all historical native verdicts remain rejected')
        if number == 1:
            need(result['owned_receipt']['GO_released'] is False
                 and result['owned_receipt']['observed_owned_tokens'] == []
                 and not (PREP / 'rq1-cpu09-mastery-native01-owned').exists(), 'preGO failure has no worker/owned directory')
        else:
            need(result['owned_receipt']['GO_released'] is True
                 and result['owned_receipt']['cleanup_accepted'] is True
                 and result['owned_receipt']['job_active_after_cleanup'] == 0, 'rejected worker reaped/Job0')
        finals.append(result)
    need(finals[3]['resources']['samples'] == 4001 and finals[3]['resources']['terminated_owned_job'] is True
         and any(row['message'] == 'monitor journal sample cap' for row in finals[3]['resources']['errors']), 'actual monitor failure04')
    need(finals[4]['resources']['errors'] == [] and finals[4]['resources']['samples'] == 1594
         and finals[4]['resources']['observed_family_peak_rss_bytes'] <= 1024**3
         and finals[4]['resources']['observed_minimum_available_ram_bytes'] >= 2*1024**3, 'actual05 monitored RAM in bounds')
    failure = read(PREP / 'rq1-cpu09-native-mastery-attempt04/failure.json')
    profile_counts = dict(__init__=25, select=2963, predict=2963, update=2963, _decayed_pi=8889)
    need(failure['error'] == "ValueError('worker elapsed allocation')" and failure['truth_accepted'] is False
         and failure['native_started'] == failure['native_returned'] == profile_counts
         and failure['native_profile_return_scope'] == 'PROFILE_RETURN_EVENTS_NOT_PROOF_OF_SUCCESSFUL_BODY_ON_FAILURE',
         'actual worker05 timeout/call-event scope')
    for index in range(1, 5):
        directory = PREP / f'rq1-cpu09-native-mastery-attempt{index:02d}'
        need(not any((directory / name).exists() for name in ('parity.json', 'confusion.json', 'native_query_readouts.jsonl', 'result.json')),
             'no completed native parity/truth artifact')
    packet = read(PREP / 'rq1_cpu09_mastery_native04_packet.json')
    contract = read(PREP / 'rq1_cpu09_native_mastery_contract04.json')
    refs = dict(contract['input_pins'])
    refs.update(packet['source_pins'])
    for name, row in refs.items():
        need(sha(ROOT / name) == row['sha256'] and (ROOT / name).stat().st_size == row['bytes'], 'reference current byte identity')
    paths, journal_refs = {}, {}

    def add(alias, path):
        safe(path)
        need(alias not in paths and Path(alias).name == alias and path.stat().st_size <= 256*1024,
             'small unique flat copy')
        need(path.suffix.lower() in ('.py', '.md', '.json', '.jsonl', '.log'), 'source/text only')
        paths[alias] = path

    for name in TOP_FILES:
        add(name, PREP / name)
    for number in range(1, 5):
        for prefix, suffix in (('worker_rq1_cpu09_native_mastery', '.py'), ('rq1_cpu09_native_mastery_contract', '.json'),
                               ('rq1_cpu09_mastery_native', '_packet.json')):
            name = f'{prefix}{number:02d}{suffix}'
            add(name, PREP / name)
    for number in range(1, 6):
        for name in (f'run_rq1_cpu09_mastery_native{number:02d}.py', f'ROOT_RQ1_CPU09_MASTERY_NATIVE_REVIEW{number:02d}.md'):
            add(name, PREP / name)
    add(Path(__file__).name, Path(__file__).resolve())
    add('report.md', REPORT)
    add('source__windows_owned_worker.py', ROOT / 'scripts/research/windows_owned_worker.py')
    add('source__evidence.py', ROOT / 'src/knowledge_tracing/evidence.py')
    folders = [('replay_pure', 'rq1-cpu09-mastery-pure01'), ('replay_pure_owned', 'rq1-cpu09-mastery-pure01-owned'),
               ('adapter_pure', 'rq1-cpu09-source-adapter-pure01'), ('adapter_pure_owned', 'rq1-cpu09-source-adapter-pure01-owned')]
    for number in range(1, 6):
        folders.append((f'native{number:02d}_outer', f'rq1-cpu09-mastery-native{number:02d}-outer'))
        if number > 1:
            folders.append((f'native{number:02d}_owned', f'rq1-cpu09-mastery-native{number:02d}-owned'))
    folders.extend((f'inner{number:02d}', f'rq1-cpu09-native-mastery-attempt{number:02d}') for number in range(1, 5))
    for label, directory in folders:
        for path in sorted((PREP / directory).iterdir()):
            need(path.is_file() and path.suffix in ('.json', '.jsonl', '.log'), 'bounded flat terminal evidence')
            if path.stat().st_size > 256*1024:
                need(path.name == 'memory.jsonl' and label in ('native04_outer', 'native05_outer'), 'only2known large journals referenced')
                name = path.relative_to(ROOT).as_posix()
                row = dict(sha256=sha(path), bytes=path.stat().st_size)
                refs[name] = row
                journal_refs[name] = row
            else:
                add(label+'__'+path.name, path)
    need(len(journal_refs) == 2, 'exact large journal references')
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)
                 for alias, path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory) <= 4*1024**2, 'compact copied evidence ceiling4MiB')
    return inventory, refs, journal_refs, pure, canary, finals, failure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--prepare-dry', action='store_true')
    parser.add_argument('--check-dry', action='store_true')
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv', '.venv only')
    need(sum((args.prepare_dry, args.check_dry, args.close)) == 1, 'one explicit operation')
    destination = ROOT / 'research_tracking/runs' / RUN_ID
    need(not destination.exists(), 'immutable destination absent')
    inventory, refs, journals, pure, canary, finals, failure = gather(args.report_sha256)
    dry = dict(run_id=RUN_ID, report_sha256=args.report_sha256, copies=inventory, reference_inputs=refs,
               large_journal_references=journals, generated_outputs=list(GENERATED),
               expected_output_count=len(inventory)+len(GENERATED), pure12_sha256=PURE_SHA,
               adapter5_sha256=CANARY_SHA, rejected_native_final_sha256=list(NATIVE_SHAS))
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=len(inventory),
                              outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'reviewed dry/current bytes identical')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', outputs=dry['expected_output_count'])))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'Root exact-dry closure approval')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys([ROOT / row['source'] for row in inventory] + [ROOT / name for name in refs] + [DRY]))
    note = ('# RQ1 — native mastery replay chưa xác minh\n\n'
            'Pure12 và adapter5 đạt. Năm native attempts bị từ chối, đã dừng. '
            'Chưa full14400parity/truth/confusion, không có scientificaccuracyfinding. '
            'Giữ rawfails/sources/reviews, hai memoryjournals lớn chỉ referenceSHA. '
            'Báo cáo tại ../../reports/rq1_cpu09_native_mastery_replay_readiness_20261109.md.\n')
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='RQ1_NATIVE_MASTERY_REPLAY_ENGINEERING_STOPPED',
            native_replay_validated=False, scientific_accuracy_finding=False, new_independent_seed_families=0), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            path = ROOT / row['source']
            need(sha(path) == row['sha256'], 'copy input before SHA')
            (out / row['copy']).write_bytes(path.read_bytes())
            need(sha(path) == sha(out / row['copy']) == row['sha256'], 'input/copy/postcopy SHA')
            copied.append(dict(**row, input_sha256_after=sha(path), copied_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', dict(files=refs, large_journals=journals, gzip_runtime_copied=False))
        write(out / 'scope.json', dict(status='STOPPED_NOT_NATIVE_VALIDATED', pure_replay_methods=12, adapter_canary_methods=5,
              accepted_native_attempts=0, rejected_native_attempts=5, full_parity=False, truth_confusion_accepted=False,
              scientific_accuracy_finding=False, independent_seed_families_added=0,
              native04_calls='UNKNOWN_LE_RESERVED', native05_profile_calls=failure['native_started'],
              profile_return_events='NOT_SUCCESSFUL_BODY_PROOF_ON_REJECTED_ATTEMPT', new_native_dispatch_authorized=False))
        write(out / 'timing_scope.json', dict(pure12_elapsed_seconds=pure['elapsed_seconds'], adapter5_elapsed_seconds=canary['elapsed_seconds'],
              native_outer_elapsed_seconds=[row['elapsed_seconds'] for row in finals], native05_worker_elapsed_seconds=failure['elapsed_seconds'],
              per_native_whole_cap_seconds=180, nested_times_not_summed=True, resources=[row['resources'] for row in finals]))
        write(out / 'source_binding.json', dict(pure12_source_sha256=pure['source_sha256'], adapter5_source_sha256=canary['source_sha256'],
              native_source_inputs_before=[row['source_inputs_before'] for row in finals],
              native_source_inputs_after=[row['source_inputs_after'] for row in finals],
              postrun_full_guards_claimed=False, presentday_archive_copy_verification_separate=True,
              source_only_snapshots_are_not_additional_test_runs=True))
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
              report_sha256=args.report_sha256, closure_executes_no_replay_or_tests=True))
        (out / 'reviewed_dry.json').write_bytes(DRY.read_bytes())
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'reviewed dry copy')
        logs = [row['source'] for row in inventory if row['source'].endswith(('.log', '.jsonl'))] + list(journals)
        (out / 'raw_log_paths.txt').write_text('\n'.join(logs)+'\n', encoding='utf-8')
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact declared outputs')
        need(all(sha(ROOT / row['source']) == row['sha256'] for row in inventory)
             and all(sha(ROOT / name) == row['sha256'] for name, row in refs.items()), 'all input/reference postcopy hashes')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == dry['expected_output_count'], 'closed output count')
    print(json.dumps(dict(**verified, path=destination.relative_to(ROOT).as_posix(), manifest_sha256=sha(destination / 'manifest.json'))))


if __name__ == '__main__':
    main()
