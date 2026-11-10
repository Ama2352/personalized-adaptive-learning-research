"""Đóng bằng chứng mới, giữ nguyên outputs/source cũ và cập nhật trạng thái."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
destination = ROOT / 'research_tracking/runs/selected-row-normalization-20261110-01'
destination.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
result = json.loads((P / 'selected-rows-integration01/result.json').read_bytes())
assert result['tests'] == 24 and len(result['exports']) == 4 and result['source_build_files'] == 189
sources = {
    'research_selected_rows.py': ROOT / 'src/knowledge_tracing/research_selected_rows.py',
    'test_research_selected_rows.py': ROOT / 'tests/shared_kt/test_research_selected_rows.py',
    'check_selected_rows_integration01.py': P / 'check_selected_rows_integration01.py',
    'run_selected_rows_integration01.py': P / 'run_selected_rows_integration01.py',
    'close_selected_rows01.py': Path(__file__),
    'result.json': P / 'selected-rows-integration01/result.json',
    'stdout.log': P / 'selected-rows-dispatch01/stdout.log',
    'stderr.log': P / 'selected-rows-dispatch01/stderr.log',
    'dispatch.json': P / 'selected-rows-dispatch01/result.json',
}
copies = []
for name, source in sources.items():
    data = source.read_bytes()
    (destination / name).write_bytes(data)
    assert source.read_bytes() == data == (destination / name).read_bytes()
    copies.append(dict(source=source.relative_to(ROOT).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
readme = '''# Chuẩn hóa đầu ra selected-only trước so sánh mô hình

## Đã kiểm

Ngày10/11/2026, `.venv` local chạy24tests thực đạt, gồm8ca mới và16ca hồi quy IO/quần thể. Kiểm trường khai báo, khóa đầy đủ, nhãn, phase, encoding, geometry AKT, lý do không dự đoán của SAKT/GKT và xác suất hữu hạn. Fixtures bao phủ cả chín ID, null/OOV, cold-unsupported và unsupported-history. Không điền xác suất thay cho null.

Bốn khai báo JSON và336dòng từ A0, A1 expert, SAKT, GKT trên corpus engineering đã được đọc qua bộ IO bounded. Mỗi mô hình có84dòng, khớp K/y với expectation độc lập đã kiểm trước đó, giữ nguyên xác suất binary64 và nguồn trước–sau. `result.json` giữ thời gian thực, inventory nguồn189file và SHA input/output. `stderr.log` có24tên tests và kết quả thực.

## Nguồn và giới hạn

Exports gốc nằm tại các run riêng trong `experiments/akt/results/`, `experiments/sakt/results/`, `experiments/gkt/results/`, đường dẫn cụ thể trong result. Không sao chép checkpoint hoặc sửa artifacts gốc. Expectation đến từ bundle `main-selection-population-integration-20261110-01`, bộ IO từ `selection-artifact-io-integration-20261110-01`.

Đây là nghiệm thu phần mềm với corpus engineering, chưa là kết quả Main60 hoặc chứng minh hiệu quả RQ3. Giải mã claim chỉ kiểm khai báo, chưa xác minh toàn bộ metadata/operation receipts, admission đủ chín mô hình, chọn winner hoặc cấp quyền refit. Gate183 giữ làm lịch sử, source189 cần refresh Gate sau khi hoàn tất các adapters. Không chạy model, truy cập Holdout hoặc dùng Modal. Lệnh launcher thử qua cmd bị lỗi quoting trước khi chạy Python, đã chuyển sang launcher file có timeout30giây, không có NN hoặc file đầu ra từ lệnh lỗi.
'''
(destination / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_SELECTED_ROWS_ENGINEERING_EVIDENCE', copies=copies,
    inputs=result['inputs_sha256'], sources_before=result['sources_before'], sources_after=result['sources_after'],
    tests=24, normalized_rows=336, model_calls=0, actual_model_selection=False, modal_usd=0,
    limits=dict(hard_child_timeout_seconds=30, cooperative_reader_seconds=20),
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(destination.iterdir()) if path.is_file()})
(destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = ROOT / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['current_gpu_training_readiness_20261110']['local_software_gate'] = 'STALE_AFTER_SELECTION_COMPONENTS_BUILD189_REFRESH_REQUIRED'
state['selection_file_admission_next_batch_20261110']['next'] = [
    'Validate three producer metadata/operation receipt schemas against pinned inputs',
    'Connect externally pinned nine-file request to accumulator/kernel',
    'Refresh software Gate after stable integration; no training on stale Gate']
state['selection_file_admission_next_batch_20261110']['token_policy_vi'] = 'Root làm tuần tự,0subagent; chỉ kiểm có mục tiêu và tái dùng bằng chứng đã đóng.'
state['selection_row_normalization_20261110'] = dict(status='ACCEPTED24_TESTS_336_ACTUAL_ROWS_NOT_METADATA_ADMISSION',
    bundle=destination.relative_to(ROOT).as_posix(), source_build_files=189, canonical_tests=8,
    regression_tests=16, normalized_rows=336, actual_model_selection=False)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
log_path = ROOT / 'docs/thesis_recovery/INVESTIGATION_LOG.md'
with log_path.open('a', encoding='utf-8') as stream:
    stream.write('\nChuẩn hóa selected rows tích hợp canonical:8tests mới+16hồi quy đạt,4claims/336dòng thật khớp independent K/y và giữ binary64. Claim decoder không thay metadata/operation admission. Build189 làm Gate cũ stale, chưa NN/selector/Holdout/Modal. Bundle selected-row-normalization-20261110-01 đóng manifest/copies/logs. Root0subagent, tiếp theo kiểm metadata3producer và request đủ9.\n')
for path, entry in ((ROOT / 'docs/REPOSITORY_MAP.md',
    '[Chuẩn hóa selected rows](../research_tracking/runs/selected-row-normalization-20261110-01/README.md)'),
    (ROOT / 'research_tracking/reports/README.md',
    '[Chuẩn hóa selected rows](../runs/selected-row-normalization-20261110-01/README.md)')):
    original = path.read_bytes()
    position = original.index(b'\n') + 1
    insertion = ('\n##10/11 — chuẩn hóa đầu ra trước so sánh mô hình\n\n' + entry +
        ' đạt24tests và336dòng của4môhình trên corpus engineering, khớp quần thể độc lập. Chưa kiểm đủ metadata/chín candidate hoặc chọn winner. Gate cần refresh trên source189.\n\n').replace('##10/', '## 10/').encode('utf-8')
    path.write_bytes(original[:position] + insertion + original[position:])
attributes = ROOT / '.gitattributes'
with attributes.open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/selected-row-normalization-20261110-01/** -text -whitespace\n/src/knowledge_tracing/research_selected_rows.py -text\n/tests/shared_kt/test_research_selected_rows.py -text\n')
print('Closed evidence', destination.relative_to(ROOT), 'outputs', len(list(destination.iterdir())))
