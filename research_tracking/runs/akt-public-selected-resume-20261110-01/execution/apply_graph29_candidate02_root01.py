"""Áp dụng batch GRAPH29 đã review nguồn, chưa chứng minh native resume."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CANDIDATE = PREP / 'cgakt-selected-resume-candidate02'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


inventory_path = CANDIDATE / 'inventory-after.json'
assert sha(inventory_path) == '9a06dd86dff3a7913a6f12781eb72fecd99089965daed127f65fbb5d3d6c38ad'
inventory = json.loads(inventory_path.read_bytes())
assert len(inventory['candidate_files']) == 6 and len(inventory['canonical_originals']) == 4
review = PREP / 'GRAPH29_CANDIDATE02_INDEPENDENT_STATIC_REVIEW01.md'
assert sha(review) == '15a262b973a0a2a3a081a75c40187ecf70c0fc7c9a707991927d2b7fbfba0819'
for row in inventory['canonical_originals']:
    assert sha(ROOT / row['source']) == row['sha256']
    original_copy = PREP / 'cgakt-selected-resume-candidate01/before' / row['source']
    assert sha(original_copy) == row['sha256']
for relative in inventory['new_canonical_paths_absent']:
    assert not (ROOT / relative).exists()
for row in inventory['candidate_files']:
    source = CANDIDATE / row['relative_path']
    assert sha(source) == row['sha256'] and source.stat().st_size == row['bytes']
    compile(ast.parse(source.read_bytes(), filename=row['relative_path']), row['relative_path'], 'exec')

for row in inventory['candidate_files']:
    target = ROOT / row['relative_path']
    target.write_bytes((CANDIDATE / row['relative_path']).read_bytes())
    assert sha(target) == row['sha256']

receipt = dict(
    status='GRAPH29_CANDIDATE02_APPLIED_AST_ONLY_METADATA_AND_NATIVE_PENDING',
    files=inventory['candidate_files'], before=inventory['canonical_originals'],
    independent_review_sha256=sha(review), actual_tests_executed=0,
    actual_model_calls=0, actual_checkpoints_saved=0,
    scope='Intentional complete-epoch Windows CPU pause/resume; default fresh wire được giữ.',
    remaining='Cần metadata cold và hai stopper cases, genuine public fresh-process parity. Crash/CUDA recovery vẫn thiếu.',
    prior_MainC221_evidence_scope='Hồ sơ lịch sử trước batch nguồn mới; Gate2 và packet native06 cần đối chiếu source mới.',
)
with (PREP / 'graph29_candidate02_root_apply01.json').open('x', encoding='utf-8') as stream:
    json.dump(receipt, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status=receipt['status'], files=6, tests_executed=0)))
