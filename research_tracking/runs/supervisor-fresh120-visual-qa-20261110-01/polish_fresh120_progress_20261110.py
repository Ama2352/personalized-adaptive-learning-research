"""Đồng bộ đoạn tiến độ đầu báo cáo với nghiệm thu CPU mới nhất."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
HUMAN = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
old = 'Bước tiếp theo là kiểm mô hình và checkpoint thật theo nguồn mới, rồi kiểm CUDA.'
new = ('Kiểm checkpoint thật theo nguồn hiện hành cũng đã đạt 18/18 ca. '
       'Các bước còn lại gồm kiểm đầy đủ khả năng tiếp tục ở cấp pipeline và kiểm CUDA.')
progress = ('Mốc cập nhật ngày 10/11, phép đối chứng nguồn đồ thị đã hoàn tất 120 ca trên mười khối mô phỏng mới. '
    'Kết quả cho thấy phần thay đổi do bật cơ chế phạt còn đổi dấu giữa các khối ở mức khởi tạo thấp và trung bình. '
    'Đối chứng năng lực cao tiếp tục tách được tác động ngoài riêng cơ chế phạt. '
    'Đây là bằng chứng chẩn đoán mới, chưa là kết luận mô hình nào tốt hơn một cách ổn định.')
md = HUMAN / 'BAO_CAO.md'
text = md.read_text(encoding='utf-8')
assert text.count(old) == 1
text = text.replace(old,new)
text = text.replace('## Quá trình đã thực hiện','**'+progress+'**\n\n## Quá trình đã thực hiện',1)
md.write_text(text,encoding='utf-8')
html = HUMAN / 'BAO_CAO_NGHIEN_CUU.html'
text = html.read_text(encoding='utf-8')
assert text.count(old) == 1
text = text.replace(old,new)
text,count = re.subn(r'(<section id="tien-do"[^>]*>.*?</h2>)',
    lambda match:match.group(1)+'<div class="finding"><p>'+progress+'</p></div>',text,count=1,flags=re.S)
assert count == 1
html.write_text(text,encoding='utf-8')
print('CURRENT_PROGRESS_AND_STALE_CHECKPOINT_WORDING_UPDATED')
