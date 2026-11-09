"""Tạo harness05 dùng prefix bytecode mới thuộc run, giữ assertion rewriting."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
old_pins = {
    'check_batchc_metadata04.py': 'cfd324306a68291a871540a2fd277aa4876cabe017d25baffb2883b73cf21398',
    'run_batchc_metadata04.py': '8048ee0fac7a9aa871ba8edd52ba6a0bbb162cf5fa36e7bc6dd73c05782ebadc',
    'batchc_metadata04_packet.json': 'cab65999ac85c3ae8be25a372e985dbff5c8d5d6338282a1ef343c73594b4d75',
}
sources = {}
for name, pin in old_pins.items():
    raw = (PREP / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin
    sources[name] = raw
rejected = json.loads((PREP / 'batchc-metadata-collection04/result.json').read_bytes())
assert rejected['pytest_stdin_null_reads'] == 1 and rejected['test_body_entries'] == 0
assert len(rejected['denied']) == 7
assert all(row['details']['raw_path'].endswith('-pytest-9.1.1.pyc') for row in rejected['denied'][:4])
assert all(row['details']['raw_path'] == '<unknown>' for row in rejected['denied'][4:])
rewrite = ROOT / '.venv/Lib/site-packages/_pytest/assertion/rewrite.py'
rewrite_sha = hashlib.sha256(rewrite.read_bytes()).hexdigest()
worker = sources['check_batchc_metadata04.py'].decode('utf-8')
outer = sources['run_batchc_metadata04.py'].decode('utf-8')
for old, new in (('metadata04', 'metadata05'), ('collection04', 'collection05'),
                 ('tests04', 'tests05'), ('mcmc04', 'mcmc05'), ('mcmt04', 'mcmt05')):
    worker, outer = worker.replace(old, new), outer.replace(old, new)
old = 'sys_before=(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv))'
new = (old[:-1] + ',sys.pycache_prefix)\n'
    "    owned_pycache_prefix=str(temporary/'fresh-bytecode')\n"
    '    need(not Path(owned_pycache_prefix).exists(),\'fresh owned bytecode prefix\')\n'
    '    sys.pycache_prefix=owned_pycache_prefix')
assert worker.count(old) == 1
worker = worker.replace(old, new)
old = 'restored=restored and sys_before==(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv))'
assert worker.count(old) == 1
worker = worker.replace(old,
    'sys.pycache_prefix=sys_before[4]\n'
    '        restored=restored and sys_before==(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv),sys.pycache_prefix)')
old = 'collection_outer_sha256=args.collection_sha256,pytest_stdin_null_reads=pytest_stdin_null_reads[0],elapsed_seconds=elapsed(),cap_seconds=cap)'
assert worker.count(old) == 1
worker = worker.replace(old,
    'collection_outer_sha256=args.collection_sha256,pytest_stdin_null_reads=pytest_stdin_null_reads[0],\n'
    '            owned_pycache_prefix_used=True,owned_pycache_prefix=owned_pycache_prefix,\n'
    '            elapsed_seconds=elapsed(),cap_seconds=cap)')
old = "need(result['deselected_nodeids']==[packet['deselect']]"
assert outer.count(old) == 1
outer = outer.replace(old,
    "need(result['owned_pycache_prefix_used'] is True,'fresh owned cache prefix used and restored')\n"
    '        ' + old)
packet = json.loads(sources['batchc_metadata04_packet.json'])
new_files = {'check_batchc_metadata05.py': worker.encode(), 'run_batchc_metadata05.py': outer.encode()}
prefix = PREP.relative_to(ROOT).as_posix() + '/'
for old, new in (('check_batchc_metadata04.py', 'check_batchc_metadata05.py'),
                 ('run_batchc_metadata04.py', 'run_batchc_metadata05.py')):
    assert packet['source_pins'].pop(prefix + old) == old_pins[old]
    packet['source_pins'][prefix + new] = hashlib.sha256(new_files[new]).hexdigest()
packet['runtime_pins'][str(rewrite)] = rewrite_sha
packet['runtime_anchor_count'] = 10
packet['bytecode_scope_vi'] = ('Lượt04 từ chối đọc Pytest PYC tại cache cũ. Lượt05 dùng sys.pycache_prefix mới trong runtime-temp của run, '
    'đặt trước importPytest và phục hồi cuối lượt. Giữ assertion rewriting và dont_write_bytecode=True. '
    'Không xóa cache, không cho thêm cache ngoài vùng owned hoặc sửa source/test population.')
new_files['batchc_metadata05_packet.json'] = (json.dumps(packet, ensure_ascii=False, indent=2) + '\n').encode()
for name in new_files:
    assert not (PREP / name).exists()
for name, raw in new_files.items():
    compile(raw, str(PREP / name), 'exec') if name.endswith('.py') else json.loads(raw)
for name, raw in new_files.items():
    with (PREP / name).open('xb') as stream:
        stream.write(raw)
    assert (PREP / name).read_bytes() == raw
print(json.dumps(dict(status='PREPARED05_NOT_EXECUTED', source_count=len(packet['source_pins']),
    runtime_anchor_count=10, hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in new_files.items()})))
