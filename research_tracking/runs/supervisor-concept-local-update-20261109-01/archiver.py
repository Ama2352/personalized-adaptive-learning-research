"""ROOT lưu publication Chặng12, UI QA đã quan sát và recovery newline; không render."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'supervisor-concept-local-update-20261109-01'
PUBLICATION = PREP / 'supervisor-concept-local-publication01'
FAILURE = PREP / 'domain-progress-newline-failure01'
HUMAN = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
DRY = PREP / 'supervisor_concept_local_archive_dry01.json'
CURRENT = {
    'BAO_CAO.md': '5cad0e89bdf3fc2e2bdff37da72da88d26f482eb22856f30c2fbe3eca78a7dac',
    'BAO_CAO_NGHIEN_CUU.html': 'a19d007c0272061317af470eda6df93bec5818dd51349040f8cf0f44cb33496f',
}
PINS = {
    'publish_supervisor_concept_local01.py': '609157893a896e053810bd71b20e55d31bd009dc6db454dbe9a05e2273399471',
    'SUPERVISOR_CONCEPT_LOCAL_INSERT_DRAFT01.md': 'd09fa4c667db9758fc2e796e122abf44dce14524e3539ba90800e59e12a1c759',
    'recover_domain_report_newline01.py': '98430ccf785643fa2e8b5a2fd4570e565de44f7b292a391c96b3b5c374011144',
    'publish_domain_progress01.py': 'e3779c4a1b2bf258b07d9915cdc0abd2ee7634ed50285b696c5c31f7f46c640f',
    'supervisor_ch12_browser_QA01.json': '46ef6ab2e9c473219bfc2934aa50a084496dfcc3fb9552f2942be5c16330c3ba',
    'ch12-desktop.png': 'e68efb6dadc00678598027c73e27ec5f776eea7b867d1830ed3aa1880a8660c7',
    'supervisor-concept-local-publication01/receipt.json': 'c29c83760b05148d4e20469940f2abe435a1b0ab7bfee05ba8d84b52cd9c0ff8',
    'domain-progress-newline-failure01/failure.json': 'ea24f0842ddd27c289781789f69284a2ac3248ccd3244eafbce131f7fa69cc53',
}
PROGRESS = ROOT / 'docs/thesis_recovery/evidence/supervisor_domain_progress_update_20261109.json'
PROGRESS_SHA = '5dedab55db057b9dca678b0c513ca3ec4c868fadd0259310ee0b4037ddf555ee'
REFERENCES = {
    'research_tracking/runs/paper1-concept-local-invariance-20261109-01/manifest.json':
        'e4176e08eb84d91c07351a073beca2305e18f028774ffe21f11cfe8a196ad191',
    'research_tracking/runs/supervisor-masking-report-qa-20261109-01/manifest.json':
        '160533c2e620add0a5aafb2bedb20ca5398d528008368b353185a0e22ee4b449',
    'research_tracking/runs/supervisor-figures-20261109-01/manifest.json':
        '9fff53c809e47f890caf8b2b491c8c37452ee74d6f9d17a04af54dcde6594758',
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
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no path alias')


def payload(path):
    physical(path)
    need(path.is_file() and path.stat().st_size <= 2 * 1024**2, 'bounded regular input')
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
        need(sha(PREP / name) == pin, 'frozen publisher/recovery/UI source bytes')
    need(sha(PROGRESS) == PROGRESS_SHA, 'actual domain prose update receipt')
    copies = {'archiver.py': Path(__file__).resolve()}
    expected_publication = {'before_BAO_CAO.md', 'before_BAO_CAO_NGHIEN_CUU.html',
        'published_BAO_CAO.md', 'published_BAO_CAO_NGHIEN_CUU.html',
        'plan.json', 'receipt.json', 'inventory_before_copy.json'}
    need({p.name for p in PUBLICATION.iterdir()} == expected_publication, 'exact publication file population')
    for name in sorted(expected_publication):
        copies['publication__' + name] = PUBLICATION / name
    receipt = read(PUBLICATION / 'receipt.json')
    plan = read(PUBLICATION / 'plan.json')
    inventory = read(PUBLICATION / 'inventory_before_copy.json')
    need(receipt['status'] == 'PUBLISHED_CHANG12_RAW_SVG_TABLES_UNCHANGED_NO_NEW_VISUAL_QA'
         and plan['status'] == 'CHECKED_CHANG12_PENDING_PUBLICATION'
         and {k:v for k,v in receipt.items() if k != 'status'} == {k:v for k,v in plan.items() if k != 'status'},
         'actual planned/published identity and historical publication scope')
    need(receipt['after_sha256'] == CURRENT and receipt['svg_raw_identical'] == receipt['tables_raw_identical'] == 11
         and receipt['visual_browser_qa'] is False and receipt['new_fixture_methods'] == 6,
         'publication receipt remains distinct from later browser QA')
    for name, pin in CURRENT.items():
        need(sha(HUMAN / name) == sha(PUBLICATION / ('published_' + name)) == pin, 'current reports match published snapshots')
        before = PUBLICATION / ('before_' + name)
        need(sha(before) == receipt['before_sha256'][name] == inventory[name]['sha256']
             and len(payload(before)) == inventory[name]['bytes'], 'before-copy human report inventory')
    before_html = payload(PUBLICATION / 'before_BAO_CAO_NGHIEN_CUU.html')
    current_html = payload(HUMAN / 'BAO_CAO_NGHIEN_CUU.html')
    for tag in (b'svg', b'table'):
        pattern = rb'<' + tag + rb'\b[^>]*>.*?</' + tag + rb'>'
        before_blocks = re.findall(pattern, before_html, re.DOTALL)
        current_blocks = re.findall(pattern, current_html, re.DOTALL)
        need(len(before_blocks) == len(current_blocks) == 11 and before_blocks == current_blocks,
             'all eleven original SVG/table byte blocks unchanged')
    section = re.search(rb'<section id="chang-12">.*?</section>', current_html, re.DOTALL)
    need(section is not None and len(re.findall(rb'<p\b', section.group())) == 5, 'five published paragraphs in Chặng12')
    qa = read(PREP / 'supervisor_ch12_browser_QA01.json')
    need(qa['status'] == 'OBSERVED_CHANG12_DESKTOP_MOBILE_QA_OWNED_TAB_CLOSED'
         and qa['source_html_sha256'] == CURRENT['BAO_CAO_NGHIEN_CUU.html']
         and qa['screenshot_viewed_by_root'] is True and qa['owned_tab_closed'] is True
         and qa['preexisting_default_tab_untouched'] is True and qa['preview_server_started'] is False,
         'actual observed QA of the exact published HTML')
    need(qa['desktop']['viewport'] == 1280 and qa['desktop']['documentWidth'] == 1265
         and qa['mobile']['viewport'] == 390 and qa['mobile']['documentWidth'] == 375
         and qa['desktop']['paragraphs'] == 5 and qa['desktop']['brokenLocalAnchors'] == 0
         and qa['desktop']['requests'] == []
         and all(qa[device]['SVGs'] == qa[device]['tables'] == 11 for device in ('desktop', 'mobile')),
         'actual desktop/mobile scope, figures and local anchors')
    need(ROOT / qa['screenshot'] == PREP / 'ch12-desktop.png', 'original viewed screenshot identity')
    failure = read(FAILURE / 'failure.json')
    need(failure['status'] == 'PRESERVED_TEXTIO_NEWLINE_FAILURE_HUMAN_REPORTS_RESTORED_EXACT'
         and failure['raw_subprocess_stderr_captured'] is False and len(failure['files']) == 5,
         'preserve normalized Root-observed newline failure, no fabricated stderr')
    need({p.name for p in FAILURE.iterdir()} == {'failure.json'} | {row['copy'] for row in failure['files'].values()},
         'exact five failure snapshots and normalized receipt')
    for row in failure['files'].values():
        path = FAILURE / row['copy']
        need(sha(path) == row['sha256'] and len(payload(path)) == row['bytes'], 'failed content snapshot SHA/size')
        copies['newline_failure__' + row['copy']] = path
    copies['newline_failure__failure.json'] = FAILURE / 'failure.json'
    for name in ('publish_supervisor_concept_local01.py', 'SUPERVISOR_CONCEPT_LOCAL_INSERT_DRAFT01.md',
                 'supervisor_ch12_browser_QA01.json', 'ch12-desktop.png',
                 'recover_domain_report_newline01.py', 'publish_domain_progress01.py'):
        copies[name] = PREP / name
    copies['domain_progress_update.json'] = PROGRESS
    original_inventory = PREP / 'domain-progress-before01/inventory-before.json'
    copies['newline_original_inventory.json'] = original_inventory
    progress = read(PROGRESS)
    need(progress['after'] == inventory and progress['svg_byte_identical'] == progress['tables_unchanged'] == 11
         and progress['newline_failure_preserved'].endswith('domain-progress-newline-failure01/failure.json')
         and progress['restored_before_update'] is True, 'actual recovery/update to pre-Chặng12 human bytes')
    original = read(original_inventory)
    references = {}
    for name, pin in REFERENCES.items():
        need(sha(ROOT / name) == pin, 'immutable related source bundle manifest')
        references[name] = dict(sha256=pin, copied=False)
    qa19 = read(ROOT / 'research_tracking/runs/supervisor-masking-report-qa-20261109-01/manifest.json')
    for name in CURRENT:
        need(original[(HUMAN / name).relative_to(ROOT).as_posix()]['sha256'] == qa19['outputs_sha256'][name],
             'pre-failure human content referenced by immutable QA19')
    references['scope'] = 'Presentation/archive only; prior scientific bundles, original PNGs and standalone SVGs remain in place.'
    rows = [dict(copy=alias, source=path.relative_to(ROOT).as_posix(), bytes=len(payload(path)), sha256=sha(path))
            for alias, path in sorted(copies.items())]
    need(len(rows) == 22 and sum(row['bytes'] for row in rows) < 2 * 1024**2, 'compact exact twenty-two copies')
    return rows, references


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
    need(not destination.exists(), 'exclusive new publication/UI bundle')
    inventory, references = gather()
    dry = dict(run_id=RUN, copies=inventory, reference_inputs=references,
        generated_outputs=list(GENERATED), expected_output_count=28, scientific_new_N=0,
        scope='HUMAN_CHANG12_PUBLICATION_OBSERVED_UI_QA_AND_NEWLINE_RECOVERY_HISTORY')
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', dry_sha256=sha(DRY), copies=22, outputs=28)))
        return
    need(read(DRY) == dry, 'exact reviewed dry/current evidence inventory')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', copies=22, outputs=28)))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact closure review')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Báo cáo GVHD — publication Chặng12 và UI QA\n\n'
        'Giữ cặp báo cáo trước/sau, kế hoạch/receipt/inventory publication và nguồn publisher. '
        'ROOT đã xem ảnh desktop Chặng12; QA ghi desktop1280/document1265 và mobile390/document375, '
        '11SVG/11bảng,5đoạn, không broken local anchor, requests rỗng; tab riêng đã đóng, tab mặc định giữ nguyên, '
        'không mở preview server. Publication receipt trước QA vẫn giữ visual_browser_qa=false. '
        'PNG ch12-desktop.png giữ nguyên byte, không render lại khi closure. '
        'Lỗi TextIO newline trước đó giữ5snapshot và normalizedfailure.json, nguồn phục hồi và publisher đã sửa. '
        'Lỗi do ROOT quan sát ở tool output; chưa có stderr subprocess riêng, không dựng lại. '
        'QA19/figures/source khoa học tham chiếu manifest, không copy lại11SVG riêng hoặc fixture lớn. '
        'Đây là bằng chứng trình bày kết quả đã có, không thêm scientific N hoặc rerun nghiên cứu.\n')
    sources = list(dict.fromkeys([ROOT / row['source'] for row in inventory]
        + [HUMAN / name for name in CURRENT] + [ROOT / name for name in REFERENCES] + [DRY]))
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='SUPERVISOR_CHANG12_PUBLICATION_UI_QA_WITH_NEWLINE_RECOVERY',
            scientific_new_N=0, svg_count=11, tables=11, browser_reexecution=False), sources=sources, note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT / row['source']
            need(sha(source) == row['sha256'], 'source SHA before copy')
            with (out / row['copy']).open('xb') as stream:
                stream.write(payload(source))
            need(sha(source) == sha(out / row['copy']) == row['sha256'], 'before/copy/after SHA identity')
            copied.append(dict(**row, source_sha256_after_copy=sha(source), copy_sha256=sha(out / row['copy'])))
        write(out / 'copy_inventory.json', copied)
        write(out / 'reference_inputs.json', references)
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(payload(DRY))
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'exact reviewed dry copy')
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
              browser_reexecution=False, research_rerun=False, canonical_human_files_modified=False))
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | {row['copy'] for row in inventory}, 'exact twenty-eight output files')
        need(gather()[0] == inventory, 'all source evidence/current reports stable after copy')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 28, 'verified twenty-eight outputs')
    print(json.dumps(dict(status='CLOSED_PUBLICATION_AND_OBSERVED_QA_ONLY', outputs=28, files_including_manifest=29,
          manifest_sha256=sha(destination / 'manifest.json'), verification=verified), ensure_ascii=False))


if __name__ == '__main__':
    main()
