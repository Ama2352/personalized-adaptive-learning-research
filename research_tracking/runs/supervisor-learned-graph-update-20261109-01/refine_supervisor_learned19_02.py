"""Chỉnh khoảng trắng văn xuôi và chuyển bảng mới thành cards trên mobile."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
before = PREP / 'supervisor-learned19-before02'
before.mkdir(exist_ok=False)
old = json.loads((PREP / 'supervisor_learned19_update01.json').read_bytes())
fixes = {'31cạnh': '31 cạnh', '18ca': '18 ca', '120lượt': '120 lượt',
         '28khái': '28 khái', '41ngày': '41 ngày', '18cặp': '18 cặp',
         '2.160vị': '2.160 vị', '720vị': '720 vị'}
receipt = dict(reason='ROOT actual desktop/mobile QA, sửa khoảng trắng mới và bảng mobile cuộn ngang thành nhóm từng khối.',
               before_sha256={}, after_sha256={})
for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html'):
    path = REPORT / name
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == old['after_sha256'][name]
    (before / name).write_bytes(raw)
    receipt['before_sha256'][name] = hashlib.sha256(raw).hexdigest()
    text = raw.decode('utf-8')
    start = text.index('## Chặng 13.') if name.endswith('.md') else text.index('<section id="chang-13">')
    finish = text.index('## Còn phải chứng minh', start) if name.endswith('.md') else text.index('<section id="con-thieu">', start)
    section = text[start:finish]
    for source, target in fixes.items():
        section = section.replace(source, target)
    if name.endswith('.html'):
        section = section.replace('<div class="table-scroll" tabindex="0">',
                                  '<div class="table-scroll progress-table" tabindex="0">')
    changed = text[:start] + section + text[finish:]
    assert re.findall(r'<svg\b.*?</svg>', changed, flags=re.S) == re.findall(r'<svg\b.*?</svg>', text, flags=re.S)
    path.write_bytes(changed.encode('utf-8'))
    receipt['after_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
with (PREP / 'supervisor_learned19_refinement02.json').open('x', encoding='utf-8') as stream:
    json.dump(receipt, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status='REFINED_CH13_PENDING_FINAL_QA', **receipt['after_sha256'])))
