"""Giữ nguyên byte các mục báo cáo cũ, chỉ chèn mục A3 mới."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import sha, write_new


def main():
    reports = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
    records = {}
    for name, start, previous in (
        ('BAO_CAO.md', '## 14/11 — A0–A3 đã hoàn tất chọn checkpoint trên Junyi',
         '## 14/11 — A2 hoàn tất bước chọn checkpoint trên Junyi'),
        ('BAO_CAO_NGHIEN_CUU.html', '<section id="cap-nhat-20261114-a3-complete">',
         '<section id="cap-nhat-20261114-a2-dispatch">')):
        path = reports / name
        relative = path.relative_to(ROOT).as_posix()
        original = subprocess.run(['git', 'show', 'HEAD:' + relative], cwd=ROOT,
                                  capture_output=True, check=True).stdout
        current = path.read_bytes()
        first = current.index(start.encode())
        last = current.index(previous.encode(), first)
        new_section = current[first:last]
        new_section = new_section.replace('trước gọi GPU; tải'.encode(), 'trước gọi GPU. Việc tải'.encode())
        position = original.index(previous.encode())
        final = original[:position] + new_section + original[position:]
        assert final.replace(new_section, b'', 1) == original
        path.write_bytes(final)
        records[relative] = dict(historical_bytes_preserved=True, new_section_bytes=len(new_section), sha256=sha(path))
    qa_path = HERE / 'a3-report-verification.json'
    qa = json.loads(qa_path.read_text())
    qa['pre_history_preservation_hashes'] = qa['reports']
    qa['reports'] = {name: record['sha256'] for name, record in records.items()}
    qa['historical_report_bytes_preserved'] = True
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_new(HERE / 'report-history-preservation.json', records)
    print(json.dumps(dict(status='PASS_HISTORICAL_REPORT_BYTES_PRESERVED')))


if __name__ == '__main__':
    main()
