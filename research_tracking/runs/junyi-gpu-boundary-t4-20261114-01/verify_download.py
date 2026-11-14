"""Kiểm archive MCP và nhận đầy đủ checkpoint/log vào output trên ổ D."""
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DOWNLOAD = ROOT / 'artifacts/akt/colab/gpu-boundary-download-20261114-01'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    progress = json.loads((HERE/'download-progress.json').read_text())
    assert progress['verified'] is True
    packed = DOWNLOAD/'evidence-download.zip.xz'
    assert sha(packed) == progress['sha256']
    archive = DOWNLOAD/'evidence-uncompressed.zip'
    if not archive.exists():
        with lzma.open(packed, 'rb') as source, archive.open('xb') as target:
            shutil.copyfileobj(source, target, 1024*1024)
    mappings = []
    with zipfile.ZipFile(archive) as source:
        assert source.testzip() is None
        for entry in source.infolist():
            name = Path(entry.filename)
            assert not name.is_absolute() and '..' not in name.parts
            if name.parts[:3] == ('experiments', 'akt', 'results'):
                assert name.parts[3] in ('gpu-boundary-t4-20261114-01', 'gpu-boundary-t4-20261114-02')
                target = ROOT/name
            else:
                assert name.parts[0] == 'runtime'
                target = ROOT/'experiments/akt/results/gpu-boundary-t4-transport-20261114-01'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            # Archive cũ được kiểm trước khi nhận, không ghi đè file đã tồn tại.
            digest = hashlib.sha256()
            with source.open(entry) as stream:
                if target.exists():
                    for chunk in iter(lambda: stream.read(1024*1024), b''):
                        digest.update(chunk)
                    assert sha(target) == digest.hexdigest()
                else:
                    with target.open('xb') as output:
                        for chunk in iter(lambda: stream.read(1024*1024), b''):
                            digest.update(chunk)
                            output.write(chunk)
            assert target.stat().st_size == entry.file_size
            assert sha(target) == digest.hexdigest()
            mappings.append(dict(remote_relative_path=entry.filename,
                                 local_path=target.relative_to(ROOT).as_posix(),
                                 bytes=entry.file_size, sha256=digest.hexdigest()))
    for run in ('gpu-boundary-t4-20261114-01', 'gpu-boundary-t4-20261114-02'):
        folder = ROOT/'experiments/akt/results'/run
        manifest = json.loads((folder/'OUTPUTS.json').read_text())
        for name, pin in manifest.items():
            assert (folder/name).stat().st_size == pin['bytes']
            assert sha(folder/name) == pin['sha256']
    receipt = dict(status='ALL_ARTIFACT_BYTES_VERIFIED', archive_sha256=progress['sha256'],
                   files=len(mappings), checkpoints=sum(row['local_path'].endswith('.pt') for row in mappings),
                   inventory=mappings)
    (HERE/'download-verification.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'inventory'}))


if __name__ == '__main__':
    main()
