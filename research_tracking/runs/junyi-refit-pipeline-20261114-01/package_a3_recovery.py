"""Gói source và checkpoint A3 đã kiểm cho một lần upload khi đổi nguồn GPU."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=int, required=True)
    args = parser.parse_args()
    checked = json.loads((HERE / f'a3-checkpoint-verified{args.attempt:02}.json').read_text())
    assert checked['status'] == 'PASS_A3_LOCAL_RECOVERY_CHECKPOINT'
    receipt_path = ROOT / checked['source_receipt']
    receipt = json.loads(receipt_path.read_text())
    source_pin = json.loads((HERE / 'a3-portable-source01.json').read_text())
    source_zip = ROOT / source_pin['archive']
    assert sha(source_zip) == source_pin['sha256']
    destination = ROOT / f'experiments/akt/results/model-export-a3-refit-recovery-20261115-{args.attempt:02}'
    destination.mkdir(parents=True, exist_ok=False)
    latest = 'outputs/' + checked['remote_checkpoint'][len('experiments/akt/results/'):]
    latest_folder = latest.rsplit('/', 1)[0]
    prefix = 'outputs/junyi-a3-refit-20261114-01/'
    entries = {}
    for name, pin in receipt['files'].items():
        if not name.startswith(prefix) or '/batch-recovery/' in name:
            continue
        if '/checkpoints/' in name:
            folder = name.rsplit('/', 1)[0]
            if folder != latest_folder and re.fullmatch(r'epoch-\d{3}', folder.split('/')[-1]) is None:
                continue
        source = receipt_path.parent / 'files' / name
        assert source.resolve().is_relative_to((receipt_path.parent / 'files').resolve())
        assert source.stat().st_size == pin['bytes'] and sha(source) == pin['sha256']
        entries['recovery/experiments/akt/results/' + name[len('outputs/'):]] = dict(source=source, pin=pin)
    assert 'recovery/' + checked['remote_checkpoint'] in entries
    archive = destination / 'COLAB_RESUME.zip'
    with zipfile.ZipFile(archive, 'x') as saved:
        saved.write(source_zip, 'SOURCE.zip', compress_type=zipfile.ZIP_STORED)
        for name, entry in entries.items():
            saved.write(entry['source'], name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        for name, entry in entries.items():
            with saved.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['pin']['sha256']
    index = dict(schema='a3-portable-refit-recovery-v1', status='RESUMABLE_PARTIAL_REFIT',
        archive=archive.name, archive_bytes=archive.stat().st_size, archive_sha256=sha(archive),
        source_zip_sha256=source_pin['sha256'], project_root='/opt/kltn',
        complete_epochs=checked['complete_epochs'], partial_epoch=checked['partial_epoch'],
        partial_optimizer_step=checked['partial_optimizer_step'], frozen_epochs=9,
        resume_checkpoint=checked['remote_checkpoint'], resume_sha256=checked['checkpoint_sha256'],
        entries={name: entry['pin'] for name, entry in entries.items()},
        source_receipt=checked['source_receipt'], next_device_verified=False,
        limits_vi='Giữ model/Adam/RNG/sampler và history. Còn học tiếp đến đủ9epoch. Phải kiểm source, runtime và thiết bị đích trước resume. Chưa upload hoặc chạy trên Colab.')
    (destination / 'RESUME_INDEX.json').write_text(json.dumps(index, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    text = f'# Checkpoint A3 để tiếp tục refit\n\nĐã học đủ {checked["complete_epochs"]}/9 epoch, đang ở epoch {checked["partial_epoch"]}, bước {checked["partial_optimizer_step"]}.\n\n`COLAB_RESUME.zip` chứa source/cache và checkpoint đã kiểm, cùng model, Adam, RNG và vị trí dữ liệu. `RESUME_INDEX.json` giữ SHA và đường dẫn phục hồi. Model refit cuối còn chờ hoàn tất 9 epoch.\n'
    (destination / 'README.md').write_text(text, encoding='utf-8')
    print(json.dumps(dict(status=index['status'], bundle=destination.relative_to(ROOT).as_posix(),
        bytes=index['archive_bytes'], sha256=index['archive_sha256']), ensure_ascii=False))


if __name__ == '__main__':
    main()
