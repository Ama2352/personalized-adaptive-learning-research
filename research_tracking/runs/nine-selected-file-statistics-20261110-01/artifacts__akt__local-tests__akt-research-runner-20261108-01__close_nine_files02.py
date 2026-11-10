"""Đóng kiểm tích hợp chín bộ file giả, không sao chép checkpoint thật."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
bundle = root / 'research_tracking/runs/nine-selected-file-statistics-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
result = json.loads((prep / 'nine-selected-files02/result.json').read_bytes())
assert result['tests'] == 67 and result['source_build_files'] == 195 and result['real_model_calls'] == 0
sources = [root / 'src/knowledge_tracing/research_selected_files.py',
    root / 'tests/shared_kt/test_research_selected_files.py', Path(__file__)]
sources += [prep / name for name in ('check_nine_files01.py', 'run_nine_files01.py',
                                   'check_nine_files02.py', 'run_nine_files02.py')]
for directory in ('nine-selected-files01', 'nine-selected-files02',
                  'nine-selected-files-dispatch01', 'nine-selected-files-dispatch02'):
    sources += sorted(path for path in (prep / directory).iterdir() if path.is_file())
copies = []
for source in sources:
    data = source.read_bytes()
    name = '__'.join(source.relative_to(root).parts)
    (bundle / name).write_bytes(data)
    assert source.read_bytes() == data == (bundle / name).read_bytes()
    copies.append(dict(source=source.relative_to(root).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
readme = '''# Tích hợp chín bộ file selected-only vào thống kê chung

Ngày10/11/2026,67tests thực đạt gồm8ca file-integration mới và59ca hồi quy. Lượt01 đạt66ca. Sau review thêm kiểm deadline sau result construction và bắt đường dẫn source_inventory đúng canonical, lượt02 đạt67ca. Giữ nguồn/tests01 và cả hai logs, không cộng thành133ca độc lập.

## Đường xử lý đã kiểm

Request ghim SHA→đủ9ID→source refs→metadata ba producer→18CSV index→nhóm9dòng K/y→accumulator→thống kê. Request chỉ cho cached statistics. Tất cả reads có byte/file/row/index/time limits, hash trước–sau và đóng handle. Không giữ body của9bảng trong RAM, không điền xác suất thiếu hoặc thay bootstrap/loss đã chốt.

Fixture độc lập lưu ở artifacts/akt/local-tests/akt-research-runner-20261108-01/nine-selected-files02/manufactured-fixture/. fixture-inventory.json trong bundle ghim từng file gốc; code dựng fixture nằm trong test được copy. State.pt của fixture chỉ là văn bản, không phải model hoặc checkpoint huấn luyện. Bằng chứng này không sử dụng dataset thật hoặc Holdout.

Fixture có4target của3learner, một OOV của A3 expert khiến quần thể chung còn3target với2learner đóng góp và1learner không đóng góp. Có36row checks,72index entries. Kernel frozen2000draws nhận thống kê này và trả A0 khi các loss đều bằng nhau. RNG global nguyên. Đây là kết quả biết trước của fixture, không phải lựa chọn mô hình KLTN.

## Các lỗi được kiểm

Thiếu candidate bị từ chối trước đọc artifact, shared-backbone sai, key khác, cả9bảng cùng nhãn sai, common population rỗng, row budget không đủ, file đổi bytes, scope refit, source bị đổi cuối lượt và deadline vượt ngay sau dựng result. Không trả winner từ kết quả dở dang. Origin/history/phase/encoding và null reasons tiếp tục do các adapter/accumulator đã chốt kiểm.

## Giới hạn

API trả thống kê và inventory đã đọc, giữ operation/freeze/refit=false. MainAdmissionStatistics giữ nguyên cờ NOT_FILE_ADMISSION. Chưa kiểm absence late-failure markers ở publication mới, chưa pin request so sánh độc lập hoặc nghiệm thu đủ9actual Main fits. Không ghi freeze, không nối main refit, không Junyi producer và không chạy model. Bốn run engineering thật đã đối chiếu riêng ở các bundle trước không thay cho9Main conditions.

Source195 làm Gate cũ stale. Cần đóng lớp publication/operation admission và refresh Gate trên source ổn định trước dùng training. Gói này hoàn thiện đường đọc/thống kê phần mềm, không thay kết luận RQ hoặc hai file báo cáo GVHD.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_MANUFACTURED_NINE_FILE_STATISTICS_EVIDENCE', copies=copies, tests=67,
    full_targets=4, common_targets=3, row_checks=36, kernel_replicates=2000,
    real_model_calls=0, actual_model_selection=False, modal_usd=0, hard_child_timeout_seconds=45,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['current_gpu_training_readiness_20261110']['local_software_gate'] = 'STALE_AFTER_SELECTION_COMPONENTS_BUILD195_REFRESH_REQUIRED'
state['selection_nine_file_statistics_20261110'] = dict(status='ACCEPTED67_TESTS_MANUFACTURED_NINE_FILE_INTEGRATION',
    bundle=bundle.relative_to(root).as_posix(), source_build_files=195, canonical_integration_tests=8,
    regression_tests=59, full_targets=4, common_targets=3, row_checks=36,
    actual_main_fits_admitted=False, real_model_calls=0, actual_model_selection=False)
state['selection_file_admission_next_batch_20261110']['next'] = [
    'Check synthetic scaling at representative selection-target count without model training',
    'Connect independently pinned operation review and late-failure absence to exclusive publication',
    'Refresh Gate after stable integration; obtain actual nine Main fits under separate authorization']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nNine-file statistics:67tests đạt, manufactured9layouts→full4/common3/36checks→frozen2000draw kernel/A0expected. Giữ01/66ca và02/67ca, không cộngN. Có trường hợp9candidate cùngsainhãn và late-result deadline bị reject. API không cấp operation/freeze/refit. Source195 Gate stale,0NN/Holdout/Modal/subagent. Bundle nine-selected-file-statistics-20261110-01.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/nine-selected-file-statistics-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/nine-selected-file-statistics-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — chín bộ file đã ghép vào thống kê chung\n\n[Hồ sơ kiểm](' + link +
        ') đạt67tests trên dữ liệu giả, nối reader/metadata/CSV/accumulator/kernel2000draws. Chưa actual Main admission hoặc lựa chọn mô hình. Source195 cần refresh Gate.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/nine-selected-file-statistics-20261110-01/** -text -whitespace\n/src/knowledge_tracing/research_selected_files.py -text\n/tests/shared_kt/test_research_selected_files.py -text\n')
print('Closed', bundle.relative_to(root), 'outputs', len(list(bundle.iterdir())))
