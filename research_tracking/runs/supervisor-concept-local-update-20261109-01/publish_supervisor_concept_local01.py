"""Chuẩn bị hoặc chèn Chặng12 bằng raw bytes, giữ nguyên bảng và SVG cũ."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = ROOT/'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
BUNDLE = ROOT/'research_tracking/runs/paper1-concept-local-invariance-20261109-01'
PUBLICATION = PREP/'supervisor-concept-local-publication01'
MANIFEST_SHA = 'e4176e08eb84d91c07351a073beca2305e18f028774ffe21f11cfe8a196ad191'
INSERT_SHA = 'd09fa4c667db9758fc2e796e122abf44dce14524e3539ba90800e59e12a1c759'
RESULT_SHA = '2790d7245b1ee548c63d994f6bc4335ae07d1cadb1f344dc34ce9e0f7c2659aa'
PROGRESS_PROOF = ROOT/'docs/thesis_recovery/evidence/supervisor_domain_progress_update_20261109.json'
PROGRESS_SHA = '5dedab55db057b9dca678b0c513ca3ec4c868fadd0259310ee0b4037ddf555ee'
BEFORE = {
    'BAO_CAO.md': '091289aaebad0845dac5ee9fd5ff95bf342523aa86fe9e8a8043d1f2e0b1ed2e',
    'BAO_CAO_NGHIEN_CUU.html': '7009c097fbfa3f8f45adab37d309e8fd102d8a8c3a9f97abff6ae899a9668e24',
}
HEADLINE = ('Đã giải thích vì sao hai đường đi khác nhau cùng dừng ở 172 lượt trong ví dụ Paper 1. '
    'Khi giữ cùng trạng thái ban đầu và cùng số ngẫu nhiên ở từng lần luyện của mỗi khái niệm, nếu cả hai nhánh đều hoàn tất, '
    'tổng lượt và trạng thái cuối bằng nhau dù thứ tự chương có thể khác. '
    'Sáu tình huống dựng tay đã kiểm cả điều kiện này và giới hạn khi dừng sớm hoặc chạm trần trạng thái.')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, expected=None):
    need(path.resolve() == path and path.is_relative_to(ROOT), 'Đường dẫn vật lý trong repository')
    raw = path.read_bytes()
    if expected is not None:
        need(digest(raw) == expected, 'SHA thay đổi '+str(path))
    return raw


def blocks(raw, tag):
    return re.findall(rb'<'+tag+rb'\b[^>]*>.*?</'+tag+rb'>', raw, flags=re.DOTALL)


def add_before(text, anchor, addition, edits):
    need(text.count(anchor) == 1 and addition not in text, 'Anchor duy nhất, chưa publication')
    edits.append((addition+anchor, anchor))
    return text.replace(anchor, addition+anchor, 1)


def build(name, raw, draft):
    # decode/encode UTF-8 giữ nguyên CR/LF trong mọi byte cũ, không qua TextIO.
    text = raw.decode('utf-8')
    newline = '\r\n' if b'\r\n' in raw else '\n'
    paragraphs = [' '.join(part.splitlines()) for part in draft.strip().split('\n\n')]
    title = paragraphs.pop(0).removeprefix('## ')
    need(title.startswith('Chặng12.') and len(paragraphs) == 5, 'Đúng draft năm đoạn')
    edits = []
    if name.endswith('.html'):
        section = ('<section id="chang-12"><div class="label">Chặng 12</div><h2>'
            +html.escape(title.split('. ', 1)[1])+'</h2><div class="measure">'
            +''.join('<p>'+html.escape(paragraph)+'</p>' for paragraph in paragraphs)
            +'</div></section>'+newline)
        text = add_before(text, '<section id="con-thieu">', section, edits)
        text = add_before(text, '<a href="#con-thieu">',
            '<a href="#chang-12">12. Khi đồ thị chỉ đổi thứ tự</a>', edits)
        text = add_before(text, '<div class="finding"><strong>Đã có bằng chứng chẩn đoán mới cho RQ1–RQ2;',
            '<p class="measure"><strong>'+html.escape(HEADLINE)+'</strong></p>'+newline, edits)
        old, new = 'Phát hiện mới nhất cho RQ1.', 'Chẩn đoán thành thạo trước đó.'
    else:
        section = ('## '+title.replace('Chặng12.', 'Chặng 12.', 1)+newline+newline
            +(newline+newline).join(paragraphs)+newline+newline)
        text = add_before(text, '## Còn phải chứng minh', section, edits)
        text = add_before(text, '## Quá trình đã thực hiện', '**'+HEADLINE+'**'+newline+newline, edits)
        old, new = '**Mốc RQ1 mới nhất.**', '**Mốc chẩn đoán thành thạo trước đó.**'
    need(text.count(old) == 1 and new not in text, 'Đổi nhãn thời gian cũ đúng một lần')
    text = text.replace(old, new, 1)
    edits.append((new, old))
    restored = text
    for updated, original in reversed(edits):
        need(restored.count(updated) == 1, 'Phép đảo chèn duy nhất')
        restored = restored.replace(updated, original, 1)
    need(restored.encode('utf-8') == raw, 'Tất cả byte ngoài các sửa đã khai báo giữ nguyên')
    output = text.encode('utf-8')
    if name.endswith('.html'):
        need(len(blocks(raw, b'svg')) == 11 and blocks(raw, b'svg') == blocks(output, b'svg'), '11 SVG raw byte-identical')
        need(len(blocks(raw, b'table')) == 11 and blocks(raw, b'table') == blocks(output, b'table'), '11 bảng raw byte-identical')
        ids = re.findall(r'\bid="([^"]+)"', text)
        need(len(ids) == len(set(ids)), 'Không trùng HTML id')
        need(all(anchor in ids for anchor in re.findall(r'href="#([^"]+)"', text)), 'Mọi anchor nội bộ hợp lệ')
    return output


def write_json(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'Chỉ dùng repository .venv')
    manifest_raw = read(BUNDLE/'manifest.json', MANIFEST_SHA)
    manifest = json.loads(manifest_raw)
    need(manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == 17, 'Bundle thực đã đóng17outputs')
    for name, expected in manifest['outputs_sha256'].items():
        need(Path(name).name == name, 'Alias output trực tiếp')
        read(BUNDLE/name, expected)
    result = json.loads(read(BUNDLE/'result.json', RESULT_SHA))
    need(result['counts']['counts'] == dict(tests=91, failures=0, errors=0, skipped=0,
        expected_failures=0, unexpected_successes=0) and result['new_fixture_methods'] == 6
        and result['returncode'] == 0 and not result['timed_out']
        and result['source_before'] == result['source_after'], 'Actual91 gồm6fixture, không phân tích lại')
    progress = json.loads(read(PROGRESS_PROOF, PROGRESS_SHA))
    need({name: info['sha256'] for name, info in progress['after'].items()} == BEFORE, 'Bind bản raw sau lần sửa newline')
    draft = read(PREP/'SUPERVISOR_CONCEPT_LOCAL_INSERT_DRAFT01.md', INSERT_SHA).decode('utf-8')
    for old, new in (('ở172', 'ở 172'), ('trạng thái1500', 'trạng thái 1500'),
                     ('ở1498', 'ở 1498'), ('ở1200', 'ở 1200'), ('tăng2', 'tăng 2'),
                     ('tăng12', 'tăng 12'), ('đủ12', 'đủ 12'), ('bằng12', 'bằng 12')):
        draft = draft.replace(old, new)
    before = {name: read(PACKET/name, expected) for name, expected in BEFORE.items()}
    after = {name: build(name, raw, draft) for name, raw in before.items()}
    receipt = dict(status='CHECKED_CHANG12_PENDING_PUBLICATION', before_sha256=BEFORE,
        after_sha256={name: digest(raw) for name, raw in after.items()}, manifest_sha256=MANIFEST_SHA,
        insert_sha256=INSERT_SHA, progress_proof_sha256=PROGRESS_SHA,
        helper_sha256=digest(read(Path(__file__).resolve())), new_fixture_methods=6,
        svg_raw_identical=11, tables_raw_identical=11, visual_browser_qa=False,
        scope_vi='Chèn diễn giải có điều kiện và headline. Đổi nhãn mốc thành thạo cũ, không đổi bảng/biểu đồ hay phân tích.')
    if args.publish:
        PUBLICATION.mkdir(exist_ok=False)
        write_json(PUBLICATION/'inventory_before_copy.json', {name: dict(bytes=len(raw), sha256=digest(raw))
            for name, raw in before.items()})
        for name, raw in before.items():
            target = PUBLICATION/('before_'+name)
            target.write_bytes(raw)
            need(read(target) == raw, 'Snapshot raw exact trước mutation')
        # Recheck cả hai nguồn sau snapshot, trước lần ghi đầu tiên.
        for name, expected in BEFORE.items():
            read(PACKET/name, expected)
        write_json(PUBLICATION/'plan.json', receipt)
        try:
            for name, raw in after.items():
                (PACKET/name).write_bytes(raw)
                need(read(PACKET/name) == raw, 'Đọc lại publication raw exact')
                (PUBLICATION/('published_'+name)).write_bytes(raw)
            read(BUNDLE/'manifest.json', MANIFEST_SHA)
            receipt['status'] = 'PUBLISHED_CHANG12_RAW_SVG_TABLES_UNCHANGED_NO_NEW_VISUAL_QA'
            write_json(PUBLICATION/'receipt.json', receipt)
        except BaseException as exc:
            write_json(PUBLICATION/'failure.json', dict(error=repr(exc),
                current_sha256={name: digest(read(PACKET/name)) for name in BEFORE},
                automatic_retry=False, automatic_rollback=False))
            raise
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
