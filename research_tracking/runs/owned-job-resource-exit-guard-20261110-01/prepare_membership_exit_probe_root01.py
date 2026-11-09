"""Dẫn xuất probe đã đạt, thêm đúng phép đọc Job sau khi handle báo kết thúc."""
from pathlib import Path
import ast
import hashlib
import json

p = Path(__file__).resolve().parent
root = p.parents[3]
mapping = {'check_a1_job_resource_probe02.py': 'check_a1_membership_exit_probe_root01.py',
           'run_a1_job_resource_probe02.py': 'run_a1_membership_exit_probe_root01.py',
           'a1_job_resource_probe02_packet.json': 'a1_membership_exit_probe_root01_packet.json',
           'a1-job-resource-probe02': 'a1-membership-exit-probe-root01'}
hashes = {}
for old, new in list(mapping.items())[:2]:
    text = (p / old).read_text(encoding='utf-8')
    for a, b in mapping.items():
        text = text.replace(a, b)
    if old.startswith('check_'):
        needle = '                after_token=helper(api,handle,child.pid)'
        assert text.count(needle) == 1
        insertion = '''                membership_after_exit = None
                try:
                    membership_after_exit = dict(returned=api.contains(handle,job_handle),error=None)
                except BaseException as caught:
                    membership_after_exit = dict(returned=None,error=dict(type=type(caught).__name__,
                        message=str(caught),winerror=getattr(caught,'winerror',None),
                        traceback=traceback.format_exc(limit=8),exit_already_proven=True))
'''
        text = text.replace(needle, insertion + needle)
        needle = "                records.append(dict(pid=child.pid,creation=before_token,old_after_exit_error=old_error,"
        assert text.count(needle) == 1
        text = text.replace(needle, needle + '\n                    membership_after_exit=membership_after_exit,')
    ast.parse(text)
    target = p / new
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
    hashes[target.relative_to(root).as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
packet = json.loads((p / 'a1_job_resource_probe02_packet.json').read_bytes())
for old in list(mapping)[:2]:
    del packet['source_pins'][(p / old).relative_to(root).as_posix()]
packet['source_pins'].update(hashes)
packet['scope_vi'] = 'Bổ sung IsProcessInJob sau exact handle signaled exit, không khẳng định nguyên nhân khi chưa quan sát.'
target = p / mapping['a1_job_resource_probe02_packet.json']
with target.open('x', encoding='utf-8') as stream:
    json.dump(packet, stream, ensure_ascii=False, indent=2)
hashes[target.relative_to(root).as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
print(json.dumps(hashes))
