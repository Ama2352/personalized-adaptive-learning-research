"""Phiên metadata128MiB có review riêng, giữ floor và toàn bộ221ca."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
review = PREP / 'BATCHC_METADATA_RESOURCE_PROFILE12_REVIEW01.md'
assert hashlib.sha256(review.read_bytes()).hexdigest() == '304287c010ba2c6279a702583f71a104c73d40f2f7a6fe412c2d37d1378c2f18'
old = {
    'check_batchc_metadata11.py': '24295b4035558f39d51556d62108414558a224200e6b80472f4633f20f054bc5',
    'run_batchc_metadata11.py': '272592f8d5757549f6af82b1f708b0f5304ca985b2e7cd058330ad0ee0319851',
    'batchc_metadata11_packet.json': '4580a6c87bc482a98be6fb17517fa3fc4be5c8a7c291ca311215ef1ac25b9ec5',
}
raw = {name: (PREP / name).read_bytes() for name in old}
assert all(hashlib.sha256(raw[name]).hexdigest() == pin for name, pin in old.items())
observed_path = PREP / 'batchc-metadata-tests08/result.json'
observed_raw = observed_path.read_bytes()
assert hashlib.sha256(observed_raw).hexdigest() == '2158794a5d6a74dd1461f8d7c05da8dd52133a0f227bbd348600e2aeba46c6a8'
observed = json.loads(observed_raw)
assert observed['test_body_entries'] == 221 and observed['counts']['failures'] == 53
assert observed['resources']['observed_peak_rss_bytes'] == 64675840
packet = json.loads(raw['batchc_metadata11_packet.json'])
prefix = PREP.relative_to(ROOT).as_posix() + '/'
outputs = {}
for name in ('check_batchc_metadata11.py', 'run_batchc_metadata11.py'):
    text = raw[name].decode('utf-8')
    for before, after in (('metadata11', 'metadata12'), ('collection11', 'collection12'),
                          ('tests11', 'tests12'), ('mcmc11', 'mcmc12'), ('mcmt11', 'mcmt12')):
        text = text.replace(before, after)
    assert text.count('512*1024**2') == 1
    text = text.replace('512*1024**2', '128*1024**2')
    if name.startswith('run_'):
        assert text.count('prelaunch_floor=2048*1024**2') == 1
        text = text.replace('prelaunch_floor=2048*1024**2', 'prelaunch_floor=1664*1024**2')
    new_name = name.replace('11', '12')
    outputs[new_name] = text.encode('utf-8')
    assert packet['source_pins'].pop(prefix + name) == old[name]
    packet['source_pins'][prefix + new_name] = hashlib.sha256(outputs[new_name]).hexdigest()
packet['resource_profile'].update(max_worker_rss_bytes=128*1024**2,
    prelaunch_minimum_available_ram_bytes=1664*1024**2,
    profile='METADATA128_V1_ROOT_REVIEWED_ADMISSION_POLICY')
assert packet['resource_profile']['minimum_available_ram_bytes'] == 1536*1024**2
packet['resource_adoption12_vi'] = (
    'Root chọn phiên metadata128 sau independent review304287c0 và đo actual08 toàn221bodies/53FAIL với peak64675840B. '
    'Trần worker giảm512→128MiB, floorfree1536MiB và prelaunchreserve=1536+128=1664MiB. '
    'Đây là admission policy metadata mới, không sửa lịch sử NO_GO. Hook/highwater scope chưa là family/hardOS quota. '
    'Passing branches chưa được đo, vượt128 hoặc floor thì REJECT và giữ raw, không tự nâng cap/retry. '
    'Cùng221IDs/source/runtime/import/Job/clocks; không model/native/GPU proof hoặc nghiên cứu đổi phương pháp.')
packet['resource_review12'] = dict(path=review.relative_to(ROOT).as_posix(),
    sha256=hashlib.sha256(review.read_bytes()).hexdigest(),
    calibration_result=observed_path.relative_to(ROOT).as_posix(),
    calibration_result_sha256=hashlib.sha256(observed_raw).hexdigest())
outputs['batchc_metadata12_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
assert len(packet['source_pins']) == 36 and len(packet['runtime_pins']) == 11
for name, content in outputs.items():
    assert not (PREP / name).exists()
    if name.endswith('.py'):
        compile(content, str(PREP / name), 'exec')
for name, content in outputs.items():
    with (PREP / name).open('xb') as stream:
        stream.write(content)
print(json.dumps(dict(status='PREPARED12_METADATA128_NOT_EXECUTED',
    hashes={name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()})))
