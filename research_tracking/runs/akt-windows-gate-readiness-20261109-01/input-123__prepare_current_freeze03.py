"""ROOT-only scratchlayout identity freeze; không Gate approval/dispatch."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert sys.executable.lower() == str(ROOT/'.venv/Scripts/python.exe').lower()
assert Path(sys.prefix).resolve() == ROOT/'.venv'
old = PREP/'gate_collection02_packet.ROOT.json'
raw = old.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '04a4b8c0a0b860973b79e09f60e64515ba204be7ee3c15fe173bb526219d6192'
packet = json.loads(raw)
expected = {
    'scripts/akt/refresh_gate2.py':'9608ddfe1450b2d78699d5ec95d26b8cd65d4439fcc7bda209f698b2e4a7f9ef',
    'tests/akt/test_gate2_refresh.py':'255c07a3a1af2d458c8586bd206a3151baadeae76d1fa0a2ce3362409da8d5df',
}
assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in expected.items())
spec = importlib.util.spec_from_file_location('current_scratch_layout_fixed_refresh',ROOT/'scripts/akt/refresh_gate2.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
current = module.gate2_build_hashes()
assert set(current) == set(packet['gate_build_hashes']) and len(current) == 154
changed = {name:digest for name,digest in current.items() if digest != packet['gate_build_hashes'][name]}
assert changed == expected
assert len(packet['test_module_sha256']) == 69
assert packet['module_groups'] == [dict(name=name,modules=paths) for name,paths in module.test_partition(ROOT)]
packet['gate_build_hashes'] = current
packet['test_module_sha256'] = {name:current[name] for name in packet['test_module_sha256']}
packet['root_freeze_reference'] = 'ROOT_REVIEWED_SCRATCH_LAYOUT_TWO_UNCOMMITTED_SOURCES_IDENTITY_ONLY_20261109'
assert 'torch' not in sys.modules
out = PREP/'gate_collection03_packet.ROOT.json'
with out.open('x',encoding='utf-8') as stream:
    json.dump(packet,stream,ensure_ascii=False,indent=2,allow_nan=False)
    stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
assert module.gate2_build_hashes() == current and old.read_bytes() == raw
assert [dict(name=name,modules=paths) for name,paths in module.test_partition(ROOT)] == packet['module_groups']
assert json.loads(out.read_bytes()) == packet and 'torch' not in sys.modules
print(json.dumps(dict(status='CURRENT_SOURCE_IDENTITY_FROZEN_NOT_GATE_APPROVAL',sources=len(current),modules=69,
    changed=changed,parent_packet_sha256=hashlib.sha256(raw).hexdigest(),
    path=out.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
