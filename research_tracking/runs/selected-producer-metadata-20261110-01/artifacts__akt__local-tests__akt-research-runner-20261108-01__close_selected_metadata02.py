"""Đóng bằng chứng metadata, giữ từng lượt và chỉ cập nhật mục lục/trạng thái."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
bundle = root / 'research_tracking/runs/selected-producer-metadata-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
result = json.loads((prep / 'selected-metadata-integration02/result.json').read_bytes())
assert result['tests'] == 39 and result['source_build_files'] == 193 and len(result['producers']) == 4
sources = [root / 'src/knowledge_tracing/research_selected_metadata.py',
    root / 'tests/shared_kt/test_research_selected_metadata.py', Path(__file__)]
sources += [prep / name for name in ('inspect_producer_bindings01.py', 'check_selected_metadata01.py',
    'run_selected_metadata01.py', 'check_selected_metadata02.py', 'run_selected_metadata02.py')]
for directory in ('selected-metadata-integration01', 'selected-metadata-integration02',
                  'selected-metadata-dispatch01', 'selected-metadata-dispatch02'):
    sources += sorted(path for path in (prep / directory).iterdir() if path.is_file())
copies = []
for source in sources:
    name = '__'.join(source.relative_to(root).parts)
    data = source.read_bytes()
    (bundle / name).write_bytes(data)
    assert source.read_bytes() == data == (bundle / name).read_bytes()
    copies.append(dict(source=source.relative_to(root).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
readme = '''# Nối metadata producer với checkpoint và quần thể

Ngày10/11/2026,39tests thực đạt trong `.venv`, gồm7ca metadata mới và32ca hồi quy. Fixtures kiểm cả9ID, ba schema thực, sai context/nguồn/runtime, selected epoch, flags refit, coverage, bytes và bảng kê COMPLETE. Lượt01 đạt39ca; sau review bổ sung đối chiếu full_selection của terminal AKT với coverage, lượt02 chạy lại39ca và4producer đều đạt. Không cộng hai lượt thành78ca độc lập.

## Đã đạt

A0, A1 expert, SAKT và GKT trên corpus engineering cùng84target đã qua đối chiếu invocation→claim→terminal→coverage→checkpoint. Các source file thực còn khớp exact vector của producer, được hash trước–sau qua reader bounded. Result02 ghi số file từng producer, SHA/size/path và thời gian. Runtime dùng đúng file đã pin. Raw invocation chứa spec được pin riêng với semantic spec/config identity, không đồng nhất hai loại hash.

Hai layouts baseline giữ population hash trung tính độc lập. AKT giữ scheme riêng, không gán nhãn nó thành K/y hash. Full K/y và336dòng được kiểm ở bundle selected-row-normalization-20261110-01, không nhân đôi exports/checkpoints ở đây.

## Phần còn thiếu

Expected claim/checkpoint identity của rehearsal này lấy từ snapshot đầu vào trước kiểm, chưa là request độc lập được review để chọn mô hình. Caller phải xác minh bytes/source snapshots trước gọi adapter thuần. Hàm trả typed claim và không cấp quyền thực thi. Chưa nối accepted-operation receipts/late-failure markers, chưa admission đủ9candidate, chưa freeze hoặc refit. Hash checkpoint không chứng minh nội dung tensor hoặc lịch sử optimizer.

Source193 cần refresh Gate sau khi ổn định tích hợp. Đây là bằng chứng phần mềm, chưa kết quả Main60/Junyi hoặc hiệu quả RQ3. Không thêm training/Holdout/Modal hoặc thay kết luận báo cáo GVHD. Gốc experiments và các bundle trước giữ nguyên.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_SELECTED_METADATA_REHEARSAL_EVIDENCE', copies=copies,
    tests=39, actual_producers=4, model_calls=0, modal_usd=0, actual_model_selection=False,
    operation_receipts_reviewed=False, hard_child_timeout_seconds=45,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['current_gpu_training_readiness_20261110']['local_software_gate'] = 'STALE_AFTER_SELECTION_COMPONENTS_BUILD193_REFRESH_REQUIRED'
state['selection_producer_metadata_20261110'] = dict(status='ACCEPTED39_TESTS_FOUR_PRODUCER_REHEARSAL',
    bundle=bundle.relative_to(root).as_posix(), source_build_files=193, canonical_tests=7,
    regression_tests=32, actual_producers=4, operation_receipts_reviewed=False,
    expected_claim_pins_independent=False, actual_model_selection=False)
state['selection_file_admission_next_batch_20261110']['next'] = [
    'Review exact controller acceptance/failure receipts and pin independent nine-file request',
    'Connect reader, metadata, rows, accumulator and kernel with bounded exclusive publication',
    'Refresh software Gate after stable integration; actual Main matrix and refits remain separate']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nProducer metadata:39tests đạt,4actual engineering producers khớp invocation/claim/terminal/coverage/checkpoint, source bytes vector và independent population expectation. Lượt02 bổ sung AKT terminal full_selection, không tăng testN hoặc researchN. Expected claim pins vẫn rehearsal, receipts chưa review, chưa9candidate/selector. Source193 Gate stale,0NN/Modal/subagent. Bundle selected-producer-metadata-20261110-01.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/selected-producer-metadata-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/selected-producer-metadata-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — metadata ba pipeline đã nối với checkpoint\n\n[Hồ sơ kiểm](' + link +
        ') đạt39tests và4producer engineering, gồm nguồn thực trước–sau. Chưa review operation receipts/request độc lập hoặc admission đủ9. Source193 cần refresh Gate.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/selected-producer-metadata-20261110-01/** -text -whitespace\n/src/knowledge_tracing/research_selected_metadata.py -text\n/tests/shared_kt/test_research_selected_metadata.py -text\n')
print('Closed', bundle.relative_to(root), 'outputs', len(list(bundle.iterdir())))
