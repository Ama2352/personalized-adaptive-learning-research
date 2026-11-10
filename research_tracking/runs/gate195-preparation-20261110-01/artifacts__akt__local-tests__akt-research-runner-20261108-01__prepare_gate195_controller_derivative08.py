"""Chỉ đổi population/pointer của controller đã review; không dispatch test."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
changes = (
    ('windows_current_gate_worker03.py', 'windows_current_gate_worker04.py', (
        (b"len(build) == 183 and len(inputs['test_module_sha256']) == 85",
         b"len(build) == 195 and len(inputs['test_module_sha256']) == 91"),
        (b'ROOT-frozen183source/85module', b'ROOT-frozen195source/91module'))),
    ('windows_current_gate_outer04.py', 'windows_current_gate_outer05.py', (
        (b'windows_current_gate_worker03.py', b'windows_current_gate_worker04.py'),)),
)
inventory, diff = [], []
for old_name, new_name, substitutions in changes:
    before = (prep / old_name).read_bytes()
    after = before
    counts = []
    for old, new in substitutions:
        count = after.count(old)
        assert count > 0, old
        counts.append(count)
        after = after.replace(old, new)
    ast.parse(after, filename=new_name)
    with (prep / new_name).open('xb') as stream:
        stream.write(after)
    inventory.append(dict(source=old_name, output=new_name, exact_substitution_counts=counts,
        source_sha256=hashlib.sha256(before).hexdigest(), output_sha256=hashlib.sha256(after).hexdigest()))
    diff.extend(difflib.unified_diff(before.decode().splitlines(keepends=True),
        after.decode().splitlines(keepends=True), fromfile=old_name, tofile=new_name))
with (prep / 'gate195_controller_derivative08.patch').open('x', encoding='utf-8') as stream:
    stream.writelines(diff)
with (prep / 'gate195_controller_derivative08.json').open('x', encoding='utf-8') as stream:
    json.dump(dict(status='SOURCE_PREPARED_AST_ONLY_NOT_EXECUTED_OR_GATE_PASS', inventory=inventory,
        source_count=195, test_modules=91, collected_case_count=None, native_tests_executed=0,
        caps_unchanged=True, RAM_admission_4GiB_unchanged=True,
        next_vi='Cần collection thật trên source195 trước khi đóng packet/full Gate; không dùng lại1913IDs cũ.'),
        stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print('Prepared195/91 controller derivative, AST only; tests not launched.')
