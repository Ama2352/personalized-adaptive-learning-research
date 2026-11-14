"""Lưu các lỗi triển khai đã dừng và trạng thái chuẩn bị image cho A2."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
files={}
for pattern in ('a2-training-request*.json','a2-mount-failure-settlement*.json',
                'staged-mount-regression*.log','a2-training0[1-7]*.log'):
    for path in HERE.glob(pattern):
        files[path.relative_to(ROOT).as_posix()]=dict(bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
for name in ('experiments/akt/modal_junyi_staged.py','tests/akt/test_junyi_staged_local.py'):
    path=ROOT/name
    files[name]=dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
receipt=dict(status='PROVIDER_PREPARATION_FAILURES_PRESERVED',files=files,
    numerical_snapshot_unchanged=True,
    note_vi='Lượt01–07 giữ lỗi cấu hình mount/image và kiểm CPU. Đọc stop acknowledgement theo từng output, chưa có epoch A2. Các cận chi là dự phòng, chi riêng thực tế chưa tách được.')
with (HERE/'provider-preparation-manifest01.json').open('x',encoding='utf-8') as stream:
    json.dump(receipt,stream,ensure_ascii=False,indent=2)
state_path=HERE/'STATE.json'
state=json.loads(state_path.read_text())
state.update(status='BUILDING_A2_LOCAL_INPUT_IMAGE_ON_MODAL_CPU',active_exec_session=35136,
    training_request='a2-training-request08.json',training_log='a2-training08.log',
    gpu_start_confirmed=False,input_transport='frozen-image-built-on-cpu',
    active_operation='image_build_then_cpu_byte_preflight_then_h100',
    current_controller='experiments/akt/modal_junyi_staged.py')
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
note='''\n## Điều chỉnh triển khai Modal trước epoch đầu\n\nLượt01 bị SDK chặn vì một Volume gắn nhiều mount. Lượt02 bị chặn do copy layer sau local runtime mount. Lượt03 không mount được vào thư mục artifacts còn file. Lượt04/05 giữ lỗi dựng image CPU do rename trên overlay và cú pháp multiline của run_commands. Lượt06 kiểm CPU bắt thiếu configs trong source image. Lượt07 kiểm toàn SHA trên Volume quá180giây, H100 chưa được gọi. Mọi App cũ đã có xác nhận dừng. Các lượt02–07 giữ settlement riêng trong ledger; số tiền đóng là cận bảo thủ, chưa phải chi thực tế.\n\nĐường thực thi sửa dùng một image chứa toàn bộ snapshot, dựng trên CPU, rồi kiểm đủ1.491file và dependency trên CPU provider trước gọi H100. GPU đọc cache từ image local, chỉ gắn Volume output. Source numerical, dữ liệu, confidence, cấu hình học và Gate trong snapshot giữ nguyên byte. Controller local sửa riêng, các kiểm hợp đồng mới nhất đạt39ca. `provider-preparation-manifest01.json` ghim source controller, tests và các log đã kết thúc. Lượt08 đang chuẩn bị image, chưa có kết quả epoch tại mốc này.\n'''
with (HERE/'README.md').open('a',encoding='utf-8') as stream:
    stream.write(note)
print('Đã lưu lịch sử lỗi provider và điểm tiếp tục A2.')
