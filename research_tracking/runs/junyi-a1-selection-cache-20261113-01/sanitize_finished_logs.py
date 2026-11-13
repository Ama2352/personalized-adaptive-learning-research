"""Giữ nguyên log gốc ở vùng private D, tạo bản ghi đã che định danh token SDK."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    names = ['h100-controller06.log', 'h100-controller07.log', 'h100-controller08.log',
             'monitor-empty-diagnostic.json']
    final_receipt = ROOT / 'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-09/receipt.json'
    if final_receipt.exists():
        names.append('h100-controller09.log')
    private = ROOT / 'artifacts/akt/private/operational-logs' / HERE.name
    private.mkdir(parents=True, exist_ok=True)
    records = []
    for name in names:
        path = HERE / name
        if not path.exists():
            continue
        raw = path.read_bytes()
        text = raw.decode('utf-8-sig')
        sanitized = re.sub(r'\bak-[A-Za-z0-9_-]+', '[MODAL_TOKEN_IDENTIFIER_REDACTED]', text)
        sanitized = '\n'.join(line.rstrip() for line in sanitized.splitlines()).rstrip() + '\n'
        if sanitized.encode('utf-8') == raw:
            continue
        original = private / (name + '.' + hashlib.sha256(raw).hexdigest()[:12] + '.raw')
        if original.exists():
            assert original.read_bytes() == raw
        else:
            original.write_bytes(raw)
        path.write_text(sanitized, encoding='utf-8', newline='\n')
        records.append({'file': name, 'original_sha256': hashlib.sha256(raw).hexdigest(),
                        'sanitized_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'original_preserved_on_d': True,
                        'original_private_path': original.relative_to(ROOT).as_posix()})
    output = HERE / 'log-redaction-h100.json'
    previous = json.loads(output.read_text()) if output.exists() else []
    output.write_text(json.dumps(previous + records, indent=2) + '\n')
    print(json.dumps({'new_sanitized_logs': len(records)}))


if __name__ == '__main__':
    main()
