"""Preview local chỉ cho lượt QA này, tự dừng sau120giây hoặc stop file."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
STOP = PREP / 'supervisor_learned19_preview01.stop'
assert not STOP.exists()
handler = partial(SimpleHTTPRequestHandler,
    directory=str(ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'))
start = time.monotonic()
with HTTPServer(('127.0.0.1', 0), handler) as server:
    server.timeout = 0.5
    print(json.dumps(dict(port=server.server_port, max_seconds=120)), flush=True)
    while time.monotonic() - start < 120 and not STOP.exists():
        server.handle_request()
print(json.dumps(dict(status='OWNED_PREVIEW_SERVER_CLOSED', seconds=time.monotonic()-start)), flush=True)
