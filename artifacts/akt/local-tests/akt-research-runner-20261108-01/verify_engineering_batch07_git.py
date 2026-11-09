"""Đọc raw Git một lần để so với manifest bundle đã commit."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BUNDLE = Path('research_tracking/runs/akt-resume-metadata-and-report-qa-20261109-01')
manifest = json.loads((ROOT / BUNDLE / 'manifest.json').read_bytes())
paths = list(manifest['outputs_sha256']) + ['manifest.json']
specs = ['HEAD:' + (BUNDLE / p).as_posix() for p in paths]
raw = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
    input=('\n'.join(specs) + '\n').encode(), stdout=subprocess.PIPE, check=True).stdout
position = 0
for relative in paths:
    end = raw.index(b'\n', position)
    size = int(raw[position:end].split()[2])
    content = raw[end + 1:end + 1 + size]
    position = end + size + 2
    expected = hashlib.sha256((ROOT / BUNDLE / relative).read_bytes()).hexdigest()
    assert hashlib.sha256(content).hexdigest() == expected, relative
result = dict(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
    raw_git_files_checked=len(paths), equal=True)
output = Path(__file__).parent / 'engineering_batch07_git_readback.json'
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
