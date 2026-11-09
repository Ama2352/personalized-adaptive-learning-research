"""Đọc ba mẫu RAM trước launcher CPU, không mở model."""
from pathlib import Path
import json
import time
import psutil

samples = []
for _ in range(3):
    samples.append(int(psutil.virtual_memory().available))
    time.sleep(.2)
limit = 4 * 2**30 + 128 * 2**20
result = {'available_ram_samples_bytes': samples, 'required_available_bytes': limit,
          'canonical_preallocation_floor_bytes': 4 * 2**30, 'extra_headroom_bytes': 128 * 2**20,
          'ready_for_root_launch_review': min(samples) >= limit, 'model_calls': 0}
path = Path(__file__).with_name('a1-light-admission04.json')
with path.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(result))
