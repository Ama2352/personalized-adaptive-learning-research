"""Đóng đối chiếu receipt lịch sử và cập nhật trạng thái, không sao chép tensor."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
bundle = root / 'research_tracking/runs/selected-operation-reconciliation-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
result = json.loads((prep / 'selected-operation-integration04/result.json').read_bytes())
assert result['tests'] == 43 and result['source_build_files'] == 193 and len(result['operation_pins']) == 4
sources = [root / 'src/knowledge_tracing/research_selected_metadata.py',
    root / 'tests/shared_kt/test_research_selected_metadata.py', Path(__file__)]
sources += [prep / name for name in ('inspect_operation_receipts01.py', 'prepare_operation_integration03.py',
    'check_selected_operations03.py', 'run_selected_operations03.py',
    'check_selected_operations04.py', 'run_selected_operations04.py')]
for directory in ('selected-operation-integration03', 'selected-operation-integration04',
                  'selected-operation-dispatch03', 'selected-operation-dispatch04'):
    sources += sorted(path for path in (prep / directory).iterdir() if path.is_file())
copies = []
for source in sources:
    data = source.read_bytes()
    name = '__'.join(source.relative_to(root).parts)
    (bundle / name).write_bytes(data)
    assert source.read_bytes() == data == (bundle / name).read_bytes()
    copies.append(dict(source=source.relative_to(root).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
total_files = sum(row['native_files'] for row in result['operation_pins'].values())
total_bytes = sum(row['native_bytes'] for row in result['operation_pins'].values())
readme = f'''# Đối chiếu hồ sơ thực thi bốn lượt CPU đã nghiệm thu

Ngày10/11/2026,43tests thực đạt, gồm4ca operation mới và39ca hồi quy. Controller được phân biệt bằng exact profile A0/A1 expert/SAKT/GKT. Không chấp nhận một status có tiền tố chung. Kiểm nested/standalone outer-owned-worker, request/worker SHA, mã thoát và Job0, cleanup/khôi phục môi trường, source/input/runtime trước–sau, thời gian, tài nguyên lấy mẫu và toàn bộ bảng kê native.

Lượt04 đã đọc/hash {total_files}native files, tổng{total_bytes}bytes, từ bốn run gốc. Đối chiếu lại input trước–sau, không tải tensor, không chạy model và không sao chép checkpoint vào bundle. Result04 giữ đầy đủ refs và số lượng từng run. Reconciliation dùng vector nguồn đã pin trong receipt lịch sử, chưa thay request độc lập của lượt so sánh mô hình tương lai.

## Lỗi được giữ và phạm vi đã sửa

Lượt03 có43tests đạt nhưng actual A0 bị KeyError ở trường đo RAM. Controller A0 cũ chỉ ghi peak_rss_bytes/min_available_ram_bytes và áp trần worker1GiB, khác ba controller mới đo worker/family2GiB. Bản04 kiểm đúng hai schema và các trần nguồn đã quy định, thêm assertion hồi quy trần A0. Giữ rejected source/tests và logs03. Không suy diễn A0 đã đo RSS toàn Job.

## Giới hạn và việc tiếp theo

Các bằng chứng fit gốc không thay đổi. Đây là đối chiếu lịch sử trên corpus engineering, chưa nâng thành Main60 hoặc thêm researchN. Adapter chỉ hỗ trợ bốn controller đã đọc nguồn, các controller A2/A3 và matrix chính cần review riêng. Không tự suy rộng approval.

Chưa pin request nine-file độc lập hoặc kiểm absence của late-failure markers tại thời điểm publication mới. Chưa kết nối đủ9candidate/accumulator/kernel, chưa chọn winner/refit. Claim identity trong rehearsal metadata vẫn lấy từ snapshot đầu vào. Gate source193 vẫn stale sau sửa module, cần refresh sau tích hợp ổn định. Không có Holdout/Modal hoặc thay kết luận khoa học trong hai file báo cáo GVHD.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_ENGINEERING_RECEIPT_RECONCILIATION', copies=copies, tests=43,
    native_files=total_files, native_bytes=total_bytes, model_calls=0, modal_usd=0,
    main_file_admission=False, actual_model_selection=False, hard_child_timeout_seconds=45,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['selection_operation_reconciliation_20261110'] = dict(status='ACCEPTED43_TESTS_FOUR_ENGINEERING_RECEIPTS',
    bundle=bundle.relative_to(root).as_posix(), source_build_files=193, canonical_operation_tests=4,
    regression_tests=39, native_files=total_files, native_bytes=total_bytes,
    main_file_admission=False, actual_model_selection=False)
state['selection_file_admission_next_batch_20261110']['next'] = [
    'Build externally pinned nine-file request and bounded reader/metadata/rows/accumulator integration',
    'Keep historical engineering controller profiles separate from future main operation review',
    'Check late-failure marker absence before exclusive publication; refresh Gate after stable integration']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write(f'\nOperation reconciliation:43tests đạt,4exact controller receipts và{total_files}nativefiles/{total_bytes}bytes được hash lại. Lỗi03 do schemaRAM A0 khác Job-family giữ nguyên,04 kiểm đúng worker1GiB/A1-SAKT-GKT2GiB. Chưa nine-file request/late-marker publication/main admission. Source193 Gate stale,0NN/Modal/subagent. Bundle selected-operation-reconciliation-20261110-01.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/selected-operation-reconciliation-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/selected-operation-reconciliation-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — đối chiếu hồ sơ thực thi bốn lượt CPU\n\n[Hồ sơ kiểm](' + link +
        f') đạt43tests và hash lại{total_files}nativefiles. Giữ riêng schema tài nguyên A0 cũ. Chưa admission matrix chính hoặc chọn winner.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/selected-operation-reconciliation-20261110-01/** -text -whitespace\n')
print('Closed', bundle.relative_to(root), 'native files', total_files, 'bytes', total_bytes)
