"""Cập nhật diễn tiến A0 validation và A1 từ evidence thực của đợt mở."""
import hashlib
import base64
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
run = 'modal-junyi-a1-b128-h100-20261113-05'
native = ROOT/'experiments/akt/results'/run
receipt_path = native/'receipt.json'
stopped_epoch = BUNDLE/'archive-verification05.json'
proof = None
monitor = BUNDLE/'monitor05.jsonl'
if monitor.exists():
    for line in monitor.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        if row.get('training', {}).get('training', {}).get('parameter_update_steps', 0):
            proof = row['training']['training']
if receipt_path.exists():
    receipt = json.loads(receipt_path.read_text())
    status = receipt['status']
else:
    status = 'TRAINING_CONFIRMED_PARTIAL_EPOCH' if proof else 'DISPATCHED_AWAITING_TRAINING_CONFIRMATION'
if stopped_epoch.exists():
    status = 'STOPPED_TRAIN_EPOCH1_COMPLETE_VALIDATION_PENDING_GPU_UTILIZATION_BLOCKED'
    proof = json.loads((BUNDLE/'epoch1-training-stats05.json').read_text())
training = ('Bản A1 cũ đã học 1.000 bước/7.365.262 target, checkpoint cùng optimizer/RNG/sampler đã lưu trên D và H100 đã dừng. Bản tối ưu đạt 2.336 ca Linux và đối chiếu H100 trên fixture, đã mở lượt mới từ seed42 với cùng cấu hình. Chưa có bằng chứng chọn lại epoch A0 trên đủ12checkpoint. Đã chuẩn bị A1 đồ thị cố định với batch128 cho train và validation, cùng split, backbone, '
    'seed và quy tắc chọn epoch của A0. Linux CPU Gate đạt 2.328 ca. Các lỗi launcher và gọi entrypoint '
    'được giữ log và đã sửa. Yêu cầu H100 hiện đã dispatch, chưa xác nhận bước học A1 thực tế. '
    'Trần đợt H100 3 USD trong tổng 30 USD toàn KLTN, checkpoint có sync bền vững và watchdog dừng GPU.')
if status not in ('DISPATCHED_AWAITING_TRAINING_CONFIRMATION',):
    training += ' Trạng thái receipt mới nhất là ' + status + '.'
if proof:
    training = ('A1 đã bắt đầu training thật trên H100 với batch128 cho cả train và validation. '
        f"Bằng chứng tiến độ gần nhất ghi {proof['optimizer_steps']} bước optimizer, "
        f"{proof['valid_targets']:,} target đã học và {proof['parameter_update_steps']} bước cập nhật trọng số. "
        'Chưa hoàn tất epoch hoặc có kết quả validation A1. Tốc độ đang chậm hơn A0, '
        'cần kiểm chi phí xử lý đồ thị. Giữ checkpoint/resume và trần H100 3 USD của đợt này. '
        'Bản cũ đã lưu checkpoint1000 riêng. Lượt bản tối ưu khởi tạo lại seed42, source đã qua 2.336 ca Linux và đối chiếu H100 fixture; chưa nghiệm thu toàn trajectory. Các lỗi thiết lập trước được giữ log.')
if stopped_epoch.exists():
    training = ('A1 bản tối ưu đã hoàn tất phần training epoch 1 trên toàn bộ13.347.331target,1.818bước optimizer, '
        'mất22phút24giây. Checkpoint trước validation cùng optimizer, RNG và trạng thái sampler đã tải về D, kiểm toàn vẹn. '
        'Validation bị ngắt khi dừng H100, chưa có kết quả lựa chọn epoch hoặc dự báo A1 để kết luận so sánh mô hình. '
        'Đã phục hồi archive đầy đủ ba checkpoint và logs. H100 đã dừng, server xác nhận0container. '
        'Số đo trong giai đoạn training ghi GPU trung bình4,98%, VRAM cao nhất5.789/81.559MiB, tiến trình chiếm gần một lõi CPU. '
        'Mức sử dụng này chưa đạt mục tiêu ít nhất50% do người dùng đặt. Cache mới chưa triển khai; việc sửa pipeline CPU/graph và kiểm lại hiệu năng là bước tiếp theo.')
report = ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
technical = ('Bản tối ưu đã kiểm trên H100 với dữ liệu tổng hợp. Loss, xác suất và tham số sau một bước Adam khớp bản cũ trong hai điều kiện đã kiểm; sai lệch gradient lớn nhất khoảng6,52×10⁻⁹. '
    'Phép kiểm kéo dài9,02giây, chưa chứng minh cả quỹ đạo training giống từng bit. '
    'Trên Junyi thật,500bước đầu bản mới mất khoảng6phút07giây, bản cũ khoảng10phút03giây trên cùng số target. '
    'Còn chờ nghiệm thu epoch đầy đủ. Checkpoint bản cũ đã được giữ; lượt chính mới bắt đầu lại từ cùng seed42 theo quyết định vận hành của agent.')
technical_md = '\n\n'+technical+'\n\n![Đối chiếu phần xử lý A1 trên H100](../../../runs/junyi-a1-selected-20261113-01/a1-vector-h100-v1.svg)\n'
path = report/'BAO_CAO.md'
text = path.read_text(encoding='utf-8')
heading = '13/11 — kiểm checkpoint A0 trên H100 và triển khai A1'
section = '\n## '+heading+'\n\n'+paragraph+'\n\n'+training+technical_md
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
figure = base64.b64encode((BUNDLE/'a1-vector-h100-v1.png').read_bytes()).decode()
section = '<section id="junyi-a1-training-20261113"><h2>'+heading+'</h2><p>'+paragraph+'</p><p>'+training+'</p><p>'+technical+'</p><figure><img style="width:100%;height:auto" alt="Đối chiếu A1 scalar và vector trên H100 bằng dữ liệu tổng hợp" src="data:image/png;base64,'+figure+'"></figure></section>\n'
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
    controller_session_id=None, app_id=json.loads((native/'dispatch.json').read_text())['app_id'],
    previous_partial_checkpoint='checkpoint1000-inspection.json',previous_run_stopped=True,
    initialization='seed42_fresh_vector_implementation',
    latest_training_proof=proof,
    cpu_gate_tests=2328, a0_selected_checkpoint_cuda_batch128_verified=True,
    a0_log_loss_delta=0, a0_epoch_choice_replayed=False,
    validation_implementation='batched_windows_v1_batch128',
    tranche_cap_usd=3, project_cap_usd=30,
    train_epoch1_complete=stopped_epoch.exists(),validation_complete=False,
    all_owned_apps_stopped=stopped_epoch.exists(), gpu_utilization_goal_percent=50,
    observed_training_gpu_utilization_percent=4.9809688581314875,
    cached_graph_pipeline_implemented=False,
    next_vi='Giữ source2/checkpoint train-epoch-001, resume validation trước khi train thêm. Thiết kế cache/fast path đồ thị, đối chiếu causal/output/gradient và checkpoint compatibility trên CPU. GPU hiện đã tắt, chỉ cấp bounded run tiếp sau khi xử lý CPU bottleneck và dự toán trong30USD.')
path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name, link in [('docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-a1-selected-20261113-01/README.md'),
                   ('research_tracking/reports/README.md','../runs/junyi-a1-selected-20261113-01/README.md')]:
    path = ROOT/name
    text = path.read_text(encoding='utf-8')
    title = '\n## 13/11 — A1 H100 và validation A0 thực\n'
    current = ('A1 đã train đủ epoch1, validation còn chờ; checkpoint/logs đã lưu D, H100 dừng. GPU training trung bình4,98%, cần xử lý nút thắt CPU trước chạy tiếp.' if stopped_epoch.exists() else ('A1 đã cập nhật trọng số trên H100, epoch còn đang chạy.' if proof else 'A1 batch128 đã dispatch, chưa xác nhận học.'))
    body = title+'\n[Hồ sơ]('+link+') có Gate Linux 2.336 ca, A0 checkpoint9 full-selection batch128 đạt Log Loss bằng giá trị cũ; '+current+'\n'
    if title in text:
        text = re.sub(re.escape(title)+r'.*?(?=\n## |\Z)',lambda _:body,text,count=1,flags=re.S)
    else:
        position = text.index('\n')
        text = text[:position]+'\n'+body+text[position:]
    path.write_text(text,encoding='utf-8')
print(json.dumps(dict(a0_cuda_checkpoint9='PASS_FULL_SELECTION',a1=status),ensure_ascii=False))
