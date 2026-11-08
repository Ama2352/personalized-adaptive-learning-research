"""Cheap owned NTFS hard-link contrast only, no Torch/import/model/optimizer."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

base = Path(__file__).resolve().parent
assert len(sys.argv) == 2 and sys.argv[1] in ('01', '02')
directory = base / ('link-control-' + sys.argv[1]); directory.mkdir(exist_ok=False)
start = time.perf_counter()
source = directory / 'source.bin'; source.write_bytes(b'owned synthetic publication control')
row = {'stage': sys.argv[1], 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
       'model_optimizer_calls': 0, 'scope': 'same directory owned hard-link permission control'}
try:
    os.link(source, directory / 'target.bin')
    assert (directory / 'target.bin').read_bytes() == source.read_bytes()
    row.update(status='HARDLINK_CREATED_EXACT', link_count=source.stat().st_nlink)
except OSError as error:
    row.update(status='HARDLINK_FAILED', error_type=type(error).__name__, error=str(error), winerror=error.winerror)
row['elapsed_seconds'] = time.perf_counter() - start
with (directory / 'result.json').open('x', encoding='utf-8') as stream:
    json.dump(row, stream, indent=2); stream.write('\n')
print(json.dumps(row))
