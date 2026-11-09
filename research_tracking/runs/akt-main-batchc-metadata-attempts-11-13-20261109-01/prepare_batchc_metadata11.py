"""Chuẩn bị11 giữ nguyên warmup/caps, mọi lượt cũ giữ nguyên."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
pins = {
    'check_batchc_metadata10.py': '27305666a158bcc46d93bdc95822023e95408e9a0623f10111a79375a4320860',
    'run_batchc_metadata10.py': '5a12497d2904429a9405adaf22e4a45841f38103cb9d5e072ecdfb57927cc9e9',
    'batchc_metadata10_packet.json': '0a21f07f2fd318679b421251bcb0406fea26d5ce1b9f6531d63ee32099c7800b',
}
raw = {name: (PREP / name).read_bytes() for name in pins}
assert all(hashlib.sha256(raw[name]).hexdigest() == pin for name, pin in pins.items())
packet = json.loads(raw['batchc_metadata10_packet.json'])
prefix = PREP.relative_to(ROOT).as_posix() + '/'
outputs = {}
for name in ('check_batchc_metadata10.py', 'run_batchc_metadata10.py'):
    candidate = raw[name].decode('utf-8')
    for before, after in (('metadata10', 'metadata11'), ('collection10', 'collection11'),
                          ('tests10', 'tests11'), ('mcmc10', 'mcmc11'), ('mcmt10', 'mcmt11')):
        candidate = candidate.replace(before, after)
    new_name = name.replace('10', '11')
    outputs[new_name] = candidate.encode('utf-8')
    assert packet['source_pins'].pop(prefix + name) == pins[name]
    packet['source_pins'][prefix + new_name] = hashlib.sha256(outputs[new_name]).hexdigest()
packet['attempt11_review_vi'] = (
    'Nguồn warmup09 đã được quan sát thành công qua collection10. Tests10 giữ NO_GO RAM trước launch. '
    'Lượt11 giữ nguyên model source,221IDs,2GiB prelaunch,1536MiB floor/512MiB RSS và thời gian120s. '
    'Chỉ namespace đổi để bảo toàn10. Root kiểm kết quả collection11 trước tests11 và từng operation tự kiểm RAM mới. '
    'Không automatic retry hoặc giảm guard.')
outputs['batchc_metadata11_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
assert len(packet['source_pins']) == 36 and len(packet['runtime_pins']) == 11
for name, content in outputs.items():
    assert not (PREP / name).exists()
    if name.endswith('.py'):
        compile(content, str(PREP / name), 'exec')
for name, content in outputs.items():
    with (PREP / name).open('xb') as stream:
        stream.write(content)
print(json.dumps(dict(status='PREPARED11_NOT_EXECUTED',
    hashes={name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()})))
