"""Lượt local tối đa45giây, không retry ngầm."""
from pathlib import Path
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'selected-metadata-dispatch01'
out.mkdir(exist_ok=False)
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    result = subprocess.run([str(root / '.venv/Scripts/python.exe'), '-B',
        str(prep / 'check_selected_metadata01.py')], cwd=root, stdout=stdout, stderr=stderr, timeout=45)
(out / 'result.json').write_text(json.dumps(dict(returncode=result.returncode, timeout_seconds=45)) + '\n')
print('returncode', result.returncode)
print((out / 'stdout.log').read_text())
print((out / 'stderr.log').read_text()[-2500:])
sys.exit(result.returncode)
