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
_files=['manifest.json']+[entry['path'] for entry in _manifest['shards']]
assert len(set(_files))==len(_files)
_inventory={}
for _name in _files:
    assert Path(_name).name==_name
    _path=_raw/_name
    assert not _path.is_symlink() and _path.is_file()
    with _path.open('rb') as _stream:
        _digest=hashlib.file_digest(_stream,'sha256').hexdigest()
    _inventory[_name]={'bytes':_path.stat().st_size,'sha256':_digest}
for _entry in _manifest['shards']:
    assert _inventory[_entry['path']]['sha256']==_entry['sha256']
assert sum(row['bytes'] for row in _inventory.values())<=2*1024**3
_archive=_tools/'A2_RAW_PARTIAL_MIGRATION01.zip'
assert not _archive.exists()
with zipfile.ZipFile(_archive,'x',compression=zipfile.ZIP_STORED) as _zip:
    _zip.writestr('INVENTORY.json',json.dumps(_inventory,sort_keys=True,separators=(',',':')))
    for _name in sorted(_inventory):
        _zip.write(_raw/_name,'raw/'+_name)
assert not Path('/proc/15696').exists()
with _archive.open('rb') as _stream:
    _archive_sha=hashlib.file_digest(_stream,'sha256').hexdigest()
_receipt={'status':'STOPPED_PARTIAL_RAW_ARCHIVED','writer_pid':15696,'writer_absent':True,
    'archive_path':str(_archive),'archive_bytes':_archive.stat().st_size,'archive_sha256':_archive_sha,
    'raw_manifest_sha256':_inventory['manifest.json']['sha256'],'raw_members':len(_inventory),
    'completed_learners':12439,'prediction_rows':1278474,'calibration_fit_complete':False}
(_tools/'A2_PARTIAL_RAW_MIGRATION_RECEIPT01.json').write_text(json.dumps(_receipt,indent=2)+'\n')
print(json.dumps(_receipt))
