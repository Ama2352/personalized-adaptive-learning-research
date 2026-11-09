"""Nghiệm thu source-map E13 và đóng hồ sơ trình bày Chặng17."""
from pathlib import Path
import hashlib
import json
import re
import shutil

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
reports = root / 'research_tracking/reports'
name = 'THESIS_RQ1_MECHANISMS_DRAFT_20261109'
canonical = reports / (name + '.md')
source_map = reports / (name + '.sources.json')
candidate = prep / (name + '.E13.candidate01.md')
candidate_map = prep / (name + '.E13.candidate01.sources.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def bundle(run_id, files, note, extra):
    target = root / 'research_tracking/runs' / run_id
    target.mkdir(exist_ok=False)
    inventory = {label: {'source': path.relative_to(root).as_posix(), 'sha256': sha(path),
                        'bytes': path.stat().st_size} for label, path in files.items()}
    write(target / 'inventory_before_copy.json', inventory)
    for label, path in files.items():
        shutil.copyfile(path, target / label)
        assert sha(target / label) == inventory[label]['sha256']
    write(target / 'review.json', extra)
    (target / 'README.md').write_text(note, encoding='utf-8')
    write(target / 'manifest.json', {'outputs_sha256': {p.name: sha(p) for p in target.iterdir() if p.is_file()},
                                   'closed': True})
    manifest = json.loads((target / 'manifest.json').read_bytes())
    assert all(sha(target / rel) == pin for rel, pin in manifest['outputs_sha256'].items())
    return target.relative_to(root).as_posix()


assert sha(canonical) == '2fab3d3744cdbbd7e2c2922d78a029297dea371bb0424a4e60d6af4bb1accd9b'
assert sha(candidate) == '956df92ae61b87374721ccf7017d4432c9fd23e4d73039eafd619a97a7e92558'
assert sha(candidate_map) == '5450ddced998296ee996d301c2ee47968a98b636bf6ce4faa3f17ec39278b9e5'
before = canonical.read_bytes()
assert len(before) == 70408 and candidate.read_bytes().startswith(before)
old = json.loads(source_map.read_bytes())
new = json.loads(candidate_map.read_bytes())
assert all(new[key] == value for key, value in old.items())
evidence = new['e13_evidence']
assert len(evidence['source_pins']) == 17 and len(evidence['assertions']) == 81
for rel, pin in evidence['source_pins'].items():
    assert sha(root / rel) == pin, rel
for item in evidence['assertions']:
    value = json.loads((root / item['source_path']).read_bytes())
    for part in item['json_pointer'].strip('/').split('/'):
        value = value[part]
    assert value == item['value'], item
for field, expected in [('theta_gate_true', 220), ('uncertainty_suppression', 0)]:
    total = sum(json.loads((root / rel).read_bytes())['groups']['all28'][field]
                for rel in evidence['source_pins'] if rel.endswith('/native__summary.json'))
    assert total == expected
appendix = candidate.read_bytes()[len(before):].decode('utf-8')
links = re.findall(r'\]\(([^)]+)\)', appendix)
assert len(links) == 8 and all((reports / rel).exists() for rel in links)
review = {'status': 'ROOT_REVIEWED_SCOPED_E13_PUBLICATION', 'prefix_bytes_exact': 70408,
          'direct_pointers_checked': 81, 'new_source_pins_checked': 17, 'links_checked': 8,
          'old_source_map_properties_preserved': len(old), 'independent_blocks': 1,
          'histories': 3, 'writing_model_world_calls': 0,
          'limits_vi': ['Không dùng 3360 lần đo lặp làm N độc lập.',
                        '215 TP và 5 FP ngoài câu đang hỏi khớp nguồn, chưa là chất lượng phân loại chung.',
                        '0/220 chỉ là cửa sổ ba lịch sử, không kết luận cổng luôn dư thừa.',
                        'Không gộp witness PG120 hoặc suy hiệu quả nhân quả của đồ thị.']}
out = prep / 'e13-publication-root01'
out.mkdir(exist_ok=False)
shutil.copyfile(canonical, out / 'before.md')
shutil.copyfile(source_map, out / 'before.sources.json')
new['e13_publication'] = review
canonical.write_bytes(candidate.read_bytes())
write(source_map, new)
assert canonical.read_bytes()[:len(before)] == before
shutil.copyfile(canonical, out / 'after.md')
shutil.copyfile(source_map, out / 'after.sources.json')
write(out / 'review.json', review)
writing_files = {p.name: p for p in out.iterdir() if p.is_file()}
writing_files['publisher.py'] = Path(__file__).resolve()
writing_files['appendix_source.md'] = prep / 'THESIS_E13_APPEND01.md'
writing_bundle = bundle('thesis-rq1-e13-full-panel-20261110-01', writing_files,
    '# E13 — phạm vi quan sát thành thạo\n\nGiữ nguyên E1–E12 và kiểm 81 JSON pointers, '
    '17 pins, 8 liên kết trước xuất bản. Ba lịch sử thuộc một block. Bản thảo chưa là nghiệm thu RQ.\n', review)

human = root / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
html = (human / 'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
prior = (prep / 'supervisor-ability-panels-update01/before_BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
assert re.findall(r'<svg\b.*?</svg>', html, re.S) == re.findall(r'<svg\b.*?</svg>', prior, re.S)
assert html.count('<table') == html.count('</table>') == 17
qa = {'desktop': {'viewport': 1280, 'document_width': 1265},
      'mobile': {'viewport': 390, 'document_width': 375, 'both_chapter17_table_widths': [335, 335]},
      'original_svg_byte_identical': 11, 'balanced_tables': 17,
      'root_viewed_desktop02_and_mobile02': True,
      'own_page_closed': True, 'preview_sessions_terminal': [42192, 91353],
      'first_attempt': 'Sandbox localhost timeout; own server stopped. Escalated local preview succeeded.',
      'scope_vi': 'Chặng17 và mốc kỹ thuật SAKT, không tăng số mẫu nghiên cứu.'}
files = {p.name: p for p in human.iterdir() if p.is_file() and p.name in ['BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html']}
for directory, prefix in [('supervisor-ability-panels-update01', 'publish__'), ('supervisor-ability-polish02', 'polish__')]:
    for p in (prep / directory).iterdir():
        if p.is_file():
            files[prefix + p.name] = p
for file in ['ability_panels_desktop01.png', 'ability_panels_mobile01.png', 'ability_panels_desktop02.png',
             'ability_panels_mobile02.png', 'publish_ability_panels_report01.py', 'polish_ability_report02.py',
             'polish_ability_mobile03.py']:
    files[file] = prep / file
qa_bundle = bundle('supervisor-ability-panel-visual-qa-20261110-01', files,
    '# Báo cáo Chặng17 — quan sát đủ miền\n\nHai báo cáo hiện hành, nguồn xuất bản và ảnh trước/sau sửa bảng '
    'mobile được giữ. Root đã xem desktop02/mobile02. Bảng vừa chiều rộng, 11 SVG giữ nguyên. '
    'Tab riêng và cả hai máy chủ preview đã đóng.\n', qa)
print(json.dumps({'writing_bundle': writing_bundle, 'qa_bundle': qa_bundle, 'review': review}, ensure_ascii=False))
