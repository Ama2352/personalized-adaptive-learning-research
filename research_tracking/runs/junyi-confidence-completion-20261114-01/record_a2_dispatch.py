"""Lưu mốc nghiệm thu snapshot và bắt đầu lượt training A2 có giới hạn."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
state_path = HERE / 'STATE.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
state.update(status='A2_SNAPSHOT_VERIFIED_TRAINING_DISPATCH_REQUESTED',
    active_operation='upload_snapshot_then_bounded_h100_training', active_exec_session=94692,
    graph_caches_complete=True, snapshot_dependency_verified=True,
    snapshot='artifacts/akt/staged/junyi-a2-expert-20261114-02',
    training_request='a2-training-request01.json', training_log='a2-training01.log',
    gpu_start_confirmed=False,
    next_steps=['Theo dõi upload và dispatch thực tế, xác minh GPU đã chạy qua dispatch/telemetry',
                'Khi dừng, xác nhận stop barrier và tải/kiểm mọi checkpoint/artifact trên D',
                'Đọc tiến độ epoch, đối soát ngân sách và tiếp tục từ checkpoint nếu cần',
                'Cập nhật báo cáo theo kết quả thực tế và commit gói hoàn thiện'])
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
note = '''\n## Nghiệm thu snapshot A2 và bắt đầu lượt chạy có giới hạn\n\nBốn cache CPU thật đã hoàn tất, gồm 13.347.331 target train và 1.600.343 target selection cho mỗi biến thể. Snapshot A2 phiên bản02 đã kiểm đủ 1.491 file, đúng checkout AKT upstream và inventory giữ nguyên sau kiểm Git. Lượt01 giữ bằng chứng lỗi thiếu thư mục Git refs trong gói file-only. Lượt02 bổ sung một ref công khai trỏ đúng commit đã ghim.\n\n`a2-snapshot-dependency-verification02.json` giữ nghiệm thu. `a2-training-request01.json` dành tối đa 2,60 USD cho một H100, watchdog 1.860 giây, tối đa một container và không retry tự động. Ledger giữ cận tổng dự kiến 25,8794 USD gồm dự phòng 3 USD. Runner đọc billing thật trước cấp GPU. Đã gọi entrypoint upload rồi training, chưa xác nhận GPU bắt đầu tại mốc ghi này. Log ở `a2-training01.log`, output dự kiến `experiments/akt/results/modal-junyi-a2-staged-h100-20261114-01/`.\n'''
with (HERE / 'README.md').open('a', encoding='utf-8') as stream:
    stream.write(note)
paragraph = ('Đã hoàn tất cả bốn cache ngữ cảnh đồ thị cho A2/A3 trên toàn bộ tập train và selection. '
    'Snapshot A2 đã qua kiểm dữ liệu, 27 trường cấu hình học so với A0/A1, toàn bộ 1.491 file và checkout AKT. '
    'Lỗi đóng gói dependency được phát hiện và sửa trong bước local. '
    'Đã gọi quy trình tải input rồi training A2 trên H100 với mức dự phòng tối đa 2,60 USD và giới hạn thời gian. '
    'Trạng thái hiện tại đang chờ xác nhận GPU bắt đầu. Kết quả epoch và checkpoint sẽ được bổ sung sau khi có output thực tế.')
report = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
md = report / 'BAO_CAO.md'
text = md.read_text(encoding='utf-8')
heading, rest = text.split('\n', 1)
md.write_text(heading + '\n\n## 14/11 — A2 đã đạt kiểm snapshot, chuyển sang lượt training có giới hạn\n\n' + paragraph + '\n\n' + rest.lstrip('\n'), encoding='utf-8')
html = report / 'BAO_CAO_NGHIEN_CUU.html'
text = html.read_text(encoding='utf-8')
marker = '<section id="cap-nhat-20261114-confidence-completion">'
assert text.count(marker) == 1
section = '<section id="cap-nhat-20261114-a2-dispatch"><h2>14/11 — A2 đã đạt kiểm snapshot, chuyển sang lượt training có giới hạn</h2><p>' + paragraph + '</p></section>\n'
html.write_text(text.replace(marker, section + marker, 1), encoding='utf-8')
print('Đã lưu mốc nghiệm thu A2 và cập nhật hai báo cáo.')
