"""Chuẩn bị request nhỏ cho cầu nối Colab hiện có, không thực thi remote."""
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REQUESTS = ROOT/'artifacts/akt/colab/requests'
BUNDLE = ROOT/'artifacts/akt/colab/sourcekit-cpu-current-20261110-01.zip'
CELL = 'D6wvrfzyoyjR'
raw = BUNDLE.read_bytes()
encoded = base64.b64encode(raw).decode('ascii')
chunks = [encoded[start:start+46000] for start in range(0, len(encoded), 46000)]
commands = []
for index, chunk in enumerate(chunks):
    code = ('KLTN_TRANSFER = []\n' if index == 0 else '')
    code += f'assert len(KLTN_TRANSFER) == {index}\n'
    code += f'KLTN_TRANSFER.append({chunk!r})\nprint("TRANSFER_PART", len(KLTN_TRANSFER))\n'
    update = REQUESTS/f'current-cpu-part-{index:02d}.json'
    run = REQUESTS/f'current-cpu-run-{index:02d}.json'
    update.write_text(json.dumps(dict(cellId=CELL, content=code)), encoding='utf-8')
    run.write_text(json.dumps(dict(cellId=CELL)), encoding='utf-8')
    assert update.stat().st_size < 48*1024
    for name, path in [('update_cell', update), ('run_code_cell', run)]:
        commands.append(dict(action='call', name=name, args_file=str(path), timeout_seconds=30))
out = ROOT/'artifacts/akt/colab/current-cpu-transfer-commands.json'
out.write_text(json.dumps(commands), encoding='utf-8')
print(json.dumps(dict(parts=len(chunks), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), commands=str(out))))
