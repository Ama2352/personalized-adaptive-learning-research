"""Bảo toàn OOF và fit ledger của confidence, tách khỏi SQLite đầu vào tái dựng."""
from pathlib import Path
import json
import sys

from package_outputs01 import ROOT, B, sha, walk, write, upload


def prepare():
    paths=walk('artifacts/akt/confidence/full-train80-20261114-02/children')
    batches=[];rows=[];size=0
    for path in sorted(paths):
        assert path.suffix in {'.json','.gz'}, str(path)
        count=path.stat().st_size
        if rows and size+count>160*1024**2:
            batches.append(dict(name=f'CONFIDENCE_OOF_FIT_LEDGER_{len(batches)+1:02d}.zip',files=rows,source_bytes=size))
            rows=[];size=0
        rows.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=count,sha256=sha(path)));size+=count
    if rows:
        batches.append(dict(name=f'CONFIDENCE_OOF_FIT_LEDGER_{len(batches)+1:02d}.zip',files=rows,source_bytes=size))
    inventory=dict(status='OOF_AND_CHILD_FIT_LEDGERS_INVENTORIED',batches=batches,
        note='OOF là đầu ra audit confidence cần giữ. SQLite rows là đầu vào phái sinh riêng, giữ local và mapping tái dựng.')
    write('CONFIDENCE_OUTPUTS_INVENTORY01.json',inventory)
    print('CONFIDENCE_PREPARED',len(paths),sum(b['source_bytes'] for b in batches),len(batches),flush=True)


if __name__=='__main__':
    if '--prepare' in sys.argv:
        prepare()
    if '--upload' in sys.argv:
        upload(json.loads((B/'CONFIDENCE_OUTPUTS_INVENTORY01.json').read_text(encoding='utf-8')),
               receipt_name='CONFIDENCE_ARCHIVES_DRIVE01.json')
