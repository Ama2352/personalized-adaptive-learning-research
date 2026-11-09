"""Nối E12 vào bản thảo, không sửa các phần nghiên cứu trước."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
DRAFT = ROOT / 'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'
BUNDLE = ROOT / 'research_tracking/runs/thesis-rq2-e12-uncertainty-20261110-01'
STATISTICS = ROOT / 'research_tracking/runs/rq2-fresh-block-uncertainty-20261110-01'
SUMMARY = PREP / 'rq2-fresh-block-uncertainty01/summary.json'
REVIEW = PREP / 'rq2_fresh_uncertainty_independent01.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


before = DRAFT.read_bytes()
assert sha(before) == 'f271493ef805ca55a2b99e0e95f2cb9346b94ccefa62a9edca9671be0739cb9d'
summary = json.loads(SUMMARY.read_bytes())
assert summary['status'] == 'POSTHOC_EXPLORATORY_NOT_RQ_COMPLETE'
manifest = json.loads((STATISTICS / 'manifest.json').read_bytes())
for name, digest in manifest['outputs_sha256'].items():
    assert sha((STATISTICS / name).read_bytes()) == digest
assert not BUNDLE.exists()
section = '''

## 15. E12 — Bất định giữa các khối và giới hạn của so sánh năng lực

Phần E11 cho thấy trung bình của tương tác nguồn đồ thị với cơ chế phạt có thể khác nhau giữa hai mức khởi tạo. Câu hỏi tiếp theo là sự khác nhau ấy có đủ rõ so với biến động giữa các khối mô phỏng hay không. Đơn vị độc lập tiếp tục là mười khối21010–21019. Các120worlds và14.400tương tác bên trong không được xem là các quan sát độc lập. Ba khối E9 không được gộp vào phép tính mới.

Gọi K(a) là phần thay đổi của chênh lệch expert–learned khi bật cơ chế phạt tại mức khởi tạo a, với định nghĩa Y và Q giữ như E11. Phân tích bổ sung xét ba trung bình gồm K(1000), K(1150) và K(1150)−K(1000) được trừ trong cùng khối. Đại lượng thứ ba trả lời trực tiếp câu hỏi tác động có khác giữa hai mức khởi tạo hay không. Việc hai khoảng riêng lẻ có quan hệ khác nhau với0 chưa tự chứng minh chênh lệch giữa hai tác động.

Nhóm dùng paired-block bootstrap với10.000lần lấy mẫu lại mười khối có hoàn lại, private seed42. Các điều kiện trong cùng khối luôn đi cùng nhau. Ba khoảng percentile loại7 dùng điều chỉnh Bonferroni, mỗi khoảng có mức danh nghĩa98,333333%, tương ứng mức đồng thời danh nghĩa95% của gia đình ba so sánh. Đây là mức xấp xỉ của bootstrap, không bảo đảm bao phủ chính xác với n=10. Các estimands và thuật toán được đóng băng trước phép tính bổ sung, nhưng kết quả mô tả đã được xem trước, nên toàn bộ phân tích mang tính thăm dò sau kết quả.

| Đại lượng | Trung bình, Elo | Khoảng bootstrap đã điều chỉnh, Elo |
|---|---:|---|
'''
labels = ['K(1000)', 'K(1150)', 'K(1150) − K(1000), trong cùng khối']
for label, row in zip(labels, summary['estimates']):
    section += f"| {label} | {row['mean']:+.6f} | {row['percentile_lower']:+.6f} đến {row['percentile_upper']:+.6f} |\n"
section += '''
Khoảng của K(1000) chứa cả giá trị âm và dương. Khoảng của K(1150) nằm phía dương trong phép thăm dò này. Tuy nhiên, khoảng của hiệu K(1150)−K(1000) còn chứa0, nên dữ liệu hiện tại chưa phân biệt rõ tác động giữa hai mức khởi tạo. Kết quả không được diễn giải thành bằng chứng khẳng định đồ thị có ích hơn cho một nhóm năng lực của người học thật.

K(1300)=0 vẫn là đối chứng bất hoạt theo điều kiện của simulator. Nhóm không lập khoảng hoặc kiểm định cho đại lượng này. Đổi nguồn đồ thị vẫn tạo Q khác0 ở mức khởi tạo1300, như E11 đã ghi, nên không được dùng K bằng0 để suy mọi đường tác động của đồ thị đã biến mất.

Độ bất định đã được lượng hóa thêm trên đúng quần thể và giữ các kết quả âm. Tăng số lần bootstrap chỉ giảm nhiễu Monte Carlo, không tạo thêm khối độc lập. Khoảng hiện có chưa bao gồm biến động do nhiều đồ thị học độc lập, nhiều seed huấn luyện, môi trường khác hoặc người học thật. RQ2 còn cần khảo sát đồ thị nhiễu và khả năng khái quát. Phần này chưa đóng RQ2 và chưa là bằng chứng ưu thế của CG-AKT.

Các phép tính đã được kiểm độc lập từ30K và10.000vector đã lưu bằng số thập phân độ chính xác60chữ số. Không lấy mẫu lại hoặc chạy mô phỏng mới trong kiểm này. Sai khác lớn nhất do số thực nhỏ hơn1,14e−16, trong ngưỡng kiểm số1e−12 đã công bố. Ngưỡng này kiểm tái lập số học, không là biên hiệu quả nghiên cứu. Bảng làm tròn sáu chữ số thập phân, JSON giữ độ chính xác đầy đủ.

[Báo cáo kỹ thuật](rq2_fresh_block_uncertainty_20261110.md). [Bằng chứng và giới hạn](../runs/rq2-fresh-block-uncertainty-20261110-01/README.md).
'''
addition = section.encode('utf-8')
after = before + addition
assert after[:len(before)] == before
BUNDLE.mkdir()
inventory = dict(before_sha256=sha(before), before_bytes=len(before),
    source_summary_sha256=sha(SUMMARY.read_bytes()), independent_review_sha256=sha(REVIEW.read_bytes()),
    statistics_manifest_sha256=sha((STATISTICS / 'manifest.json').read_bytes()),
    script_sha256=sha(Path(__file__).read_bytes()))
with (BUNDLE / 'inventory_before_copy.json').open('x') as stream:
    json.dump(inventory, stream, indent=2)
for name, content in [('before.md', before), ('after.md', after)]:
    with (BUNDLE / name).open('xb') as stream:
        stream.write(content)
shutil.copyfile(Path(__file__), BUNDLE / Path(__file__).name)
DRAFT.write_bytes(after)
assert DRAFT.read_bytes()[:len(before)] == before
(BUNDLE / 'README.md').write_text(
    '# E12 nối bất định theo khối vào bản thảo\n\n'
    'Giữ nguyên toàn bộ prefix E1–E11, thêm định nghĩa ba estimands, cách lấy mẫu theo block, '
    'bảng interval và giới hạn hậu nghiệm. Không thêm dữ liệu hoặc modelcalls. '
    'Đã kiểm nguồn và số liệu từ bundle thống kê đã nghiệm thu. Review văn phong độc lập còn chờ, '
    'không suy từ nghiệm thu số học thành nghiệm thu toàn bộ luận văn.\n', encoding='utf-8')
outputs = {path.relative_to(BUNDLE).as_posix(): sha(path.read_bytes()) for path in BUNDLE.iterdir() if path.is_file()}
with (BUNDLE / 'manifest.json').open('x') as stream:
    json.dump(dict(kind='thesis_e12_exploratory_uncertainty_append', outputs_sha256=outputs,
        independent_prose_review_pending=True), stream, indent=2)
print(json.dumps(dict(prefix_bytes=len(before), prefix_preserved=True, after_sha256=sha(after))))
