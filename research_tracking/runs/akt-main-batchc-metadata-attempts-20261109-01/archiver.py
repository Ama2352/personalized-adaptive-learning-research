"""ROOT đóng chung01–05; chỉ lưu bằng chứng, không chạy collection/tests."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'akt-main-batchc-metadata-attempts-20261109-01'
DRAFT = PREP / 'BATCHC_METADATA_ATTEMPTS_REPORT_DRAFT01.md'
REPORT = ROOT / 'research_tracking/reports/akt_main_batchc_metadata_attempts_20261109.md'
DRY = PREP / 'batchc_metadata_attempts_archive_dry01.json'
PINS = {
    '01': ('ece478f552ab0d283ac335ca50d46fa7675b6bff66f573e2eda8159d21b1b9fc',
           'a047e2b2363147f922ce2cda0dd185a5177c0ae70364e724e906eef6bd40cebd',
           'c497fe4324d16b4f4d76181df3fff018fc4295095310aaf7d66be102c9ef93e8',
           '8d7d7f6465ff63c8d2ff8a4509242fdf6770b8ab6dad2f657240b0450996f93c'),
    '02': ('874e62e7e5bf12b8dff75fd55c334461ef07fee9c477ec23b30abf73c03671a7',
           'fdd7d052bffbf95d479f4c563c78228410a4c9ee9601b04077ddf19a121bd15a',
           '6b23c1ed7af561b2bf7694740bfddf4a071a8d9106dbfa6376debc41306a3a73',
           '993540446f4b94bf9e28001094f8bcc1b4f55f74b8a8baf91bc9e2a24d521cd2'),
    '03': ('83d2f34eb8fefa96efbef5ccbd42541a568e9dad64492fef4cc1983e0803e332',
           'c58211a5e86988a8dbdb2b30a71e9e69c234af9f6f8b6105280ac4122b623552',
           'b16abb885d5dd0f3e501c864b409bc276abc901dd662f9e2b9aca7cc6b3f50fe',
           '73dadea3a54414c09ae2f3271315f55d75db7d8b35fa11a3704f53c53748ede5'),
    '04': ('cfd324306a68291a871540a2fd277aa4876cabe017d25baffb2883b73cf21398',
           '8048ee0fac7a9aa871ba8edd52ba6a0bbb162cf5fa36e7bc6dd73c05782ebadc',
           'cab65999ac85c3ae8be25a372e985dbff5c8d5d6338282a1ef343c73594b4d75',
           '3a1e112fe5d09bf965d4e2bfc541c412eb7ab60a50e5c1ea88d425e0f20bc48f'),
    '05': ('2cda0c96fbd4c2ed43213c0f503179d07bf4930dbc7d2a5c3d0687ebea24c0a2',
           '40518df8e58dcffe7014f50ab0c94d8382891e9de2d9b19d6ff2925cf36a5d53',
           '1b1f1a27b8feac1baa58f8752c1032adeed10e49b37b95bd65ecdecaefec2da1',
           'a84dd9a35653d01062218642ec1184291533b7bcec41dcc58a79a4afad1cb52b'),
}
PREPARERS = {
    'prepare_batchc_metadata04.py': 'e6ceee14ce39ffbd7886a26105c10fedaa1c1eb80249aa6eec4ced2824ecaa59',
    'prepare_batchc_metadata05.py': 'fbf693caec5744945f2d32dc449ee20ccc682fe9c976c079ed9d163cfbe33116',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json',
             'reviewed_dry.json', 'closure_review.json')
OWNED = {'final.json', 'GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stdout.log', 'stderr.log'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical ROOT path')
    cursor = ROOT
    for part in ('', *path.relative_to(ROOT).parts):
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no path alias')


def payload(path):
    physical(path)
    need(path.is_file() and path.stat().st_size <= 2 * 1024**2, 'bounded regular evidence')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable read size')
    return raw


def sha(path):
    return hashlib.sha256(payload(path)).hexdigest()


def read(path):
    return json.loads(payload(path))


def write(path, value):
    physical(path)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def gather(report_sha):
    need(re.fullmatch('[a-f0-9]{64}', report_sha) and sha(DRAFT) == report_sha, 'ROOT-reviewed report')
    copies = {'archiver.py': Path(__file__).resolve(), 'report_snapshot.md': DRAFT}
    references = {}
    results = {}
    for name, pin in PREPARERS.items():
        need(sha(PREP / name) == pin, 'Root preparer source')
        copies[name] = PREP / name
    for attempt, pins in PINS.items():
        names = (f'check_batchc_metadata{attempt}.py', f'run_batchc_metadata{attempt}.py',
                 f'batchc_metadata{attempt}_packet.json')
        for name, pin in zip(names, pins[:3]):
            need(sha(PREP / name) == pin, 'frozen worker/controller/packet')
            copies[name] = PREP / name
        packet = read(PREP / names[2])
        child_dir = PREP / f'batchc-metadata-collection{attempt}'
        owned_dir = PREP / f'batchc-metadata-collection{attempt}-owned'
        need(sha(owned_dir / 'final.json') == pins[3], 'actual Root outer verdict')
        outer = read(owned_dir / 'final.json')
        references[attempt] = dict(source_sha256=packet['source_pins'], runtime_sha256=packet['runtime_pins'],
            scope='HISTORICAL_PACKET_AND_RECEIPT_REFERENCES_NOT_RUNTIME_BYTE_COPIES')
        need(len(packet['source_pins']) == 33 and len(packet['runtime_pins']) == (8 if attempt <= '03' else 9 if attempt == '04' else 10),
             'actual packet source/runtime anchor counts')
        if attempt == '05':
            need(not child_dir.exists() and {p.name for p in owned_dir.iterdir()} == {'final.json'}, 'no child05 or owned launch files')
            need(outer == dict(status='NO_GO_METADATA_RAM', available_ram_bytes=1654325248,
                 prelaunch_minimum_available_ram_bytes=2147483648, owned_launch_started=False, automatic_retry=False), 'actual05 NO_GO')
            copies['attempt05__owned__final.json'] = owned_dir / 'final.json'
            results[attempt] = dict(status=outer['status'], owned_launch_started=False, counts=None,
                child_observations_available=False, available_ram_bytes=outer['available_ram_bytes'])
            continue
        child = read(child_dir / 'result.json')
        owned = read(owned_dir / 'receipt.json')
        need(child['status'] == outer['status'] == 'REJECTED_BATCHC_METADATA_KEEP_ALL'
             and child['accepted'] is False and child['mode'] == 'collect'
             and child['counts'] is None and child['nodeids'] == []
             and child['test_body_entries'] == child['test_protocol_entries'] == 0, 'preserve rejection and zero body, no claimed test count')
        need(child['source_before'] == child['source_after'] == packet['source_pins']
             and child['runtime_before'] == child['runtime_after'] == packet['runtime_pins']
             and child['environment_and_sys_restored'] is True
             and child['actual_scientific_modules_absent'] is True, 'actual child source/runtime/restoration observations')
        need(owned == outer['receipt'] and owned['returncode'] == 1 and owned['accepted'] is False
             and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
             and owned['cleanup_errors'] == [] and outer['automatic_retry'] is False, 'actual rejected owned terminal and cleanup')
        child_names = {'result.json'} if attempt == '01' else {'result.json', 'native_metadata.json', 'pytest.log'}
        if attempt == '04':
            child_names.add('pytest-file.log')
        need({p.name for p in child_dir.iterdir() if p.is_file()} == child_names
             and {p.name for p in owned_dir.iterdir()} == OWNED, 'exact flat raw population')
        for name in sorted(child_names):
            path = child_dir / name
            need(outer['outputs'][name] == dict(bytes=len(payload(path)), sha256=sha(path)), 'raw child output binding')
            copies[f'attempt{attempt}__child__{name}'] = path
        need(set(outer['outputs']) == child_names, 'no omitted child flat output')
        for name in sorted(OWNED):
            copies[f'attempt{attempt}__owned__{name}'] = owned_dir / name
        need(payload(owned_dir / 'stdout.log') == payload(owned_dir / 'stderr.log') == b'', 'actual empty owned streams')
        results[attempt] = dict(status=outer['status'], counts=None, nodeids=[], test_bodies=0,
            child_seconds=child['elapsed_seconds'], outer_seconds=outer['elapsed_seconds'], resources=child['resources'],
            error=child['error'], denied=child['denied'], pytest_exit_code=child['pytest_exit_code'],
            collection_errors=child['collection_errors'], cleanup_accepted=True, job_active_after_cleanup=0)
        if attempt == '01':
            need(child['error'] == dict(type='ValueError', message='cooperative metadata RAM cap/floor'), 'actual01 RAM guard')
        if attempt == '03':
            denial = child['denied'][0]
            need(denial['details'] == dict(raw_path='nul', resolved_path=str(ROOT / 'nul'), mode='r', flags=32896)
                 and denial['caller_frames'][1]['function'] == '__init__'
                 and denial['caller_frames'][1]['line'] == 489, 'actual observed capture stdin target')
        if attempt == '04':
            need(child['pytest_stdin_null_reads'] == 1 and len(child['denied']) == 7
                 and all(row['details']['raw_path'].endswith('-pytest-9.1.1.pyc') for row in child['denied'][:4])
                 and all(row['details']['raw_path'] == '<unknown>' for row in child['denied'][4:])
                 and len(child['collection_errors']) == 4, 'actual seven04 denials and four collection errors')
    references['prior_unexecuted_archive'] = {
        name: dict(path=(PREP / name).relative_to(ROOT).as_posix(), sha256=sha(PREP / name), copied=False)
        for name in ('archive_batchc_metadata_ram01.py', 'BATCHC_METADATA_COLLECTION01_RAM_AND_CP05_REVIEW01.md')}
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), bytes=len(payload(path)), sha256=sha(path))
                 for alias, path in sorted(copies.items())]
    need(len(inventory) == 59 and sum(row['bytes'] for row in inventory) < 1024**2, 'compact fifty-nine exact copies')
    return inventory, references, results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-sha256', required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare-dry', action='store_true')
    action.add_argument('--check-dry', action='store_true')
    action.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv', 'repository .venv only')
    destination = ROOT / 'research_tracking/runs' / RUN
    physical(destination)
    physical(REPORT)
    need(not destination.exists() and not REPORT.exists(), 'exclusive new combined evidence and report')
    inventory, references, results = gather(args.report_sha256)
    dry = dict(run_id=RUN, report_sha256=args.report_sha256, report=REPORT.relative_to(ROOT).as_posix(),
        copies=inventory, reference_inputs=references, attempt_summaries=results,
        generated_outputs=list(GENERATED), expected_output_count=65,
        scope='FOUR_REJECTED_PREBODY_COLLECTIONS_AND_ONE_PRELAUNCH_NO_GO_NO_TEST_PASS')
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=59, outputs=65)))
        return
    need(read(DRY) == dry, 'exact reviewed dry/current inventory')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', copies=59, outputs=65)))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact-dry closure approval')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    with REPORT.open('xb') as stream:
        stream.write(payload(DRAFT))
    need(sha(REPORT) == args.report_sha256, 'canonical report reviewed exact bytes')
    note = ('# Main C — collection01–05 chưa có population/test PASS\n\n'
        'Giữ nguyên bốn lượt REJECTED trước test body và lượt05 NO_GO trước launch. '
        'Raw01–04 có counts NULL, IDs rỗng, body0 và cleanup Job0. Lượt05 không có child/Job receipt. '
        'Có15controller/packet,40raw phẳng và Root preparer04/05; không copy runtime-temp/cache tree/dependencies/corpus. '
        'Source33/runtime8→9→10 giữ trong reference metadata. Đọc report_snapshot.md để phân biệt guard NUL, '
        'cache Pytest, assertion chuẩn bị7vs4 và RAM admission. Closure chỉ lưu bằng chứng, không rerun hoặc đổi REJECTED thành PASS.\n')
    sources = list(dict.fromkeys([ROOT / row['source'] for row in inventory] + [REPORT, DRY]
        + [ROOT / row['path'] for row in references['prior_unexecuted_archive'].values()]))
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='BATCHC_METADATA_PREBODY_FAILURE_AND_NO_GO_HISTORY',
            rejected_operations=4, prelaunch_no_go=1, accepted_collection=False, test_counts=None,
            test_bodies=0, native_authority=False), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source SHA before copy')
            with (out / row['copy']).open('xb') as stream:
                stream.write(payload(source))
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/source-after exact SHA')
            copied.append(dict(**row, source_sha256_after_copy=sha(source), copy_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', references)
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(payload(DRY))
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'reviewed dry byte identity')
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
              report_sha256=args.report_sha256, collection_or_tests_rerun=False,
              operation_statuses={attempt: item['status'] for attempt, item in results.items()}))
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact sixty-five output files')
        need(all(sha(ROOT / row['source']) == row['sha256'] for row in inventory), 'all selected sources stable')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 65, 'verified sixty-five outputs')
    print(json.dumps(dict(status='CLOSED_PREBODY_FAILURE_HISTORY_ONLY', outputs=65, files_including_manifest=66,
          manifest_sha256=sha(destination / 'manifest.json'), report_sha256=sha(REPORT), verification=verified), ensure_ascii=False))


if __name__ == '__main__':
    main()
