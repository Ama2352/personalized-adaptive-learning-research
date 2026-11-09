"""Đóng bằng chứng dừng RAM đã có terminal; không replay hoặc phân tích JSONL."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
REPORT = PREP / 'CPU09_TARGETED_FULL_REPORT_DRAFT01.md'
CONTRACT = PREP / 'rq1_cpu09_targeted_full_contract01.json'
INNER = ROOT / 'experiments/gam_kt/results/rq1-cpu09-native-mastery-20261109-01'
OUTER = PREP / 'rq1-cpu09-targeted-full-native01-outer'
OWNED = PREP / 'rq1-cpu09-targeted-full-native01-owned'
RUN_ID = 'rq1-cpu09-native-mastery-20261109-01'
DRY = PREP / 'cpu09_targeted_full_archive_dry01.json'
FINAL_SHA = 'cd9d9b490c6484e390c0baab96a5fc63b08a3d83643a80f5502ca82932d98605'
PINS = {
    'worker_rq1_cpu09_targeted_full01.py': '703875efd07854874dc68c042ef5a7f1a84b83be504e8c090c94e418d437cebc',
    'run_rq1_cpu09_targeted_full01.py': 'feba22d87f10adf7b0065d6ace261b08c4ca4c53d3be27a289ecaef513351900',
    'rq1_cpu09_targeted_full_contract01.json': '6cfd2cfbe6d3398ea96128c2dcf72a1cad9da052c82b1289a9f6527afc6822d8',
    'pilot_rq1_cpu09_targeted_observer03.py': '1c84c3271556d2aa7b5d0ae709122504c2a4a008e8e9c4aa524d0345a10f5baf',
    'CPU09_TARGETED_FULL_ROOT_REVIEW01.md': '7eb1d1721cb9384668f614ae2342eb4b7e2b269a221a95ff1d8c167629ceb753',
    'verify_cpu09_full_ram_stop01.py': '374c1a7cb0a683f10812231125f51ceb35a562b2db1c3f28cb02341ab20663f5',
    'cpu09_full_ram_stop_postcheck01.json': '1c6eb0e3653bc2f0bbf0a79b5f5dfbe46f9fa76a08ff9ffdb28573db961192cd',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json',
             'scope.json', 'timing_scope.json', 'closure_review.json', 'reviewed_dry.json', 'raw_log_paths.txt')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path, cap=4 * 1024**2):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical root-bound input')
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current /= part
        need(not current.is_symlink() and not getattr(current, 'is_junction', lambda: False)(), 'no aliases')
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular file')
    size, digest = 0, hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(65536):
            size += len(block)
            need(size <= cap, 'stream byte cap')
            digest.update(block)
    need(size == path.stat().st_size, 'stable byte size')
    return digest.hexdigest()


def read(path):
    sha(path, 1024**2)
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def gather(args):
    need(all(re.fullmatch('[a-f0-9]{64}', value) for value in (args.report_sha256, args.outer_sha256)), 'external actual pins required')
    need(sha(REPORT) == args.report_sha256, 'reviewed actual report bytes')
    need(args.outer_sha256 == FINAL_SHA, 'this archive preserves the one actual RAM-rejected attempt')
    need(sha(OUTER / 'final.json') == args.outer_sha256, 'actual terminal SHA before parse; pending run cannot dry')
    for name, pin in PINS.items():
        need(sha(PREP / name) == pin, 'frozen executed source')
    contract, terminal = read(CONTRACT), read(OUTER / 'final.json')
    status = terminal['status']
    accepted = False
    need(status == 'REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY', 'actual RAM-rejected terminal only')
    need(terminal['whole_cap_seconds'] == 300 and terminal['old_five_attempt_lane_reopened'] is False
         and terminal['automatic_retry'] is False, 'same operation/no retry scope')
    resources, receipt = terminal['resources'], terminal['receipt']
    need(terminal['validation'] is None and terminal['outputs'] == {} and terminal['source_input_after'] == {},
         'no completed parity, scientific output admission, or worker source-postcheck')
    need(receipt['accepted'] is False and receipt['cleanup_accepted'] is True
         and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
         and receipt['returncode'] == 1 and terminal['environment_restored'] is True
         and resources['monitor_stopped'] is True and resources['terminated_owned_job'] is True,
         'actual rejected worker with verified owned cleanup')
    need(resources['observed_family_peak_rss_bytes'] == 171565056
         and resources['observed_minimum_available_ram_bytes'] == 2104508416
         and resources['observed_minimum_available_ram_bytes'] < contract['limits']['min_available_ram_bytes']
         and resources['errors'] == [{'type': 'ValueError', 'message': 'actual family RSS/freeRAM caps'}],
         'actual RAM-floor failure, not inferred zero native work')
    proof = read(PREP / 'cpu09_full_ram_stop_postcheck01.json')
    need(proof['status'] == 'VERIFIED_SOURCE_INTEGRITY_AFTER_RAM_TERMINATION_NOT_REPLAY_ACCEPTANCE'
         and proof['source_files_checked'] == len(proof['source_after']) == 50
         and proof['full_parity_completed'] is False and proof['truth_evaluation_completed'] is False
         and proof['actual_constructor_and_update_counts'] == 'UNKNOWN_AFTER_HARD_TERMINATION'
         and proof['reservation_upper_bounds'] == contract['direct_call_caps']
         and proof['job_active_after_cleanup'] == 0 and proof['environment_restored'] is True
         and proof['monitor_stopped'] is True, 'independent post-termination integrity proof only')
    expected_inner = {'native_metadata.json', 'pure_checks.json', 'reservation.json'}
    need({path.name for path in INNER.iterdir()} == expected_inner
         and set(proof['actual_worker_outputs']) == expected_inner, 'only three actual worker receipts')
    for name, record in proof['actual_worker_outputs'].items():
        need(sha(INNER / name, 1024**2) == record['sha256']
             and (INNER / name).stat().st_size == record['bytes'], 'actual inner file matches independent proof')
    pure, reservation = read(INNER / 'pure_checks.json'), read(INNER / 'reservation.json')
    need(pure['manufactured_checks'] == 5 and pure['native_calls'] == 0,
         'five manufactured helper checks only, not total worker native counts')
    need(reservation['status'] == 'RESERVED_ALL120_POLICIES_BEFORE_ANY_FACTORY'
         and reservation['direct_caps'] == contract['direct_call_caps']
         and reservation['hardkill_counts'] == 'UNKNOWN_LE_RESERVED_UNTIL_TERMINAL', 'durable reservation is an upper bound')
    paths, refs = {}, {}

    def add(alias, path):
        sha(path, 1024**2)
        need(alias not in paths and Path(alias).name == alias and not any(c in alias for c in '\t\r\n'), 'flat unique copy alias')
        need(path.suffix.lower() in ('.py', '.json', '.md', '.log', '.jsonl'), 'selected small text evidence only')
        paths[alias] = path

    def reference(path, cap, role):
        key = path.relative_to(ROOT).as_posix()
        refs[key] = dict(sha256=sha(path, cap), bytes=path.stat().st_size, copied=False, role=role)

    for name in PINS:
        add(name, PREP / name)
    add('report.md', REPORT)
    add(Path(__file__).name, Path(__file__).resolve())
    for index, name in enumerate(args.extra_small_input):
        relative = Path(name)
        need(not relative.is_absolute() and '..' not in relative.parts, 'explicit root-relative additional review/refusal only')
        add(f'extra_{index:02d}__{relative.name}', ROOT / relative)
    expected_inputs = contract['bindings'] | contract['historical_reference_inputs']
    need(proof['source_after'] == expected_inputs, 'fifty independently checked current/historical source identities')
    for name, record in expected_inputs.items():
        path = ROOT / name
        need(sha(path) == record['sha256'] and path.stat().st_size == record['bytes'], 'archive-time source/input bytes')
        reference(path, 4 * 1024**2, 'BOUND_ORIGINAL_SOURCE_INPUT_REFERENCE')
    for path in sorted(INNER.iterdir()):
        add('worker__' + path.name, path)
    expected_outer = {'admission.json', 'final.json', 'memory.jsonl'}
    expected_owned = {'GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stderr.log', 'stdout.log'}
    need({path.name for path in OUTER.iterdir()} == expected_outer
         and {path.name for path in OWNED.iterdir()} == expected_owned, 'exact actual terminal evidence files')
    need(read(OWNED / 'receipt.json') == receipt, 'embedded and owned terminal receipt agree')
    for prefix, directory in (('outer', OUTER), ('owned', OWNED)):
        for path in sorted(directory.iterdir()):
            add(prefix + '__' + path.name, path)
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), sha256=sha(path, 1024**2), bytes=path.stat().st_size)
                 for alias, path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory) <= 4 * 1024**2, 'compact copies4MiB, big outputs reference only')
    return inventory, refs, terminal, accepted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--outer-sha256', required=True)
    parser.add_argument('--extra-small-input', action='append', default=[])
    parser.add_argument('--prepare-dry', action='store_true')
    parser.add_argument('--check-dry', action='store_true')
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv', 'repository .venv only')
    need(sum((args.prepare_dry, args.check_dry, args.close)) == 1, 'one explicit metadata operation')
    destination = ROOT / 'research_tracking/runs' / RUN_ID
    need(not destination.exists(), 'new immutable small bundle absent')
    inventory, refs, terminal, accepted = gather(args)
    dry = dict(run_id=RUN_ID, report_sha256=args.report_sha256, actual_outer_sha256=args.outer_sha256,
        actual_terminal_status=terminal['status'], native_accepted=accepted, copies=inventory, reference_inputs=refs,
        generated_outputs=list(GENERATED), expected_output_count=len(inventory) + len(GENERATED))
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'reviewed dry matches actual current bytes')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', outputs=dry['expected_output_count'])))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact-dry closure review')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Full cached CPU09 native mastery — hồ sơ dừng RAM\n\n'
        'Native verdict REJECTED được giữ trong scope.json. Archive completed chỉ xác nhận lưu hồ sơ. '
        'Năm kiểm helper đã qua; actual constructors/updates UNKNOWN sau termination, giới hạn bởi reservation120/14400. '
        'Không có readouts/parity/truth mới. Source/review/ba inner receipts và outer/owned logs được copy trước/sau SHA. '
        'ROOT kiểm độc lập50source/input SHA sau termination, không thay scientific admission. '
        'Old5failurelane không mở lại, không replay/fit/model trongclosure. '
        'Report tại [report.md](report.md). Descriptiveoldpilot, no newN/CI/causalbenefit.\n')
    sources = [ROOT / row['source'] for row in inventory] + [ROOT / name for name in refs] + [DRY]
    sources = list(dict.fromkeys(sources))
    with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='CPU09_TARGETED_FULL_NATIVE_MASTERY_ARCHIVE',
        actual_terminal_verdict=terminal['status'], actual_native_accepted=accepted,
        actual_call_counts='UNKNOWN_AFTER_HARD_TERMINATION', new_independent_N=0),
        sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source, 1024**2) == row['sha256'], 'beforecopy source SHA')
            with (out / row['copy']).open('xb') as stream:
                stream.write(source.read_bytes())
            need(sha(source, 1024**2) == sha(out / row['copy'], 1024**2) == row['sha256'], 'source/copy/source-after SHA')
            copied.append(dict(**row, source_after_copy_sha256=sha(source, 1024**2), copied_sha256=sha(out / row['copy'], 1024**2)))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', refs)
        write(out / 'scope.json', dict(actual_terminal_status=terminal['status'], actual_native_accepted=accepted,
            scientific_JSONL_copied=False, scientific_output_relative=INNER.relative_to(ROOT).as_posix(),
            full_parity_completed=False, truth_evaluation_completed=False,
            actual_constructor_and_update_counts='UNKNOWN_AFTER_HARD_TERMINATION',
            reservation_upper_bounds=read(CONTRACT)['direct_call_caps'],
            independent_source_integrity_proof='cpu09_full_ram_stop_postcheck01.json',
            old_five_attempt_lane_reopened=False, new_independent_N=0, no_reexecution_at_closure=True,
            archive_completed_does_not_promote_rejected_native=True))
        write(out / 'timing_scope.json', dict(actual_outer_elapsed_before_receipt_seconds=terminal['elapsed_before_receipt_seconds'],
            whole_cap_seconds=300, resource_receipt=terminal['resources'], nested_times_not_summed=True,
            root_observed_stdout_after_final_seconds=9.804927600023802,
            root_stdout_time_origin='ROOT_TOOL_TERMINAL_MESSAGE_SESSION5883_NOT_WORKER_RECEIPT',
            no_runtime_forecast_claimed=True))
        write(out / 'closure_review.json', dict(reference=args.review_reference,
            dry_sha256=args.expected_dry_sha256, actual_outer_sha256=args.outer_sha256, report_sha256=args.report_sha256))
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(DRY.read_bytes())
        (out / 'raw_log_paths.txt').write_text('\n'.join(row['source'] for row in inventory if row['source'].endswith(('.log', '.jsonl'))) + '\n', encoding='utf-8')
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact small outputs')
        need(all(sha(ROOT / row['source'], 1024**2) == row['sha256'] for row in inventory), 'all copied inputs unchanged')
        for name, record in refs.items():
            need(sha(ROOT / name, max(4 * 1024**2, record['bytes'])) == record['sha256'], 'all referenced originals unchanged')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == dry['expected_output_count'], 'verified exact manifest output count')
    print(json.dumps(dict(**verified, manifest_sha256=sha(destination / 'manifest.json'), path=destination.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
