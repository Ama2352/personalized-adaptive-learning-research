"""Chia ZIP vượt giới hạn connector, đối chiếu SHA và giữ nguyên bản gốc."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'experiments/akt/results/artifact-offload-20261116-01'
PARTS = OUTPUT / 'drive-transfer-parts-20261116-01'
CHUNK_BYTES = 96 * 1024**2


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan = json.loads((OUTPUT / 'FIRST_DRIVE_UPLOAD_BATCH.json').read_text(encoding='utf-8'))
    PARTS.mkdir(exist_ok=False)
    archives = []
    for item in plan['files']:
        if item['bytes'] <= 100 * 1024**2:
            continue
        source = ROOT / item['path']
        assert sha(source) == item['sha256']
        parts = []
        with source.open('rb') as stream:
            index = 1
            while block := stream.read(CHUNK_BYTES):
                name = source.name + f'.part{index:02d}'
                path = PARTS / name
                with path.open('xb') as output:
                    output.write(block)
                digest = hashlib.sha256(block).hexdigest()
                assert sha(path) == digest
                parts.append(dict(name=name, bytes=len(block), sha256=digest))
                index += 1
        combined = hashlib.sha256()
        for part in parts:
            with (PARTS / part['name']).open('rb') as stream:
                for block in iter(lambda: stream.read(1024**2), b''):
                    combined.update(block)
        assert combined.hexdigest() == item['sha256'] == sha(source)
        assert sum(part['bytes'] for part in parts) == item['bytes']
        archives.append(dict(name=source.name, source=item['path'], bytes=item['bytes'], sha256=item['sha256'], parts=parts))
    manifest = dict(schema='kltn-drive-split-v1', chunk_bytes=CHUNK_BYTES, archives=archives,
                    originals_preserved=True, reason_vi='Connector từ chối file lớn hơn 100 MiB. Ghép phần theo manifest để khôi phục nguyên ZIP.')
    (PARTS / 'DRIVE_PARTS_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    receipt = dict(status='PASS_SPLIT_AND_RECONSTRUCTION_HASH', manifest= (PARTS / 'DRIVE_PARTS_MANIFEST.json').relative_to(ROOT).as_posix(),
        manifest_sha256=sha(PARTS / 'DRIVE_PARTS_MANIFEST.json'), archives=len(archives), parts=sum(len(item['parts']) for item in archives),
        bytes=sum(item['bytes'] for item in archives), originals_preserved=True,
        failed_upload01_vi='HTTP 413 trước action, 108428632 byte vượt giới hạn 104857600 byte, chưa tạo file01 trên Drive.')
    (HERE / 'DRIVE_PARTS_PREPARED.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
