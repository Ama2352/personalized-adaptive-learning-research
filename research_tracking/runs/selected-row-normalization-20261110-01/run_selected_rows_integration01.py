"""Lượt local tối đa30giây, log riêng, không tự retry."""
from pathlib import Path
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'selected-rows-dispatch01'
out.mkdir(exist_ok=False)
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    result = subprocess.run([str(root / '.venv/Scripts/python.exe'), '-B',
        str(prep / 'check_selected_rows_integration01.py')], cwd=root, stdout=stdout, stderr=stderr, timeout=30)
(out / 'result.json').write_text(json.dumps({'returncode': result.returncode, 'timeout_seconds': 30}) + '\n')
print('returncode', result.returncode)
print((out / 'stdout.log').read_text())
print((out / 'stderr.log').read_text())
sys.exit(result.returncode)
