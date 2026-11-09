"""Đóng bằng chứng metadata34 và các lần thất bại, giữ nguyên nguồn."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUNDLE = ROOT / 'research_tracking/runs/sakt-selected-metadata-20261110-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


result = json.loads((PREP / 'sakt-selected-metadata05-owned/final.json').read_bytes())
assert result['status'] == 'ACCEPTED_34_SAKT_SELECTED_METADATA_NOT_NATIVE'
assert result['errors'] == []
assert result['child_result']['counts'] == dict(tests=34, failures=0, errors=0, skipped=0)
assert result['owned_receipt']['job_active_after_cleanup'] == 0
sources = [ROOT / name for name in (
    'src/knowledge_tracing/sakt/research_execution.py',
    'src/knowledge_tracing/sakt/research_runner.py',
    'tests/sakt/test_research_selected_runner.py',
    'docs/thesis_recovery/30_SAKT_RESEARCH_NUMERICAL_RECIPE_V1.md')]
for path in sources[:3]:
    key = path.relative_to(ROOT).as_posix()
    assert result['source_before'][key] == result['source_after'][key] == sha(path)
paths = list(sources)
for attempt in range(1, 6):
    suffix = f'{attempt:02d}'
    paths.extend(PREP / name for name in (
        f'check_sakt_selected_metadata{suffix}.py',
        f'run_sakt_selected_metadata{suffix}.py',
        f'sakt_selected_metadata{suffix}_packet.json'))
    for directory in (f'sakt-selected-metadata{suffix}', f'sakt-selected-metadata{suffix}-owned'):
        paths.extend(path for path in (PREP / directory).rglob('*')
                     if path.is_file() and path.suffix in ('.json', '.jsonl', '.xml', '.log'))
paths.extend(path for path in (PREP / 'sakt-selected-canonical-apply01').rglob('*') if path.is_file())
paths.extend(PREP / name for name in (
    'SAKT07_CANONICAL_METADATA_HANDOFF01.md', 'SAKT07_NUMERICAL_SELECTED_PRODUCER_PROPOSAL01.md',
    'SAKT07_SELECTED_CANDIDATE_HANDOFF01.md', 'sakt_research_execution_candidate01.py',
    'sakt_research_runner_candidate01.py', 'test_sakt_selected_candidates01.py'))
paths.append(Path(__file__))
paths = sorted(set(paths))
assert not BUNDLE.exists()
inventory = []
for path in paths:
    assert path.is_file() and not path.is_symlink() and path.stat().st_size <= 4 * 1024**2
    relative = path.relative_to(ROOT).as_posix()
    destination = relative if not path.is_relative_to(PREP) else 'execution/' + path.relative_to(PREP).as_posix()
    inventory.append(dict(source=relative, destination=destination, bytes=path.stat().st_size, sha256=sha(path)))
assert sum(row['bytes'] for row in inventory) <= 24 * 1024**2
BUNDLE.mkdir()
write(BUNDLE / 'inventory_before_copy.json', inventory)
for row in inventory:
    target = BUNDLE / row['destination']
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / row['source'], target)
    assert sha(target) == row['sha256'] and sha(ROOT / row['source']) == row['sha256']
(BUNDLE / 'README.md').write_text(
    '# SAKT selected producer qua kiểm metadata\n\n'
    'Producer và admission mới đã qua 34 ca metadata trong 3,84 giây, không failure/error/skip. '
    'Nguồn và runtime trước–sau khớp, owned Job kết thúc với 0 tiến trình. '
    'Giữ cả bốn lần chưa nghiệm thu trước đó và nguyên nhân trong logs. '
    'Lần04 có34test đạt nhưng bị loại vì audit chưa phân loại đầy đủ các yêu cầu tạo link của pytest. '
    'Lần05 chỉ nhận diện đúng callsite và đường dẫn tạm sở hữu riêng, vẫn từ chối tạo link ở hệ điều hành.\n\n'
    'Recipe d200 đã chốt trước fit. Bằng chứng này kiểm đường cấp quyền, nhập liệu và hợp đồng đầu ra '
    'với fixture. Chưa nghiệm thu positive normal-entry training, chưa có SAKT fitted baseline, '
    'CUDA hoặc kết quả so sánh RQ. Không dùng credit Modal.\n', encoding='utf-8')
outputs = {path.relative_to(BUNDLE).as_posix(): sha(path) for path in BUNDLE.rglob('*') if path.is_file()}
write(BUNDLE / 'manifest.json', dict(kind='sakt_selected_metadata_34_and_failures', outputs_sha256=outputs))
print(json.dumps(dict(bundle=str(BUNDLE), inputs=len(inventory), bytes=sum(row['bytes'] for row in inventory))))
