"""Giữ nguyên byte lịch sử khi thêm mốc tiến độ vào hai báo cáo hiện hành."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
REPORT = 'research_tracking/supervisor_reports/2026-11-10/01_tien_do/'
for filename in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html'):
    name = REPORT + filename
    path = ROOT / name
    baseline = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
    current = path.read_text(encoding='utf-8')
    normalized = baseline.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    if filename.endswith('.md'):
        start = current.index('## 14/11 — A2 đã đạt kiểm snapshot')
        end = current.index('## 14/11 — Hoàn tất confidence', start)
        inserted = current[start:end]
        assert current.replace(inserted, '', 1).strip() == normalized.strip()
        anchor = '## 14/11 — Hoàn tất confidence'.encode('utf-8')
    else:
        start = current.index('<section id="cap-nhat-20261114-a2-dispatch">')
        end = current.index('<section id="cap-nhat-20261114-confidence-completion">', start)
        inserted = current[start:end]
        assert current.replace(inserted, '', 1) == normalized
        anchor = b'<section id="cap-nhat-20261114-confidence-completion">'
    assert baseline.count(anchor) == 1
    path.write_bytes(baseline.replace(anchor, inserted.encode('utf-8') + anchor, 1))
print('Đã giữ nguyên byte phần báo cáo lịch sử.')
