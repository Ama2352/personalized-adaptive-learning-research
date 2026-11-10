"""Đóng lượt kiểm checkpoint, giữ failure01 và không sao chép state.pt."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
bundle = root / 'research_tracking/runs/selected-checkpoint-binding-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
result = json.loads((prep / 'selected-checkpoint-integration02/result.json').read_bytes())
assert result['tests'] == 32 and result['source_build_files'] == 191 and len(result['checkpoints']) == 4
sources = [root / 'src/knowledge_tracing/research_selected_checkpoint.py',
           root / 'tests/shared_kt/test_research_selected_checkpoint.py', Path(__file__)]
sources += [prep / name for name in ('inspect_selected_checkpoint_schemas01.py',
    'check_selected_checkpoints01.py', 'run_selected_checkpoints01.py',
    'check_selected_checkpoints02.py', 'run_selected_checkpoints02.py')]
for directory in ('selected-checkpoint-integration01', 'selected-checkpoint-integration02',
                  'selected-checkpoint-dispatch01', 'selected-checkpoint-dispatch02'):
    sources += sorted(path for path in (prep / directory).iterdir() if path.is_file())
copies = []
for source in sources:
    relative = source.relative_to(root)
    target = bundle / '__'.join(relative.parts)
    data = source.read_bytes()
    target.write_bytes(data)
    assert source.read_bytes() == data == target.read_bytes()
    copies.append(dict(source=relative.as_posix(), output=target.name, sha256=sha(data), size_bytes=len(data)))
readme = '''# Liên kết checkpoint tốt nhất trước so sánh mô hình

Ngày10/11/2026, kiểm local `.venv` thực đạt32tests, gồm8ca checkpoint và24ca hồi quy đọc/quần thể/dòng CSV. Lượt02 đọc/hash lại bốn checkpoint A0, A1 expert, SAKT, GKT đã có. Đối chiếu COMPLETE→metadata→state, epoch tốt nhất, encoding, vocabulary, runtime, train80 và identity đầy đủ. Đọc state bằng streaming hash, không tải tensor hoặc tạo model.

## Kết quả và nguồn

Epoch tốt nhất là A0=4/7epochs, A1 expert=4/7, SAKT=1/6, GKT=6/11. Giữ riêng phase train80 của checkpoint và phase selection của claim. Bảng ánh xạ kiến trúc/nguồn đồ thị được tái dùng từ research_main_stage.CANDIDATE_BINDINGS. Artifact gốc vẫn ở experiments/<model>/results/, không sao chép state.pt vào bundle. Result02 ghi từng byte count, inventory nguồn191file, thời gian thực và kiểm hash trước–sau.

Lượt01 có31tests đạt nhưng bị từ chối khi đọc checkpoint A1 thật do validator so A1_EXPERT với tên kiến trúc A1. Nguồn bị từ chối, logs và pins01 được giữ. Lượt02 sửa theo bảng ánh xạ sẵn có và bổ sung regression kiểm kiến trúc/graph source riêng. Không sửa checkpoint hoặc model để vượt kiểm.

## Giới hạn

Đây là rehearsal lớp checkpoint trong file admission. Expected identity của lượt này được snapshot từ metadata thực trước khi kiểm, chưa là request provenance độc lập hoặc accepted-operation receipt đã review. Kiểm byte/hash không chứng minh tensor, optimizer/RNG hoặc lịch sử thực thi. Những bằng chứng đó nằm tại các bundle nghiệm thu producer trước đây và phải được nối riêng. Fixture schema2 chỉ kiểm logic metadata AKT, chưa chạy CUDA.

Chưa đủ admission chín candidate, chưa chọn mô hình/freeze/refit hoặc có kết quả Main60. Gate183 là lịch sử, source191 cần refresh sau khi hoàn tất adapter. Không có NN, Holdout hoặc chi Modal. Hai file báo cáo GVHD giữ nội dung khoa học hiện hành vì gói này không thay kết luận nghiên cứu.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_SELECTED_CHECKPOINT_ENGINEERING_EVIDENCE', copies=copies,
    tests=32, actual_checkpoints=4, model_calls=0, modal_usd=0, reviewed_operation_receipts=False,
    external_freeze_authority=False, hard_child_timeout_seconds=45,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['current_gpu_training_readiness_20261110']['local_software_gate'] = 'STALE_AFTER_SELECTION_COMPONENTS_BUILD191_REFRESH_REQUIRED'
state['selection_checkpoint_binding_20261110'] = dict(status='ACCEPTED32_TESTS_FOUR_CHECKPOINT_REHEARSAL',
    bundle=bundle.relative_to(root).as_posix(), source_build_files=191, canonical_tests=8,
    regression_tests=24, actual_checkpoints=4, reviewed_operation_receipts=False,
    nine_candidate_admission_complete=False, actual_model_selection=False)
state['selection_file_admission_next_batch_20261110']['next'] = [
    'Connect checkpoint checks and producer invocation/terminal/coverage/source bindings',
    'Review exact controller acceptance/failure receipts and pin nine-file request',
    'Integrate accumulator/kernel; refresh Gate after stable integration']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nCheckpoint binding:32tests đạt và4checkpoint thật đã hash/JSON-check, không deserialize. Failure01 do lẫn tên kiến trúc A1 với candidate A1_EXPERT giữ nguyên;02 tái dùng CANDIDATE_BINDINGS và thêm regression. Identity snapshot chỉ rehearsal, chưa provenance/receipt admission. Build191 Gate stale,0NN/Modal/subagent. Bundle selected-checkpoint-binding-20261110-01.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/selected-checkpoint-binding-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/selected-checkpoint-binding-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — liên kết checkpoint trước so sánh mô hình\n\n[Hồ sơ kiểm](' + link +
        ') đạt32tests và đọc/hash4checkpoint thật, giữ failure do ánh xạ tên kiến trúc. Chưa admission provenance/chín candidate. Source191 cần refresh Gate.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/selected-checkpoint-binding-20261110-01/** -text -whitespace\n/src/knowledge_tracing/research_selected_checkpoint.py -text\n/tests/shared_kt/test_research_selected_checkpoint.py -text\n')
print('Closed', bundle.relative_to(root), 'outputs', len(list(bundle.iterdir())))
