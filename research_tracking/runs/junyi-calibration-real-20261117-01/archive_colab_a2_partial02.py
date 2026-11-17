"""Đóng gói raw A2 đã dừng để tiếp tục trên CPU local, giữ nguyên từng byte."""
from pathlib import Path
import hashlib
import json
import os
import zipfile

_raw=Path('/__modal/volumes/vo-dv1975utRQbmagCjA0brSe/junyi-calibration-real-20261117-01/a2-raw-freecpu-a2-001/payloads/raw')
_tools=Path('/content/kltn-free-cpu-tools')
assert not Path('/proc/15696').exists() and _raw.resolve()==_raw
_manifest=json.loads((_raw/'manifest.json').read_text())
assert _manifest['status']=='incomplete' and _manifest['prediction_rows']==1278474
assert len(_manifest['completed_users'])==12439 and len(_manifest['shards'])==12439
def inventory_raw(root, manifest):
    names=['manifest.json']+[entry['path'] for entry in manifest['shards']]
    if len(set(names))!=len(names):
        raise ValueError('Duplicate raw shard path')
    inventory={}
    for name in names:
        if Path(name).name!=name:
            raise ValueError('Raw shard basename required')
        path=root/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>64*1024**2:
            raise ValueError('Bounded physical raw file required')
        with path.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        inventory[name]={'bytes':path.stat().st_size,'sha256':digest}
    for entry in manifest['shards']:
        expected=entry.get('sha256')
        if expected is not None and expected!=inventory[entry['path']]['sha256']:
            raise ValueError('Raw shard SHA mismatch')
    if sum(row['bytes'] for row in inventory.values())>2*1024**3:
        raise ValueError('Raw archive byte limit')
    return inventory

_inventory=inventory_raw(_raw,_manifest)
_archive=_tools/'A2_RAW_PARTIAL_MIGRATION02.zip'
assert not _archive.exists()
with zipfile.ZipFile(_archive,'x',compression=zipfile.ZIP_STORED) as _zip:
    _zip.writestr('INVENTORY.json',json.dumps(_inventory,sort_keys=True,separators=(',',':')))
    for _name in sorted(_inventory):
        _zip.write(_raw/_name,'raw/'+_name)
with zipfile.ZipFile(_archive) as _checked:
    for _name,_pin in _inventory.items():
        with _checked.open('raw/'+_name) as _stream:
            assert hashlib.file_digest(_stream,'sha256').hexdigest()==_pin['sha256']
assert not Path('/proc/15696').exists()
with _archive.open('rb') as _stream:
    _archive_sha=hashlib.file_digest(_stream,'sha256').hexdigest()
_receipt={'status':'STOPPED_PARTIAL_RAW_ARCHIVED','writer_pid':15696,'writer_absent':True,
    'archive_path':str(_archive),'archive_bytes':_archive.stat().st_size,'archive_sha256':_archive_sha,
    'raw_manifest_sha256':_inventory['manifest.json']['sha256'],'raw_members':len(_inventory),
    'completed_learners':12439,'prediction_rows':1278474,'calibration_fit_complete':False}
(_tools/'A2_PARTIAL_RAW_MIGRATION_RECEIPT02.json').write_text(json.dumps(_receipt,indent=2)+'\n')
print(json.dumps(_receipt))
