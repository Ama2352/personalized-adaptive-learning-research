"""Giữ actual stdout ABI; không dùng preview hoặc biến suy đoán thành observed."""
import hashlib
import json
from pathlib import Path
work = Path(__file__).resolve().parent
private = work.parents[1] / 'private/colab-bridge/session-a67c8207b6224b9398ad00cfa0876435'
old = set(json.loads((work/'actual-abi-probe02-before-run.json').read_bytes()))
found = [p for p in private.glob('result-*.json') if p.name not in old]
assert len(found) == 1
raw = found[0].read_bytes()
rpc = json.loads(raw)
assert rpc.get('is_error') is False
outputs = (rpc.get('structured_content') or rpc['data'])['outputs']
assert not any(row.get('output_type') == 'error' for row in outputs)
stdout = ''.join(''.join(row['text']) if isinstance(row['text'],list) else row['text']
    for row in outputs if row.get('output_type') == 'stream' and row.get('name') == 'stdout')
result = json.loads(stdout)
assert result['status'] == 'ACTUAL_STDLIB_ABI_ONLY_NOT_GPU_READY'
assert result['host_abi'] == result['target_abi']
assert result['model_imports'] == result['gpu_queries'] == result['installs'] == 0
with (work/'actual-abi-probe02-result.json').open('x', encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
with (work/'actual-abi-probe02-provenance.json').open('x', encoding='utf-8') as stream:
    json.dump(dict(rpc_sha256=hashlib.sha256(raw).hexdigest(),
        cell_source_sha256=hashlib.sha256((work/'actual-abi-probe02-cell.py').read_bytes()).hexdigest(),
        actual_stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        scope='Fresh stdlib ABI CPU-host/target -I -S -B; source01 added but NOT run. No package/venv/source changes.'),stream,indent=2)
print(json.dumps(result,ensure_ascii=False))
