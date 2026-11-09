"""Tạo lượt10 mới từ09 đã review, giữ nguyên floor/caps và quần thể221ca."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
pins = {
    'check_batchc_metadata09.py': '2df7c013e362339a18222be500759fa36a785c69bf7cda1c2278340aee3f7b5b',
    'run_batchc_metadata09.py': 'bdb258fb87e4a07ec1a40e5380be83b79a641daf5ab159a695a75d58574bc229',
    'batchc_metadata09_packet.json': '8864e4b78d7ce02a5dab2950623b479e0b598c329266802bde98ba905c8246d9',
    'windows_metadata_platform09.py': '2f137875cf3e18eabf94b66fab1d8a3e2502f9ed45a7f791e21883f2831ec560',
}
raw = {name: (PREP / name).read_bytes() for name in pins}
assert all(hashlib.sha256(raw[name]).hexdigest() == pin for name, pin in pins.items())
packet = json.loads(raw['batchc_metadata09_packet.json'])
prefix = PREP.relative_to(ROOT).as_posix() + '/'
outputs = {}
for name in ('check_batchc_metadata09.py', 'run_batchc_metadata09.py'):
    candidate = raw[name].decode('utf-8')
    for before, after in (('metadata09', 'metadata10'), ('collection09', 'collection10'),
                          ('tests09', 'tests10'), ('mcmc09', 'mcmc10'), ('mcmt09', 'mcmt10')):
        candidate = candidate.replace(before, after)
    new_name = name.replace('09', '10')
    outputs[new_name] = candidate.encode('utf-8')
    assert packet['source_pins'].pop(prefix + name) == pins[name]
    packet['source_pins'][prefix + new_name] = hashlib.sha256(outputs[new_name]).hexdigest()
packet['attempt10_review_vi'] = (
    '09 giữ nguyên NO_GO trước child. Root đo RAM mới2536251392B trên ngưỡng2GiB. '
    'Lượt10 chỉ đổi tên output/basetemp/worker để giữ09 immutable. '
    'Giữ warmup platform thật09, nguồn mô hình,221IDs, floors và caps. '
    'Outer vẫn tự kiểm RAM thực trước GO, không tự retry hoặc hạ guard.')
outputs['batchc_metadata10_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
assert len(packet['source_pins']) == 36 and len(packet['runtime_pins']) == 11
for name, content in outputs.items():
    assert not (PREP / name).exists()
    if name.endswith('.py'):
        compile(content, str(PREP / name), 'exec')
for name, content in outputs.items():
    with (PREP / name).open('xb') as stream:
        stream.write(content)
print(json.dumps(dict(status='PREPARED10_NOT_EXECUTED',
    hashes={name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()})))
