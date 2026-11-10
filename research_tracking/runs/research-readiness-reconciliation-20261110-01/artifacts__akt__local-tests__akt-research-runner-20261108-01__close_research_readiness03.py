"""Đóng audit tài liệu/tracker, kiểm liên kết và không tạo kết quả khoa học mới."""
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'research-readiness-reconciliation01'
bundle = root / 'research_tracking/runs/research-readiness-reconciliation-20261110-01'
bundle.mkdir(exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()
qa = json.loads((out / 'reconciliation.json').read_bytes())
assert qa['tasks'] == 178 and len(qa['changed_tasks']) == 8 and qa['figures_verified_after_actual_write'] == 11
sources = [Path(__file__)] + [prep / name for name in ('inspect_research_readiness01.py',
    'reconcile_research_readiness02.py', 'repair_readiness_report_bytes03.py')]
sources += sorted(path for path in out.iterdir() if path.is_file())
copies = []
for source in sources:
    data = source.read_bytes()
    name = '__'.join(source.relative_to(root).parts)
    (bundle / name).write_bytes(data)
    assert source.read_bytes() == data == (bundle / name).read_bytes()
    copies.append(dict(source=source.relative_to(root).as_posix(), output=name, sha256=sha(data), size_bytes=len(data)))
readme = '''# Đối chiếu tiến độ nghiên cứu và loại bỏ trạng thái lỗi thời

Ngày10/11/2026, rà lại sổ gap/backlog sau các gói phần mềm và bằng chứng RQ đã nghiệm thu. Đợt này không tạo thêm tương tác, train, thống kê hoặc kết luận nghiên cứu. Không đọc dataset hoặc Test.

## Phát hiện và sửa

RESEARCH_GAPS vẫn là snapshot ban đầu, gồm các nhận định chưa tìm thấy simulator, chưa có graph experiment và chưa có đề cương. Bảng hiện hành14gap đã nối nguồn mới và giữ nguyên snapshot lịch sử bên dưới. Các việc định vị tài liệu được tách khỏi bằng chứng RQ còn thiếu. Thêm gap giao diện hai môi trường và demo/viết cuối để giữ đủ scope.

Ba PDF chuẩn trong paper1/paper2 khớp nguyên byte ba file người dùng cung cấp trên Desktop. pdf-identity.json ghi SHA/size/path thực của cả hai bản. Đây là kiểm identity, không phải một lượt đọc lại nội dung hoặc một phê duyệt phương pháp mới.

Backlog giữ178ID, cập nhật8parent tasks từ bằng chứng hiện có, ghi previous_status và giới hạn từng mục. Không có task nào được chuyển sang completed trong lượt này. current_execution_queue dùng6ID sẵn có, Root tuần tự. execution_authorized vẫnfalse, không cấp fullCV/Holdout/cloud/final selection.

RESEARCH_PROGRESS làm rõ Gate183/1913 thuộc mốc trước, source195 đang chờ Gate mới sau RAM NO-GO. Hai file GVHD sửa một cụm thời gian Gate và thêm một đoạn giải thích mục đích kiểm ghép dữ liệu giả. Không biến71tests hay reader1260 thành kết quả so sánh neural.

## Kiểm và giới hạn

Đã parse lại JSON, kiểm178ID duy nhất, các evidence links hiện hành và source paths.11SVG giữ nguyên byte,17tables giữ nguyên, HTML ngoài đúng hai phép sửa prose khôi phục được nguyên bản bằng phép đảo. Không có browser/visual QA mới vì chỉ thay nội dung trong bố cục hiện hành; đây là static QA.

Text writer02 đã làm đôi CRLF trong hai báo cáo, phát hiện trước commit.03 tái dựng từ snapshot byte ban đầu và chỉ áp dụng hai phép sửa nội dung. Giữ post02 để audit; bản chính đã sửa, không còn CRCRLF. Không sửa lại bundle cũ hoặc kết quả thực nghiệm.

Các RQ vẫn chưa hoàn tất. Matrix neural, Junyi producer, calibration/mastery/outcome, noise/history, demo fitted learner và thesis/article/defense vẫn còn trong sổ gap. Gate cần thêm RAM để chạy, các việc nhẹ có thể tiếp tục. Modal0USD.
'''
(bundle / 'README.md').write_text(readme, encoding='utf-8')

gap_path = root / 'research_tracking/RESEARCH_GAPS.md'
gap = gap_path.read_text(encoding='utf-8')
before_gap = (out / 'before__research_tracking__RESEARCH_GAPS.md').read_text(encoding='utf-8')
assert gap.split('## Snapshot kiểm toán ban đầu\n\n', 1)[1] == before_gap.split('\n\n', 1)[1]
links = []
for name in ('research_tracking/RESEARCH_GAPS.md', 'research_tracking/RESEARCH_PROGRESS.md'):
    path = root / name
    text = path.read_text(encoding='utf-8').split('## Snapshot kiểm toán ban đầu', 1)[0]
    for ref in re.findall(r'\]\(([^)]+)\)', text):
        if not ref.startswith(('http:', 'https:', '#')):
            target = (path.parent / ref.split('#', 1)[0]).resolve()
            assert target.is_relative_to(root) and target.is_file(), (name, ref)
            links.append(dict(document=name, reference=ref))
tasks = json.loads((root / 'docs/thesis_recovery/TASKS.json').read_bytes())
assert len(tasks['tasks']) == len({item['id'] for item in tasks['tasks']}) == 178
assert tasks['execution_authorized'] is False
for update in qa['changed_tasks']:
    for reference in update['evidence']:
        assert (root / reference).is_file(), reference
for name, expected in qa['files'].items():
    assert sha((root / name).read_bytes()) == expected['after_sha256']
check = dict(status='STATIC_QA_ACCEPTED', validated_links=len(links), links=links,
    tasks=178, report_svg_bytes_unchanged=11, report_table_count=17,
    historical_gap_snapshot_unchanged=True, visual_browser_review=False, new_research_samples=0)
(bundle / 'static-qa.json').write_text(json.dumps(check, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
manifest = dict(kind='CLOSED_RESEARCH_READINESS_RECONCILIATION', copies=copies, changed_files=qa['files'],
    new_research_samples=0, model_calls=0, Holdout_access=False, modal_usd=0,
    outputs={path.name: dict(sha256=sha(path.read_bytes()), size_bytes=path.stat().st_size)
             for path in sorted(bundle.iterdir())})
(bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['research_readiness_reconciliation_20261110'] = dict(status='ACCEPTED_TRACKER_AND_REPORT_STATIC_QA',
    bundle=bundle.relative_to(root).as_posix(), canonical_pdf_identities=3,
    current_gaps=14, updated_parent_tasks=8, task_ids_preserved=178,
    report_svg_preserved=11, report_tables=17, new_research_samples=0,
    visual_browser_review=False)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nReadiness reconciliation:3PDF repo/Desktop identical,14current gaps và8parent statuses sửa theo evidence,178IDs giữ. Snapshot gap cũ nguyên; không taskcompleted/newN. Hai report đổi cụmGate và thêm mục đích readerfixture,11SVG nguyên/17tables, staticQA. Writer02 CRLF lỗi đã03 sửa từbytebefore trướccommit, giữpost02. Gate195 vẫnSTALE/RAMNO-GO,0NN/Modal/subagent. Bundle research-readiness-reconciliation-20261110-01.\n')
for path, link in ((root / 'docs/REPOSITORY_MAP.md', '../research_tracking/runs/research-readiness-reconciliation-20261110-01/README.md'),
                   (root / 'research_tracking/reports/README.md', '../runs/research-readiness-reconciliation-20261110-01/README.md')):
    data = path.read_bytes()
    position = data.index(b'\n') + 1
    note = ('\n## 10/11 — sổ khoảng trống và tiến độ đã đối chiếu lại\n\n[Hồ sơ audit](' + link +
        ') xác nhận3PDF chuẩn,14gap hiện hành và cập nhật8parent tasks. Giữ178IDs,11SVG và17tables. Không có kết quả nghiên cứu mới; hai file GVHD đã làm rõ trạng thái chuẩn bị.\n\n').encode('utf-8')
    path.write_bytes(data[:position] + note + data[position:])
with (root / '.gitattributes').open('a', encoding='utf-8') as stream:
    stream.write('\n/research_tracking/runs/research-readiness-reconciliation-20261110-01/** -text -whitespace\n')
print('Closed', bundle.relative_to(root), 'validated links', len(links), 'static QA accepted.')
