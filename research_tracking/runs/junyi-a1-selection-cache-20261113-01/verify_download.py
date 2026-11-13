"""Kiểm archive Modal đã tải D, giải nén chỉ file mới và giữ nguyên file cũ."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
LOGICAL = 'modal-junyi-a1-b128-h100-20261113-07'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', choices=('09',), required=True)
    args = parser.parse_args()
    execution = 'modal-junyi-a1-b128-h100-20261113-' + args.attempt
    native = ROOT / 'experiments/akt/results' / execution
    receipt = json.loads((native / 'receipt.json').read_text())
    guard = json.loads((native / 'app-budget-guard.json').read_text())
    assert guard['stop_acknowledged'] is True
    assert receipt['download_inventory_verified'] is True
    archive = native / 'artifacts.zip'
    assert sha(archive) == receipt['archive_sha256']
    assert archive.stat().st_size == receipt['archive_bytes']
    allowed = {LOGICAL, execution + '-driver', execution + '-operation'}
    extracted = []
    existing = []
    with zipfile.ZipFile(archive) as saved:
        inventory = json.loads(saved.read('SHA256.json'))
        assert set(saved.namelist()) == set(inventory) | {'SHA256.json'}
        # Kiểm mọi member trước khi ghi file nào.
        for name, pin in inventory.items():
            relative = PurePosixPath(name)
            assert relative.parts[:3] == ('experiments', 'akt', 'results')
            assert relative.parts[3] in allowed
            assert not relative.is_absolute() and '..' not in relative.parts
            assert ':' not in name and '\\' not in name
            with saved.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == pin['sha256']
            destination = ROOT / Path(*relative.parts)
            assert destination.resolve().is_relative_to(ROOT / 'experiments/akt/results')
            if destination.exists():
                assert destination.is_file() and sha(destination) == pin['sha256'], name
        for name, pin in inventory.items():
            destination = ROOT / Path(*PurePosixPath(name).parts)
            if destination.exists():
                existing.append(name)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with saved.open(name) as source, destination.open('xb') as target:
                while block := source.read(1024 * 1024):
                    target.write(block)
            assert sha(destination) == pin['sha256']
            extracted.append(name)
    result = {'status': 'PASS_ALL_ARTIFACTS_VERIFIED_ON_D', 'run_id': execution,
              'archive_sha256': receipt['archive_sha256'], 'archive_bytes': receipt['archive_bytes'],
              'new_files': extracted, 'unchanged_existing_files': existing,
              'app_stop_acknowledged': True}
    (HERE / ('archive-extraction' + args.attempt + '.json')).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'new_files': len(extracted), 'existing_files': len(existing)}))


if __name__ == '__main__':
    main()
