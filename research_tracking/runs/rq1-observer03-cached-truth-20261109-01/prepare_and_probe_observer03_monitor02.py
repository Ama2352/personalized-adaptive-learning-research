"""Hoist cấu hình ctypes một lần, giữ analyzer/tests và kiểm3samples metadata."""
import ast
import hashlib
import json
from pathlib import Path
import textwrap
import time

PREP = Path(__file__).resolve().parent
ROOT = PREP.parents[3]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


old_source = PREP / 'run_observer03_cached_truth01.py'
old_raw = old_source.read_bytes()
assert sha(old_raw) == '3e28dd3f9b9ea7131797595a9c6c7875745dbb1b1f95c5cc9b6a935c462df868'
old_packet = PREP / 'observer03_cached_truth01_packet.json'
assert sha(old_packet.read_bytes()) == 'e387f9925154d464ee7d566bf88a014dd4d7a88872cc2f035d25a4ef9e01595a'
text = old_raw.decode('utf-8')
begin = text.index('def memory():\n')
instances = text.index('    status, process = Status(), Counters()\n', begin)
setup = text[begin+len('def memory():\n'):instances]
assert setup.count('class ') == 2 and setup.count('ctypes.WinDLL') == 2
new_text = text[:begin] + textwrap.dedent(setup) + '\n\ndef memory():\n' + text[instances:]
new_text = new_text.replace("PACKET = PREP / 'observer03_cached_truth01_packet.json'",
                            "PACKET = PREP / 'observer03_cached_truth02_packet.json'")
new_source = PREP / 'run_observer03_cached_truth02.py'
assert not new_source.exists()
compile(ast.parse(new_text, filename=str(new_source)), str(new_source), 'exec')
new_source.write_bytes(new_text.encode('utf-8'))

packet = json.loads(old_packet.read_bytes())
old_relative = old_source.relative_to(ROOT).as_posix()
new_relative = new_source.relative_to(ROOT).as_posix()
assert packet['source_pins'].pop(old_relative) == sha(old_raw)
packet['source_pins'][new_relative] = sha(new_source.read_bytes())
for config in packet['phases'].values():
    config['child'] = config['child'].replace('01', '02')
    config['owned'] = config['owned'].replace('01', '02')
    assert not (PREP / config['child']).exists() and not (PREP / config['owned']).exists()
packet['resource_fix02'] = dict(
    old_source_sha256=sha(old_raw), old_packet_sha256=sha(old_packet.read_bytes()),
    reason='Status/Counters, pointer prototypes và WinDLL được cấu hình một lần thay vì mỗi lần đo.',
    analyzer_or_test_change=False, resource_cap_change=False,
)
new_packet = PREP / 'observer03_cached_truth02_packet.json'
assert not new_packet.exists()
new_packet.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert all(sha((ROOT / relative).read_bytes()) == digest for relative, digest in packet['source_pins'].items())

# Module chạy với __name__ riêng. CLI/worker/outer và mọi input khoa học không chạy.
namespace = dict(__name__='observer03_monitor_metadata_probe', __file__=str(new_source))
start = time.perf_counter()
exec(compile(new_text, str(new_source), 'exec'), namespace)
ctypes = namespace['ctypes']


def identities():
    return tuple(id(value) for value in (
        namespace['Status'], namespace['Counters'], ctypes.POINTER(namespace['Status']),
        ctypes.POINTER(namespace['Counters']), namespace['kernel'], namespace['psapi'],
        namespace['kernel'].GlobalMemoryStatusEx, namespace['psapi'].GetProcessMemoryInfo,
    ))


initial_ids = identities()
initial_cache_keys = frozenset(ctypes._pointer_type_cache)
sizes = [len(initial_cache_keys)]
samples = []
for _ in range(3):
    assert time.perf_counter() - start < 1
    samples.append(namespace['memory']())
    assert identities() == initial_ids and frozenset(ctypes._pointer_type_cache) == initial_cache_keys
    sizes.append(len(ctypes._pointer_type_cache))
elapsed = time.perf_counter() - start
assert elapsed < 1 and len(set(sizes)) == 1
assert sha(old_source.read_bytes()) == '3e28dd3f9b9ea7131797595a9c6c7875745dbb1b1f95c5cc9b6a935c462df868'
result = dict(status='CONFIRMED_STABLE_TYPES_DLLS_AND_PROTOTYPES_THREE_METADATA_CALLS',
              controller_sha256=sha(new_source.read_bytes()), packet_sha256=sha(new_packet.read_bytes()),
              pointer_cache_sizes=sizes, object_identities_stable=True, samples=samples,
              elapsed_seconds=elapsed, model_calls=0, scientific_data_files_read=0,
              analyzer_sha256=packet['source_pins'][packet['analyzer']],
              tests_sha256=packet['source_pins'][packet['tests']], resource_caps=packet['resource_caps'])
with (PREP / 'observer03_monitor_type_cache02_result.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({key: result[key] for key in ('status', 'controller_sha256', 'packet_sha256', 'pointer_cache_sizes', 'elapsed_seconds')}))
