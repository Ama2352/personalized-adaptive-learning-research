"""Bổ sung đúng lock được runtime probe đọc; giữ quần thể221 và profile14."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
pins = {
    'check_batchc_metadata14.py': '3ffd0c32a758af5fb99dd6120c1883cb94ec659fa7cce394bc292a16e0c32d30',
    'run_batchc_metadata14.py': '1890f5c0d8bda6cfce36714c18ce55b1043837b0d14eee567c44685896fb14f4',
    'batchc_metadata14_packet.json': '0657219e8909d965aea5eeb943268951513413b849fc0f3bb773ee44afcf7f52',
}
raw = {name: (PREP / name).read_bytes() for name in pins}
assert all(hashlib.sha256(raw[name]).hexdigest() == pin for name, pin in pins.items())
failed = json.loads((PREP / 'batchc-metadata-tests14/result.json').read_bytes())
assert failed['counts'] == dict(tests=221, failures=1, errors=0, skipped=0)
assert failed['test_body_entries'] == 221 and len(failed['denied']) == 1
assert Path(failed['denied'][0]['details']['resolved_path']) == ROOT / 'requirements-akt.lock.txt'
lock = ROOT / 'requirements-akt.lock.txt'
lock_pin = '3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a'
assert hashlib.sha256(lock.read_bytes()).hexdigest() == lock_pin
packet = json.loads(raw['batchc_metadata14_packet.json'])
prefix = PREP.relative_to(ROOT).as_posix() + '/'
outputs = {}
for name in ('check_batchc_metadata14.py', 'run_batchc_metadata14.py'):
    text = raw[name].decode('utf-8')
    for before, after in (('metadata14', 'metadata15'), ('collection14', 'collection15'),
                          ('tests14', 'tests15'), ('mcmc14', 'mcmc15'), ('mcmt14', 'mcmt15')):
        text = text.replace(before, after)
    new_name = name.replace('14', '15')
    outputs[new_name] = text.encode('utf-8')
    assert packet['source_pins'].pop(prefix + name) == pins[name]
    packet['source_pins'][prefix + new_name] = hashlib.sha256(outputs[new_name]).hexdigest()
assert 'requirements-akt.lock.txt' not in packet['source_pins']
packet['source_pins']['requirements-akt.lock.txt'] = lock_pin
packet['dependency_review15_vi'] = (
    'Actual14 chạy đủ221bodies,220PASS/1FAIL. Denial duy nhất là read requirements-akt.lock.txt '
    'từ test_probe_does_not_write_bytecode_into_upstream_checkout→inspect_runtime:134→sha256_file. '
    'Root đọc runtime probe/test/lock và thêm đúng readonly byteSHA3e721fdb. '
    'Không allowlist cả root, cài package, đổi assertion/source mô hình hoặc bỏ testcase. '
    'Profile14 và toàn221IDs giữ theo hợp đồng; phải recollect và chạy đủ221 trong namespace15 riêng.')
packet['failure14_reference'] = dict(path='artifacts/akt/local-tests/akt-research-runner-20261108-01/batchc-metadata-tests14/result.json',
    sha256=hashlib.sha256((PREP / 'batchc-metadata-tests14/result.json').read_bytes()).hexdigest())
outputs['batchc_metadata15_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
assert len(packet['source_pins']) == 37 and len(packet['runtime_pins']) == 11
for name, content in outputs.items():
    assert not (PREP / name).exists()
    if name.endswith('.py'):
        compile(content, str(PREP / name), 'exec')
for name, content in outputs.items():
    with (PREP / name).open('xb') as stream:
        stream.write(content)
print(json.dumps(dict(status='PREPARED15_ONE_EXACT_LOCK_INPUT_NOT_EXECUTED',
    hashes={name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()})))
