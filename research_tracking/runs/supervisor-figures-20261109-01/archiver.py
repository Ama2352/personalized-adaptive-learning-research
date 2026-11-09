"""ROOT tách nguyên byte11SVG từ HTML đã QA; không render hoặc chạy nghiên cứu."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'supervisor-figures-20261109-01'
HUMAN_HTML = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html'
QA = ROOT / 'research_tracking/runs/supervisor-masking-report-qa-20261109-01'
HTML_SHA = '1d69c037458e9938902284eeebfcc3b3353dc84dffd2bda5ad20af8e614a22a1'
QA_MANIFEST_SHA = '160533c2e620add0a5aafb2bedb20ca5398d528008368b353185a0e22ee4b449'
DRY = PREP / 'supervisor_figures_archive_dry01.json'
SVG = re.compile(rb'<svg\b.*?</svg>', re.DOTALL)
FIGURE = re.compile(rb'<figure\b[^>]*>.*?</figure>', re.DOTALL)
GENERATED = ('README.md', 'execution.log', 'figure_index.json', 'figure_index.md',
             'source_references.json', 'copy_inventory.json', 'archiver.py',
             'reviewed_dry.json', 'closure_review.json')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path,
         'physical ROOT-bound path')
    cursor = ROOT
    for part in ('', *path.relative_to(ROOT).parts):
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(),
             'no input/output alias')


def payload(path):
    physical(path)
    need(path.is_file() and path.stat().st_size <= 2 * 1024**2, 'bounded regular evidence')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable read size')
    return raw


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(payload(path))


def write(path, value):
    physical(path)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def text(raw):
    return html.unescape(re.sub(r'<[^>]+>', '', raw.decode('utf-8'))).strip()


def slug(title):
    normalized = unicodedata.normalize('NFKD', title.replace('Đ', 'D').replace('đ', 'd'))
    ascii_title = normalized.encode('ascii', 'ignore').decode().lower()
    return re.sub('[^a-z0-9]+', '-', ascii_title).strip('-')[:96].rstrip('-')


def links(raw):
    return [html.unescape(match.decode('utf-8'))
            for match in re.findall(rb'href="([^"]*)"', raw)]


def gather():
    manifest_raw = payload(QA / 'manifest.json')
    need(digest(manifest_raw) == QA_MANIFEST_SHA, 'immutable QA19 manifest')
    manifest = json.loads(manifest_raw)
    need(manifest['status'] == 'completed' and manifest['svg_count'] == 11, 'completed QA snapshot')
    source = payload(HUMAN_HTML)
    snapshot = payload(QA / 'BAO_CAO_NGHIEN_CUU.html')
    old = payload(QA / 'before_BAO_CAO_NGHIEN_CUU.html')
    need(source == snapshot and digest(source) == HTML_SHA
         == manifest['outputs_sha256']['BAO_CAO_NGHIEN_CUU.html'], 'current HTML exact QA snapshot bytes')
    need(digest(old) == manifest['outputs_sha256']['before_BAO_CAO_NGHIEN_CUU.html'], 'old ten-figure snapshot')
    all_svgs = list(SVG.finditer(source))
    old_svgs = SVG.findall(old)
    figures = list(FIGURE.finditer(source))
    need(len(all_svgs) == len(figures) == 11 and len(old_svgs) == 10
         and [match.group() for match in all_svgs[:10]] == old_svgs, 'eleven SVGs and first-ten raw identity')
    source_section = re.search(rb'<section id="nguon">.*?</section>', source, re.DOTALL)
    need(source_section is not None, 'literal report source section')
    citations = [text(item) for item in re.findall(rb'<li\b[^>]*>(.*?)</li>', source_section.group(), re.DOTALL)]
    records = []
    blobs = {}
    for ordinal, figure in enumerate(figures, 1):
        local = list(SVG.finditer(figure.group()))
        captions = list(re.finditer(rb'<figcaption\b[^>]*>(.*?)</figcaption>', figure.group(), re.DOTALL))
        need(len(local) == len(captions) == 1, 'exactly one SVG and caption per figure')
        svg = local[0].group()
        start = figure.start() + local[0].start()
        end = start + len(svg)
        need((start, end) == all_svgs[ordinal - 1].span() and source[start:end] == svg,
             'exact global SVG byte span')
        element = ET.fromstring(svg)
        need(element.tag == '{http://www.w3.org/2000/svg}svg', 'standalone SVG namespace')
        titles = element.findall('{http://www.w3.org/2000/svg}title')
        descriptions = element.findall('{http://www.w3.org/2000/svg}desc')
        need(len(titles) == len(descriptions) == 1, 'one original title and description')
        title = ''.join(titles[0].itertext()).strip()
        description = ''.join(descriptions[0].itertext()).strip()
        filename = f'{ordinal:02d}-{slug(title)}.svg'
        need(title and description and filename not in blobs, 'unique semantic ordinal filename')
        section_starts = list(re.finditer(rb'<section\b[^>]*>', source[:figure.start()]))
        need(section_starts, 'figure belongs to a report section')
        section_start = section_starts[-1].start()
        section_end = source.find(b'</section>', figure.end()) + len(b'</section>')
        need(section_end >= figure.end(), 'closed containing report section')
        section = source[section_start:section_end]
        heading = re.search(rb'<h2\b[^>]*>(.*?)</h2>', section, re.DOTALL)
        section_id = re.search(rb'id="([^"]+)"', section_starts[-1].group())
        caption = captions[0].group(1)
        caption_start = figure.start() + captions[0].start(1)
        records.append(dict(ordinal=ordinal, file=filename, title=title, description=description,
            figcaption=text(caption), figcaption_html=caption.decode('utf-8'),
            figcaption_sha256=digest(caption), figcaption_start_byte=caption_start,
            figcaption_end_byte=caption_start + len(caption),
            svg_sha256=digest(svg), svg_bytes=len(svg), source_start_byte=start, source_end_byte=end,
            source_line_1based=source[:start].count(b'\n') + 1,
            section_id=None if section_id is None else section_id.group(1).decode('utf-8'),
            section_heading=None if heading is None else text(heading.group(1)),
            literal_figure_hrefs=links(figure.group()), literal_section_hrefs=links(section),
            original_text_labels=[''.join(node.itertext()) for node in element.iter('{http://www.w3.org/2000/svg}text')],
            previous_ten_byte_identical=ordinal <= 10,
            provenance_scope='SVG/caption/section literal from pinned HTML; no inferred per-figure dataset mapping'))
        blobs[filename] = svg
    references = dict(current_html=dict(path=HUMAN_HTML.relative_to(ROOT).as_posix(), bytes=len(source), sha256=HTML_SHA),
        qa_bundle=dict(path=QA.relative_to(ROOT).as_posix(), manifest_sha256=QA_MANIFEST_SHA,
            snapshot_html_sha256=digest(snapshot), before_html_sha256=digest(old),
            existing_screenshot=dict(path=(QA / 'stage11-desktop.png').relative_to(ROOT).as_posix(),
                sha256=manifest['outputs_sha256']['stage11-desktop.png'], copied=False)),
        literal_global_report_sources=citations,
        global_sources_scope='Danh mục nguồn chung trong HTML; không tự gán mỗi nguồn cho một biểu đồ.',
        data_scope='Nhãn, caption và số đã có trong SVG. Chưa đọc lại corpus hoặc tính lại bảng số liệu.',
        scientific_new_N=0, redraw=False, png_generation=False, browser_run=False)
    return records, blobs, references


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
    need(not destination.exists(), 'exclusive new figure bundle')
    records, blobs, references = gather()
    dry = dict(run_id=RUN, figure_count=11, figures=records, source_references=references,
        archiver_sha256=sha(Path(__file__).resolve()), generated_outputs=list(GENERATED), expected_output_count=20)
    if args.prepare_dry:
        write(DRY, dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED', figures=11, outputs=20, dry_sha256=sha(DRY))))
        return
    need(json.loads(payload(DRY)) == dry, 'reviewed exact dry/current figure slices')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED', figures=11, outputs=20)))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact-dry closure review')
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Lưu riêng11biểu đồ báo cáo GVHD\n\n'
        'Tách nguyên byte SVG từ HTML hiện hành trùng snapshot QA19. Tên file gồm thứ tự và tiêu đề. '
        'figure_index.json giữ title/desc/caption, nhãn chữ gốc, byte offsets và SHA; figure_index.md giúp tra cứu. '
        'Mười SVG đầu trùng nguyên byte với bản HTML trước chặng11. Không vẽ lại, không sửa số, không render PNG '
        'hoặc chạy browser/nghiên cứu. Đây là lưu phần trình bày của số liệu đã có, không thêm mẫu độc lập. '
        'Nguồn chung và liên kết chỉ chép đúng từ HTML; không tự suy diễn mapping mỗi biểu đồ sang dataset. '
        'HTML gốc, screenshot PNG và bundle QA lịch sử giữ nguyên. Closure xác nhận integrity lưu file.\n')
    sources = [HUMAN_HTML, QA / 'manifest.json', QA / 'BAO_CAO_NGHIEN_CUU.html',
               QA / 'before_BAO_CAO_NGHIEN_CUU.html', Path(__file__).resolve(), DRY]
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='VERBATIM_SUPERVISOR_SVG_PRESENTATION_ARCHIVE',
            figures=11, scientific_new_N=0, browser_reexecution=False, redraw=False), sources=sources, note=note) as out:
        copies = []
        for row in records:
            raw = payload(HUMAN_HTML)[row['source_start_byte']:row['source_end_byte']]
            need(raw == blobs[row['file']] and digest(raw) == row['svg_sha256'], 'source span SHA before copy')
            with (out / row['file']).open('xb') as stream:
                stream.write(raw)
            after = payload(HUMAN_HTML)[row['source_start_byte']:row['source_end_byte']]
            need(after == raw and sha(HUMAN_HTML) == HTML_SHA and sha(out / row['file']) == digest(raw),
                 'source span/copy/source-after exact bytes')
            copies.append(dict(file=row['file'], bytes=len(raw), sha256_before_copy=digest(raw),
                sha256_after_copy=sha(out / row['file']), source_span_sha256_after_copy=digest(after)))
        write(out / 'figure_index.json', dict(figures=records, source_html_sha256=HTML_SHA,
              byte_offsets='zero-based, end-exclusive', scientific_new_N=0))
        index = ['# Mục lục11SVG\n', 'Các hình trình bày số liệu đã có; không thêm N hoặc lượt nghiên cứu.\n',
                 '| SVG | Tiêu đề | Chú thích gốc |', '|---|---|---|']
        for row in records:
            title = row['title'].replace('|', '\\|').replace('\n', ' ')
            caption = row['figcaption'].replace('|', '\\|').replace('\n', ' ')
            index.append(f"| [{row['ordinal']:02d}]({row['file']}) | {title} | {caption} |")
        with (out / 'figure_index.md').open('x', encoding='utf-8') as stream:
            stream.write('\n'.join(index) + '\n')
        write(out / 'source_references.json', references)
        archiver = payload(Path(__file__).resolve())
        with (out / 'archiver.py').open('xb') as stream:
            stream.write(archiver)
        need(sha(out / 'archiver.py') == digest(archiver) == dry['archiver_sha256'], 'archiver exact copy')
        write(out / 'copy_inventory.json', copies)
        with (out / 'reviewed_dry.json').open('xb') as stream:
            stream.write(payload(DRY))
        need(sha(out / 'reviewed_dry.json') == args.expected_dry_sha256, 'exact reviewed dry copy')
        write(out / 'closure_review.json', dict(reference=args.review_reference, dry_sha256=args.expected_dry_sha256,
              svg_count=11, extraction_only=True, browser_or_research_rerun=False))
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED) | set(blobs), 'exact twenty output files')
        need(gather()[0] == records, 'all source slices/metadata stable after copy')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 20, 'verified twenty outputs')
    print(json.dumps(dict(status='CLOSED_VERBATIM_FIGURES_ONLY', figures=11, outputs=20,
          files_including_manifest=21, manifest_sha256=sha(destination / 'manifest.json'), verification=verified), ensure_ascii=False))


if __name__ == '__main__':
    main()
