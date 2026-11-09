"""Ghép E9 đã review vào bản thảo, không chạy model hoặc simulator."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
MD = ROOT / 'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'
MAP = MD.with_suffix('.sources.json')
CANDIDATE = PREP / 'THESIS_RQ1_MECHANISMS_DRAFT_20261109.E9candidate01.md'
APPEND = PREP / 'THESIS_RQ1_E9_SOURCE_MAP_APPEND_CANDIDATE01.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def pointer(path, text):
    value = json.loads(path.read_bytes())
    for part in text.lstrip('/').split('/'):
        key = part.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value

assert sha(MD) == 'd329b198aeb6eebeb39c6ee201ba0fa0d60466b8f11334dd72515e5e6cc45982'
assert sha(MAP) == '24d8c050b2d146c60737dd4b8284b8470d5d2be33e0bcbdeb6f0afc4f5f32efb'
assert sha(CANDIDATE) == '229bc01786e55c88fc21751a34dadf36cc9c8abcaf41e9aa21eeedac533d3828'
assert sha(APPEND) == 'd94537f88c9a46d57e54a29e7a0f27a20b2c4bc0887a5f4650720cc54b71c9e1'
old_md, old_map = MD.read_bytes(), MAP.read_bytes()
assert len(old_md) == 43799 and CANDIDATE.read_bytes().startswith(old_md)
merged = json.loads(old_map)
append = json.loads(APPEND.read_bytes())
e9 = append['e9_evidence']
for name, expected in {**merged['sources_sha256'], **e9['new_sources_sha256']}.items():
    assert sha(ROOT / name) == expected, name
assert len(e9['numeric_assertions']) == 66
for row in e9['numeric_assertions']:
    actual = pointer(ROOT / row['source_path'], row['json_pointer'])
    assert type(actual) is type(row['value']) and actual == row['value'], row
for row in e9['derived_assertions']:
    assert row['operation'] == 'sum'
    assert sum(pointer(ROOT / row['source_path'], p) for p in row['json_pointers']) == row['value']
for name, expected in e9['new_sources_sha256'].items():
    assert name not in merged['sources_sha256'] or merged['sources_sha256'][name] == expected

destination = ROOT / 'research_tracking/runs/thesis-rq1-e9-writing-20261109-01'
assert not destination.exists()
before = PREP / 'thesis-rq1-e9-before01'
before.mkdir(exist_ok=False)
(before / MD.name).write_bytes(old_md)
(before / MAP.name).write_bytes(old_map)
tail = CANDIDATE.read_bytes()[len(old_md):].decode('utf-8')
tail = tail.replace('Candidate prose chờ ROOT review trước xuất bản. Các mục1–11 cùng toàn bộ nguồn E1–E8 giữ nguyên byte trong bản candidate nối tiếp.',
    'Root đã đối chiếu 18 nguồn cùng 66 giá trị theo đường dẫn JSON và hai phép cộng từ dữ liệu đã lưu trước xuất bản. Các mục 1–11 cùng toàn bộ nguồn E1–E8 được giữ nguyên.')
new_md = old_md + tail.encode('utf-8')
links = []
for link in re.findall(rb'\]\(([^)]+)\)', new_md):
    target = link.decode('utf-8').split('#', 1)[0]
    if target and not target.startswith(('https://', 'http://')):
        assert (MD.parent / target).resolve().exists(), target
        links.append(target)
MD.write_bytes(new_md)
assert MD.read_bytes()[:43799] == old_md
merged['e9_previous_header'] = {k: merged[k] for k in ('status', 'draft_sha256', 'source_count')}
merged['status'] = 'PUBLISHED_E9_THESIS_DRAFT_EVIDENCE_BOUND_NOT_FINAL_RQ'
merged['draft_sha256'] = sha(MD)
merged['sources_sha256'].update(e9['new_sources_sha256'])
merged['source_count'] = len(merged['sources_sha256'])
merged['evidence_mapping'].update(append['evidence_mapping'])
merged['e9_candidate_parent'] = append['candidate_parent']
merged['e9_evidence'] = e9
merged['e9_evidence']['publication_status'] = 'ROOT_VERIFIED_AND_PUBLISHED_FROM_CLOSED_BUNDLE'
merged['e9_current_link_validation'] = dict(checked=len(links), all_local_targets_exist=True,
                                         direct_JSON_assertions=66, derived_sums=2)
merged['model_calls_scope'] = 'Calls performed by document analysis/publication, not calls inside referenced scientific runs.'
save(MAP, merged)
review = dict(status='PUBLISHED_E9_APPEND_ONLY', prior_bytes_preserved=43799,
    prior_draft_sha256=sha(before / MD.name), prior_map_sha256=sha(before / MAP.name),
    current_draft_sha256=sha(MD), current_map_sha256=sha(MAP),
    sources=merged['source_count'], direct_JSON_assertions=66, derived_sums=2,
    new_model_or_world_calls=0, scientific_independent_N_added=0)
save(PREP / 'thesis_e9_publication_review01.json', review)
files = {'before__' + MD.name: before / MD.name, 'before__' + MAP.name: before / MAP.name,
         'after__' + MD.name: MD, 'after__' + MAP.name: MAP,
         'candidate.md': CANDIDATE, 'source_map_append.json': APPEND,
         'publication_review.json': PREP / 'thesis_e9_publication_review01.json',
         'publication_builder.py': Path(__file__).resolve()}
inventory = [dict(copy=name, source=path.relative_to(ROOT).as_posix(), sha256=sha(path))
             for name, path in files.items()]
save(PREP / 'thesis_e9_inventory_before01.json', inventory)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
with record_evidence_run(ROOT, destination.name, sources=[*files.values(),
        *(ROOT / name for name in e9['new_sources_sha256'])],
        metadata=dict(kind='THESIS_E9_EVIDENCE_BOUND_WRITING', model_calls=0, new_independent_N=0),
        note='# E9 — phần viết nối tiếp từ đối chứng nguồn đồ thị\n\nRoot đã đọc luận điểm và kiểm18nguồn/66pointers/hai phép cộng, giữ43.799bytes E1–E8. Lượt viết không chạy model hoặc tăng mẫu. Kết quả tham chiếu learned19 giữ điều kiện tái dựng initial state, ba blocks dùng lại và chưa xác lập thứ hạng graph.\n') as out:
    for row in inventory:
        source = ROOT / row['source']
        assert sha(source) == row['sha256']
        (out / row['copy']).write_bytes(source.read_bytes())
        assert sha(source) == sha(out / row['copy']) == row['sha256']
    save(out / 'copy_inventory.json', inventory)
verified = verify_evidence_bundle(destination)
print(json.dumps(dict(**review, bundle_outputs=verified['artifacts'], manifest_sha256=sha(destination / 'manifest.json'))))
