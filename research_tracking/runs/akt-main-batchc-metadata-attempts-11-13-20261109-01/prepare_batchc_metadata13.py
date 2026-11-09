"""Namespace13 riêng, cùng metadata128 đã review; không tự chạy hoặc retry."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
pins = {
    'check_batchc_metadata12.py': '9bc908c3e90783b1596cc95ce6e551d15277c7061847347b008a8b12b1fb6713',
    'run_batchc_metadata12.py': 'e0498feded8d46956cec3fd40d9504b51aca8783cfe5fc85c901d58117a2e83b',
    'batchc_metadata12_packet.json': 'f0a954c55c1d798e8fd30bc9d99274dc18d2bb1a7c757ca17e87d5227773b630',
}
raw = {name: (PREP / name).read_bytes() for name in pins}
assert all(hashlib.sha256(raw[name]).hexdigest() == pin for name, pin in pins.items())
packet = json.loads(raw['batchc_metadata12_packet.json'])
prefix = PREP.relative_to(ROOT).as_posix() + '/'
outputs = {}
for name in ('check_batchc_metadata12.py', 'run_batchc_metadata12.py'):
    content = raw[name].decode('utf-8')
    for before, after in (('metadata12', 'metadata13'), ('collection12', 'collection13'),
                          ('tests12', 'tests13'), ('mcmc12', 'mcmc13'), ('mcmt12', 'mcmt13')):
        content = content.replace(before, after)
    new_name = name.replace('12', '13')
    outputs[new_name] = content.encode('utf-8')
    assert packet['source_pins'].pop(prefix + name) == pins[name]
    packet['source_pins'][prefix + new_name] = hashlib.sha256(outputs[new_name]).hexdigest()
packet['attempt13_review_vi'] = (
    '12tests NO_GO tại available1171968000B, không child. '
    '13 chỉ namespace mới sau điều kiện RAM mới, cùng128MiB/floor1536/admission1664 và221IDs. '
    'Root orchestration đọc và kiểm actual collection13 before tests13 trong cùng chuỗi bounded, tránh phụ thuộc observation cũ. '
    'Mỗi operation vẫn tự kiểm RAM mới; không vòng lặp tự retry, đổi cap hoặc model execution.')
outputs['batchc_metadata13_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
for name, content in outputs.items():
    assert not (PREP / name).exists()
    if name.endswith('.py'):
        compile(content, str(PREP / name), 'exec')
for name, content in outputs.items():
    with (PREP / name).open('xb') as stream:
        stream.write(content)
print(json.dumps({name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()}))
