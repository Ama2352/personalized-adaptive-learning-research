"""Render HTML bằng Chrome headless có profile và owned Job riêng, giữ ảnh QA."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
HTML = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html'
OUT = PREP / 'supervisor-masking-render01'
OWNED = PREP / 'supervisor-masking-render01-owned'
CHROME = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
sys.path.insert(0, str(ROOT / 'scripts/research'))
from windows_owned_worker import run_owned, worker_gate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if '--worker' in sys.argv:
    owner = worker_gate()
    assert Path(sys.prefix).resolve() == ROOT / '.venv' and not OUT.exists()
    expected_html = sys.argv[sys.argv.index('--worker') + 1]
    assert sha(HTML) == expected_html and CHROME.is_file()
    OUT.mkdir()
    png = OUT / 'stage11-desktop.png'
    command = [str(CHROME), '--headless=new', '--disable-gpu', '--disable-background-networking',
        '--disable-component-update', '--disable-extensions', '--no-first-run', '--no-default-browser-check',
        '--no-proxy-server', '--metrics-recording-only', '--disable-crash-reporter', '--hide-scrollbars',
        '--window-size=1280,1600', '--virtual-time-budget=1200', '--user-data-dir=' + str(OUT / 'profile'),
        '--screenshot=' + str(png), HTML.as_uri() + '#chang-11']
    started = time.perf_counter()
    errors, returncode = [], None
    try:
        with (OUT / 'chrome-stdout.log').open('xb') as stdout, (OUT / 'chrome-stderr.log').open('xb') as stderr:
            completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=22)
        returncode = completed.returncode
        assert returncode == 0 and png.is_file() and png.stat().st_size < 10 * 1024**2
        header = png.read_bytes()[:24]
        assert header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1280, 1600)
        assert sha(HTML) == expected_html
    except BaseException as error:
        errors.append(dict(type=type(error).__name__, message=str(error)))
    write(OUT / 'result.json', dict(status='RENDERED_PENDING_VISUAL_INSPECTION' if not errors else 'REJECTED_KEEP_LOGS',
        errors=errors, returncode=returncode, html_sha256=expected_html, chrome_exe_sha256=sha(CHROME),
        screenshot_sha256=sha(png) if png.is_file() else None, width=1280, height=1600,
        worker_seconds=time.perf_counter() - started, no_server_started=True, headless=True,
        browser_profile_relative=(OUT / 'profile').relative_to(ROOT).as_posix(), owner=owner))
    raise SystemExit(0 if not errors else 1)

assert Path(sys.prefix).resolve() == ROOT / '.venv' and not OUT.exists() and not OWNED.exists()
started = time.perf_counter()
receipt = run_owned(Path(__file__).resolve(), ['--worker', sha(HTML)], OWNED,
    expected_worker_sha256=sha(Path(__file__).resolve()), approval_reference='ROOT_REPORT_STAGE11_VISUAL_QA_NO_SERVER',
    max_seconds=30, cleanup_reserve_seconds=5, max_output_bytes=65536)
if not OWNED.exists():
    OWNED.mkdir()
write(OWNED / 'receipt.json', receipt)
record = json.loads((OUT / 'result.json').read_bytes()) if (OUT / 'result.json').is_file() else None
accepted = (receipt['accepted'] is True and receipt['cleanup_accepted'] is True
    and receipt['job_active_after_cleanup'] == 0 and record is not None and record['errors'] == [])
write(OWNED / 'final.json', dict(status='RENDERED_JOB0_PENDING_VISUAL_INSPECTION' if accepted else 'REJECTED_RENDER_KEEP_LOGS',
    receipt=receipt, result=record, outer_seconds=time.perf_counter() - started,
    server_started=False, requires_image_inspection=accepted))
print(json.dumps(dict(status='RENDERED_JOB0_PENDING_VISUAL_INSPECTION' if accepted else 'REJECTED_RENDER_KEEP_LOGS',
                      job_active_after_cleanup=receipt['job_active_after_cleanup'], result=record)))
raise SystemExit(0 if accepted else 1)
