"""Nén snapshot A3 đã kiểm để chuyển nguồn GPU, chưa upload hoặc training."""
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    snapshot = ROOT / 'artifacts/akt/staged/junyi-a3-refit-short-20261115-01'
    checked = json.loads((snapshot / 'CPU_CHECK.json').read_text())
    assert checked['status'] == 'PASS_LOCAL_STAGE_INPUTS'
    inventory = json.loads((snapshot / 'INPUTS.json').read_text())
    archive = ROOT / 'artifacts/akt/staged-archives/junyi-a3-refit-short-20261115-01.zip'
    started = time.monotonic()
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as saved:
        for name in sorted(inventory['files']):
            saved.write(snapshot / 'project' / name, 'project/' + name)
        for name in ('INPUTS.json', 'CPU_CHECK.json'):
            saved.write(snapshot / name, name)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        assert len(saved.namelist()) == len(inventory['files']) + 2
    result = dict(status='LOCAL_PORTABLE_SOURCE_ARCHIVE_VERIFIED',
        archive=archive.relative_to(ROOT).as_posix(), bytes=archive.stat().st_size,
        sha256=digest, source_snapshot=snapshot.relative_to(ROOT).as_posix(),
        members=len(inventory['files'])+2, seconds=time.monotonic()-started,
        uploaded=False, limits_vi='Chỉ đóng gói local. Không chứa token hoặc checkpoint. Khi chuyển sang máy đích phải kiểm SHA archive và từng member theo INPUTS trước khi chạy.')
    with (HERE / 'a3-portable-source01.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
