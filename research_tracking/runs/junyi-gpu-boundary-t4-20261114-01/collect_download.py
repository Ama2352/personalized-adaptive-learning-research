"""Nhận chunk MCP đã có trên D, kiểm SHA và dựng lại archive bất biến."""
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIVATE = ROOT / 'artifacts/akt/private/colab-bridge/session-5ee09dc12b3a40c68f2c01d4fe8344d5'
DESTINATION = ROOT / 'artifacts/akt/colab/gpu-boundary-download-20261114-01'
SIZE = 107242140
SHA256 = '9888cdf0ac29b13d99354f6c2e132510683be5bfc63d500efa51c98fe6e9500f'
BLOCK = 200000
COUNT = (SIZE + BLOCK - 1) // BLOCK


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    receipts = {}
    ledger = DESTINATION / 'received.json'
    if ledger.exists():
        receipts = json.loads(ledger.read_text())
    seen = set(receipts.get('parsed_responses', []))
    chunks = receipts.get('chunks', {})
    for response in PRIVATE.glob('result-*.json'):
        if response.name in seen:
            continue
        try:
            payload = json.loads(response.read_text())
        except ValueError:
            continue  # Client vẫn có thể đang ghi response.
        for output in (payload.get('structured_content') or {}).get('outputs', []):
            text = output.get('text', [])
            if isinstance(text, list):
                text = ''.join(text)
            try:
                event = json.loads(text)
            except (ValueError, TypeError):
                continue
            if type(event) is not dict or event.get('status') != 'EVIDENCE_CHUNK':
                continue
            index = event['index']
            assert type(index) is int and 0 <= index < COUNT
            assert event['offset'] == index * BLOCK
            raw = base64.b64decode(event['data'], validate=True)
            assert len(raw) == event['bytes'] == min(BLOCK, SIZE-index*BLOCK)
            digest = hashlib.sha256(raw).hexdigest()
            assert digest == event['sha256']
            part = DESTINATION / f'{index:03d}.bin'
            if part.exists():
                assert part.read_bytes() == raw
            else:
                part.write_bytes(raw)
            chunks[str(index)] = dict(bytes=len(raw), sha256=digest, response=response.name)
        seen.add(response.name)
    ledger.write_text(json.dumps(dict(chunks=chunks, parsed_responses=sorted(seen)), indent=2)+'\n')
    missing = [index for index in range(COUNT) if str(index) not in chunks]
    status = dict(received_chunks=len(chunks), total_chunks=COUNT, missing=missing,
                  destination=DESTINATION.relative_to(ROOT).as_posix(), verified=False)
    if not missing:
        archive = DESTINATION / 'evidence-download.zip.xz'
        if not archive.exists():
            with archive.open('xb') as stream:
                for index in range(COUNT):
                    stream.write((DESTINATION / f'{index:03d}.bin').read_bytes())
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        assert archive.stat().st_size == SIZE and digest == SHA256
        status.update(verified=True, bytes=SIZE, sha256=digest)
    (HERE / 'download-progress.json').write_text(json.dumps(status, indent=2)+'\n')
    print(json.dumps(status))


if __name__ == '__main__':
    main()
