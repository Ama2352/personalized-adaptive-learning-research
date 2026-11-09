"""ROOT lưu metadata06–10; không chạy lại collection/tests hoặc nhận MainC PASS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'akt-main-batchc-metadata-attempts-06-10-20261109-01'
DESTINATION = ROOT/'research_tracking/runs'/RUN
DRAFT = PREP/'BATCHC_METADATA_ATTEMPTS_06_10_REPORT_DRAFT01.md'
REPORT = ROOT/'research_tracking/reports/akt_main_batchc_metadata_attempts_06_10_20261109.md'
DRY = PREP/'batchc_metadata_attempts_06_10_archive_dry01.json'
SOURCE_PINS = {
    'check_batchc_metadata06.py': 'cf5292139fa07722c8ce6c29561d34307414231bcfad898364d1a9669d1c86e1',
    'run_batchc_metadata06.py': '52abfeaf998ff853fbe356621dcf080db38a2755ae5449214c43e8cf511051f0',
    'batchc_metadata06_packet.json': '5c5896b348d204dcd69554648a9c56919de2ba3ac0c563ec2648e386cdc96d36',
    'check_batchc_metadata07.py': 'd25bdcb6c7121a5cecf44cbfeb67f2e8a21b2363c9e3611f5ca9bc3e4e89dae6',
    'run_batchc_metadata07.py': 'c91cedc9be322f269978395e0a4824a074492444cd4bbfb6d1fd55585d0ca73d',
    'batchc_metadata07_packet.json': '9abda15740eb9a3fbed57b302448ebdea09e16b46a0c10fe55f808726c540a99',
    'check_batchc_metadata08.py': '6b81a431727208841fb1dd9257aae9866d09adea38648bbfa6a1596526efc292',
    'run_batchc_metadata08.py': '4c967369a8c66d621453a0b728e56f36000868bcf105b13e12601ac34860ad79',
    'batchc_metadata08_packet.json': 'ae777054795a5718fe1f242d84a7bb00df98c256fab0130b9c3c5de510672e18',
    'check_batchc_metadata09.py': '2df7c013e362339a18222be500759fa36a785c69bf7cda1c2278340aee3f7b5b',
    'run_batchc_metadata09.py': 'bdb258fb87e4a07ec1a40e5380be83b79a641daf5ab159a695a75d58574bc229',
    'batchc_metadata09_packet.json': '8864e4b78d7ce02a5dab2950623b479e0b598c329266802bde98ba905c8246d9',
    'check_batchc_metadata10.py': '27305666a158bcc46d93bdc95822023e95408e9a0623f10111a79375a4320860',
    'run_batchc_metadata10.py': '5a12497d2904429a9405adaf22e4a45841f38103cb9d5e072ecdfb57927cc9e9',
    'batchc_metadata10_packet.json': '0a21f07f2fd318679b421251bcb0406fea26d5ce1b9f6531d63ee32099c7800b',
    'prepare_batchc_metadata09.py': '06c3d126f44354cd0a222fd1fec4494a040fa1207c0b3fed136603fb65c59dd1',
    'prepare_batchc_metadata10.py': '7e48acb1c0e39badb2c07a7a950460f20572e0a4ccea2384dd93d074e0801f34',
    'windows_metadata_platform09.py': '2f137875cf3e18eabf94b66fab1d8a3e2502f9ed45a7f791e21883f2831ec560',
}
FINAL_PINS = {
    'collection06': '286cbd6ff884afa1b912ad8b45ff28991e9d777a15ab6ca187cd402756e1558a',
    'collection07': 'c4f534c9ed113528aa8c9bb299180039e385bb2bfeae03c6e1426d7b94d11548',
    'tests07': 'c3e7d3500dbfa69b059ef40c4e8738a7be824fcc6cd629b446ea6cca44f7e984',
    'collection08': 'b61372a096fbad8009d3cc41f32c60494ecbe6fe9b433bb7ef9e8b56d5e2c82c',
    'tests08': '0f5b86278c4d1f83fa1397561102c66dd42f421680b8db35d5671ab69b3c1550',
    'collection09': '3cba041da195cd81b01fc52c72e033b002bf4e6f6b8729245754f0b2d00ad6f6',
    'collection10': '8cfc6761da3b70c206c49a7386f9905e6717b030bfc8c81047f5e26b2860a2cd',
    'tests10': 'c10135ec646c219e861016143c121282a9ed59de0dfe14de7ceff4ef97022b85',
}
REFERENCES = {
    'research_tracking/runs/akt-main-batchc-metadata-attempts-20261109-01/manifest.json': '25ca4b701886e188447d6275887d9ed72f26fe5936cafc734dface16f25dff57',
    'src/knowledge_tracing/evidence.py': '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/APPLY_BATCHC_ROOT_REVIEW01.md': 'de15ae53aac04e8498c5aa28884245c0bc65439ea1fb5b4c8ef3794e81ef8a3d',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/BATCHC_STATE_CLOSURE_AID01.md': 'f68d902bb5af02541896624da05eace6195b80f21e99a8237be3f7241426c874',
}
OWNED_NAMES = {'final.json', 'GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stdout.log', 'stderr.log'}
COLLECT_NAMES = {'native_metadata.json', 'pytest-file.log', 'pytest.log', 'result.json'}
TEST_NAMES = COLLECT_NAMES|{'events.jsonl', 'junit.xml'}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_inputs.json', 'reviewed_dry.json', 'closure_review.json')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'Physical ROOT path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'Không theo alias')


def payload(path):
    physical(path)
    need(path.is_file() and path.stat().st_size <= 2*1024**2, 'File evidence≤2MiB')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'File size ổn định')
    return raw


def sha(path):
    return hashlib.sha256(payload(path)).hexdigest()


def read(path):
    return json.loads(payload(path))


def write(path, value):
    physical(path)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def direct_files(directory):
    physical(directory)
    return {p.name for p in directory.iterdir() if p.is_file()}


def gather(report_sha):
    need(re.fullmatch(r'[a-f0-9]{64}', report_sha) and sha(DRAFT) == report_sha, 'Exact reviewed report SHA')
    copies = {'archiver.py': Path(__file__).resolve(), 'report_snapshot.md': DRAFT}
    for name, pin in SOURCE_PINS.items():
        need(sha(PREP/name) == pin, 'Frozen source/packet/preparer '+name)
        copies[name] = PREP/name
    for name, pin in REFERENCES.items():
        need(sha(ROOT/name) == pin, 'Reference SHA '+name)
    packets = {number:read(PREP/f'batchc_metadata{number}_packet.json') for number in ('06', '07', '08', '09', '10')}
    references = dict(fixed=REFERENCES, historical_packet_bindings={})
    for number, packet in packets.items():
        source_count, runtime_count = (33, 10) if number == '06' else (36, 10) if number == '07' else (36, 11)
        need(len(packet['source_pins']) == source_count and len(packet['runtime_pins']) == runtime_count,
             'Exact historical packet source/runtime population')
        references['historical_packet_bindings'][number] = dict(source_sha256=packet['source_pins'], runtime_sha256=packet['runtime_pins'],
            scope='SOURCE_RUNTIME_BINDINGS_METADATA_ONLY_NOT_BYTE_COPIES_OR_CURRENT_RUNTIME_ATTESTATION')
    results, children = {}, {}
    for suffix, pin in FINAL_PINS.items():
        owned = PREP/f'batchc-metadata-{suffix}-owned'
        child = PREP/f'batchc-metadata-{suffix}'
        need(sha(owned/'final.json') == pin, 'Pinned actual outer verdict '+suffix)
        outer = read(owned/'final.json')
        if suffix in ('collection09', 'tests10'):
            need(not child.exists() and direct_files(owned) == {'final.json'}, 'NO_GO không child/Job inherited')
            available = 1838166016 if suffix == 'collection09' else 2122240000
            need(outer == dict(status='NO_GO_METADATA_RAM', available_ram_bytes=available,
                prelaunch_minimum_available_ram_bytes=2147483648, owned_launch_started=False, automatic_retry=False), 'Actual NO_GO RAM')
            copies[suffix+'_owned__final.json'] = owned/'final.json'
            results[suffix] = outer
            continue
        need(direct_files(owned) == OWNED_NAMES, 'Exact owned raw membership '+suffix)
        names = TEST_NAMES if suffix.startswith('tests') else COLLECT_NAMES
        need(direct_files(child) == names and set(outer['outputs']) == names, 'Exact child raw membership '+suffix)
        receipt = read(owned/'receipt.json')
        need(receipt == outer['receipt'] and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True,
             'Actual owned cleanup/Job0 '+suffix)
        for name in OWNED_NAMES:
            copies[suffix+'_owned__'+name] = owned/name
        for name in names:
            record = outer['outputs'][name]
            need(sha(child/name) == record['sha256'] and (child/name).stat().st_size == record['bytes'], 'Outer-bound child raw SHA '+suffix+'/'+name)
            copies[suffix+'__'+name] = child/name
        result = read(child/'result.json')
        need(result['source_before'] == result['source_after'] and result['runtime_before'] == result['runtime_after']
             and result['environment_and_sys_restored'] is True and result['actual_scientific_modules_absent'] is True,
             'Observed source/runtime/environment integrity '+suffix)
        expected_status = 'ACCEPTED_BATCHC_COLLECTION_ONLY_NOT_TEST_PASS' if suffix in ('collection07', 'collection08', 'collection10') else 'REJECTED_BATCHC_METADATA_KEEP_ALL'
        need(outer['status'] == expected_status and 0 <= outer['elapsed_seconds'] < outer['allocation']['whole_seconds'], 'Actual status/budget '+suffix)
        children[suffix] = result
        results[suffix] = dict(status=outer['status'], child_seconds=result['elapsed_seconds'], outer_stored_seconds=outer['elapsed_seconds'],
            body_entries=result['test_body_entries'], protocol_entries=result['test_protocol_entries'], counts=result['counts'],
            selected_ids=result['actual_selected_count'], cleanup_accepted=True, job_after_cleanup=0)
    six = children['collection06']
    need(six['actual_selected_count'] == 155 and six['test_body_entries'] == 0 and six['counts'] is None
         and len(six['collection_errors']) == len(six['denied']) == 2
         and all(row['details']['raw_path'].replace('\\', '/').endswith('/src/knowledge_tracing/research_selection.py') for row in six['denied']), '06partial dependency-read failure')
    for suffix in ('collection07', 'collection08', 'collection10'):
        result = children[suffix]
        need(result['accepted'] is True and result['mode'] == 'collect' and result['test_body_entries'] == 0
             and result['actual_selected_count'] == 221 and result['denied'] == [], 'Collection accepted not test PASS')
        need(result['nodeids'] == children['collection07']['nodeids'] and len(result['actual_new_nodeids']) == 17
             and len(result['actual_prior_nodeids']) == 204 and len(result['deselected_nodeids']) == 1,
             'Same221IDs/17new/204prior/native exclusion')
    seven, eight = children['tests07'], children['tests08']
    need(seven['test_body_entries'] == 85 and seven['counts'] == dict(tests=86, failures=0, errors=1, skipped=0)
         and seven['pytest_exit_code'] == 3, '07partial harness error preserved')
    need(eight['test_body_entries'] == 221 and eight['test_protocol_entries'] == 221
         and eight['counts'] == dict(tests=221, failures=53, errors=0, skipped=0)
         and eight['path_open_restored'] is True and eight['optional_pytest_symlink_blocks']['count'] == 183,
         '08full bodies/53FAIL and restoration, no PASS promotion')
    for suffix, cases, failures, errors in (('tests07', 86, 0, 1), ('tests08', 221, 53, 0)):
        xml = ET.fromstring(payload(PREP/f'batchc-metadata-{suffix}'/'junit.xml'))
        rows = list(xml.iter('testcase'))
        need(len(rows) == cases and sum(row.find('failure') is not None for row in rows) == failures
             and sum(row.find('error') is not None for row in rows) == errors
             and all(row.find('skipped') is None for row in rows), 'Actual physical JUnit outcomes '+suffix)
        if suffix == 'tests08':
            texts = [''.join(row.find('failure').itertext()) for row in rows if row.find('failure') is not None]
            need(all(all(word in text for word in ('inspect_runtime', 'platform.platform', '_syscmd_ver'))
                     and 'nul' in text.lower() for text in texts), 'All53traces share observed metadata chain')
    metadata10 = read(PREP/'batchc-metadata-collection10/native_metadata.json')
    need(metadata10['public_apis'] == ['platform.uname', 'platform.processor', 'platform.platform']
         and metadata10['phase_closed'] is True and metadata10['platform_cache_after_close_equal'] is True
         and metadata10['helper_calls'] == 2 and metadata10['outside_phase_popen_attempts'] == 0
         and metadata10['outside_phase_socket_attempts'] == 0, 'Genuine warmup confirmed in collection10 only')
    references['interpretation'] = dict(accepted_collection_operations=3, accepted_test_operations=0,
        native_authority=False, GPU_verified=False, source09_warmup_verified_only_by_collection10=True,
        original01_05_not_modified=True, all53_failure_traces_first_observed_chain_not_proof_no_other_defects=True,
        ROOT_terminal_observations_not_fabricated_raw_logs=dict(tests07_seconds=35.188362, tests08_seconds=36.517482))
    inventory = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), bytes=len(payload(path)), sha256=sha(path))
                 for alias, path in sorted(copies.items())]
    need(len(inventory) == 92 and sum(row['bytes'] for row in inventory) < 4*1024**2, 'Exact92smallcopies, total<4MiB')
    return inventory, references, results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-sha256', required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare-dry', action='store_true')
    modes.add_argument('--check-dry', action='store_true')
    modes.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'Repository .venv only')
    physical(DESTINATION)
    physical(REPORT)
    need(not DESTINATION.exists() and not REPORT.exists(), 'Exclusive new run/report, never overwrite')
    inventory, references, results = gather(args.report_sha256)
    dry = dict(run_id=RUN, report=REPORT.relative_to(ROOT).as_posix(), report_sha256=args.report_sha256,
        copies=inventory, reference_inputs=references, operation_summaries=results,
        generated_outputs=list(GENERATED), expected_output_count=98,
        scope='OPERATIONAL_FAILURE_HISTORY_COLLECTION_ACCEPTED_TESTS_REJECTED_OR_NO_GO_NOT_MAIN_C_ACCEPTANCE')
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=92, outputs=98)))
        return
    need(read(DRY) == dry, 'Exact dry/current inputs')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', copies=92, outputs=98)))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact-dry closure review')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    with REPORT.open('xb') as stream:
        stream.write(payload(DRAFT))
        stream.flush()
        os.fsync(stream.fileno())
    need(sha(REPORT) == args.report_sha256, 'Published report exact reviewed bytes')
    note = ('# MainC metadata06–10 — hồ sơ vận hành, chưa MainC acceptance\n\n'
            'Giữ collection06partial155;07/08/10collectionaccepted221 chỉ là lập population. '
            'Tests07partial85bodies/internalerror;tests08đủ221bodies168PASS/53FAIL. '
            '09collection và10tests NO_GO RAM trướcchild. Warmup09 chỉ runtime verified trong collection10.\n\n'
            '92copies gồm72raw trực tiếp,18worker/outer/packet/preparer/helper sources và report/archiver. '
            'Không cachetree/runtime/corpus/fullproduction copies. Closed01–05manifest reference bất biến. '
            'Closure completed chỉ lưu evidence, không sửa verdict, không fit/CUDA hoặc retry grant.\n')
    sources = [ROOT/row['source'] for row in inventory]+[ROOT/name for name in REFERENCES]+[REPORT, DRY]
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='BATCHC_METADATA_06_10_OPERATIONAL_FAILURE_HISTORY',
        operations=8, accepted_collections=3, accepted_tests=0, no_go_before_launch=2,
        tests08_counts=dict(tests=221, passed=168, failures=53, errors=0, skipped=0),
        MainC_verified=False, native_authority=False), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT/row['source']
            need(sha(source) == row['sha256'], 'SHA before copy')
            with (out/row['copy']).open('xb') as stream:
                stream.write(payload(source))
                stream.flush()
                os.fsync(stream.fileno())
            need(sha(source) == sha(out/row['copy']) == row['sha256'], 'Source/copy/source-after SHA')
            copied.append(dict(row, copy_sha256=sha(out/row['copy']), source_sha256_after_copy=sha(source)))
        write(out/'copy_inventory.json', dict(before=inventory, after=copied, unchanged=True))
        write(out/'reference_inputs.json', references)
        with (out/'reviewed_dry.json').open('xb') as stream:
            stream.write(payload(DRY))
        write(out/'closure_review.json', dict(dry_sha256=args.expected_dry_sha256,
            review_reference=args.review_reference, no_execution_rerun=True, scope='Operational archive review only'))
        again, again_refs, again_results = gather(args.report_sha256)
        need(again == inventory and again_refs == references and again_results == results, 'All source/input copies unchanged')
        expected = {row['copy'] for row in inventory}|set(GENERATED)
        need({p.name for p in out.iterdir()} == expected|{'manifest.json'}, 'Exact98outputmembership before closure')
    verification = verify_evidence_bundle(DESTINATION)
    need(verification['artifacts'] == 98 and set(read(DESTINATION/'manifest.json')['outputs_sha256']) == expected,
         'Closed98outputs and manifest SHA inventory')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(DESTINATION/'manifest.json'))))


if __name__ == '__main__':
    main()
