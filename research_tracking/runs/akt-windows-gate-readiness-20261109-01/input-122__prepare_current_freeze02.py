"""Chốt đúng hai source fix hiện hành; identity freeze, chưa là Gate approval."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
old = PREP/'gate_collection01_packet.ROOT.json'
assert hashlib.sha256(old.read_bytes()).hexdigest() == 'bacc6e49d14d244396b7be03cf68c62daefa8c14adf056b1f0c5cde8b8f1ed90'
packet = json.loads(old.read_bytes())
spec = importlib.util.spec_from_file_location('current_basetemp_fixed_refresh',ROOT/'scripts/akt/refresh_gate2.py')
module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
current = module.gate2_build_hashes()
assert set(current) == set(packet['gate_build_hashes']) and len(current) == 154
changed = {n:h for n,h in current.items() if h != packet['gate_build_hashes'][n]}
assert changed == {
    'scripts/akt/refresh_gate2.py':'8cd02e93250301f3c2e0e35b98ca495a4a79faebe237edbd837d923df3a93dcc',
    'tests/akt/test_gate2_refresh.py':'e3911ec7a6cf0cf7dfd87159aa1861a21e18b80fef42044a5b4d09aa1d26e108',
}
packet['gate_build_hashes'] = current
packet['test_module_sha256'] = {name:current[name] for name in packet['test_module_sha256']}
assert packet['module_groups'] == [dict(name=n,modules=m) for n,m in module.test_partition(ROOT)]
assert 'torch' not in sys.modules
packet['root_freeze_reference'] = 'ROOT_REVIEWED_BASETEMP_FIX_TWO_UNCOMMITTED_SOURCES_IDENTITY_ONLY_20261109'
out = PREP/'gate_collection02_packet.ROOT.json'
with out.open('x',encoding='utf-8') as stream:
    json.dump(packet,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(status='CURRENT_SOURCE_IDENTITY_FROZEN_NOT_GATE_APPROVAL',sources=len(current),changed=changed,
                      path=out.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
