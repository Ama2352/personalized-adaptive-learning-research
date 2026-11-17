"""Giữ lỗi Windows A3 và dựng snapshot chỉ gồm shard đã commit."""
import hashlib
import json
from pathlib import Path
import shutil
import psutil

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
VOLUME=ROOT/'artifacts/akt/local-calibration/20261117'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    for process in psutil.process_iter(['name','cmdline']):
        command=process.info['cmdline'] or []
        if any('local_calibration_migration.py' in value for value in command) and 'A3' in command:
            raise RuntimeError('A3 writer still present')
    source=VOLUME/'junyi-calibration-real-20261117-01/a3-raw-freecpu-a3-100/payloads/raw'
    manifest=json.loads((source/'manifest.json').read_text())
    assert manifest['status']=='incomplete'
    names={'manifest.json',*(row['path'] for row in manifest['shards'])}
    inventory={path.name:dict(bytes=path.stat().st_size,sha256=sha(path))
        for path in source.iterdir() if path.is_file()}
    assert names.issubset(inventory) and all(Path(name).name==name for name in names)
    destination=VOLUME/'a3-partial-snapshot-100'
    destination.mkdir(exist_ok=True)
    for name in sorted(names):
        target=destination/name
        if not target.exists():shutil.copyfile(source/name,target)
        assert sha(target)==inventory[name]['sha256']
    marker=VOLUME/'A3_WRITER_STOPPED_100.json'
    marker.write_text(json.dumps(dict(status='LOCAL_CPU_WRITER_STOPPED',local_process_absent=True,
        raw_manifest_sha256=sha(source/'manifest.json'),failure_log_sha256=sha(BUNDLE/'local-a3-join100.txt')),indent=2)+'\n')
    descriptor=dict(path=str(destination),manifest_sha256=sha(source/'manifest.json'),
        files={name:inventory[name] for name in names},writer_stop_receipt=dict(path=str(marker),sha256=sha(marker)))
    (VOLUME/'A3_SNAPSHOT_100.json').write_text(json.dumps(descriptor,indent=2)+'\n')
    receipt=dict(status='FAILED_A3_LOCAL_WRITER_CLOSED_SNAPSHOT_VERIFIED',prediction_rows=manifest['prediction_rows'],
        completed_learners=len(manifest['completed_users']),all_source_files=inventory,
        preserved_unlisted_files=sorted(set(inventory)-names),snapshot_descriptor_sha256=sha(VOLUME/'A3_SNAPSHOT_100.json'),
        source_manifest_sha256=sha(source/'manifest.json'),original_files_deleted=False)
    (BUNDLE/'LOCAL_A3_RECOVERY100.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('A3_SNAPSHOT_VERIFIED',manifest['prediction_rows'],len(names),flush=True)


if __name__=='__main__':main()
