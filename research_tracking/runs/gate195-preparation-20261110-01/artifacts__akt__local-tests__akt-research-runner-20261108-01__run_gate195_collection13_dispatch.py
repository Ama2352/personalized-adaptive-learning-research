"""Root dispatch collect-only đã ghim, giữ lỗi admission và timeout70giây."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
dispatch = json.loads((prep / 'gate195_collection13_dispatch.json').read_bytes())
assert hashlib.sha256((root / dispatch['outer']).read_bytes()).hexdigest() == dispatch['outer_sha256']
out = prep / 'gate195-collection13-dispatch'
out.mkdir(exist_ok=False)
command = [str(root / '.venv/Scripts/python.exe'), '-B', str(root / dispatch['outer']),
    '--packet', str(root / dispatch['packet']), '--packet-sha256', dispatch['packet_sha256'],
    '--worker-sha256', dispatch['worker_sha256'], '--approval-reference', dispatch['approval_reference']]
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    result = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr, timeout=70)
(out / 'result.json').write_text(json.dumps(dict(returncode=result.returncode, timeout_seconds=70)) + '\n')
print('returncode', result.returncode)
print((out / 'stdout.log').read_text())
print((out / 'stderr.log').read_text()[-2200:])
sys.exit(result.returncode)
