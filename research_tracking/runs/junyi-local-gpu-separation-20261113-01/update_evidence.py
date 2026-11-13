"""Ghi chỉ mục nghiệm thu local và nối cập nhật vào báo cáo hiện hành."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
if (BUNDLE / 'MANIFEST.json').exists():
    raise SystemExit('Gói đã đóng, dùng run mới để ghi nghiệm thu tiếp theo.')


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def insert_once(path, marker, content):
    raw = path.read_bytes()
    block = content.encode('utf-8')
    if block not in raw:
        assert raw.count(marker) == 1
        path.write_bytes(raw.replace(marker, marker + block, 1))


sources = [
    'experiments/akt/junyi_staged_io.py',
    'experiments/akt/modal_junyi_staged.py',
    'scripts/akt/prepare_junyi_gpu_stage.py',
    'scripts/akt/run_junyi_gpu_stage.py',
    'scripts/akt/build_colab_bundle.py',
    'tests/akt/test_junyi_staged_local.py',
    'tests/akt/test_colab_bundle.py',
]
for name in sources:
    ast.parse((ROOT / name).read_text(encoding='utf-8'))
checks = []
for args in [
    ['scripts/akt/prepare_junyi_gpu_stage.py', '--help'],
    ['experiments/akt/modal_junyi_staged.py', '--snapshot', 'artifacts/akt/modal/not-prepared',
     '--request', 'artifacts/akt/modal/not-approved.json'],
]:
    result = subprocess.run([sys.executable, '-B', *args], cwd=ROOT,
                            capture_output=True, text=True, timeout=30, check=True)
    checks.append(dict(args=args, exit_code=result.returncode, stdout=result.stdout))
assert json.loads(checks[-1]['stdout'])['status'] == 'NO_CLOUD_ACTION'
write_json(BUNDLE / 'entrypoint-checks.json', dict(status='PASS_LOCAL_ENTRYPOINTS', checks=checks,
                                                parsed_sources=sources, modal_spent_usd=0))
state = dict(status='LOCAL_STAGED_IMPLEMENTATION_VERIFIED_PLATFORM_PENDING',
             updated_at='2026-11-14', tests_passed=71, tests_log='tests10.log',
             modal_spent_usd=0, gpu_started=False, training_started=False,
             actual_baseline_audit='actual-baseline-audit.json',
             next=['fit_real_train80_confidence_cpu_with_spool_resume',
                   'fresh_source_and_linux_gate', 'bounded_cuda_parity_resume',
                   'reserve_budget_for_fit_refit_evaluation_before_training'])
write_json(BUNDLE / 'STATE.json', state)

old = ROOT / 'research_tracking/runs/junyi-a2-a3-preparation-20261113-01'
old_state = json.loads((old / 'STATE.json').read_text(encoding='utf-8'))
for task in old_state['tasks']:
    if task['id'] == 'A24':
        task['status'] = 'IMPLEMENTED_LOCAL_VERIFIED_PLATFORM_PENDING'
        task['evidence'] = str(BUNDLE.relative_to(ROOT)).replace('\\', '/') + '/README.md'
old_state['next'][1] = 'validate_staged_pipeline_on_linux_cuda_after_real_confidence'
write_json(old / 'STATE.json', old_state)
addition = ('\n\n## Tiếp nối 14/11 — controller staged đã có kiểm local\n\n'
            'A24 đã triển khai CPU local chuẩn bị/upload → function GPU → xác nhận dừng → '
            'CPU local download/nén. 71 ca local đạt, gồm lỗi và checkpoint recovery bằng Modal giả lập. '
            'Chưa kiểm cloud/CUDA thật, chưa fit confidence thật và chưa training A2/A3. '
            '[Hồ sơ tiếp nối](../junyi-local-gpu-separation-20261113-01/README.md). '
            'Kế hoạch ba CPU/GPU App ở trên được thay bằng CPU local ở hai đầu theo yêu cầu mới.\n')
if addition.encode('utf-8') not in (old / 'README.md').read_bytes():
    with (old / 'README.md').open('ab') as stream:
        stream.write(addition.encode('utf-8'))

report = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
md = '''
## 14/11 — Chuẩn bị A2/A3 với chi phí GPU được tách khỏi xử lý ngoài training

Sau khi A0 và A1 đã hoàn tất bước chọn checkpoint Junyi, bước tiếp theo là A2 dùng độ tin cậy từng cạnh và A3 có thêm cổng điều chỉnh ảnh hưởng đồ thị. Trước khi thuê GPU tiếp, đã triển khai luồng CPU local chuẩn bị dữ liệu và upload, function GPU chạy học và validation, sau đó CPU local nhận và đóng gói kết quả khi GPU đã dừng.

Đã đối chiếu 27 trường cấu hình học, cấu hình số học và định danh dữ liệu với model A0/A1 đã lưu. Bộ kiểm local đạt 71 ca, bao gồm gián đoạn, checkpoint và tải artifact sai byte. Chưa dùng thêm credit trong đợt này. Đây là tiến bộ về độ sẵn sàng thực thi RQ3, chưa bổ sung kết quả thực nghiệm để kết luận đồ thị có ích.

Trước training A2/A3 còn phải fit confidence từ TRAIN80, nghiệm thu source mới trên Linux và kiểm ngắn CUDA/resume. A0 lịch sử chọn epoch bằng validation batch 1, chỉ epoch 9 đã được replay batch 128, nên vẫn giữ giới hạn khi diễn giải so sánh. Đọc batch và lưu checkpoint vẫn cần thời gian trong function GPU. Chưa đo mức tiết kiệm thực tế của luồng mới.

'''
md_path = report / 'BAO_CAO.md'
raw = md_path.read_bytes()
if md.encode('utf-8') not in raw:
    first_line = raw.index(b'\n') + 1
    md_path.write_bytes(raw[:first_line] + md.encode('utf-8') + raw[first_line:])
html = '''
<section id="cap-nhat-20261114-staged">
<h2>14/11 — Chuẩn bị A2/A3 trước lượt thuê GPU tiếp theo</h2>
<p>Sau khi A0 và A1 hoàn tất bước chọn checkpoint Junyi, đã triển khai luồng CPU local chuẩn bị và upload dữ liệu, function GPU chạy học và validation, rồi CPU local nhận và đóng gói kết quả sau khi GPU dừng. A2 bổ sung độ tin cậy từng cạnh. A3 thêm cổng điều chỉnh ảnh hưởng đồ thị.</p>
<p><strong>Đã đạt</strong> đối chiếu 27 trường cấu hình học, cấu hình số học và định danh dữ liệu với model A0/A1 đã lưu. 71 ca kiểm local đạt, gồm gián đoạn, checkpoint và toàn vẹn artifact. Đợt này dùng 0 USD Modal.</p>
<p><strong>Còn thiếu</strong> fit confidence từ TRAIN80, Gate Linux mới và kiểm ngắn CUDA/resume trước training A2/A3. Những ca đạt hiện tại dùng Modal giả lập. Đây là tiến bộ chuẩn bị RQ3, chưa bổ sung bằng chứng về lợi ích đồ thị. A0 chỉ có checkpoint epoch 9 được replay validation batch 128, ranking toàn 12 epoch còn chưa đối chiếu. Đọc batch và lưu checkpoint vẫn nằm trong function GPU. Mức tiết kiệm thực tế của luồng mới chưa được đo.</p>
</section>
'''
insert_once(report / 'BAO_CAO_NGHIEN_CUU.html', b'</header>', html)
html_path = report / 'BAO_CAO_NGHIEN_CUU.html'
raw = html_path.read_bytes()
raw = raw.replace('cập nhật 13/11/2026'.encode(), 'cập nhật 14/11/2026'.encode(), 1)
html_path.write_bytes(raw)
for name, marker, link in [
    ('docs/REPOSITORY_MAP.md', b'# ', '../research_tracking/runs/'),
    ('research_tracking/reports/README.md', b'# ', '../runs/'),
]:
    path = ROOT / name
    raw = path.read_bytes()
    text = ('\n## 14/11 — Tách CPU local và GPU cho A2/A3\n\n'
            '[Hồ sơ](' + link + BUNDLE.name + '/README.md) giữ 71 ca local đạt, '
            'đối chiếu 27 trường với A0/A1 thật, stop barrier trước download/nén và checkpoint recovery. '
            'Chưa fit confidence thật, kiểm Linux/CUDA hay training A2/A3. Đợt này 0 USD Modal.\n\n').encode()
    if text not in raw:
        line = raw.index(b'\n') + 1
        path.write_bytes(raw[:line] + text + raw[line:])

# Manifest OPEN trước đó được cập nhật vì STATE/README của gói đó vừa ghi tiến độ.
old_manifest = json.loads((old / 'MANIFEST.json').read_text(encoding='utf-8'))
assert old_manifest['status'].startswith('OPEN')
for name in ('STATE.json', 'README.md'):
    payload = (old / name).read_bytes()
    old_manifest['files'][name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
write_json(old / 'MANIFEST.json', old_manifest)
manifest = dict(status='CLOSED_LOCAL_VERIFIED_PLATFORM_PENDING', sources={}, files={})
for name in sources:
    payload = (ROOT / name).read_bytes()
    manifest['sources'][name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
for path in sorted(BUNDLE.iterdir()):
    if path.is_file() and path.name != 'MANIFEST.json':
        payload = path.read_bytes()
        manifest['files'][path.name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
write_json(BUNDLE / 'MANIFEST.json', manifest)
print(json.dumps(state))
