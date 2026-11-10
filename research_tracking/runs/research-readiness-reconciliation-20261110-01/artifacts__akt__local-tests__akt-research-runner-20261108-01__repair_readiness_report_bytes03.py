"""Sửa chuyển CRLF do text writer, tái dựng từ snapshot và chỉ thay prose đã định."""
from pathlib import Path
import ast
import hashlib
import json
import re

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'research-readiness-reconciliation01'
tree = ast.parse((prep / 'reconcile_research_readiness02.py').read_bytes())
values = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in ('old_phrase', 'new_phrase', 'note', 'md_anchor', 'html_anchor'):
            values[name] = ast.literal_eval(node.value)
assert len(values) == 5
qa_path = out / 'reconciliation.json'
qa = json.loads(qa_path.read_bytes())
for filename in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html'):
    name = 'research_tracking/supervisor_reports/2026-11-10/01_tien_do/' + filename
    target = root / name
    before = (out / ('before__' + name.replace('/', '__'))).read_bytes()
    post02 = target.read_bytes()
    (out / ('post02_before_CRLF_repair__' + filename)).write_bytes(post02)
    changed = before.replace(values['old_phrase'].encode(), values['new_phrase'].encode())
    if filename.endswith('.md'):
        anchor = values['md_anchor'].encode()
        changed = changed.replace(anchor, (values['note'] + '\n\n').encode() + anchor)
    else:
        anchor = values['html_anchor'].encode()
        note = ('<p>' + values['note'] + '</p>').encode()
        changed = changed.replace(anchor, anchor + note)
        svgs = lambda data: re.findall(rb'<svg\b.*?</svg>', data, re.S)
        assert svgs(before) == svgs(changed) and len(svgs(changed)) == 11
        assert changed.replace(note, b'').replace(values['new_phrase'].encode(), values['old_phrase'].encode()) == before
    assert b'\r\r\n' not in changed
    target.write_bytes(changed)
    assert target.read_bytes() == changed
    qa['files'][name]['after_sha256'] = hashlib.sha256(changed).hexdigest()
qa['report_line_endings'] = 'REPAIRED_FROM_BEFORE_BYTES_ONLY_INTENDED_PROSE_EDITS_RETAINED'
qa['figures_verified_after_actual_write'] = 11
qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Repaired CRLF from original bytes;11SVG and all non-edited HTML bytes preserved.')
