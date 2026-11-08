"""ROOT closure: cached join đã chạy, không chạy lại phân tích/model."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
RUN = 'rq1-query-decision-overlap-20261109-01'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
plan_path = P/'rq1_query_overlap_plan01.json'
assert sha(plan_path) == '10b955b88b1fa57fa36044415e7574aa78d07fd87a2eaff5ff8993b66f8b2412'
plan = json.loads(plan_path.read_bytes())
for name, expected in plan['sources_sha256'].items(): assert sha(ROOT/name) == expected
outer = json.loads((P/'rq1-query-overlap01-owned/final.json').read_bytes())
assert outer['status'] == 'ACCEPTED_CACHED_JOIN_NOT_NEW_RESEARCH_SAMPLE' and outer['seconds'] < 10
summary = json.loads((P/'rq1-query-overlap01/summary.json').read_bytes())
# Independent direct mapping: không import analyzer, không reuse group builder.
masters, controllers = [json.loads((ROOT/b/'event_flags.json').read_bytes()) for b in plan['input_bundles']]
right = {(r['seed'], r['profile'], r['event_id']): r for r in controllers}
counts = Counter()
for row in masters:
    paired = right[(row['seed'], row['profile'], row['event_id'])]
    counts['%d%d%d' % (row['query_native_M_changed'], row['query_raw_criterion_changed'],
                       paired['full']['selected_index'] != paired['empty']['selected_index'])] += 1
actual = {f'{i:03b}': counts[f'{i:03b}'] for i in range(8)}
assert actual == summary['groups']['pooled']['cells']
assert sum(actual.values()) == 1080
copies = {
    'analyze_rq1_query_decision_overlap.py': ROOT/'scripts/research/analyze_rq1_query_decision_overlap.py',
    'test_rq1_query_decision_overlap.py': ROOT/'tests/shared_kt/test_rq1_query_decision_overlap.py',
    'plan.json': plan_path,
    'worker.py': P/'check_rq1_overlap01.py', 'outer.py': P/'run_rq1_overlap01.py',
    'archiver.py': Path(__file__),
    'report_snapshot.md': ROOT/'research_tracking/reports/rq1_query_decision_overlap_20261109.md',
}
for directory, prefix in ((P/'rq1-query-overlap01','child'), (P/'rq1-query-overlap01-owned','owned')):
    for path in directory.iterdir():
        assert path.is_file() and not path.is_symlink() and path.stat().st_size <= 1024**2
        copies[prefix+'__'+path.name] = path
inventory = {name: dict(source=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                       sha256=sha(path)) for name, path in copies.items()}
inventory_path = P/'rq1_overlap_copy_inventory_before01.json'
dump(inventory_path, inventory)  # Persist trước copy, không move input.
note = ('# RQ1 — đối chiếu query và lựa chọn trên kết quả đã lưu\n\n'
        'Hai marginal22 chỉ trùng2snapshots:20rawcriterion-only,20CID-only,2both; '
        '5query-M khác không trùngCID. Đơn vị1080cặp snapshot,9chuỗi cũ; không '
        'thêm model/seed/learner, không causal/calibration/learningbenefit.\n\n'
        'summary.json giữ16nhóm/8ô kể cả0. Tám fixtures phần mềm không researchN. '
        'Nguồn trace/controller cũ được tham chiếu trong plan.json; không copy lại '
        'gzip hoặc sửa bundle đã đóng. child__ và owned__ là logs/receipts thực tế; '
        'execution.log chỉ là đóng gói. report_snapshot.md giải thích kết luận và giới hạn.\n')
sources = [ROOT/n for n in plan['sources_sha256']] + [plan_path, Path(__file__), copies['report_snapshot.md']]
with record_evidence_run(ROOT, RUN, metadata=dict(kind='RQ1_CACHED_QUERY_DECISION_COOCCURRENCE',
        paired_snapshots=1080, new_independent_N=0, model_calls=0,
        fixture_tests=8, research_inference='DESCRIPTIVE_NOT_CAUSAL',
        source_bundles=plan['input_bundles']), sources=sources, note=note) as out:
    dump(out/'copy_inventory_before.json', inventory)
    for name, source in copies.items():
        shutil.copy2(source, out/name)
        assert sha(source) == sha(out/name) == inventory[name]['sha256']
    # Summary alias để link report đọc trực tiếp.
    shutil.copy2(P/'rq1-query-overlap01/summary.json', out/'summary.json')
    dump(out/'independent_crosscheck.json', dict(status='MATCHED_ALL_EIGHT_POOLED_CELLS',
        cells=actual, pairs=1080, analysis_function_called=False, source_bundles=plan['input_bundles']))
    dump(out/'copy_inventory.json', dict(status='ALL_COPIES_BYTE_EXACT_SOURCE_UNCHANGED',
        copies={name:sha(out/name) for name in copies}))
verification = verify_evidence_bundle(ROOT/'research_tracking/runs'/RUN)
print(json.dumps(dict(status='CLOSED_VERIFIED', verification=verification,
                     manifest_sha256=sha(ROOT/'research_tracking/runs'/RUN/'manifest.json'))))
