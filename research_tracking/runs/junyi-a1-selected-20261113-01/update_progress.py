"""Cập nhật diễn tiến A0 validation và A1 từ evidence thực của đợt mở."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
replay = json.loads((BUNDLE/'a0-validation-replay03.json').read_text())
assert replay['status'] == 'PASS_SELECTED_A0_CHECKPOINT_BATCH128'
assert replay['results'][0]['absolute_log_loss_delta'] == 0
paragraph = (
    'Sau phép kiểm CPU, đã đối chiếu checkpoint A0 epoch 9 thật trên H100 bằng validation batch128. '
    'Toàn bộ 1.600.343 target selection khớp dữ liệu và thứ tự lịch sử, 0 OOV. Log Loss bằng giá trị '
    'validation cũ 0,3535801768 trong độ chính xác đã lưu. Lượt dự đoán mất 25,11 giây, trọng số giữ nguyên. '
    'Checkpoint này vốn được train bằng batch128. Chưa kiểm lại cách chọn epoch trên đủ 12 checkpoint. '
    'Kết quả mới xác nhận validation batch128 cho checkpoint được chọn trên selection thật.'
)
run = 'modal-junyi-a1-b128-h100-20261113-04'
native = ROOT/'experiments/akt/results'/run
receipt_path = native/'receipt.json'
if receipt_path.exists():
    receipt = json.loads(receipt_path.read_text())
    status = receipt['status']
else:
    status = 'DISPATCHED_AWAITING_TRAINING_CONFIRMATION'
training = ('Đã chuẩn bị A1 đồ thị cố định với batch128 cho train và validation, cùng split, backbone, '
    'seed và quy tắc chọn epoch của A0. Linux CPU Gate đạt 2.328 ca. Các lỗi launcher và gọi entrypoint '
    'được giữ log và đã sửa. Yêu cầu H100 hiện đã dispatch, chưa xác nhận bước học A1 thực tế. '
    'Trần đợt H100 3 USD trong tổng 30 USD toàn KLTN, checkpoint có sync bền vững và watchdog dừng GPU.')
if status not in ('DISPATCHED_AWAITING_TRAINING_CONFIRMATION',):
    training += ' Trạng thái receipt mới nhất là ' + status + '.'
report = ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
path = report/'BAO_CAO.md'
text = path.read_text(encoding='utf-8')
heading = '13/11 — kiểm checkpoint A0 trên H100 và triển khai A1'
section = '\n## '+heading+'\n\n'+paragraph+'\n\n'+training+'\n'
pattern = r'\n## '+re.escape(heading)+r'\n.*?(?=\n## |\Z)'
if re.search(pattern,text,re.S):
    text = re.sub(pattern,lambda _:section,text,count=1,flags=re.S)
else:
    anchor = '\n## 13/11 — chuẩn bị tối ưu validation'
    assert anchor in text
    text = text.replace(anchor,section+anchor,1)
path.write_text(text,encoding='utf-8')
path = report/'BAO_CAO_NGHIEN_CUU.html'
text = path.read_text(encoding='utf-8')
section = '<section id="junyi-a1-training-20261113"><h2>'+heading+'</h2><p>'+paragraph+'</p><p>'+training+'</p></section>\n'
pattern = r'<section id="junyi-a1-training-20261113">.*?</section>\n?'
if re.search(pattern,text,re.S):
    text = re.sub(pattern,lambda _:section,text,count=1,flags=re.S)
else:
    anchor = '<section id="junyi-validation-batch-20261113">'
    assert anchor in text
    text = text.replace(anchor,section+anchor,1)
path.write_text(text,encoding='utf-8')
path = ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(path.read_text(encoding='utf-8-sig'))
state['junyi_a1_selected_20261113'] = dict(status=status,
    evidence=BUNDLE.relative_to(ROOT).as_posix(), active_run=run,
    controller_session_id=6983, app_id='ap-FRKGoDvxn2ACYocsKlhinp',
    cpu_gate_tests=2328, a0_selected_checkpoint_cuda_batch128_verified=True,
    a0_log_loss_delta=0, a0_epoch_choice_replayed=False,
    validation_implementation='batched_windows_v1_batch128',
    tranche_cap_usd=3, project_cap_usd=30,
    next_vi='Đọc receipt/guard/monitor của run04, theo dõi đến checkpoint và dừng App, kiểm archive và đối soát tổng chi trước lượt mới. Không coi dispatch là training.')
path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name, link in [('docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-a1-selected-20261113-01/README.md'),
                   ('research_tracking/reports/README.md','../runs/junyi-a1-selected-20261113-01/README.md')]:
    path = ROOT/name
    text = path.read_text(encoding='utf-8')
    title = '\n## 13/11 — A1 H100 và validation A0 thực\n'
    body = title+'\n[Hồ sơ]('+link+') có Gate Linux 2.328 ca, A0 checkpoint9 full-selection batch128 đạt Log Loss bằng giá trị cũ; A1 batch128 đã dispatch, chưa xác nhận học.\n'
    if title in text:
        text = re.sub(re.escape(title)+r'.*?(?=\n## |\Z)',lambda _:body,text,count=1,flags=re.S)
    else:
        position = text.index('\n')
        text = text[:position]+'\n'+body+text[position:]
    path.write_text(text,encoding='utf-8')
print(json.dumps(dict(a0_cuda_checkpoint9='PASS_FULL_SELECTION',a1=status),ensure_ascii=False))
