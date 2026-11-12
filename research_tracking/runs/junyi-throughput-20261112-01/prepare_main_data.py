"""Đóng gói đúng TRAIN80/selection10 đã kiểm, phục vụ lượt selected tiếp theo."""
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
started = time.monotonic()
cache = ROOT/'artifacts/akt/window-cache/full-train80-20261112-02'
cohort = ROOT/'artifacts/akt/junyi-cohorts/outer4-selected-full-20261112-03'
manifest = json.loads((cache/'manifest.json').read_text())
cohort_manifest = json.loads((cohort/'manifest.json').read_text())
assert all(cohort_manifest[name] is False for name in
           ('calibration_events_included','outer_validation_events_included','holdout_events_included'))
paths = [cache/'manifest.json',cache/'COMPLETE.json',
         cache.with_suffix('.encoding.json'),cache.with_suffix('.encoding.receipt.json'),
         ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json',
         cohort/'manifest.json',cohort/'canonical.parquet',cohort/'assignments.parquet']
paths += [cache/entry['name'] for entry in manifest['shards']]
pins = {}
archive = ROOT/'artifacts/akt/modal/junyi-throughput-20261112-01/full-selected-data.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as saved:
    for path in paths:
        assert path.resolve().is_relative_to(ROOT/'artifacts/akt') and not path.is_symlink()
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream,'sha256').hexdigest()
        name = path.relative_to(ROOT).as_posix()
        pins[name] = dict(bytes=path.stat().st_size,sha256=digest)
        if path.suffix=='.npz':
            expected = manifest['shards'][int(path.stem.split('-')[1])]
            assert pins[name]['sha256']==expected['sha256'] and pins[name]['bytes']==expected['bytes']
        saved.write(path,name)
    saved.writestr('MANIFEST.json',json.dumps(dict(files=pins,scope='FULL_TRAIN80_SELECTION10_ONLY'),indent=2))
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream,'sha256').hexdigest()
result = dict(status='FULL_SELECTED_DATA_PACKET_PREPARED_NOT_UPLOADED',archive=archive.relative_to(ROOT).as_posix(),
    archive_sha256=digest,archive_bytes=archive.stat().st_size,files=pins,seconds=time.monotonic()-started,
    train_targets=13347331,selection_targets=1600343,calibration_events=False,
    outer_validation_events=False,holdout_events=False,training_performed=False)
(BUNDLE/'full-main-data-packet.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'}),flush=True)
