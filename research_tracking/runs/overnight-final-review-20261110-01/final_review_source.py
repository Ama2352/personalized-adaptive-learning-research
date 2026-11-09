"""Đóng kiểm cuối, giữ cả bản trước/sau và bằng chứng Git đã đọc lại."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import shutil

root = Path(__file__).resolve().parents[4]
p = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
report = root / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
gate = json.loads((root / 'artifacts/akt/preflight/gate2-evidence-win-current-gate-20261110-07.json').read_bytes())
assert len(gate['build_hashes']) == 183
assert all(sha(root / path) == pin for path, pin in gate['build_hashes'].items())
before = (p / 'final-report-story-polish01/before_BAO_CAO_NGHIEN_CUU.html').read_bytes()
current = (report / 'BAO_CAO_NGHIEN_CUU.html').read_bytes()
assert re.findall(rb'<svg\b.*?</svg>', before, re.S) == re.findall(rb'<svg\b.*?</svg>', current, re.S)
assert current.count(b'<table') == current.count(b'</table>') == 17
bundle = root / 'research_tracking/runs/overnight-final-review-20261110-01'
bundle.mkdir(exist_ok=False)
files = {path.name: path for path in (p / 'final-report-story-polish01').iterdir() if path.is_file()}
for name in ['polish_final_report_story01.py', 'final_story_desktop01.png', 'final_story_mobile01.png',
             'overnight_git_bundles_readback05_20261110.json', 'overnight_git_bundles_readback06_20261110.json',
             'overnight_git_bundles_readback07_20261110.json', 'verify_overnight_git_bundles07_20261110.py']:
    files[name] = p / name
files['final_review_source.py'] = Path(__file__).resolve()
inventory = {name: {'source': path.relative_to(root).as_posix(), 'sha256': sha(path)} for name, path in files.items()}
(bundle / 'inventory_before_copy.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
for name, path in files.items():
    shutil.copyfile(path, bundle / name)
    assert sha(bundle / name) == inventory[name]['sha256']
proof = {'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'current_gate_source_hashes_matched': 183,
    'gate_tests_rerun_in_final_check': False, 'original_svg_preserved': 11, 'tables': 17,
    'first_progress_block': 'research finding', 'mobile': {'viewport': 390, 'document_width': 375},
    'desktop_and_mobile_images_viewed': True, 'own_browser_closed': True, 'own_preview_session_terminal': 26871,
    'capture_note_vi': 'Lượt lấy kích thước đầu gọi innerWidth sai ngữ cảnh sau khi đã lưu hai ảnh. Lượt đọc DOM kế tiếp đạt, ảnh đã xem.',
    'all_native_jobs_terminal_and_clean': True, 'modal_used_usd': 0,
    'remaining_vi': ['Main60 và Junyi đầy đủ', 'External freeze từ đủ chín candidates',
        'Fresh refit/calibration', 'Fitted online/controller', 'Current Linux/CUDA và unexpected-fault/durability/throughput'],
    'RQ_completion_claim': False}
(bundle / 'review.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(bundle / 'README.md').write_text('# Kiểm cuối đợt tự động10/11\n\n'
    'Báo cáo ưu tiên phát hiện RQ1–RQ2 trước phần chuẩn bị mô hình và giảm thuật ngữ ở đoạn mới. '
    'Giữ11SVG/17bảng, Root đã xem desktop/mobile. Trình duyệt riêng vàpreview đãđóng. '
    'Đối chiếu183sourcehash hiện hành đạt, không chạy lại1913tests. Ba proofGit giữ các lần đọc blob trước đó, '
    'không là nghiệm thu hiệu quả nghiên cứu. Maintraining/CUDA/refit/closedloop và hoàn tấtRQ còn thiếu.\n', encoding='utf-8')
manifest = {'status': 'completed', 'outputs_sha256': {path.name: sha(path) for path in bundle.iterdir() if path.is_file()}}
(bundle / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
assert all(sha(bundle / name) == pin for name, pin in manifest['outputs_sha256'].items())
state_path = root / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['overnight_session_20261110']['current_status'] = 'BOUNDED_WORK_PACKAGES_CLOSED_AND_FINAL_CHECKS_PASS'
state['overnight_session_20261110']['final_review_bundle'] = bundle.relative_to(root).as_posix()
state['overnight_session_20261110']['work_packages_closed_at_utc'] = proof['completed_at_utc']
state['overnight_session_20261110']['next_batch_vi'] = 'Hoàn thiện artifact admission/externalfreeze và refit/calibration; kiểm runtimeColabLinux/CUDA khi có kết nối. Không tự chiModal.'
state['human_final_CPU_report_20261110']['narrative_polish_and_final_review_bundle'] = bundle.relative_to(root).as_posix()
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nKiểm cuối:183sourcehashGate hiện hành khớp, không rerun1913tests. Gitrawreadback341files '
        'của sáu bundle mới đạt tại0299cc3. Báo cáo đã đặt phát hiện khoa học trước mốc phần mềm, '
        'desktop/mobile đã xem,11SVG nguyên/17tables, browser vàpreview đều đóng. '
        'Các nativejobs terminal/Job0, không cóModalcompute. Gói việc đã đóng, cácRQ/mainmatrix vẫn còn thiếu.\n')
print(json.dumps({'bundle': bundle.relative_to(root).as_posix(), 'gate_hashes': 183, 'review_pass': True}))
