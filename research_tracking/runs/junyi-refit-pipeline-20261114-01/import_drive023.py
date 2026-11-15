"""Nhập bản sao Drive023, giữ manifest gốc và kiểm từng file trước resume."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    source = next((ROOT / 'artifacts/akt/colab').glob('*023*.zip'))
    source_sha = digest(source.read_bytes())
    pointer = json.loads((ROOT / 'artifacts/akt/colab/LATEST_FROM_DRIVE.json').read_text())
    output = ROOT / 'experiments/akt/results/colab-junyi-a3-refit-20261115-023-import'
    output.mkdir(exist_ok=True)
    assert not (output / 'COMPLETE.json').exists(), 'Bundle đã nghiệm thu'
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        manifest_name = next(name for name in names if name.endswith('/BACKUP_COMPLETE.json'))
        raw = archive.read(manifest_name)
        assert digest(raw) == pointer['sha256']
        manifest = json.loads(raw)
        assert manifest['status'] == 'PASS_DRIVE_CHECKPOINT_BACKUP'
        assert manifest['execution_id'] == 'colab-junyi-a3-refit-20261115-023'
        (output / 'DRIVE_BACKUP_COMPLETE.json').write_bytes(raw)
        prefix = manifest['execution_id'] + '/files/'
        files = {}
        missing = []
        for name, pin in manifest['files'].items():
            relative = PurePosixPath(name)
            assert not relative.is_absolute() and '..' not in relative.parts and ':' not in name and '\\' not in name
            assert name.startswith('experiments/akt/results/')
            member = prefix + name
            if member not in names:
                assert pin['drive_relative'].startswith('completed/')
                missing.append(name)
                continue
            raw = archive.read(member)
            assert len(raw) == pin['bytes'] and digest(raw) == pin['sha256']
            key = 'outputs/' + name.removeprefix('experiments/akt/results/')
            path = output / 'files' / key
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                assert path.stat().st_size == pin['bytes'] and digest(path.read_bytes()) == pin['sha256']
            else:
                path.write_bytes(raw)
            files[key] = dict(bytes=pin['bytes'], sha256=pin['sha256'])
        key = 'outputs/' + manifest['checkpoint'].removeprefix('experiments/akt/results/')
        assert key in files and files[key]['sha256'] == manifest['checkpoint_sha256']
        folder = (output / 'files' / key).parent
        metadata = json.loads((folder / 'metadata.json').read_text())
        marker = json.loads((folder / 'COMPLETE.json').read_text())
        assert digest((folder / 'metadata.json').read_bytes()) == marker['metadata_sha256']
        assert metadata['checkpoint_sha256'] == marker['checkpoint_sha256'] == manifest['checkpoint_sha256']
        logical = output / 'files/outputs/junyi-a3-refit-20261114-01'
        run_manifest = json.loads((logical / 'run-manifest.json').read_text())
        assert metadata['identity'] == run_manifest
        receipt = dict(status='PARTIAL_JUNYI_REFIT90', files=files,
                       source='IMPORTED_IMMUTABLE_DRIVE_TRANCHE', original_manifest_sha256=pointer['sha256'],
                       complete_epochs=manifest['complete_epochs'], partial_epoch=manifest['partial_epoch'],
                       partial_optimizer_step=manifest['partial_optimizer_step'])
        (output / 'remote-inventory.json').write_text(json.dumps(receipt, indent=2) + '\n')
        proof = dict(status='LOCAL_IMPORTED_CHECKPOINT_VERIFIED', files=len(files),
                     source_zip=source.relative_to(ROOT).as_posix(), source_sha256=source_sha,
                     checkpoint=manifest['checkpoint'], checkpoint_sha256=manifest['checkpoint_sha256'],
                     complete_epochs=manifest['complete_epochs'], partial_epoch=manifest['partial_epoch'],
                     partial_optimizer_step=manifest['partial_optimizer_step'], frozen_epochs=manifest['frozen_epochs'],
                     missing_historical_files_on_drive=missing, identity_matches_manifest=True,
                     gpu_stop_claimed=False, output=output.relative_to(ROOT).as_posix())
        assert digest(source.read_bytes()) == source_sha
        (output / 'COMPLETE.json').write_text(json.dumps(proof, indent=2) + '\n')
        with (HERE / 'a3-drive023-import-proof.json').open('x', encoding='utf-8') as stream:
            json.dump(proof, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps(proof, ensure_ascii=False))


if __name__ == '__main__':
    main()
