"""ROOT đóng hồ sơ lineage đã kiểm; không chạy verifier/builder hoặc render lại."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'supervisor-figure-data-lineage-20261109-01'
DRY = PREP / 'figure_data_lineage_archive_dry01.json'
FIGURE_MANIFEST = ROOT / 'research_tracking/runs/supervisor-figures-20261109-01/manifest.json'
FIGURE_MANIFEST_SHA = '9fff53c809e47f890caf8b2b491c8c37452ee74d6f9d17a04af54dcde6594758'
PINS = {
    'FIGURE_DATA_LINEAGE_DRAFT01.json': 'bf2128507f850d6d33177814af148fc63132e6594187c875d99da8f80eb5a775',
    'verify_figure_data_lineage01.py': 'cdd2005c4474c67eeb9df3b8e28d8f8f1f51c569274c29a2cc2ba9e40de7ad78',
    'run_figure_data_lineage01.py': '05944c0217c54e19695b3d787ec9c52c4a4266dd0a328f583959ec818078ee2f',
    'figure-data-lineage-verification01/result.json': 'c6bf896d92ad545ad3c1166c5fcd035aee28ccd0a0e96e5a881122c501b6c8f1',
    'figure-data-lineage-outer01/final.json': '6b74454232079db56cce3b12c18a94f31d10ffde6dbc9b849288596d0819e152',
    'figure-data-lineage-outer01/stdout.log': 'b33a7227eddad273e7c094bb275702860f01472ee7e58614d9dc16a51626b4fe',
    'figure-data-lineage-outer01/stderr.log': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
}
BUILDERS = ('html_builder', 'notebook_builder', 'process_builder', 'cross_builder', 'candidate_builder')
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
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no input/output alias')


def payload(path):
    physical(path)
    need(path.is_file() and path.stat().st_size <= 2 * 1024**2, 'bounded regular source')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable source size')
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
        need(sha(PREP / name) == pin, 'actual frozen lineage/verifier/raw receipt')
    need(sha(FIGURE_MANIFEST) == FIGURE_MANIFEST_SHA, 'immutable eleven-SVG bundle')
    lineage = read(PREP / 'FIGURE_DATA_LINEAGE_DRAFT01.json')
    actual = read(PREP / 'figure-data-lineage-verification01/result.json')
    outer = read(PREP / 'figure-data-lineage-outer01/final.json')
    need(actual['status'] == 'VERIFIED_FIGURE_DATA_LINEAGE_AND_STORED_SVG_BYTES_NOT_REBUILD'
         and actual['accepted'] is True and actual['error'] is None
         and actual['lineage_sha256'] == PINS['FIGURE_DATA_LINEAGE_DRAFT01.json']
         and actual['helper_sha256'] == PINS['verify_figure_data_lineage01.py']
         and actual['builder_execution'] is False and actual['render'] is False
         and actual['scientific_modules_absent'] is True and actual['scientific_new_N'] == 0
         and actual['end_to_end_rebuild'] == 'UNKNOWN_NOT_PERFORMED', 'actual accepted metadata-only child')
    expected = dict(registered_sources=27, closed_manifest_bindings=17, stored_svgs=11,
        primary_pointer_value_checks=54, denominator_pointer_checks=4, primary_Y_pointer_checks=36,
        cached_Psi_arithmetic_checks=9, legacy_claim_metadata_checks=14, builder_sources_AST_checked=8)
    need(all(actual['result'][key] == value for key, value in expected.items())
         and actual['result']['cached_notebook_svg_cells'] == [5, 8, 11, 13, 16, 20]
         and len(actual['result']['figures']) == 11, 'actual complete verification population')
    need(outer['status'] == 'ACCEPTED_FIGURE_LINEAGE_METADATA_ONLY' and outer['accepted'] is True
         and outer['returncode'] == 0 and outer['timed_out'] is False and outer['whole_cap_seconds'] == 30
         and outer['helper_sha256'] == actual['helper_sha256']
         and outer['result_sha256'] == PINS['figure-data-lineage-verification01/result.json']
         and 0 <= outer['elapsed_seconds'] < 30
         and actual['cooperative_cap_seconds'] == 20 and 0 <= actual['elapsed_seconds'] < 20
         and actual['disk_bytes_read'] <= 20 * 1024**2, 'actual bounded outer/child receipt')
    need({path.name for path in (PREP / 'figure-data-lineage-verification01').iterdir()} == {'result.json'}
         and {path.name for path in (PREP / 'figure-data-lineage-outer01').iterdir()} == {'final.json', 'stdout.log', 'stderr.log'},
         'exact actual raw outputs and no postwrite rejection')
    verified_inputs = actual['source_before']
    need(len(verified_inputs) == 51 and verified_inputs == actual['source_after'], 'actual fifty-one pre/post input hashes')
    for name, pin in verified_inputs.items():
        need(sha(ROOT / name) == pin, 'previously verified input still exact; no verifier rerun')
    copies = {
        'lineage.json': PREP / 'FIGURE_DATA_LINEAGE_DRAFT01.json',
        'verifier.py': PREP / 'verify_figure_data_lineage01.py',
        'outer.py': PREP / 'run_figure_data_lineage01.py',
        'verification_result.json': PREP / 'figure-data-lineage-verification01/result.json',
        'outer_final.json': PREP / 'figure-data-lineage-outer01/final.json',
        'stdout.log': PREP / 'figure-data-lineage-outer01/stdout.log',
        'stderr.log': PREP / 'figure-data-lineage-outer01/stderr.log',
        'archiver.py': Path(__file__).resolve(),
    }
    need(len(lineage['source_registry']) == 27 and len(lineage['figures']) == 11, 'lineage registry population')
    for name in BUILDERS:
        row = lineage['source_registry'][name]
        path = ROOT / row['path']
        need(path.suffix == '.py' and sha(path) == row['sha256'] and len(payload(path)) == row['bytes'], 'five exact builder source versions')
        copies['builder__' + path.name] = path
    masking = ROOT / 'research_tracking/runs/supervisor-masking-report-qa-20261109-01/publish_masking_supervisor01.py'
    need(sha(masking) == lineage['source_registry']['masking_builder']['sha256'], 'already archived masking builder reference')
    rows = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=len(payload(path)))
            for alias, path in sorted(copies.items())]
    need(len(rows) == 13 and sum(row['bytes'] for row in rows) <= 512 * 1024, 'compact thirteen selected copies')
    references = dict(figure_bundle_manifest=dict(path=FIGURE_MANIFEST.relative_to(ROOT).as_posix(), sha256=FIGURE_MANIFEST_SHA),
        registered_sources=lineage['source_registry'], actual_verified_input_sha256=verified_inputs,
        masking_builder=dict(path=masking.relative_to(ROOT).as_posix(), sha256=sha(masking), copied=False),
        builder_copy_scope='Five current versions not found as output SHA in the static reviewed run-manifest search; no claim about unmanifested copies.',
        copied_aggregates_html_notebooks_svgs_runtime=False,
        end_to_end_rebuild='UNKNOWN_NOT_PERFORMED', scientific_new_N=0)
    return rows, references, actual, outer


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
    need(not destination.exists(), 'exclusive new lineage evidence bundle')
    inventory, references, actual, outer = gather()
    dry = dict(run_id=RUN, copies=inventory, reference_inputs=references,
        generated_outputs=list(GENERATED), expected_output_count=19,
        scope='ACCEPTED_STATIC_LINEAGE_AND_STORED_SVG_VERIFICATION_NOT_END_TO_END_REBUILD')
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=13, outputs=19)))
        return
    need(read(DRY) == dry, 'exact reviewed dry/current source inventory')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', copies=13, outputs=19)))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact closure review')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Nguồn số liệu của11SVG báo cáo GVHD\n\n'
        'Giữ lineage, verifier stdlib, outer và raw result/stdout/stderr đã chạy; thêm năm phiên bản builder để tái tra cứu. '
        'ROOT đã kiểm27registered sources,17manifest bindings,54pointer/value,4denominator,36Yterms,9phép tính Psi, '
        '14claim metadata,8builder AST và11SVG nguyên byte. Sáu cached notebook cells được kiểm có SVG, không thực thi cell. '
        'Child0,31591959996148944s trong cooperative20s; outer0,4179373999941163s trong30s. '
        'Đọc6.214.374B,51inputSHA trước/sau trùng. Không có RSS monitor, hardOS quota hoặc Job receipt trong outer này. '
        'Không chạy builder/render/nghiên cứu khi verification hoặc closure. End-to-end rebuild/bitwise editorial chain vẫn UNKNOWN. '
        'C01–C14 là catalog lịch sử, không tự đồng nhất các estimand mới. Các giới hạn đơn vị/mẫu số nằm trong lineage.json. '
        'Bundle SVG gốc9fff53… và aggregate/HTML/notebook chỉ tham chiếu SHA, không copy lại. '
        'Publisher masking đã có bản trong QA19 và chỉ được tham chiếu. Không thêm scientific N hoặc cập nhật báo cáo hiện hành.\n')
    sources = list(dict.fromkeys([ROOT / row['source'] for row in inventory]
        + [ROOT / name for name in references['actual_verified_input_sha256']]
        + [ROOT / references['masking_builder']['path'], DRY]))
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='SUPERVISOR_FIGURE_DATA_LINEAGE_METADATA_VERIFICATION',
            scientific_new_N=0, svg_count=11, verifier_executed_before_closure=True,
            builder_execution=False, render=False, end_to_end_rebuild='UNKNOWN_NOT_PERFORMED'), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source SHA before copy')
            with (out / row['copy']).open('xb') as stream:
                stream.write(payload(source))
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'source/copy/source-after SHA equality')
            copied.append(dict(**row, source_sha256_after_copy=sha(source), copy_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', references)
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(payload(DRY))
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'exact reviewed dry copy')
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
              actual_verification_result_sha256=PINS['figure-data-lineage-verification01/result.json'],
              verifier_rerun_at_closure=False, builder_or_render_execution=False,
              actual_child_seconds=actual['elapsed_seconds'], actual_outer_seconds=outer['elapsed_seconds']))
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact nineteen output files')
        need(gather()[0] == inventory, 'all copied/referenced inputs remain exact after copy')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 19, 'verified nineteen outputs')
    print(json.dumps(dict(status='CLOSED_LINEAGE_METADATA_EVIDENCE_NOT_REBUILD', outputs=19, files_including_manifest=20,
          manifest_sha256=sha(destination / 'manifest.json'), verification=verified), ensure_ascii=False))


if __name__ == '__main__':
    main()
