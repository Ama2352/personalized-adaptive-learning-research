"""ROOT lưu collection11–13 và tests12 NO_GO; không chạy lại metadata/tests."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'akt-main-batchc-metadata-attempts-11-13-20261109-01'
DRY = PREP / 'batchc_metadata_11_13_archive_dry01.json'
PRIOR = ROOT / 'research_tracking/runs/akt-main-batchc-metadata-attempts-06-10-20261109-01'
PRIOR_SHA = '412da03714d2381745b75082c0abda41a7dc1b48503119ac7f367b2391a9594d'
CALIBRATION_SHA = '2158794a5d6a74dd1461f8d7c05da8dd52133a0f227bbd348600e2aeba46c6a8'
PINS = {
    'prepare_batchc_metadata11.py': 'eee22d491e31d0fee2fc7c95a90d66d9f35afba9bdc8f7ac80833422a4fed138',
    'prepare_batchc_metadata12.py': 'f32bb1f5066f1964d644bdb973d888093e07a3b054cf7deafb09ad27570d670e',
    'BATCHC_METADATA_RESOURCE_PROFILE12_REVIEW01.md': '304287c010ba2c6279a702583f71a104c73d40f2f7a6fe412c2d37d1378c2f18',
    'check_batchc_metadata11.py': '24295b4035558f39d51556d62108414558a224200e6b80472f4633f20f054bc5',
    'run_batchc_metadata11.py': '272592f8d5757549f6af82b1f708b0f5304ca985b2e7cd058330ad0ee0319851',
    'batchc_metadata11_packet.json': '4580a6c87bc482a98be6fb17517fa3fc4be5c8a7c291ca311215ef1ac25b9ec5',
    'check_batchc_metadata12.py': '9bc908c3e90783b1596cc95ce6e551d15277c7061847347b008a8b12b1fb6713',
    'run_batchc_metadata12.py': 'e0498feded8d46956cec3fd40d9504b51aca8783cfe5fc85c901d58117a2e83b',
    'batchc_metadata12_packet.json': 'f0a954c55c1d798e8fd30bc9d99274dc18d2bb1a7c757ca17e87d5227773b630',
    'batchc-metadata-collection11-owned/final.json': '18e6b18c39b69a167e7e1024bb68662c1dabbe81d0ae60b000516c47c8f6b993',
    'batchc-metadata-collection12/result.json': 'da1c25a4ac97709d831c61720af2a83e68cc6cbe6a75530d95aaecabf24da0e6',
    'batchc-metadata-collection12-owned/final.json': '9a8978b90e9d72e707c8b9f7936a370acc735ba5f10f87db26d78a548603acf7',
    'batchc-metadata-tests12-owned/final.json': 'c96c59e3d19136a04d973e277f75a591df12a12e18432f1045ec0bffe0f94650',
    'prepare_batchc_metadata13.py': '8cfaeb568e6f013ddae9f43d20ff098c5a85f2638df9d0d0420eab68d1f414e6',
    'check_batchc_metadata13.py': '8169c83ad32e75df4aa4ce5b2b60e11eaff685d829a89b01d103857ab32fa7b0',
    'run_batchc_metadata13.py': '32d7bc270e596f57db9c0ce1dfc6ce474069979ed842a990ca9ec6b0be2e4d26',
    'batchc_metadata13_packet.json': 'b5876d55682b9a9821437e1d5ab21bcde517e533d910fe215a4e4902124a1b18',
    'batchc-metadata-collection13/result.json': 'b6e9f7c3285479a2c37b79dcfeb661238b262d07eacb5b353cd0488f1bdbe526',
    'batchc-metadata-collection13-owned/final.json': '088f1c30f13f1b61eac2ade7ac3616df4ae1c4983ba40fe2e9918925c795ece7',
    'batchc-metadata-tests13-owned/final.json': 'f7c0daf984acf0659aa8a0d68ba5f36359389ed512cc72b87f5a117774c95e79',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json',
             'reviewed_dry.json', 'closure_review.json')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical ROOT path')
    cursor = ROOT
    for part in ('', *path.relative_to(ROOT).parts):
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no source/output alias')


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


def gather():
    for name, pin in PINS.items():
        need(sha(PREP / name) == pin, 'frozen Root preparation/review/raw receipt')
    copies = {'archiver.py': Path(__file__).resolve()}
    for name in PINS:
        if '/' not in name:
            copies[name] = PREP / name
    packets = {attempt: read(PREP / f'batchc_metadata{attempt}_packet.json') for attempt in ('11', '12', '13')}
    for packet in packets.values():
        need(len(packet['source_pins']) == 36 and len(packet['runtime_pins']) == 11
             and len(packet['expected_nodeids']) == len(set(packet['expected_nodeids'])) == 221,
             'source/runtime/exact physical population')
    need(packets['11']['expected_nodeids'] == packets['12']['expected_nodeids']
         and packets['11']['allocations'] == packets['12']['allocations']
         and packets['11']['deselect'] == packets['12']['deselect'], 'same cases/time allocation/single exclusion')
    need(packets['13']['expected_nodeids'] == packets['12']['expected_nodeids']
         and packets['13']['allocations'] == packets['12']['allocations']
         and packets['13']['deselect'] == packets['12']['deselect']
         and packets['13']['resource_profile'] == packets['12']['resource_profile'], 'namespace13 keeps exact metadata128 profile/population')
    old, new = packets['11']['resource_profile'], packets['12']['resource_profile']
    need(old['max_worker_rss_bytes'] == 512 * 1024**2 and old['prelaunch_minimum_available_ram_bytes'] == 2048 * 1024**2
         and new['max_worker_rss_bytes'] == 128 * 1024**2 and new['prelaunch_minimum_available_ram_bytes'] == 1664 * 1024**2
         and old['minimum_available_ram_bytes'] == new['minimum_available_ram_bytes'] == 1536 * 1024**2,
         'explicit separate metadata resource profiles')
    no_go = {}
    for label, stem, available, floor in (
        ('collection11', 'batchc-metadata-collection11', 2140545024, 2147483648),
        ('tests12', 'batchc-metadata-tests12', 1171968000, 1744830464),
        ('tests13', 'batchc-metadata-tests13', 1646731264, 1744830464)):
        child_dir = PREP / stem
        owned_dir = PREP / (stem + '-owned')
        need(not child_dir.exists() and {path.name for path in owned_dir.iterdir()} == {'final.json'}, 'NO_GO before child/Job launch')
        receipt = read(owned_dir / 'final.json')
        need(receipt == dict(status='NO_GO_METADATA_RAM', available_ram_bytes=available,
             prelaunch_minimum_available_ram_bytes=floor, owned_launch_started=False, automatic_retry=False), 'actual immutable NO_GO admission')
        no_go[label] = receipt
        copies[label + '__owned__final.json'] = owned_dir / 'final.json'
    collections = {}
    for attempt in ('12', '13'):
        child_dir = PREP / f'batchc-metadata-collection{attempt}'
        owned_dir = PREP / f'batchc-metadata-collection{attempt}-owned'
        child_names = {'result.json', 'native_metadata.json', 'pytest.log', 'pytest-file.log'}
        owned_names = {'final.json', 'GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stdout.log', 'stderr.log'}
        need({path.name for path in child_dir.iterdir() if path.is_file()} == child_names
             and {path.name for path in owned_dir.iterdir()} == owned_names, 'exact accepted collection flat output population')
        child = read(child_dir / 'result.json')
        outer = read(owned_dir / 'final.json')
        owned = read(owned_dir / 'receipt.json')
        packet = packets[attempt]
        need(child['status'] == 'ACCEPTED_BATCHC_COLLECTION_CHILD' and child['accepted'] is True
             and child['mode'] == outer['mode'] == 'collect' and child['pytest_exit_code'] == 0
             and child['error'] is None and child['denied'] == child['collection_errors'] == []
             and child['counts'] is None and child['test_body_entries'] == child['test_protocol_entries'] == 0,
             'accepted collection-only, no test-body or test-PASS claim')
        need(child['nodeids'] == packet['expected_nodeids'] and len(child['actual_new_nodeids']) == 17
             and len(child['actual_prior_nodeids']) == 204 and child['actual_selected_count'] == 221,
             'actual 221 ordered IDs/17new/204prior')
        need(child['source_before'] == child['source_after'] == packet['source_pins']
             and child['runtime_before'] == child['runtime_after'] == packet['runtime_pins']
             and child['environment_and_sys_restored'] is True and child['actual_scientific_modules_absent'] is True,
             'actual source/runtime/restoration observations')
        peak, free = {'12': (53014528,2302234624), '13': (52617216,1934610432)}[attempt]
        need(child['resources'] == dict(samples=11, observed_peak_rss_bytes=peak,
             observed_minimum_available_ram_bytes=free), 'actual collection resource samples only')
        need(outer['status'] == 'ACCEPTED_BATCHC_COLLECTION_ONLY_NOT_TEST_PASS' and outer['errors'] == []
             and outer['child_result'] == child and outer['receipt'] == owned
             and outer['source_after'] == packet['source_pins'] and outer['runtime_after'] == packet['runtime_pins']
             and outer['allocation'] == packet['allocations']['collect'] and outer['automatic_retry'] is False,
             'actual same-source accepted collection outer')
        need(owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
             and owned['actual_worker_in_job_before_GO'] is True and owned['job_active_after_cleanup'] == 0
             and owned['errors'] == owned['cleanup_errors'] == [], 'actual collection ownership/Job cleanup')
        for name in sorted(child_names):
            path = child_dir / name
            need(outer['outputs'][name] == dict(bytes=len(payload(path)), sha256=sha(path)), 'actual child file SHA binding')
            copies[f'collection{attempt}__child__' + name] = path
        need(set(outer['outputs']) == child_names, 'no omitted flat child outputs')
        for name in sorted(owned_names):
            copies[f'collection{attempt}__owned__' + name] = owned_dir / name
        collections[attempt] = dict(status=outer['status'],nodeids=221,new=17,prior=204,test_bodies=0,
            child_seconds=child['elapsed_seconds'],outer_seconds=outer['elapsed_seconds'],resources=child['resources'])
    need(sha(PRIOR / 'manifest.json') == PRIOR_SHA, 'immutable prior06–10 archive')
    prior_manifest = read(PRIOR / 'manifest.json')
    need(prior_manifest['outputs_sha256']['tests08__result.json'] == CALIBRATION_SHA
         and sha(PRIOR / 'tests08__result.json') == CALIBRATION_SHA, 'reference-only actual08 calibration receipt')
    calibration = read(PRIOR / 'tests08__result.json')
    need(calibration['status'] == 'REJECTED_BATCHC_METADATA_KEEP_ALL' and calibration['test_body_entries'] == 221
         and calibration['counts']['failures'] == 53 and calibration['resources']['observed_peak_rss_bytes'] == 64675840,
         'calibration receipt remains failed, not 221PASS')
    references = dict(prior_archive=dict(path=PRIOR.relative_to(ROOT).as_posix(), manifest_sha256=PRIOR_SHA),
        prior08_calibration=dict(path=(PRIOR / 'tests08__result.json').relative_to(ROOT).as_posix(),
            sha256=CALIBRATION_SHA, copied=False, scope='221bodies/53FAIL observed footprint, not passing-suite bound'),
        packet_inputs={attempt: dict(source_sha256=value['source_pins'], runtime_sha256=value['runtime_pins'])
                       for attempt, value in packets.items()},
        tests12_execution=False, tests13_execution=False, native_or_cuda_proof=False,
        scope='Source/runtime references retained; no runtime-temp/cache/old01–10 artifact copies.')
    rows = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), bytes=len(payload(path)), sha256=sha(path))
            for alias, path in sorted(copies.items())]
    need(len(rows) == 39 and sum(row['bytes'] for row in rows) < 1024**2, 'compact exact thirty-nine copies')
    return rows, references, dict(no_go=no_go,collections=collections,distinct_ordered_test_ids=221,tests_started=False)


def main():
    parser = argparse.ArgumentParser()
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
    need(not destination.exists(), 'exclusive new11–13 evidence bundle')
    inventory, references, summary = gather()
    dry = dict(run_id=RUN, copies=inventory, reference_inputs=references, actual_summary=summary,
        generated_outputs=list(GENERATED), expected_output_count=45,
        scope='COLLECTION11_NO_GO_COLLECTION12_13_ACCEPTED_SAME221_IDS_TESTS12_13_NO_GO_NO_TEST_PASS')
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=39, outputs=45)))
        return
    need(read(DRY) == dry, 'exact reviewed dry/current inputs')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', copies=39, outputs=45)))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact closure review')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Main C metadata11–13 — hai collection đạt, tests chưa khởi chạy\n\n'
        'Collection11 NO_GO với available2.140.545.024B dưới admission2GiB; chưa child. '
        'ROOT duyệt profile metadata128MiB worker/floor1536MiB/prelaunch1664MiB, '
        'giữ actual08 đã đi qua221bodies nhưng53FAIL và review304287…; không đổi verdict cũ. '
        'Collection12 và13 mỗi lượt ACCEPTED cùng221orderedIDs,17mới/204prior,0body,countsNULL, '
        'source36/runtime11 ổn định và cleanup Job0. Có221IDs phân biệt, không cộng hai lượt thành442test PASS. '
        'Collection12 peak53.014.528B/minfree2.302.234.624B,child1,964442499971483s/outer2,4202014000038616s; '
        'collection13 peak52.617.216B/minfree1.934.610.432B,child5,985917899990454s/outer7,306537900003605s. '
        'Mỗi collection có11resource samples. Metadata Windows dùng helper đã ghim với lệnh hệ thống giới hạn. '
        'Tests12 và13 đều NO_GO trước child/Job: available1.171.968.000B và1.646.731.264B dưới admission1.744.830.464B. '
        'Giữ9worker/outer/packet,3Rootpreparers,review và25raw phẳng; không copy runtime-temp/cache, runtimebytes hoặc raw08 cũ. '
        'Đo RAM là cooperative worker hooks/high-water, chưa là family/hardOS quota. '
        'Chưa có forward/backward/optimizer hoặc workload mô hình/CUDA trong các operation này, chưa có test PASS cho Main C. '
        'Những source ngoài36bindings và các kiểm GKT riêng không thuộc nghiệm thu collection này. '
        'Không tự retry/nâng cap hoặc cấp quyền fit/GPU/RQ completion. Closure chỉ xác nhận lưu bằng chứng.\n')
    sources = list(dict.fromkeys([ROOT / row['source'] for row in inventory]
        + [PRIOR / 'manifest.json', PRIOR / 'tests08__result.json', DRY]))
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='BATCHC_METADATA_RESOURCE_ADOPTION_COLLECTION_AND_NO_GO',
            accepted_collection_ids=221, tests12_executed=False, tests13_executed=False, test_pass_claim=False,
            scientific_new_N=0, automatic_retry=False), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source SHA before copy')
            with (out / row['copy']).open('xb') as stream:
                stream.write(payload(source))
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/source-after SHA')
            copied.append(dict(**row, source_sha256_after_copy=sha(source), copy_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', references)
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(payload(DRY))
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'exact reviewed dry copy')
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
              actual_summary=summary, collection_or_tests_rerun=False, shared_canonical_report_modified=False))
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact forty-five outputs')
        need(gather()[0] == inventory, 'all selected/reference inputs remain exact after copy')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 45, 'verified forty-five outputs')
    print(json.dumps(dict(status='CLOSED_COLLECTION_AND_NO_GO_EVIDENCE_NOT_TEST_PASS', outputs=45, files_including_manifest=46,
          manifest_sha256=sha(destination / 'manifest.json'), verification=verified), ensure_ascii=False))


if __name__ == '__main__':
    main()
