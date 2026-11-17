"""Khôi phục snapshot A2 bất biến trong cache local đã được duyệt."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
VOLUME = ROOT / 'artifacts/akt/local-calibration/20261117'
sys.path.insert(0, str(ROOT / 'scripts/akt'))
from free_cpu_calibration import download


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import AuthorizedSession
    pin = json.loads((BUNDLE / 'A2_PARTIAL_RAW_DRIVE01.json').read_text())
    target = VOLUME / 'incoming/A2_RAW_PARTIAL.zip'
    with AuthorizedSession(Credentials.from_authorized_user_file(str(
            ROOT / 'artifacts/akt/private/colab-session/drive-controller-credentials.json'))) as session:
        download(session, pin, target)
    destination = VOLUME / 'a2-partial-snapshot'
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(target) as archive:
        inventory = json.loads(archive.read('INVENTORY.json'))
        print('INVENTORY_TYPE', type(inventory).__name__, flush=True)
        assert set(archive.namelist()) == {'INVENTORY.json', *('raw/' + name for name in inventory)}
        for name, member in inventory.items():
            assert Path(name).name == name
            data = archive.read('raw/' + name)
            assert len(data) == member['bytes'] and hashlib.sha256(data).hexdigest() == member['sha256']
            path = destination / name
            if path.exists():
                assert sha(path) == member['sha256']
            else:
                path.write_bytes(data)
    assert sha(destination / 'manifest.json') == pin['raw_manifest_sha256']
    stop = json.loads((BUNDLE / 'COLAB_LOCAL_MIGRATION_STOP01.json').read_text())
    release = json.loads((BUNDLE / 'COLAB_RELEASE_AFTER_MIGRATION01.json').read_text())
    assert stop['writer_stopped_verified'] and release['owned_endpoint_absent']
    marker = VOLUME / 'A2_WRITER_STOPPED.json'
    marker.write_text(json.dumps(dict(status='COLAB_CPU_WRITER_STOPPED', remote_process_absent=True,
        raw_manifest_sha256=pin['raw_manifest_sha256'], source_stop_receipt_sha256=sha(
        BUNDLE / 'COLAB_LOCAL_MIGRATION_STOP01.json'), release_receipt_sha256=sha(
        BUNDLE / 'COLAB_RELEASE_AFTER_MIGRATION01.json')), indent=2) + '\n')
    descriptor = dict(path=str(destination), manifest_sha256=pin['raw_manifest_sha256'], files=inventory,
        writer_stop_receipt=dict(path=str(marker), sha256=sha(marker)))
    (VOLUME / 'A2_SNAPSHOT.json').write_text(json.dumps(descriptor, indent=2) + '\n')
    total = sum(path.stat().st_size for path in VOLUME.rglob('*') if path.is_file())
    assert total < 4_000_000_000
    receipt = dict(status='LOCAL_A2_PARTIAL_SNAPSHOT_VERIFIED', files=len(inventory),
        archive_sha256=sha(target), snapshot_descriptor=str(VOLUME / 'A2_SNAPSHOT.json'),
        snapshot_sha256=sha(VOLUME / 'A2_SNAPSHOT.json'), cache_bytes=total)
    (BUNDLE / 'LOCAL_A2_SNAPSHOT01.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
