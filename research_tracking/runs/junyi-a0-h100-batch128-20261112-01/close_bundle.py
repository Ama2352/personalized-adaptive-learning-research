"""Đóng hồ sơ H100 bằng inventory SHA-256, giữ nguyên checkpoint gốc."""
import ast
import hashlib
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
manifest = BUNDLE/'FINAL_MANIFEST.json'
assert not manifest.exists(), 'Bundle đã đóng, không ghi đè.'
for script in BUNDLE.glob('*.py'):
    ast.parse(script.read_text(encoding='utf-8-sig'))
qa = json.loads((BUNDLE/'report-check.json').read_text())
assert qa['status'] == 'PASS_STATIC_DATA_AND_RENDER'
with (BUNDLE/'README.md').open('a', encoding='utf-8') as stream:
    stream.write('\n\n## Kiểm báo cáo và đóng bundle\n\n'
        'Đã kiểm tự động số liệu, model SHA, số dự báo, 12 epoch, App stopped và bố cục ngữ cảnh trước cập nhật. '
        'Đã xem figure cuối cùng, screenshot desktop 1440px và khung hẹp 600px. Chrome kiểm thử đã kết thúc, không tạo preview server. '
        'Lượt Chrome đầu trong môi trường hạn chế lỗi Crashpad; chạy lại với quyền mở Chrome cục bộ thành công. '
        'Screenshot 390px bị giới hạn viewport tối thiểu của Chrome headless nên không dùng làm kiểm mobile đạt, ảnh gốc vẫn giữ. '
        'Không xác nhận kiểm thiết bị di động thực. report-check.json ghi hai viewport đã nghiệm thu. '
        'Các script Python trong bundle đã parse cú pháp. Không chạy thêm training hoặc đọc Holdout.\n\n'
        'Bundle đóng sau FINAL_MANIFEST.json. Mọi cập nhật tiếp theo dùng bundle mới và tham chiếu hồ sơ này, không sửa bằng chứng đã đóng.\n')
state_path = BUNDLE/'INVOCATION_STATE.json'
state = json.loads(state_path.read_text())
state['bundle_closed'] = True
state['status'] = 'CLOSED_VERIFIED_SELECTED_EXPORTED_REPORT_COMPLETE'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def identify(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''):
            digest.update(chunk)
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                sha256=digest.hexdigest())

files = [identify(p) for p in sorted(BUNDLE.rglob('*')) if p.is_file()]
external_paths = [
    ROOT/'research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html',
    ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do/BAO_CAO.md',
    ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html',
    ROOT/'research_tracking/COMPUTE_BUDGET.json',
]
external_paths.extend(sorted((ROOT/'experiments/akt/results/model-export-a0-batch128-20261112-01').glob('*')))
for sequence in ('01', '02', '03'):
    directory = ROOT/f'experiments/akt/results/modal-junyi-a0-b128-h100-20261112-{sequence}'
    external_paths.extend(sorted(directory.glob('*.zip')))
document = dict(status='CLOSED', date='2026-11-13',
    note_vi='SHA file trong bundle cố định. Các báo cáo/chỉ mục bên ngoài là snapshot tại lúc đóng, có thể được cập nhật hợp lệ sau này. Manifest không tự băm chính nó.',
    inputs_outputs=files, external_snapshots=[identify(p) for p in external_paths if p.is_file()])
manifest.write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(status='CLOSED', bundle_files=len(files), external_files=len(document['external_snapshots']))))
