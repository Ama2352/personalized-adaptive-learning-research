"""So raw Git với manifest của các bundle vừa đóng bằng một subprocess."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
NAMES = ('owned-job-resource-exit-guard-20261110-01','a1-expert-selected-engineering-20261110-01','gkt-selected-engineering-20261110-01','a0-a1-cached-export-check-20261110-01','supervisor-final-cpu-progress-qa-20261110-01','main-selection-population-candidate-20261110-01')
checks = []
counts = {}
for name in NAMES:
    directory = Path('research_tracking/runs')/name
    manifest = json.loads((ROOT/directory/'manifest.json').read_bytes())
    outputs = dict(manifest['outputs_sha256'])
    outputs['manifest.json'] = hashlib.sha256((ROOT/directory/'manifest.json').read_bytes()).hexdigest()
    counts[name] = len(outputs)
    checks.extend(((directory/relative).as_posix(),digest) for relative,digest in outputs.items())
raw = subprocess.run(['git','cat-file','--batch'],cwd=ROOT,
    input=('\n'.join('HEAD:'+path for path,_ in checks)+'\n').encode(),
    stdout=subprocess.PIPE,check=True).stdout
offset = 0
for path,expected in checks:
    end = raw.index(b'\n',offset)
    header = raw[offset:end].split()
    assert len(header)==3 and header[1]==b'blob',path
    size = int(header[2])
    content = raw[end+1:end+1+size]
    assert hashlib.sha256(content).hexdigest()==expected,path
    offset = end+size+2
assert offset == len(raw)
result = dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
    counts=counts,total_raw_files_checked=len(checks),all_equal=True,
    scope='RawGit byte integrity only, not scientific validity or RQ completion.')
(Path(__file__).parent/'overnight_git_bundles_readback07_20261110.json').write_text(
    json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
