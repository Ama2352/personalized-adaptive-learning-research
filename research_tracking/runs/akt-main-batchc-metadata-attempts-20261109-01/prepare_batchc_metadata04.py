"""Tạo harness04 với ngoại lệ đọc stdin NUL của Pytest đã quan sát."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
pins = {
    'check_batchc_metadata03.py': '83d2f34eb8fefa96efbef5ccbd42541a568e9dad64492fef4cc1983e0803e332',
    'run_batchc_metadata03.py': 'c58211a5e86988a8dbdb2b30a71e9e69c234af9f6f8b6105280ac4122b623552',
    'batchc_metadata03_packet.json': 'b16abb885d5dd0f3e501c864b409bc276abc901dd662f9e2b9aca7cc6b3f50fe',
}
sources = {}
for name, pin in pins.items():
    raw = (PREP / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin
    sources[name] = raw
actual = json.loads((PREP / 'batchc-metadata-collection03/result.json').read_bytes())
denial = actual['denied'][0]
assert denial['details'] == dict(raw_path='nul', resolved_path=str(ROOT / 'nul'), mode='r', flags=32896)
assert denial['caller_frames'][1]['file'] == str(ROOT / '.venv/Lib/site-packages/_pytest/capture.py')
assert denial['caller_frames'][1]['function'] == '__init__' and denial['caller_frames'][1]['line'] == 489
capture = ROOT / '.venv/Lib/site-packages/_pytest/capture.py'
capture_sha = hashlib.sha256(capture.read_bytes()).hexdigest()
assert capture_sha == '12004dbff0ab7b34141ff53e33e616db2e857c695f64e640631f5abe30619145'
worker = sources['check_batchc_metadata03.py'].decode('utf-8').replace('metadata03', 'metadata04').replace('collection03', 'collection04').replace('tests03', 'tests04').replace('mcmc03', 'mcmc04').replace('mcmt03', 'mcmt04')
old = 'null_count=[0];import_breadcrumbs=[]'
assert worker.count(old) == 1
worker = worker.replace(old, 'null_count=[0];pytest_stdin_null_reads=[0];import_breadcrumbs=[]')
marker = "            path=Path(name).absolute().resolve()"
assert worker.count(marker) == 1
exception = '''            if not writing and name==os.devnull and phase[0]=='metadata_pytest':
                caller=sys._getframe(1)
                try:
                    exact_capture=(caller.f_code.co_filename==str(ROOT/'.venv/Lib/site-packages/_pytest/capture.py')
                        and caller.f_code.co_name=='__init__' and caller.f_lineno==489)
                finally:del caller
                need(exact_capture and mode=='r' and flags==32896 and pytest_stdin_null_reads[0]<4,
                    'only observed pinned Pytest stdin read of exact os.devnull')
                pytest_stdin_null_reads[0]+=1
                return
'''
worker = worker.replace(marker, exception + marker)
marker = "collection_outer_sha256=args.collection_sha256,elapsed_seconds=elapsed(),cap_seconds=cap)"
assert worker.count(marker) == 1
worker = worker.replace(marker,
    "collection_outer_sha256=args.collection_sha256,pytest_stdin_null_reads=pytest_stdin_null_reads[0],elapsed_seconds=elapsed(),cap_seconds=cap)")
outer = sources['run_batchc_metadata03.py'].decode('utf-8').replace('metadata03', 'metadata04').replace('collection03', 'collection04').replace('tests03', 'tests04').replace('mcmc03', 'mcmc04').replace('mcmt03', 'mcmt04')
packet = json.loads(sources['batchc_metadata03_packet.json'])
worker_name, outer_name = 'check_batchc_metadata04.py', 'run_batchc_metadata04.py'
new = {worker_name: worker.encode('utf-8'), outer_name: outer.encode('utf-8')}
prefix = PREP.relative_to(ROOT).as_posix() + '/'
for old_name, new_name in (('check_batchc_metadata03.py', worker_name), ('run_batchc_metadata03.py', outer_name)):
    assert packet['source_pins'].pop(prefix + old_name) == pins[old_name]
    packet['source_pins'][prefix + new_name] = hashlib.sha256(new[new_name]).hexdigest()
packet['runtime_pins'][str(capture)] = capture_sha
packet['runtime_anchor_count'] = 9
packet['pytest_capture_exception_vi'] = ('Lượt03 đo được exact os.devnull read-only, mode r/flags32896 tại pinned _pytest/capture.py:489 FDCapture.__init__. '
    'Chỉ phase metadata_pytest, tối đa4read, không cho alias hoặc mở file dự án khác. Giữ mọi guard/caps và exact single deselection.')
new['batchc_metadata04_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
for name in new:
    assert not (PREP / name).exists()
for name, raw in new.items():
    with (PREP / name).open('xb') as stream:
        stream.write(raw)
    assert (PREP / name).read_bytes() == raw
print(json.dumps(dict(status='PREPARED04_NOT_EXECUTED',
    hashes={name: hashlib.sha256(raw).hexdigest() for name, raw in new.items()},
    source_count=len(packet['source_pins']), runtime_anchor_count=9)))
