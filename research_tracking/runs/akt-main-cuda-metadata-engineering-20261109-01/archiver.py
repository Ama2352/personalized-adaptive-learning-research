"""ROOT đóng hồ sơ metadata221ca; chỉ copy/kiểm bằng chứng, không chạy test."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'akt-main-cuda-metadata-engineering-20261109-01'
DRY = PREP / 'main_cuda_metadata_archive_dry01.json'
PINS = {
    'check_batchc_metadata14.py': '3ffd0c32a758af5fb99dd6120c1883cb94ec659fa7cce394bc292a16e0c32d30',
    'run_batchc_metadata14.py': '1890f5c0d8bda6cfce36714c18ce55b1043837b0d14eee567c44685896fb14f4',
    'batchc_metadata14_packet.json': '0657219e8909d965aea5eeb943268951513413b849fc0f3bb773ee44afcf7f52',
    'check_batchc_metadata15.py': 'c0eda85ae42f0d0cb97090468b2b67c18efb3a3c4cde356406b398dfb599c7a2',
    'run_batchc_metadata15.py': 'd543fbafed8faf0d6840e36d9fbc27df53305b85a23534bc54c4772c5276357b',
    'batchc_metadata15_packet.json': '8415d7bcad0f0d714bb09f774724fb72536397e1d289d3fe83420db147428df2',
    'prepare_batchc_metadata14.py': '3831c86af9dfab790df5c3e880eee1e51074c04cdfad6bdbb147bf1f62ffe8c9',
    'prepare_batchc_metadata15.py': '5f346137545707006d6b94d5eb8b11de3023457a2eb2c0572ad8f39d5670c5da',
    'BATCHC_METADATA_RESOURCE_PROFILE14_REVIEW01.md': 'f00431adbb9e66d6ce5af81efdd041805af871918453c18a868db5b632bf43b0',
    'APPLY_BATCHC_ROOT_REVIEW01.md': 'de15ae53aac04e8498c5aa28884245c0bc65439ea1fb5b4c8ef3794e81ef8a3d',
    'batchc-canonical-apply01.json': '8f608a5d66b8afa2dda730aac690b36e41a017fe8e6b59c21026c4c52dc5a3b7',
    'cuda-main-batchc-candidate01/candidate-inventory.json': 'bc8a3af1d7661f32b387ccf9df2e12be53d7b46d765973c6e7514d46d160f8e0',
    'cuda-main-batchc-candidate01/inventory-before.json': '07b8e308deef4bc65aaf45e28d664eb4ddc91355d3599ab79af18601d480397d',
    'cuda-main-batchc-candidate01/copy-verification-before.json': 'd08328e0190d0f08e6c0ef502810b51dbe2c56339f062825e8395813718f0b5e',
}
OUTER_PINS = {
    'collection14': '1fe6676bfff798698a700b3241523ca48b8abd9d3ab916a6a8d699de22190e70',
    'tests14': '7684ad3f4e87c3c561323d5b902f9af7628a8839439fb141eded595599e9c913',
    'collection15': '5176f50bc0e225d357c540fcc402770206c4866ce21e4f7620f27c3e6150eef4',
    'tests15': 'de4415589065d635396fd23e711a3891233af37534249ec22dc521b40c79b836',
}
PRIOR = {
    'akt-main-batchc-metadata-attempts-20261109-01': '25ca4b701886e188447d6275887d9ed72f26fe5936cafc734dface16f25dff57',
    'akt-main-batchc-metadata-attempts-06-10-20261109-01': '412da03714d2381745b75082c0abda41a7dc1b48503119ac7f367b2391a9594d',
    'akt-main-batchc-metadata-attempts-11-13-20261109-01': 'a7cc60d85b1acd851c6a73f3d5155cfc8ec92eb618ff629ade4d644b52d20cb1',
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


def gather(report, report_sha):
    need(sha(report) == report_sha, 'ROOT reviewed report bytes')
    copies = {'archiver.py': Path(__file__).resolve(), 'readiness_report.md': report}
    for name, pin in PINS.items():
        need(sha(PREP / name) == pin, 'frozen preparation/review/apply input')
        copies[name.replace('/', '__')] = PREP / name
    packets = {a: read(PREP / f'batchc_metadata{a}_packet.json') for a in ('14', '15')}
    need(packets['14']['expected_nodeids'] == packets['15']['expected_nodeids']
         and packets['14']['allocations'] == packets['15']['allocations']
         and packets['14']['resource_profile'] == packets['15']['resource_profile']
         and packets['14']['deselect'] == packets['15']['deselect']
         == 'tests/akt/test_runtime.py::test_native_akt_import_cpu', 'same population/caps/exact one exclusion')
    summary = {}
    for attempt, source_count in (('14', 36), ('15', 37)):
        packet = packets[attempt]
        need(len(packet['source_pins']) == source_count and len(packet['runtime_pins']) == 11
             and len(packet['expected_nodeids']) == len(set(packet['expected_nodeids'])) == 221, 'exact input/population counts')
        profile = packet['resource_profile']
        need(profile['max_worker_rss_bytes'] == 128 * 1024**2
             and profile['minimum_available_ram_bytes'] == 1024**3
             and profile['prelaunch_minimum_available_ram_bytes'] == 1280 * 1024**2, 'explicit metadata14 RAM adoption')
        for mode in ('collection', 'tests'):
            label = mode + attempt
            child_dir = PREP / ('batchc-metadata-' + label)
            owned_dir = PREP / ('batchc-metadata-' + label + '-owned')
            need(sha(owned_dir / 'final.json') == OUTER_PINS[label], 'actual ROOT external outer SHA')
            child, outer, owned = read(child_dir / 'result.json'), read(owned_dir / 'final.json'), read(owned_dir / 'receipt.json')
            child_names = {'result.json', 'native_metadata.json', 'pytest.log', 'pytest-file.log'}
            if mode == 'tests':
                child_names |= {'events.jsonl', 'junit.xml'}
            owned_names = {'final.json', 'GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stdout.log', 'stderr.log'}
            need({p.name for p in child_dir.iterdir() if p.is_file()} == child_names
                 and {p.name for p in owned_dir.iterdir()} == owned_names, 'exact raw flat output population')
            need(child['source_before'] == child['source_after'] == packet['source_pins']
                 and child['runtime_before'] == child['runtime_after'] == packet['runtime_pins']
                 and outer['source_before'] == outer['source_after'] == packet['source_pins']
                 and outer['runtime_before'] == outer['runtime_after'] == packet['runtime_pins']
                 and child['nodeids'] == packet['expected_nodeids']
                 and child['environment_and_sys_restored'] is True
                 and child['path_open_restored'] is True and child['actual_scientific_modules_absent'] is True,
                 'actual source/runtime/population/restoration')
            need(outer['receipt'] == owned and owned['cleanup_accepted'] is True
                 and owned['actual_worker_in_job_before_GO'] is True and owned['job_active_after_cleanup'] == 0
                 and owned['popen_handle_closed'] is True and owned['cleanup_errors'] == [], 'actual ownership/cleanup')
            need(set(outer['outputs']) == child_names, 'all child outputs hash-bound by ROOT outer')
            for name in sorted(child_names):
                source = child_dir / name
                need(outer['outputs'][name] == dict(bytes=len(payload(source)), sha256=sha(source)), 'original child output SHA')
                copies[label + '__child__' + name] = source
            for name in sorted(owned_names):
                copies[label + '__owned__' + name] = owned_dir / name
            failed = label == 'tests14'
            if mode == 'collection':
                need(child['counts'] is None and child['test_protocol_entries'] == child['test_body_entries'] == 0
                     and child['accepted'] is True and outer['status'] == 'ACCEPTED_BATCHC_COLLECTION_ONLY_NOT_TEST_PASS',
                     'accepted collection-only scope')
            else:
                counts = dict(tests=221, failures=int(failed), errors=0, skipped=0)
                cases = list(ET.fromstring(payload(child_dir / 'junit.xml')).iter('testcase'))
                actual = dict(tests=len(cases), failures=sum(len(list(c.iter('failure'))) for c in cases),
                    errors=sum(len(list(c.iter('error'))) for c in cases), skipped=sum(len(list(c.iter('skipped'))) for c in cases))
                need(child['counts'] == actual == counts and child['test_protocol_entries'] == child['test_body_entries'] == 221,
                     'preserve actual failed14/accepted15 physical JUnit counts')
            if failed:
                need(child['accepted'] is False and child['pytest_exit_code'] == 1 and owned['returncode'] == 1
                     and outer['status'] == 'REJECTED_BATCHC_METADATA_KEEP_ALL' and len(child['denied']) == 1
                     and Path(child['denied'][0]['details']['resolved_path']) == ROOT / 'requirements-akt.lock.txt', 'actual14 missing readonly lock pin failure')
            else:
                need(child['accepted'] is True and child['pytest_exit_code'] == 0 and child['denied'] == []
                     and outer['errors'] == [] and outer['child_result'] == child
                     and owned['accepted'] is True and owned['returncode'] == 0, 'accepted actual terminal')
            memory = child['resources']
            need(memory['samples'] > 0 and memory['observed_peak_rss_bytes'] <= 128 * 1024**2
                 and memory['observed_minimum_available_ram_bytes'] >= 1024**3, 'actual metadata resource observations')
            summary[label] = dict(status=outer['status'], counts=child['counts'], bodies=child['test_body_entries'],
                child_seconds=child['elapsed_seconds'], outer_seconds=outer['elapsed_seconds'], resources=child['resources'])
    current = read(PREP / 'batchc-metadata-tests15/result.json')
    need(current['resources'] == dict(samples=1116, observed_peak_rss_bytes=55996416,
         observed_minimum_available_ram_bytes=1374326784) and current['optional_pytest_symlink_blocks']['count'] == 183,
         'exact accepted15 resource/link observations')
    applied = read(PREP / 'batchc-canonical-apply01.json')
    need(len(applied['files']) == 8, 'eight reviewed applied canonical files')
    for name, row in applied['files'].items():
        need(sha(ROOT / name) == row['candidate_sha256'] == packets['15']['source_pins'][name], 'current applied bytes match tested source')
        copies['applied__' + name.replace('/', '__')] = ROOT / name
    prior = []
    for name, pin in PRIOR.items():
        path = ROOT / 'research_tracking/runs' / name / 'manifest.json'
        need(sha(path) == pin, 'immutable prior archive manifest')
        prior.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=pin, copied=False))
    references = dict(prior_archives=prior, packet_inputs={a: dict(source_sha256=p['source_pins'], runtime_sha256=p['runtime_pins'])
        for a, p in packets.items()}, scientific_new_N=0, native_or_cuda_proof=False,
        scope='Metadata-only acceptance; source/runtime references are not additional runtime-byte copies.')
    rows = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), bytes=len(payload(path)), sha256=sha(path))
            for alias, path in sorted(copies.items())]
    need(len(rows) == 72 and sum(r['bytes'] for r in rows) < 3 * 1024**2, 'compact exact seventy-two copies')
    return rows, references, summary


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare-dry', action='store_true')
    action.add_argument('--check-dry', action='store_true')
    action.add_argument('--close', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--report-sha256', required=True)
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv', 'repository .venv only')
    destination = ROOT / 'research_tracking/runs' / RUN
    physical(destination)
    need(not destination.exists(), 'exclusive new evidence bundle')
    rows, references, summary = gather(args.report, args.report_sha256)
    dry = dict(run_id=RUN, copies=rows, reference_inputs=references, actual_summary=summary,
        generated_outputs=list(GENERATED), expected_output_count=78, scope='MAIN_CUDA_METADATA_ONLY_221_PASS_KEEP_FAILED14')
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=72, outputs=78)))
        return
    need(read(DRY) == dry, 'exact reviewed dry/current input bytes')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', copies=72, outputs=78)))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact closure approval')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Main CUDA BatchC — metadata221ca đã nghiệm thu\n\n'
        'Lượt14 đủ221bodies nhưng220PASS/1FAIL do thiếu đúng readonly lock pin; giữ REJECTED. '
        'ROOT thêm lock3e721fdb vào namespace15, nguồn/testcase giữ nguyên. Lượt15 accepted221JUnit/protocol/bodies0FES, '
        '37source/11runtime ổn định, sys/env/Path.open khôi phục, actual scientific modules absent, denied rỗng, Job0cleanup. '
        'Metadata128MiB worker/floor1GiB/admission1280MiB là profile riêng đã duyệt. '
        'Peak55996416B/minfree1374326784B/1116samples là cooperative worker observations. '
        'Không có forward/backward/optimizer hoặc workload mô hình/CUDA; metadata Windows thật có receipt riêng. '
        'Tám file applied snapshots khớp receipt; current Gate/native CPU checkpoint/CUDA chưa được xác nhận. '
        'Đọc readiness_report.md và reference_inputs.json cho nguồn, lịch sử01–13 và giới hạn. Closure lưu bằng chứng, không cấp execution authority.\n')
    sources = list(dict.fromkeys([ROOT / row['source'] for row in rows]
        + [ROOT / ref['path'] for ref in references['prior_archives']] + [DRY]))
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='MAIN_CUDA_METADATA_ENGINEERING', tests=221,
            failures=0, errors=0, skipped=0, failed14_preserved=True, scientific_new_N=0, native_or_cuda_proof=False),
            sources=sources, note=note) as out:
        copied = []
        for row in rows:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source inventory before copy')
            with (out / row['copy']).open('xb') as stream:
                stream.write(payload(source))
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/source-after exact SHA')
            copied.append(dict(**row, source_sha256_after_copy=sha(source), copy_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', references)
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(payload(DRY))
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'exact dry snapshot')
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
            actual_summary=summary, tests_rerun=False, shared_canonical_report_modified=False))
        need({p.name for p in out.iterdir() if p.name != 'manifest.json'} == set(GENERATED) | {r['copy'] for r in rows}, 'exact78outputs')
        need(gather(args.report, args.report_sha256)[0] == rows, 'all inputs unchanged after copies')
    verification = verify_evidence_bundle(destination)
    need(verification['artifacts'] == 78, 'verified78outputs')
    print(json.dumps(dict(status='CLOSED_METADATA_ONLY_NOT_NATIVE_CUDA', outputs=78, files_including_manifest=79,
        manifest_sha256=sha(destination / 'manifest.json'), verification=verification), ensure_ascii=False))


if __name__ == '__main__':
    main()
