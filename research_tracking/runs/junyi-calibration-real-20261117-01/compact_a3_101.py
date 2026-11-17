"""Compact A3 đã audit và sao lưu Drive, kiểm toàn record-stream trước fit."""
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
VOLUME=ROOT/'artifacts/akt/local-calibration/20261117'
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(1,str(ROOT/'scripts/akt'))
from local_calibration_compact import compact_raw_export


def main():
    source=VOLUME/'junyi-calibration-real-20261117-01/a3-raw-freecpu-a3-101/payloads'
    accepted=json.loads((BUNDLE/'LOCAL_A3_RAW_ACCEPTANCE101.json').read_text())
    assert accepted['status']=='LOCAL_RAW_AUDIT_COMPLETE_DRIVE_VERIFIED'
    pin=next(row for row in accepted['result']['publish_receipt']['files'] if row['path']=='RAW_EXPORT.zip')
    with (source/'RAW_EXPORT.zip').open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==pin['sha256']
    with zipfile.ZipFile(source/'RAW_EXPORT.zip') as archive:
        inventory=json.loads(archive.read('INVENTORY.json'))
    started=time.monotonic()
    result=compact_raw_export(source/'raw',VOLUME/'a3-compact101',
        expected_manifest_sha256=inventory['manifest.json']['sha256'],
        shard_sha256={name:row['sha256'] for name,row in inventory.items() if name!='manifest.json'})
    assert result['rows']==1621484 and result['original_shards']==15847 and result['compacted_shards']==50
    result['wall_seconds']=time.monotonic()-started
    result['original_archive_drive_file_id']=pin['file_id']
    result['original_archive_sha256']=pin['sha256']
    (BUNDLE/'COMPACT_A3_FULL_PARITY101.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FULL_A3_COMPACT_EXACT_STREAM_VERIFIED',result['rows'],result['compacted_shards'],flush=True)


if __name__=='__main__':main()
