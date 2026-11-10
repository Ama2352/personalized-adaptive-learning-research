"""Đóng gói phần publication đã kiểm, dừng mở rộng ngoài nhu cầu thí nghiệm."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'nine-review-publication01'
bundle = root / 'research_tracking/runs/nine-review-publication-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
result = json.loads((out / 'result.json').read_bytes())
assert result['tests'] == 78 and result['source_build_files'] == 195 and result['real_model_calls'] == 0
sources = [root / 'src/knowledge_tracing/research_selected_files.py',
           root / 'tests/shared_kt/test_research_selected_files.py', Path(__file__)]
sources += [prep / name for name in ('check_nine_review_publication01.py', 'run_nine_review_publication01.py')]
sources += [path for directory in (out, prep / 'nine-review-publication-dispatch01')
            for path in sorted(directory.iterdir()) if path.is_file()]
sources += sorted((out / 'manufactured-fixture/research_tracking/runs/review-test').iterdir())
copies = []
for number, source in enumerate(sources):
    name = f'{number:02d}__{source.stem[:65]}{source.suffix}'
    data = source.read_bytes()
    (bundle / name).write_bytes(data)
    assert source.read_bytes() == data == (bundle / name).read_bytes()
    copies.append(dict(source=source.relative_to(root).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
readme = '''# Công bố review thống kê chín điều kiện bằng fixtures

Ngày10/11/2026,78tests thực đạt trong58,996giây, toàn bộ lượt driver64,382giây dưới timeout90giây. Gồm7ca publication mới và71ca trước. Dùng9producer giả/4target, không dataset thật, NN, Holdout hoặc lựa chọn mô hình thật.

Entry publish_nine_statistics_review đọc request đã pin, giữ tổng quota/time xuyên pha, tạo run mới dưới research_tracking/runs, ghi statistics/coverage/input-inventory, fsync/readback, pin atomic publisher và rehash input/output. COMPLETE được công bố qua helper không ghi đè đã có. Khi lỗi muộn xảy ra, FAILURE ưu tiên và caller không được nghiệm thu operation. Có kiểm quota, run cũ, đường dẫn bảo vệ, input/output đổi sau COMPLETE và deadline sau COMPLETE. Không reset input budget khi chuyển sang publication.

Gói review giữ operation/selection/freeze/refit=false. Caller vẫn phải nghiệm thu thực thi và actual9Main fits trước các quyết định tiếp theo. Các JSON fixture được copy có nhãn rõ, state.pt giả chỉ là văn bản và giữ ở local-tests. Không gọi COMPLETE này là system freeze hoặc kết quả RQ3. Source195 đã thay hash so với snapshot08 trước đó, Gate hiện tại vẫn stale và cần source freeze/collection mới.

Theo chỉ đạo mới của người dùng, dừng mở rộng các lớp tổng quát ở đây. Chỉ sửa tiếp khi một thí nghiệm nghiên cứu chính thực sự bị chặn. Ưu tiên chuyển sang bằng chứng RQ1/RQ2, GPU tối thiểu và các fit CG-AKT cần thiết. Scope đề cương, human approval và ngân sách30USD free credits giữ nguyên. Modal đã dùng0USD.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')
manifest = dict(kind='CLOSED_CACHED_STATISTICS_PUBLICATION_FIXTURES', copies=copies, tests=78,
    real_model_calls=0, actual_model_selection=False, external_freeze_authority=False, modal_usd=0,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['current_gpu_training_readiness_20261110']['local_software_gate'] = 'STALE_SOURCE195_PUBLICATION_CHANGED_NEW_FREEZE_REQUIRED'
state['selection_cached_publication_20261110'] = dict(status='ACCEPTED78_FIXTURE_TESTS_NOT_MAIN_FREEZE',
    bundle=bundle.relative_to(root).as_posix(), sources=195, tests=78, real_model_calls=0,
    generic_expansion_deferred_until_research_requires_it=True)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nCached publication đã chốt78tests/0FES, fixture9×4target, exclusivewrite/rehash/failureoverride và không resetbudget. Không actualMain/modelselection. Source195 cần freeze mới. Theo user, dừng genericengineering để ưu tiên nghiên cứu chính trong kịch bản7ngày. Bundle nine-review-publication-20261110-01,0NN/Modal/subagent.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/nine-review-publication-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/nine-review-publication-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — chốt gói review thống kê, chuyển ưu tiên sang nghiên cứu\n\n[Hồ sơ78tests](' + link +
        ') giữ input/output hashes, lỗi muộn và quota. Đây là fixtures, chưa Main freeze. Dừng mở rộng tổng quát khi chưa có thí nghiệm bị chặn.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/nine-review-publication-20261110-01/** -text -whitespace\n')
print('Closed78tested batch, scientific-priority directive recorded.')
