"""Root áp profile metadata128/minfree1024V2 đã review, chưa chạy tests."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
review = PREP / 'BATCHC_METADATA_RESOURCE_PROFILE14_REVIEW01.md'
assert hashlib.sha256(review.read_bytes()).hexdigest() == 'f00431adbb9e66d6ce5af81efdd041805af871918453c18a868db5b632bf43b0'
pins = {
    'check_batchc_metadata13.py': '8169c83ad32e75df4aa4ce5b2b60e11eaff685d829a89b01d103857ab32fa7b0',
    'run_batchc_metadata13.py': '32d7bc270e596f57db9c0ce1dfc6ce474069979ed842a990ca9ec6b0be2e4d26',
    'batchc_metadata13_packet.json': 'b5876d55682b9a9821437e1d5ab21bcde517e533d910fe215a4e4902124a1b18',
}
raw = {name: (PREP / name).read_bytes() for name in pins}
assert all(hashlib.sha256(raw[name]).hexdigest() == pin for name, pin in pins.items())
packet = json.loads(raw['batchc_metadata13_packet.json'])
prefix = PREP.relative_to(ROOT).as_posix() + '/'
outputs = {}
for name in ('check_batchc_metadata13.py', 'run_batchc_metadata13.py'):
    text = raw[name].decode('utf-8')
    for before, after in (('metadata13', 'metadata14'), ('collection13', 'collection14'),
                          ('tests13', 'tests14'), ('mcmc13', 'mcmc14'), ('mcmt13', 'mcmt14')):
        text = text.replace(before, after)
    assert text.count('1536*1024**2') == 1 and text.count('128*1024**2') == 1
    text = text.replace('1536*1024**2', '1024*1024**2')
    if name.startswith('run_'):
        assert text.count('prelaunch_floor=1664*1024**2') == 1
        text = text.replace('prelaunch_floor=1664*1024**2', 'prelaunch_floor=1280*1024**2')
    new_name = name.replace('13', '14')
    outputs[new_name] = text.encode('utf-8')
    assert packet['source_pins'].pop(prefix + name) == pins[name]
    packet['source_pins'][prefix + new_name] = hashlib.sha256(outputs[new_name]).hexdigest()
assert packet['resource_profile']['max_worker_rss_bytes'] == 128*1024**2
packet['resource_profile'].update(minimum_available_ram_bytes=1024*1024**2,
    prelaunch_minimum_available_ram_bytes=1280*1024**2,
    profile='METADATA128_MINFREE1024_V2_ROOT_REVIEWED')
packet['resource_adoption14_vi'] = (
    'Root chọn profile mới sau independentreviewf00431ad cho đúng221metadata/mockcases. '
    'Floor thực giảm1536→1024MiB; admission1280MiB gồm1024floor+128worker+128launcher margin. '
    'Giới hạn worker128MiB vẫn là điều kiện từ chối. Review nguồn không chứng nhận trước footprint221PASS. '
    'Không đổi assertions, population, source model, runtime hoặc import/process guards. '
    'Mỗi operation kiểm RAM thực, giữ oldNO_GO theo policy cũ. Vi phạm phảiREJECT, giữraw, không tựwiden/retry. '
    'Đo theo cooperative hooks/Windows high-water, không hardOS/family memory quota. '
    'Profile này không cấp quyền native model/checkpoint/GPU hoặc researchfit.')
packet['resource_review14'] = dict(path=review.relative_to(ROOT).as_posix(),
    sha256=hashlib.sha256(review.read_bytes()).hexdigest())
outputs['batchc_metadata14_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
assert len(packet['source_pins']) == 36 and len(packet['runtime_pins']) == 11 and len(packet['expected_nodeids']) == 221
for name, content in outputs.items():
    assert not (PREP / name).exists()
    if name.endswith('.py'):
        compile(content, str(PREP / name), 'exec')
for name, content in outputs.items():
    with (PREP / name).open('xb') as stream:
        stream.write(content)
print(json.dumps(dict(status='PREPARED_METADATA14_V2_NOT_EXECUTED',
    hashes={name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()})))
