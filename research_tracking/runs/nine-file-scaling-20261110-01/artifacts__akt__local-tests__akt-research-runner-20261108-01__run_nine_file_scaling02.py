"""Lượt CPU synthetic tối đa120giây gồm tests và reader45giây, không retry."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'nine-file-scaling-dispatch02'
out.mkdir(exist_ok=False)
with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
    result = subprocess.run([str(root / '.venv/Scripts/python.exe'), '-B', str(prep / 'check_nine_file_scaling02.py')],
        cwd=root, stdout=stdout, stderr=stderr, timeout=120)
(out / 'result.json').write_text(json.dumps(dict(returncode=result.returncode, timeout_seconds=120)) + '\n')
print('returncode', result.returncode)
print((out / 'stdout.log').read_text())
print((out / 'stderr.log').read_text()[-1800:])
sys.exit(result.returncode)

