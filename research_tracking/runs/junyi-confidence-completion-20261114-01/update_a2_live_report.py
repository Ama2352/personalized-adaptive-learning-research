"""Ghi mốc A2 training thật và số đo CPU trước GPU vào báo cáo hiện hành."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
execution='modal-junyi-a2-staged-h100-20261114-09'
output=ROOT/'experiments/akt/results'/execution
provider=json.loads((output/'provider-cpu-preflight.json').read_text())
assert provider['status']=='PASS_STAGED_PROVIDER_INPUTS'
progress=json.loads((HERE/'a2-remote-progress.jsonl').read_text().splitlines()[-1])
assert progress['runtime.json']['cuda_available'] is True
state_path=HERE/'STATE.json'
state=json.loads(state_path.read_text())
state.update(status='A2_MAIN_SELECTED_TRAINING_ON_H100',active_exec_session=48883,
    active_operation='bounded_h100_training_then_stop_and_collect',
    training_request='a2-training-request09.json',training_log='a2-training09.log',
    snapshot='artifacts/akt/staged/junyi-a2-expert-20261114-03',
    gpu_start_confirmed=True,execution_id=execution,
    provider_cpu_preflight_seconds=provider['total_seconds'],
    provider_cpu_hashing_seconds=provider['hashing_seconds'],
    linux_gate=dict(status='PASS',passed=2615,output='experiments/akt/results/modal-junyi-a2-a3-final-cpu-20261114-03'),
    latest_observation='a2-remote-progress.jsonl')
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paragraphs=[
    'A2 đã bắt đầu huấn luyện thật trên Junyi bằng H100. Mô hình dùng cùng TRAIN80 gồm 126.774 người học, 13.347.331 lượt trả lời và tập selection gồm 1.600.343 lượt trả lời như A0/A1. A2 bổ sung trọng số độ tin cậy cho từng cạnh đã ước lượng hoàn toàn từ TRAIN80.',
    'Để hạn chế thời gian thuê GPU, toàn bộ cache và source được đóng vào image bằng CPU trước khi gọi H100. Lượt kiểm provider mới nhất đối chiếu đủ 1.491 file và chạy đúng bước kiểm runtime trong 9,53 giây, trong đó kiểm SHA mất 4,66 giây. GPU đọc input từ file local của container và ghi checkpoint vào Volume riêng.',
    'Trước lượt này đã sửa các lỗi tích hợp mount/image và đường dẫn xuất báo cáo runtime. Source numerical sau sửa đã đạt 2.615 ca kiểm Linux. Các lượt lỗi có log và xác nhận dừng App. Lượt H100 trước bị dừng ở bước runtime sau khoảng 6 giây, chưa học epoch. Bộ kiểm controller local hiện hành đạt 40 ca.',
    'Ở mốc đầu tiên được lưu, epoch 1 đã học 600 bước và khoảng 4,40 triệu lượt trả lời trong 59 giây pha train. VRAM khoảng 5,65 GiB, GPU trung bình đoạn đo gần nhất khoảng 40%. Cần hoàn tất epoch để xác nhận thời gian train và selection đầy đủ. Checkpoint được lưu định kỳ để tiếp tục nếu hết thời hạn lượt chạy.',
    'Phần đang chạy là chọn checkpoint trên TRAIN80/selection của Development outer fold 4. Refit, calibration và đánh giá độc lập còn chờ. Chưa có kết quả đối chứng cuối của A2 để kết luận hiệu quả đồ thị cho RQ3.'
]
report=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
md=report/'BAO_CAO.md'
raw=md.read_bytes()
start=raw.index('## 14/11 — A2 đã đạt kiểm snapshot'.encode())
end=raw.index('## 14/11 — Hoàn tất confidence'.encode(),start)
section='## 14/11 — A2 đã bắt đầu huấn luyện thật trên Junyi\n\n'+'\n\n'.join(paragraphs)+'\n\n'
md.write_bytes(raw[:start]+section.encode()+raw[end:])
html=report/'BAO_CAO_NGHIEN_CUU.html'
raw=html.read_bytes()
start=raw.index(b'<section id="cap-nhat-20261114-a2-dispatch">')
end=raw.index(b'<section id="cap-nhat-20261114-confidence-completion">',start)
section='<section id="cap-nhat-20261114-a2-dispatch"><h2>14/11 — A2 đã bắt đầu huấn luyện thật trên Junyi</h2>'+''.join('<p>'+p+'</p>' for p in paragraphs)+'</section>\n'
html.write_bytes(raw[:start]+section.encode()+raw[end:])
with (HERE/'README.md').open('a',encoding='utf-8') as stream:
    stream.write('\n## A2 đã bắt đầu training thật\n\nSource03 sửa đường dẫn runtime đạt Gate Linux 2.615 ca. Snapshot03 giữ cùng worker request, confidence, data và numeric profile, qua nghiệm thu CPU và checkout. Lượt09 CPU provider đạt 9,5268 giây, gồm 4,6607 giây SHA. Đã xác nhận CUDA và 600 bước epoch1 bằng telemetry, xem `a2-remote-progress.jsonl`. Một H100 với cap2,60USD; chờ kết thúc, stop acknowledgement và thu đủ artifact trước khi đóng lượt.\n')
print('Đã cập nhật báo cáo và trạng thái A2 training thật.')
