"""Bổ sung cache thật platform.platform trong cùng bootstrap Windows đã giới hạn."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
old = {
    'check_batchc_metadata08.py': '6b81a431727208841fb1dd9257aae9866d09adea38648bbfa6a1596526efc292',
    'run_batchc_metadata08.py': '4c967369a8c66d621453a0b728e56f36000868bcf105b13e12601ac34860ad79',
    'batchc_metadata08_packet.json': 'ae777054795a5718fe1f242d84a7bb00df98c256fab0130b9c3c5de510672e18',
    'prediction_mastery_trace_worker03.py': 'fc067d67ebc9018722aa66367fc186fe4a10e0f0b112475372f8024d4d74d631',
}
raws = {name: (PREP / name).read_bytes() for name in old}
assert all(hashlib.sha256(raws[name]).hexdigest() == pin for name, pin in old.items())
helper = raws['prediction_mastery_trace_worker03.py'].decode('utf-8')
old_api = "public_apis=['platform.uname','platform.processor']"
assert helper.count(old_api) == 1
helper = helper.replace(old_api, "public_apis=['platform.uname','platform.processor','platform.platform']")
marker = "        processor = platform.processor(); check()"
assert helper.count(marker) == 1
helper = helper.replace(marker, marker + "\n        platform_text = platform.platform(); check()\n"
    "        need(type(platform_text) is str and 0 < len(platform_text) <= 2048, 'bounded real platform string')\n"
    "        receipt['platform_text'] = platform_text")
marker = "    need(receipt['uname_cache_identity_reused'] is True and receipt['processor_repeat_equal'] is True, 'actual warmed metadata reuse')"
assert helper.count(marker) == 1
helper = helper.replace(marker,
    "    receipt['platform_cache_after_close_equal'] = platform.platform() == platform_text\n"
    "    require_metadata_closed(receipt)\n" + marker + "\n"
    "    need(receipt['platform_cache_after_close_equal'] is True, 'real platform cache reusable after closing metadata phase')")
new_files = {'windows_metadata_platform09.py': helper.encode('utf-8')}
packet = json.loads(raws['batchc_metadata08_packet.json'])
prefix = PREP.relative_to(ROOT).as_posix() + '/'
for old_name in ('check_batchc_metadata08.py', 'run_batchc_metadata08.py'):
    text = raws[old_name].decode('utf-8')
    for before, after in (('metadata08', 'metadata09'), ('collection08', 'collection09'),
                          ('tests08', 'tests09'), ('mcmc08', 'mcmc09'), ('mcmt08', 'mcmt09')):
        text = text.replace(before, after)
    name = old_name.replace('08', '09')
    new_files[name] = text.encode('utf-8')
    assert packet['source_pins'].pop(prefix + old_name) == old[old_name]
    packet['source_pins'][prefix + name] = hashlib.sha256(new_files[name]).hexdigest()
old_helper = prefix + 'prediction_mastery_trace_worker03.py'
assert packet['metadata_helper'] == old_helper
assert packet['source_pins'].pop(old_helper) == old['prediction_mastery_trace_worker03.py']
packet['metadata_helper'] = prefix + 'windows_metadata_platform09.py'
packet['source_pins'][packet['metadata_helper']] = hashlib.sha256(new_files['windows_metadata_platform09.py']).hexdigest()
packet['metadata_review_vi'] = ('JUnit08 có53failures cùng chuỗi inspect_runtime→platform.platform→win32_ver→_syscmd_ver→NUL. '
    'Derivative helper giữ nguyên whitelist literal cmd/c ver≤3 và đóng phase trước tests. '
    'Bổ sung gọi API thật platform.platform trong cùng bootstrap, sau đó kiểm cache được dùng lại khi phase đã đóng. '
    'Không cho subprocess/network sau metadata, không fake OS, sửa test hoặc thay source mô hình.')
new_files['batchc_metadata09_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
assert len(packet['source_pins']) == 36 and len(packet['runtime_pins']) == 11
for name, raw in new_files.items():
    assert not (PREP / name).exists()
    if name.endswith('.py'):
        compile(raw, str(PREP / name), 'exec')
for name, raw in new_files.items():
    with (PREP / name).open('xb') as stream:
        stream.write(raw)
print(json.dumps(dict(status='PREPARED09_NOT_EXECUTED',
    hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in new_files.items()})))
