"""Lưu snapshot báo cáo và QA đã quan sát, không kiểm giao diện lại."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'supervisor-masking-report-qa-20261109-01'
assert Path(sys.prefix).resolve() == ROOT / '.venv'
assert not (ROOT / 'research_tracking/runs' / RUN).exists()
base = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
sources = {
    'browser_qa.json': PREP / 'supervisor_masking_managed_browser_QA01.json',
    'stage11-desktop.png': PREP / 'stage11-managed-desktop.png',
    'local_render_failure.json': PREP / 'supervisor-masking-render01/result.json',
    'local_render_owned_receipt.json': PREP / 'supervisor-masking-render01-owned/receipt.json',
    'local_render_stdout.log': PREP / 'supervisor-masking-render01/chrome-stdout.log',
    'local_render_stderr.log': PREP / 'supervisor-masking-render01/chrome-stderr.log',
    'publish_masking_supervisor01.py': PREP / 'publish_masking_supervisor01.py',
    'finalize_masking_supervisor_qa01.py': PREP / 'finalize_masking_supervisor_qa01.py',
    'render_supervisor_masking01.py': PREP / 'render_supervisor_masking01.py',
    'before_inventory.json': PREP / 'supervisor-before-masking01/inventory-before.json',
    'before_BAO_CAO.md': PREP / 'supervisor-before-masking01/BAO_CAO.md',
    'before_BAO_CAO_NGHIEN_CUU.html': PREP / 'supervisor-before-masking01/BAO_CAO_NGHIEN_CUU.html',
    'BAO_CAO.md': base / 'BAO_CAO.md',
    'BAO_CAO_NGHIEN_CUU.html': base / 'BAO_CAO_NGHIEN_CUU.html',
    'supervisor_update_proof.json': ROOT / 'docs/thesis_recovery/evidence/supervisor_masking_update_20261109.json',
    Path(__file__).name: Path(__file__).resolve(),
}


def digest(path):
    assert path.resolve() == path and path.is_relative_to(ROOT) and path.is_file()
    assert path.stat().st_size < 2 * 1024**2 and not path.is_symlink()
    return hashlib.sha256(path.read_bytes()).hexdigest()


proof = json.loads(sources['supervisor_update_proof.json'].read_bytes())
browser = json.loads(sources['browser_qa.json'].read_bytes())
receipt = json.loads(sources['local_render_owned_receipt.json'].read_bytes())
assert proof['visual_render'] and browser['owned_tab_closed'] and not browser['preview_server_started']
assert receipt['job_active_after_cleanup'] == 0
for name, identity in proof['after'].items():
    assert digest(base / name) == identity['sha256']
assert digest(sources['browser_qa.json']) == proof['browser_qa']['sha256']
assert digest(sources['stage11-desktop.png']) == proof['browser_qa']['screenshot']['sha256']
manifest = ROOT / 'research_tracking/runs/rq1-mastery-ready-masking-20261109-01/manifest.json'
assert digest(manifest) == '9cbb7a276b750bf079f544ba69a4d0cf1ea28b89140707957630630a20aa9a4b'
inventory = [dict(copy=name, source=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
    sha256=digest(path)) for name, path in sources.items()]
assert sum(row['bytes'] for row in inventory) < 2 * 1024**2
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

note = ('# Báo cáo GVHD — chặng11 và QA giao diện\n\n'
    'Snapshot hai file người đọc, mười biểu đồ cũ giữ nguyên và biểu đồ chặng11 mới. '
    'Giữ JSON desktop1280/mobile390 cùng ảnh desktop mà ROOT đã xem trực tiếp. '
    'BBox được đo trước hai chỉnh khoảng trắng cuối ở title/footnote, ảnh sau chỉnh đã được xem. '
    'Tab kiểm riêng đã đóng, không mở preview server. '
    'Lượt Chrome local trước đó lỗi crashpad, có stdout/stderr/result và receipt Job0 riêng. '
    'Không có screenshot từ lượt lỗi và không chạy lại browser khi đóng gói. '
    'Đây là bằng chứng trình bày, số nghiên cứu tham chiếu bundle rq1-mastery-ready-masking-20261109-01, '
    'không thêm mẫu hoặc kết luận nghiên cứu. Các file báo cáo hiện hành vẫn ở supervisor_reports.\n')
with record_evidence_run(ROOT, RUN, metadata=dict(kind='SUPERVISOR_REPORT_SNAPSHOT_AND_OBSERVED_UI_QA',
    scientific_new_N=0, report_stage=11, svg_count=11, tables=11,
    browser_reexecution=False, source_manifest_sha256=digest(manifest)),
    sources=list(sources.values()) + [manifest], note=note) as destination:
    for row in inventory:
        source = ROOT / row['source']
        assert digest(source) == row['sha256']
        with (destination / row['copy']).open('xb') as stream:
            stream.write(source.read_bytes())
        assert digest(source) == digest(destination / row['copy']) == row['sha256']
    with (destination / 'copy_inventory.json').open('x', encoding='utf-8') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    assert len(list(destination.iterdir())) == len(sources) + 4
verified = verify_evidence_bundle(destination)
assert verified['artifacts'] == len(sources) + 3
print(json.dumps(dict(**verified, manifest_sha256=digest(destination / 'manifest.json'))))
