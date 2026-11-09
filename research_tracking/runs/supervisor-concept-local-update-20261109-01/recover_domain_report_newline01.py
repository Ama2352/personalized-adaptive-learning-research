"""Giữ failure ghi xuống dòng và phục hồi hai báo cáo đúng byte snapshot."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
original = PREP / 'domain-progress-before01'
inventory = json.loads((original / 'inventory-before.json').read_bytes())
failure = PREP / 'domain-progress-newline-failure01'
failure.mkdir(exist_ok=False)
paths = [ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do' / name
    for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html')]
extras = [ROOT / 'research_tracking/reports/paper1_seeded_domain_smoke_readiness_20261109.md',
    ROOT / 'experiments/simulator/README.md', PREP / 'publish_domain_progress01.py']
records = {}
for index, path in enumerate(paths + extras):
    raw = path.read_bytes()
    target = failure / (str(index) + '__' + path.name)
    with target.open('xb') as stream:
        stream.write(raw)
    assert target.read_bytes() == raw
    records[path.relative_to(ROOT).as_posix()] = dict(sha256=hashlib.sha256(raw).hexdigest(),
        bytes=len(raw), copy=target.name)
for index, path in enumerate(paths):
    before = (original / (str(index) + '__' + path.name)).read_bytes()
    expected = inventory[path.relative_to(ROOT).as_posix()]['sha256']
    assert hashlib.sha256(before).hexdigest() == expected
    path.write_bytes(before)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
note = dict(status='PRESERVED_TEXTIO_NEWLINE_FAILURE_HUMAN_REPORTS_RESTORED_EXACT',
    files=records, original_inventory='domain-progress-before01/inventory-before.json',
    observed_failure='ROOT tool output AssertionError at SVG byte comparison, publish_domain_progress01.py line77',
    raw_subprocess_stderr_captured=False, root_cause='TextIO newline translation on Windows while writing decoded existing bytes',
    unchanged_tracking_files=True, restore_scope='Only the two human reports, byte-identical to pre-update snapshots',
    report_and_role_created_by_failed_attempt_retained=True)
with (failure / 'failure.json').open('x', encoding='utf-8') as stream:
    json.dump(note, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status=note['status'], restored_reports=2)))
