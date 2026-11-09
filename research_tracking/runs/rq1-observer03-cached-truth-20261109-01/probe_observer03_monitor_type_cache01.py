"""Ba lời gọi metadata xác nhận giữ lại ctypes types, không đọc dữ liệu nghiên cứu."""
import time
START = time.perf_counter()
import ast
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path

PREP = Path(__file__).resolve().parent
source = PREP / 'run_observer03_cached_truth01.py'
raw = source.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '3e28dd3f9b9ea7131797595a9c6c7875745dbb1b1f95c5cc9b6a935c462df868'
tree = ast.parse(raw)
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('need', 'memory')]
assert len(functions) == 2
namespace = dict(ctypes=ctypes, wintypes=wintypes)
exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), namespace)
cache = ctypes._pointer_type_cache
sizes = [len(cache)]
samples = []
for _ in range(3):
    assert time.perf_counter() - START < 1
    samples.append(namespace['memory']())
    sizes.append(len(cache))
assert [b-a for a, b in zip(sizes, sizes[1:])] == [2, 2, 2]
elapsed = time.perf_counter() - START
assert elapsed < 1
result = dict(status='CONFIRMED_TWO_RETAINED_POINTER_TYPES_PER_MEMORY_CALL',
              controller_sha256=hashlib.sha256(raw).hexdigest(), calls=3,
              pointer_cache_sizes=sizes, samples=samples, elapsed_seconds=elapsed,
              actual_model_calls=0, scientific_data_files_read=0,
              limitation='Xác nhận cơ chế giữ types. Chưa quy từng byte peak của lượt cached vào nguyên nhân này.')
with (PREP / 'observer03_monitor_type_cache01_result.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status=result['status'], sizes=sizes, elapsed_seconds=elapsed)))
