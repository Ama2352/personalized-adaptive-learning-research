"""Nối E10 từ witness đã đóng, giữ byte prefix và nguồn bằng chứng."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[4]
BUNDLE = ROOT / 'research_tracking/runs/thesis-rq1-e10-writing-20261110-01'
WITNESS = ROOT / 'research_tracking/runs/rq1-observer03-cached-truth-20261109-01'
DRAFT = ROOT / 'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'
REPORT = ROOT / 'research_tracking/reports/rq1_on_policy_mastery_witness_20261109.md'
HUMAN = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def copy_verified(source, target):
    digest = sha(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(target) == digest
    return digest


summary = json.loads((WITNESS / 'cached02_child__summary.json').read_bytes())
crosscheck = json.loads((WITNESS / 'observer03_truth120_independent_crosscheck01.json').read_bytes())
assert summary['queried_concept_time_rows'] == crosscheck['joined_rows'] == 120
assert summary['history_count'] == 1 and summary['new_independent_N'] == 0
assert summary['native_M_by_latent'] == summary['theta_gate_by_latent'] == {'00': 0, '01': 120, '10': 0, '11': 0}
assert summary['uncertainty_suppression_by_latent'] == {'latent_false': 0, 'latent_true': 0}
assert summary['theta_threshold'] == 1250 and summary['stored_pi_threshold'] == .55
assert crosscheck['first_visit_analysis']['observed_concepts'] == 22
assert crosscheck['first_visit_analysis']['latent_positive_first_visits'] == 22
assert all(row['theta_est'] == 1200 and row['already_latent_positive']
           for row in crosscheck['first_visit_analysis']['rows'])

section = '''

## 13. Bổ sung E10 về trạng thái thành thạo tại các câu được chọn

### Vì sao cần đối chiếu quyết định với trạng thái mô phỏng

Paper2 đã đặt dự báo đáp án vào một hệ thống chọn bài. Để giải thích vì sao thay đổi dự báo có thể chưa dẫn đến thay đổi kết quả học, cần biết quyết định thành thạo có phản ánh trạng thái mà simulator đang mô phỏng hay không. Câu hỏi này bổ sung cho việc đo sai số dự báo. Dự báo đáp án và trạng thái thành thạo là hai đại lượng phục vụ hai bước khác nhau của cùng hệ thống.

Nhóm đối chiếu lại một lịch sử PG đã lưu, gồm120 lượt hỏi trước khi cập nhật bằng đáp án hiện tại. Hai đường tín hiệu và điều chỉnh theo cha trong bộ ước lượng được tắt, điều chỉnh cục bộ cũng tắt. Bộ chọn bài vẫn dùng đồ thị tiên quyết. Vì vậy, cấu hình này chỉ tắt các đường đã nêu của bộ ước lượng. Các bản ghi được ghép theo đúng câu hỏi, khái niệm, thời điểm và giá trị dự báo với trạng thái thật đã lưu của simulator. Đây là phân tích dữ liệu cũ, không thêm người học hoặc lượt tương tác mới. [E10a]

### Kết quả đối chiếu và lý do cần đọc cùng cách lấy mẫu

Quy tắc Paper2 xét cả điểm kiến thức ước lượng đạt1250 và chỉ số bất định không vượt0,55. Phép đối chiếu dùng trạng thái latent của simulator tại cùng ngưỡng1250. Trong120 lượt hỏi được quan sát, khái niệm đang hỏi luôn đạt tiêu chí latent, trong khi điểm kiến thức ước lượng luôn dưới ngưỡng. Kết quả gồm120 quan sát trên22 khái niệm riêng biệt của một lịch sử. [E10a]

| Quyết định tại khái niệm được hỏi | Latent chưa đạt | Latent đã đạt |
|---|---:|---:|
| Mô hình chưa công nhận thành thạo | 0 | 120 |
| Mô hình công nhận thành thạo | 0 | 0 |

Điểm kiến thức ước lượng chưa đạt ở cả120 lượt nên điều kiện bất định chưa có cơ hội chặn thêm một trường hợp đã vượt ngưỡng điểm. Quan sát này chưa đo được vai trò tăng thêm của điều kiện bất định khi điểm kiến thức đã đạt. Nó cũng chưa đo ảnh hưởng của bất định đối với dự báo, cập nhật trạng thái hoặc cách xếp hạng ứng viên.

Bảng chỉ gồm những câu do hệ thống quyết định giao. Trong source Paper2, bộ chọn ưu tiên các khái niệm được đánh giá chưa thành thạo và ưu tiên điểm thành thạo thấp trong nhóm ứng viên. Do đó, quần thể được quan sát đã chịu ảnh hưởng của mô hình và chính sách. Bộ chọn còn có nhánh ôn tập cùng nhánh xử lý khi mọi khái niệm đã thành thạo, nên việc toàn bộ120 điểm ước lượng dưới ngưỡng vẫn là kết quả riêng của lịch sử này. Bảng chưa đánh giá trạng thái của toàn bộ28 khái niệm tại cùng những thời điểm. [E10b]

### Năng lực ban đầu giới hạn điều có thể kết luận về học tập

Kiểm lần xuất hiện đầu cho thấy cả22 khái niệm đã được phục vụ đều đạt tiêu chí latent ngay từ lần thực hành đầu tiên, trong khi điểm ước lượng khởi tạo bằng1200. Phân tích phương trình của phiên bản này cho thấy mức tăng latent không âm và forgetting kéo về mức nền ban đầu. Với các khái niệm có mức nền đã vượt ngưỡng, trạng thái tiếp tục nằm trên ngưỡng. Phát hiện về lần xuất hiện đầu là kiểm cơ chế hậu nghiệm trên lịch sử đã chọn. [E10c]

Vì vậy, lịch sử này chưa cung cấp một lần chuyển latent từ chưa đạt sang đạt tại các khái niệm đã được phục vụ. Khác biệt giữa quyết định và latent cần được đọc cùng khởi tạo năng lực cao và cách chọn câu. Sáu khái niệm chưa xuất hiện cần bằng chứng riêng. Không gán kết quả của22 khái niệm này cho mọi hồ sơ PG, mọi seed hoặc toàn bộ28 khái niệm.

### Đóng góp chẩn đoán và phần thực nghiệm còn thiếu

E10 chỉ ra rằng đánh giá quyết định thành thạo cần kiểm soát cách chọn quần thể. Phép đánh giá chỉ lấy các câu hệ thống đang giao dễ tập trung vào những trạng thái mà chính mô hình đang coi là chưa đạt. Điều này có thể che khuất khả năng đánh giá những khái niệm khác và làm khó việc tách tác dụng của từng điều kiện trong quyết định.

Bước tiếp theo được đề xuất là đối chiếu một tập khái niệm và thời điểm định trước, độc lập với câu được chọn, đồng thời giữ cả trạng thái ước lượng và latent tương ứng. Thiết kế đó cần được chốt trong hợp đồng thực nghiệm trước khi dùng làm đánh giá chính. Các phép so sánh đồ thị, hiệu chỉnh xác suất, trạng thái khởi đầu thấp hơn và đánh giá kết quả học trên nhiều người học vẫn còn thiếu. Một lịch sử với120 thời điểm tương quan chưa hoàn tất RQ1 hoặc RQ2 và chưa chứng minh lợi ích của graph.

### Nguồn bổ sung E10

- **E10a** dùng [summary của witness](../runs/rq1-observer03-cached-truth-20261109-01/cached02_child__summary.json), [120 bản ghi đã ghép](../runs/rq1-observer03-cached-truth-20261109-01/cached02_child__joined120.json) và [kiểm độc lập](../runs/rq1-observer03-cached-truth-20261109-01/observer03_truth120_independent_crosscheck01.json).
- **E10b** dùng [review source và cách diễn giải mẫu](../runs/rq1-observer03-cached-truth-20261109-01/OBSERVER03_CACHED120_SELECTION_INTERPRETATION_REVIEW01.md), cùng [báo cáo chuyên đề](rq1_on_policy_mastery_witness_20261109.md).
- **E10c** dùng first_visit_analysis trong kiểm độc lập và phương trình source được truy vết trong review. Phép kiểm đã đọc đủ14.400 hàng cache và CRC trước khi lấy120 hàng. Không cộng120 lượt hỏi vào số mẫu độc lập.

Các mục trước E10 giữ nguyên byte. [Bundle viết E10](../runs/thesis-rq1-e10-writing-20261110-01/README.md) giữ before/after, kiểm các số liệu đã trích và nguồn bằng chứng. Việc viết không thực hiện thêm model/world call hoặc thay thiết kế thực nghiệm.
'''
assert '## 13. Bổ sung E10' not in DRAFT.read_text(encoding='utf-8')
BUNDLE.mkdir(exist_ok=False)
files = [DRAFT, REPORT, HUMAN / 'BAO_CAO.md', HUMAN / 'BAO_CAO_NGHIEN_CUU.html']
before = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in files}
write(BUNDLE / 'inventory_before_copy.json', before)
for file in files:
    copy_verified(file, BUNDLE / 'before' / file.name)
original = DRAFT.read_bytes()
with DRAFT.open('ab') as stream:
    stream.write(section.encode('utf-8'))
assert DRAFT.read_bytes()[:len(original)] == original
old = 'Cả 120 khái niệm đang được hỏi đều đạt tiêu chí latent'
new = 'Trong cả 120 lượt hỏi trên 22 khái niệm riêng biệt, khái niệm đang hỏi đều đạt tiêu chí latent'
for file in files[1:]:
    text = file.read_text(encoding='utf-8')
    assert text.count(old) == 1, file
    previous_svg = re.findall(r'<svg\b.*?</svg>', text, flags=re.S)
    text = text.replace(old, new)
    assert re.findall(r'<svg\b.*?</svg>', text, flags=re.S) == previous_svg
    file.write_text(text, encoding='utf-8')
for file in files:
    copy_verified(file, BUNDLE / 'after' / file.name)
sources = [WITNESS / name for name in ('manifest.json', 'cached02_child__summary.json',
    'cached02_child__joined120.json', 'observer03_truth120_independent_crosscheck01.json',
    'OBSERVER03_CACHED120_SELECTION_INTERPRETATION_REVIEW01.md')]
write(BUNDLE / 'source_map.json', dict(
    inputs_sha256={str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in sources},
    checked_claims=dict(rows=120, histories=1, observed_concepts=22, initial_latent_positive=22,
        first_estimated_theta=1200, theta_threshold=1250, pi_threshold=.55,
        native_matrix=summary['native_M_by_latent'], new_independent_N=0),
    original_prefix_bytes=len(original), original_prefix_preserved=True,
    change='Cách diễn đạt120khái niệm được làm rõ thành120lượt trên22khái niệm, không đổi số liệu.',
))
copy_verified(Path(__file__).resolve(), BUNDLE / Path(__file__).name)
(BUNDLE / 'README.md').write_text(
    '# Viết E10 từ witness thành thạo đã nghiệm thu\n\n'
    'Nối phần13 của bản thảo RQ1 sau E9. Giữ nguyên byte prefix, có before/after và source map đã kiểm. '
    'Làm rõ cách gọi120lượt hỏi trên22khái niệm trong technicalreport và hai fileGVHD. '
    'Không có mẫu mới, không model call, không đổi phương pháp. '
    'Chưa global mastery accuracy, calibration, graph effect hoặc RQ completion.\n', encoding='utf-8')
write(BUNDLE / 'manifest.json', dict(kind='thesis_writing_from_closed_evidence',
    outputs_sha256={str(p.relative_to(BUNDLE)).replace('\\', '/'): sha(p)
        for p in BUNDLE.rglob('*') if p.is_file()}))
print(json.dumps(dict(status='E10_PUBLISHED_PREFIX_PRESERVED', prefix_bytes=len(original),
    human_reports_clarified=True, new_model_calls=0), ensure_ascii=False))
