"""Đóng benchmark file synthetic và lỗi trước đó, giữ nguyên CSV/checkpoint gốc."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
bundle = root / 'research_tracking/runs/nine-file-scaling-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
result = json.loads((prep / 'nine-file-scaling02/result.json').read_bytes())
failure = json.loads((prep / 'nine-file-scaling01/failure.json').read_bytes())
assert result['tests'] == 71 and result['full_targets'] == 1260 and result['source_build_files'] == 195
sources = [root / name for name in ('src/knowledge_tracing/research_selection_io.py',
    'src/knowledge_tracing/research_selected_files.py', 'tests/shared_kt/test_research_selection_io.py',
    'tests/shared_kt/test_research_selected_files.py')]
sources += [Path(__file__)] + [prep / name for name in ('check_nine_file_scaling01.py', 'run_nine_file_scaling01.py',
                                                      'check_nine_file_scaling02.py', 'run_nine_file_scaling02.py')]
for directory in ('nine-file-scaling01', 'nine-file-scaling02', 'nine-file-scaling-dispatch01', 'nine-file-scaling-dispatch02'):
    sources += sorted(path for path in (prep / directory).iterdir() if path.is_file())
copies = []
for source in sources:
    data = source.read_bytes()
    name = '__'.join(source.relative_to(root).parts)
    (bundle / name).write_bytes(data)
    assert source.read_bytes() == data == (bundle / name).read_bytes()
    copies.append(dict(source=source.relative_to(root).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
readme = f'''# Quy mô đọc file chín điều kiện với1.260target giả

Ngày10/11/2026,71tests đạt trong `.venv` và lượt synthetic9conditions×1.260target hoàn tất. Fixture có6learner×210events,18CSV,11.340row checks,22.680index entries, common1.259target do1OOV của A3 expert. Không có dữ liệu/model thật hoặc Holdout.

## Số đo và nguyên nhân

Lượt01 có68tests đạt nhưng reader bị từ chối sau{failure['elapsed_seconds']:.3f}giây tại cap45giây. Cách cũ mở lại file và kiểm đường dẫn mỗi lần đọc một dòng. Nguồn trước sửa và failure/stdout/stderr được giữ ở bundle này. Không nâng cap rồi coi là sửa thành công.

Lượt02 giữ45giây reader cap, hoàn tất trong{result['file_read_seconds']:.3f}giây, peak worker{result['peak_worker_rss_bytes']}bytes, fixture{result['fixture_bytes']}bytes. Explicit max_open_files đổi từ1 sang18 để giữ các CSV đã xác minh trong context. Mỗi dòng vẫn kiểm length/SHA/K, file handle được bind identity trước đọc, kiểm lại stamp/path khi đóng và toàn input được rehash cuối. ExitStack đóng handle trước kiểm cuối. Callers dùng cap1 vẫn giữ cách đọc cũ và được kiểm hồi quy. Kết quả thống kê, coverage, input inventory và logical read-byte count của hai cách khớp trong fixture cùng4target.

Không gọi đây là tỷ lệ tăng tốc định lượng vì lượt cũ chưa hoàn tất và chưa ghi số dòng đã xử lý lúc timeout. So sánh quan sát là timeout45giây với cap1, sau sửa hoàn tất11,807giây với cap18 trên cùng quy mô target và workload giả. Peak lấy từ process high-water mark, không phải OS hard memory quota. Giới hạn outer120giây áp dụng bằng timeout child, không có subprocess/model/network bên trong.

## Bằng chứng và giới hạn

71tests gồm bảo toàn đường đọc cũ, handle close, cursor hết hiệu lực, tamper trong context, handle limit, parity của cả9môhình, population và kernel. Không cộng68và71thành139ca độc lập. Result02 giữ source195 trước–sau, caps, RAM, thời gian, read bytes và trạng thái không chọn mô hình. Fixture-inventory02 ghim các file ở local-tests/nine-file-scaling02/manufactured-fixture; các file giả và sources còn tại đó, không sao chép toàn bộ vào Git.

Đây là throughput đọc artifact sau training, không phải training/GPU throughput hoặc bằng chứng RQ3. Chưa có main operation admission, exclusive freeze/publication, actual9fits hoặc refit. Source195 cần Gate mới, Linux/CUDA/fault recovery/durability và GPU cost còn chưa đo. Không dùng Modal. Hai file báo cáo GVHD giữ kết luận khoa học hiện hành, kế hoạch GPU07 được cập nhật trạng thái chuẩn bị.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_SYNTHETIC_FILE_SCALING_EVIDENCE', copies=copies, tests=71,
    full_targets=1260, common_targets=1259, row_checks=11340, real_model_calls=0, modal_usd=0,
    actual_model_selection=False, training_throughput_measured=False, hard_child_timeout_seconds=120,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['selection_file_scaling_20261110'] = dict(status='ACCEPTED71_TESTS_SYNTHETIC1260',
    bundle=bundle.relative_to(root).as_posix(), source_build_files=195, reader_seconds=result['file_read_seconds'],
    peak_worker_rss_bytes=result['peak_worker_rss_bytes'], full_targets=1260, common_targets=1259,
    index_entries=22680, max_open_files=18, prior_timeout_preserved=True, real_model_calls=0,
    actual_model_selection=False, training_throughput_measured=False)
state['selection_file_admission_next_batch_20261110']['next'] = [
    'Connect independently pinned operation review and late-failure absence to exclusive publication',
    'Refresh software Gate on stable source; retain explicit18-handle reader profile',
    'Validate actual Linux/CUDA/recovery and measure GPU throughput before Modal grant']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write(f'\nSynthetic file scaling:01/68tests đạt nhưng reader timeout45, giữ nguồn/failure. Scoped cursors cap18 và ExitStack giữ hash/identity/rehash.02/71tests đạt,1260targets/11340checks/22680indices, reader{result["file_read_seconds"]:.3f}s/45s, peak{result["peak_worker_rss_bytes"]}B. Không training/GPU throughput hoặc RQ evidence. Source195 Gate stale,0NN/Modal/subagent. Bundle nine-file-scaling-20261110-01, GPUplan07 cập nhật.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/nine-file-scaling-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/nine-file-scaling-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — reader đủ quy mô1.260target giả\n\n[Hồ sơ kiểm](' + link +
        ') đạt71tests, reader11,807giây/45giây và peak57.769.984bytes. Giữ timeout cũ, cap18handle được đo riêng. Đây là đọc artifact, chưa là GPU training throughput.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/nine-file-scaling-20261110-01/** -text -whitespace\n')
print('Closed', bundle.relative_to(root), 'outputs', len(list(bundle.iterdir())))
